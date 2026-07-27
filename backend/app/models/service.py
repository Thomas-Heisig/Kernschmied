# F:\Kernschmied\backend\app\models\service.py

"""
Zentrale Anwendungsschicht des Kernschmied-Modellsystems.

Der ModelService verbindet:

- validierte model.json-Manifeste,
- die kontrollierte ModelProviderRegistry,
- serverseitige Secret-Auflösung,
- Dependency Injection,
- den ModelLifecycleManager,
- Autorisierung,
- Modellauflösung,
- Generierung und Streaming.

Architekturregeln:

1. Discovery bedeutet niemals automatische Freigabe.
2. Nur registrierte Provider dürfen instanziiert werden.
3. Manifeste dürfen keine Python-Importpfade bestimmen.
4. Secrets werden nicht aus provider.config gelesen.
5. Jede Benutzeraktion kann serverseitig autorisiert werden.
6. Providerfehler werden in stabile Modellfehler übersetzt.
7. Der Service ist kein globales Singleton.
8. Runtime-Aktivierung ersetzt keine persistente Konfiguration.
9. Provider werden erst bei tatsächlicher Verwendung erzeugt.
10. Das Herunterfahren eines Providers darf andere Provider nicht
    blockieren.

Typischer Ablauf:

    discover_model_manifest_paths()
        ↓
    load_model_manifest()
        ↓
    ModelService.register_manifest()
        ↓
    ModelLifecycleDefinition
        ↓
    ModelLifecycleManager
        ↓
    generate() / stream()
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, Protocol, TypeAlias, runtime_checkable

from app.contracts.model_backend import (
    BaseModelBackend,
    GenerationRequest,
    ModelInfo,
    StreamEvent,
)
from app.models.errors import (
    DuplicateModelManifestError,
    DuplicateModelRegistrationError,
    InvalidModelProviderConfigurationError,
    ModelAccessDeniedError,
    ModelCapabilityNotSupportedError,
    ModelDisabledError,
    ModelError,
    ModelNotRegisteredError,
    ModelProviderCreationError,
    ModelProviderDependencyError,
    ModelUnavailableError,
    translate_provider_error,
)
from app.models.lifecycle import (
    ModelLifecycleDefinition,
    ModelLifecycleManager,
    ModelLifecyclePolicy,
    ModelLifecycleSnapshot,
)
from app.models.manifest import (
    LoadedModelManifest,
    ModelManifest,
    ModelManifestCapability,
    ModelSecretReference,
    discover_model_manifest_paths,
    load_model_manifest,
)
from app.models.providers import ModelProviderRegistry


logger = logging.getLogger(__name__)


DEFAULT_DISCOVERY_RECURSIVE: Final[bool] = True
DEFAULT_DISCOVERY_FOLLOW_SYMLINKS: Final[bool] = False


# ============================================================
# Typen und Protokolle
# ============================================================


class ModelServiceAction(StrEnum):
    """
    Autorisierbare Aktionen des ModelService.
    """

    LIST = "list"
    READ = "read"
    USE = "use"
    STREAM = "stream"
    REGISTER = "register"
    UNREGISTER = "unregister"
    ENABLE = "enable"
    DISABLE = "disable"
    RELOAD = "reload"
    LOAD = "load"
    UNLOAD = "unload"
    SHUTDOWN = "shutdown"


class ModelRegistrationStatus(StrEnum):
    """
    Ergebnisstatus eines Registrierungsversuchs.
    """

    REGISTERED = "registered"
    REPLACED = "replaced"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ModelAccessContext:
    """
    Kontext für serverseitige Autorisierungsentscheidungen.

    Der Service interpretiert Rollen oder Berechtigungen nicht selbst.
    Diese Entscheidung bleibt bei der injizierten Authorizer-Komponente.
    """

    subject_id: str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None

    roles: frozenset[str] = field(default_factory=lambda: frozenset())
    
    permissions: frozenset[str] = field(default_factory=lambda: frozenset())

    attributes: dict[str, Any] = field(default_factory=lambda: {})

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "roles",
            frozenset(
                str(role).strip()
                for role in self.roles
                if str(role).strip()
            ),
        )
        object.__setattr__(
            self,
            "permissions",
            frozenset(
                str(permission).strip()
                for permission in self.permissions
                if str(permission).strip()
            ),
        )
        object.__setattr__(
            self,
            "attributes",
            dict(self.attributes),
        )


@dataclass(frozen=True, slots=True)
class ModelAuthorizationRequest:
    """
    Vollständige Anfrage an den ModelAuthorizer.
    """

    action: ModelServiceAction
    model_id: str | None
    provider_type: str | None
    context: ModelAccessContext
    metadata: dict[str, Any] = field(
        default_factory=lambda: {},
    )


@runtime_checkable
class ModelAuthorizer(Protocol):
    """
    Schnittstelle für serverseitige Modellautorisierung.
    """

    def authorize(
        self,
        request: ModelAuthorizationRequest,
    ) -> bool | Awaitable[bool]:
        """
        Gibt True zurück, wenn die Aktion erlaubt ist.
        """
        return True  # Protokoll-Implementierung liefert immer True


@dataclass(frozen=True, slots=True)
class ModelSecretResolutionContext:
    """
    Kontext für die Auflösung einer Secret-Referenz.
    """

    model_id: str
    provider_type: str
    manifest_path: Path
    secret_name: str
    access_context: ModelAccessContext | None = None


@runtime_checkable
class ModelSecretResolver(Protocol):
    """
    Löst eine Manifest-Secret-Referenz kontrolliert auf.
    """

    def resolve(
        self,
        reference: ModelSecretReference,
        context: ModelSecretResolutionContext,
    ) -> Any | Awaitable[Any]:
        """
        Liefert den tatsächlichen Secret-Wert.

        Der Wert darf nicht protokolliert oder in Diagnoseobjekten
        gespeichert werden.
        """


DependencyProvider: TypeAlias = Callable[
    [
        LoadedModelManifest,
        ModelAccessContext | None,
    ],
    Mapping[str, Any]
    | Awaitable[Mapping[str, Any]],
]


@dataclass(frozen=True, slots=True)
class ModelRegistrationResult:
    """
    Ergebnis eines einzelnen Registrierungsversuchs.
    """

    model_id: str | None
    manifest_path: Path
    status: ModelRegistrationStatus

    provider_type: str | None = None
    message: str | None = None
    error_type: str | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ModelDiscoveryReport:
    """
    Zusammenfassung einer Manifest-Discovery.
    """

    discovered_paths: tuple[Path, ...]
    results: tuple[ModelRegistrationResult, ...]

    @property
    def registered_count(self) -> int:
        return sum(
            result.status
            in {
                ModelRegistrationStatus.REGISTERED,
                ModelRegistrationStatus.REPLACED,
            }
            for result in self.results
        )

    @property
    def failed_count(self) -> int:
        return sum(
            result.status == ModelRegistrationStatus.FAILED
            for result in self.results
        )

    @property
    def skipped_count(self) -> int:
        return sum(
            result.status == ModelRegistrationStatus.SKIPPED
            for result in self.results
        )


@dataclass(frozen=True, slots=True)
class ModelServiceInfo:
    """
    Sichere kombinierte Diagnoseansicht eines registrierten Modells.
    """

    model_id: str
    display_name: str
    description: str | None

    provider_type: str
    manifest_enabled: bool
    runtime_enabled: bool
    effectively_enabled: bool

    status: str
    runtime: str

    capabilities: tuple[str, ...]
    tags: tuple[str, ...]

    manifest_path: Path
    lifecycle: ModelLifecycleSnapshot | None

    metadata: Mapping[str, Any]


@dataclass(slots=True)
class _ModelServiceRecord:
    """
    Interner veränderbarer Service-Eintrag.
    """

    loaded_manifest: LoadedModelManifest
    runtime_enabled: bool

    registration_index: int
    registered_at_loop_time: float

    last_access_context: ModelAccessContext | None = None

    @property
    def manifest(self) -> ModelManifest:
        return self.loaded_manifest.manifest

    @property
    def model_id(self) -> str:
        return self.manifest.id

    @property
    def provider_type(self) -> str:
        return self.manifest.provider.type

    @property
    def effectively_enabled(self) -> bool:
        return (
            self.manifest.is_enabled
            and self.runtime_enabled
        )


# ============================================================
# Standardimplementierungen
# ============================================================


class AllowAllModelAuthorizer:
    """
    Authorizer für lokale Entwicklung.

    Dieses Verhalten sollte nicht für Internet- oder Intranetprofile
    verwendet werden, sofern dort Autorisierung vorgeschrieben ist.
    """

    def authorize(
        self,
        request: ModelAuthorizationRequest,
    ) -> bool:
        del request
        return True


class NullModelSecretResolver:
    """
    Resolver, der keine Secrets bereitstellt.

    Optionale Secret-Referenzen liefern None. Erforderliche Referenzen
    erzeugen einen ModelProviderDependencyError.
    """

    def resolve(
        self,
        reference: ModelSecretReference,
        context: ModelSecretResolutionContext,
    ) -> Any:
        if reference.required:
            raise ModelProviderDependencyError(
                provider_type=context.provider_type,
                model_id=context.model_id,
                dependency=(
                    f"Secret-Resolver für "
                    f"'{context.secret_name}'"
                ),
            )

        return None


# ============================================================
# ModelService
# ============================================================


class ModelService:
    """
    Zentrale Anwendungsschicht für registrierte Modelle.

    Der Service besitzt keine globale Instanz. Er sollte im
    Application-Lifespan erzeugt und anschließend per Dependency
    Injection weitergegeben werden.
    """

    def __init__(
        self,
        *,
        provider_registry: ModelProviderRegistry,
        lifecycle: ModelLifecycleManager,
        secret_resolver: ModelSecretResolver | None = None,
        authorizer: ModelAuthorizer | None = None,
        common_dependencies: Mapping[str, Any] | None = None,
        dependency_provider: DependencyProvider | None = None,
        allowed_manifest_directories: Sequence[str | Path] = (),
    ) -> None:
        self._provider_registry = provider_registry
        self._lifecycle = lifecycle

        self._secret_resolver = (
            secret_resolver
            or NullModelSecretResolver()
        )
        self._authorizer = (
            authorizer
            or AllowAllModelAuthorizer()
        )

        self._common_dependencies = dict(
            common_dependencies or {},
        )
        self._dependency_provider = dependency_provider

        self._allowed_manifest_directories = tuple(
            Path(directory).expanduser().resolve()
            for directory in allowed_manifest_directories
        )

        self._records: dict[
            str,
            _ModelServiceRecord,
        ] = {}

        self._registry_lock = asyncio.Lock()
        self._registration_counter = 0

        self._started = False
        self._shutdown_requested = False

    # ========================================================
    # Eigenschaften
    # ========================================================

    @property
    def provider_registry(self) -> ModelProviderRegistry:
        return self._provider_registry

    @property
    def lifecycle(self) -> ModelLifecycleManager:
        return self._lifecycle

    @property
    def count(self) -> int:
        return len(self._records)

    @property
    def started(self) -> bool:
        return self._started

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    # ========================================================
    # Start und Shutdown
    # ========================================================

    async def start(self) -> None:
        """
        Startet den zugehörigen ModelLifecycleManager.
        """

        if self._shutdown_requested:
            raise RuntimeError(
                "Ein beendeter ModelService kann nicht erneut "
                "gestartet werden.",
            )

        if self._started:
            return

        await self._lifecycle.start()
        self._started = True

    async def shutdown(
        self,
        *,
        raise_on_error: bool = False,
    ) -> tuple[ModelError, ...]:
        """
        Beendet alle verwalteten Backends.

        Fehler einzelner Provider verhindern standardmäßig nicht den
        Shutdown der übrigen Provider.
        """

        if self._shutdown_requested:
            return ()

        self._shutdown_requested = True

        errors = await self._lifecycle.shutdown(
            raise_on_error=raise_on_error,
        )

        self._started = False

        return errors

    # ========================================================
    # Registrierung
    # ========================================================

    async def register_manifest(
        self,
        loaded_manifest: LoadedModelManifest,
        *,
        replace: bool = False,
        runtime_enabled: bool | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> ModelRegistrationResult:
        """
        Registriert ein validiertes Manifest.

        Die Registrierung:

        - prüft die serverseitige Provider-Freigabeliste,
        - erzeugt noch keinen Provider,
        - löst noch keine Secrets auf,
        - öffnet keine Netzwerkverbindungen,
        - lädt kein Modell.
        """

        manifest = loaded_manifest.manifest
        model_id = manifest.id
        provider_type = manifest.provider.type

        await self._authorize(
            action=ModelServiceAction.REGISTER,
            model_id=model_id,
            provider_type=provider_type,
            context=access_context,
            metadata={
                "manifest_path": str(
                    loaded_manifest.manifest_path,
                ),
            },
        )

        if self._shutdown_requested:
            raise ModelUnavailableError(
                model_id,
                provider_type=provider_type,
                reason=(
                    "Der ModelService wurde bereits beendet."
                ),
            )

        if not self._provider_registry.has(
            provider_type,
        ):
            raise InvalidModelProviderConfigurationError(
                provider_type=provider_type,
                model_id=model_id,
                field="provider.type",
                reason=(
                    "Der Provider ist nicht in der serverseitigen "
                    "Freigabeliste registriert."
                ),
                request_id=(
                    access_context.request_id
                    if access_context
                    else None
                ),
            )

        existing_record: _ModelServiceRecord | None

        async with self._registry_lock:
            existing_record = self._records.get(
                model_id,
            )

        if existing_record is not None and not replace:
            raise DuplicateModelRegistrationError(
                model_id,
                request_id=(
                    access_context.request_id
                    if access_context
                    else None
                ),
            )

        if existing_record is not None:
            await self._replace_existing_record(
                existing_record,
            )

        effective_runtime_enabled = (
            runtime_enabled
            if runtime_enabled is not None
            else manifest.is_enabled
        )

        loop = asyncio.get_running_loop()

        async with self._registry_lock:
            self._registration_counter += 1

            record = _ModelServiceRecord(
                loaded_manifest=loaded_manifest,
                runtime_enabled=effective_runtime_enabled,
                registration_index=self._registration_counter,
                registered_at_loop_time=loop.time(),
                last_access_context=access_context,
            )

            self._records[model_id] = record

        lifecycle_definition = self._create_lifecycle_definition(
            record,
        )

        try:
            await self._lifecycle.register(
                lifecycle_definition,
            )
        except Exception:
            async with self._registry_lock:
                current_record = self._records.get(
                    model_id,
                )

                if current_record is record:
                    del self._records[model_id]

            raise

        return ModelRegistrationResult(
            model_id=model_id,
            manifest_path=loaded_manifest.manifest_path,
            provider_type=provider_type,
            status=(
                ModelRegistrationStatus.REPLACED
                if existing_record is not None
                else ModelRegistrationStatus.REGISTERED
            ),
        )

    async def register_manifest_file(
        self,
        manifest_path: str | Path,
        *,
        replace: bool = False,
        runtime_enabled: bool | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> ModelRegistrationResult:
        """
        Lädt und registriert eine einzelne model.json-Datei.
        """

        loaded_manifest = load_model_manifest(
            manifest_path,
            allowed_base_directories=(
                self._allowed_manifest_directories
                or None
            ),
        )

        return await self.register_manifest(
            loaded_manifest,
            replace=replace,
            runtime_enabled=runtime_enabled,
            access_context=access_context,
        )

    async def discover_and_register(
        self,
        base_directories: Sequence[str | Path] | None = None,
        *,
        recursive: bool = DEFAULT_DISCOVERY_RECURSIVE,
        follow_symlinks: bool = DEFAULT_DISCOVERY_FOLLOW_SYMLINKS,
        replace: bool = False,
        continue_on_error: bool = True,
        access_context: ModelAccessContext | None = None,
    ) -> ModelDiscoveryReport:
        """
        Findet, validiert und registriert Manifeste isoliert.

        Discovery allein erteilt keine Benutzerberechtigung. Es werden nur
        Provider akzeptiert, die bereits in der festen Provider-Registry
        freigegeben sind.
        """

        directories = tuple(
            Path(directory).expanduser().resolve()
            for directory in (
                base_directories
                if base_directories is not None
                else self._allowed_manifest_directories
            )
        )

        paths = discover_model_manifest_paths(
            directories,
            recursive=recursive,
            follow_symlinks=follow_symlinks,
        )

        results: list[ModelRegistrationResult] = []
        model_paths: dict[str, list[Path]] = {}

        for path in paths:
            try:
                loaded_manifest = load_model_manifest(
                    path,
                    allowed_base_directories=directories,
                )

                model_paths.setdefault(
                    loaded_manifest.model_id,
                    [],
                ).append(path)

                duplicate_paths = model_paths[
                    loaded_manifest.model_id
                ]

                if len(duplicate_paths) > 1 and not replace:
                    raise DuplicateModelManifestError(
                        loaded_manifest.model_id,
                        manifest_paths=[
                            str(item)
                            for item in duplicate_paths
                        ],
                        request_id=(
                            access_context.request_id
                            if access_context
                            else None
                        ),
                    )

                result = await self.register_manifest(
                    loaded_manifest,
                    replace=replace,
                    access_context=access_context,
                )

                results.append(result)

            except Exception as exc:
                result = self._registration_error_result(
                    path=path,
                    error=exc,
                )
                results.append(result)

                logger.warning(
                    "Model manifest registration failed",
                    extra={
                        "manifest_path": str(path),
                        "error_type": (
                            exc.__class__.__name__
                        ),
                        "error_code": getattr(
                            exc,
                            "code",
                            None,
                        ),
                    },
                    exc_info=exc,
                )

                if not continue_on_error:
                    raise

        return ModelDiscoveryReport(
            discovered_paths=paths,
            results=tuple(results),
        )

    async def unregister_model(
        self,
        model_id: str,
        *,
        access_context: ModelAccessContext | None = None,
    ) -> bool:
        """
        Entfernt ein Modell aus Service und Lifecycle.
        """

        record = self._get_record(
            model_id,
        )

        await self._authorize(
            action=ModelServiceAction.UNREGISTER,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        removed = await self._lifecycle.unregister(
            record.model_id,
            shutdown_backend=True,
        )

        async with self._registry_lock:
            self._records.pop(
                record.model_id,
                None,
            )

        return removed

    async def reload_manifest(
        self,
        model_id: str,
        *,
        access_context: ModelAccessContext | None = None,
    ) -> ModelRegistrationResult:
        """
        Liest das bestehende Manifest erneut ein und ersetzt die
        Registrierung kontrolliert.
        """

        record = self._get_record(
            model_id,
        )

        await self._authorize(
            action=ModelServiceAction.RELOAD,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        loaded_manifest = load_model_manifest(
            record.loaded_manifest.manifest_path,
            allowed_base_directories=(
                self._allowed_manifest_directories
                or None
            ),
        )

        return await self.register_manifest(
            loaded_manifest,
            replace=True,
            runtime_enabled=record.runtime_enabled,
            access_context=access_context,
        )

    async def _replace_existing_record(
        self,
        record: _ModelServiceRecord,
    ) -> None:
        try:
            await self._lifecycle.unregister(
                record.model_id,
                shutdown_backend=True,
            )
        finally:
            async with self._registry_lock:
                current = self._records.get(
                    record.model_id,
                )

                if current is record:
                    del self._records[
                        record.model_id
                    ]

    # ========================================================
    # Runtime-Aktivierung
    # ========================================================

    async def enable_model(
        self,
        model_id: str,
        *,
        access_context: ModelAccessContext | None = None,
    ) -> None:
        """
        Aktiviert ein Modell für die aktuelle Service-Laufzeit.

        Dies verändert das Manifest und die persistente Konfiguration
        nicht.
        """

        record = self._get_record(
            model_id,
        )

        await self._authorize(
            action=ModelServiceAction.ENABLE,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        if not record.manifest.is_enabled:
            raise ModelDisabledError(
                record.model_id,
                request_id=(
                    access_context.request_id
                    if access_context
                    else None
                ),
            )

        record.runtime_enabled = True
        record.last_access_context = access_context

    async def disable_model(
        self,
        model_id: str,
        *,
        unload: bool = False,
        access_context: ModelAccessContext | None = None,
    ) -> None:
        """
        Deaktiviert ein Modell für die aktuelle Service-Laufzeit.
        """

        record = self._get_record(
            model_id,
        )

        await self._authorize(
            action=ModelServiceAction.DISABLE,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        record.runtime_enabled = False
        record.last_access_context = access_context

        if unload:
            await self._lifecycle.unload(
                record.model_id,
                wait_for_active_operations=True,
            )

    # ========================================================
    # Abfragen
    # ========================================================

    def has_model(
        self,
        model_id: str,
    ) -> bool:
        normalized = self._normalize_model_id(
            model_id,
        )

        return normalized in self._records

    def get_manifest(
        self,
        model_id: str,
    ) -> ModelManifest:
        return self._get_record(
            model_id,
        ).manifest

    def get_loaded_manifest(
        self,
        model_id: str,
    ) -> LoadedModelManifest:
        return self._get_record(
            model_id,
        ).loaded_manifest

    def list_model_ids(
        self,
        *,
        enabled_only: bool = False,
    ) -> tuple[str, ...]:
        records = self._records.values()

        if enabled_only:
            records = (
                record
                for record in records
                if record.effectively_enabled
            )

        return tuple(
            sorted(
                record.model_id
                for record in records
            ),
        )

    async def list_models(
        self,
        *,
        enabled_only: bool = False,
        access_context: ModelAccessContext | None = None,
    ) -> tuple[ModelServiceInfo, ...]:
        """
        Liefert sichere Modellinformationen.

        Modelle, für die READ nicht erlaubt ist, werden nicht ausgegeben.
        """

        await self._authorize(
            action=ModelServiceAction.LIST,
            model_id=None,
            provider_type=None,
            context=access_context,
        )

        result: list[ModelServiceInfo] = []

        records = sorted(
            self._records.values(),
            key=lambda item: (
                item.manifest.presentation.sort_order,
                item.manifest.display_name.lower(),
                item.model_id,
            ),
        )

        for record in records:
            if enabled_only and not record.effectively_enabled:
                continue

            if not await self._is_authorized(
                action=ModelServiceAction.READ,
                model_id=record.model_id,
                provider_type=record.provider_type,
                context=access_context,
            ):
                continue

            result.append(
                self._create_service_info(
                    record,
                ),
            )

        return tuple(result)

    async def get_model_info(
        self,
        model_id: str,
        *,
        include_provider_info: bool = False,
        access_context: ModelAccessContext | None = None,
    ) -> ModelServiceInfo | tuple[ModelServiceInfo, ModelInfo]:
        """
        Liefert die Manifestansicht und optional die Provideransicht.

        include_provider_info=True kann ein Backend erzeugen und laden,
        abhängig von der Providerimplementierung.
        """

        record = self._get_record(
            model_id,
        )

        await self._authorize(
            action=ModelServiceAction.READ,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        service_info = self._create_service_info(
            record,
        )

        if not include_provider_info:
            return service_info

        self._ensure_enabled(
            record,
            access_context=access_context,
        )

        backend = await self._lifecycle.get_backend(
            record.model_id,
            ensure_loaded=False,
        )

        provider_info = await backend.get_model(
            record.model_id,
        )

        return service_info, provider_info

    # ========================================================
    # Lifecycle-Aktionen
    # ========================================================

    async def load_model(
        self,
        model_id: str,
        *,
        access_context: ModelAccessContext | None = None,
    ) -> BaseModelBackend:
        record = self._get_record(
            model_id,
        )

        self._ensure_enabled(
            record,
            access_context=access_context,
        )

        await self._authorize(
            action=ModelServiceAction.LOAD,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        record.last_access_context = access_context

        return await self._lifecycle.ensure_ready(
            record.model_id,
            load=True,
        )

    async def unload_model(
        self,
        model_id: str,
        *,
        wait_for_active_operations: bool = True,
        access_context: ModelAccessContext | None = None,
    ) -> bool:
        record = self._get_record(
            model_id,
        )

        await self._authorize(
            action=ModelServiceAction.UNLOAD,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        return await self._lifecycle.unload(
            record.model_id,
            wait_for_active_operations=(
                wait_for_active_operations
            ),
        )

    # ========================================================
    # Generierung
    # ========================================================

    async def generate(
        self,
        model_id: str,
        request: GenerationRequest,
        *,
        timeout_seconds: float | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> StreamEvent:
        """
        Führt eine nicht streamende Modellgenerierung aus.
        """

        record = self._get_record(
            model_id,
        )

        self._ensure_enabled(
            record,
            access_context=access_context,
        )
        self._validate_request_capabilities(
            record,
            request,
        )

        await self._authorize(
            action=ModelServiceAction.USE,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        record.last_access_context = access_context

        try:
            return await self._lifecycle.generate(
                record.model_id,
                request,
                timeout_seconds=timeout_seconds,
                request_id=(
                    access_context.request_id
                    if access_context
                    else None
                ),
            )

        except ModelError:
            raise

        except Exception as exc:
            raise translate_provider_error(
                exc,
                provider_type=record.provider_type,
                model_id=record.model_id,
                request_id=(
                    access_context.request_id
                    if access_context
                    else None
                ),
            ) from exc

    async def stream(
        self,
        model_id: str,
        request: GenerationRequest,
        *,
        idle_timeout_seconds: float | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """
        Führt eine streamende Modellgenerierung aus.
        """

        record = self._get_record(
            model_id,
        )

        self._ensure_enabled(
            record,
            access_context=access_context,
        )
        self._require_capability(
            record,
            ModelManifestCapability.STREAMING.value,
            access_context=access_context,
        )
        self._validate_request_capabilities(
            record,
            request,
        )

        await self._authorize(
            action=ModelServiceAction.STREAM,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        record.last_access_context = access_context

        try:
            async for event in self._lifecycle.stream(
                record.model_id,
                request,
                idle_timeout_seconds=idle_timeout_seconds,
                request_id=(
                    access_context.request_id
                    if access_context
                    else None
                ),
            ):
                yield event

        except ModelError:
            raise

        except Exception as exc:
            raise translate_provider_error(
                exc,
                provider_type=record.provider_type,
                model_id=record.model_id,
                request_id=(
                    access_context.request_id
                    if access_context
                    else None
                ),
            ) from exc

    # ========================================================
    # Factory und Abhängigkeiten
    # ========================================================

    def _create_lifecycle_definition(
        self,
        record: _ModelServiceRecord,
    ) -> ModelLifecycleDefinition:
        manifest = record.manifest
        lifecycle_manifest = manifest.lifecycle

        policy_defaults = ModelLifecyclePolicy()

        policy = ModelLifecyclePolicy(
            generation_timeout_seconds=(
                lifecycle_manifest.generation_timeout_seconds
                if lifecycle_manifest.generation_timeout_seconds
                is not None
                else policy_defaults.generation_timeout_seconds
            ),
            stream_idle_timeout_seconds=(
                lifecycle_manifest.stream_idle_timeout_seconds
                if lifecycle_manifest.stream_idle_timeout_seconds
                is not None
                else policy_defaults.stream_idle_timeout_seconds
            ),
            idle_unload_seconds=(
                lifecycle_manifest.idle_unload_seconds
            ),
            shutdown_timeout_seconds=(
                lifecycle_manifest.shutdown_timeout_seconds
                if lifecycle_manifest.shutdown_timeout_seconds
                is not None
                else policy_defaults.shutdown_timeout_seconds
            ),
            unload_when_idle=(
                lifecycle_manifest.unload_when_idle
            ),
            eager_create=lifecycle_manifest.eager_create,
            eager_load=lifecycle_manifest.eager_load,
        )

        async def backend_factory() -> BaseModelBackend:
            return await self._create_backend(
                record,
            )

        return ModelLifecycleDefinition(
            model_id=manifest.id,
            provider_type=manifest.provider.type,
            factory=backend_factory,
            policy=policy,
            metadata={
                "manifest_path": str(
                    record.loaded_manifest.manifest_path,
                ),
                "manifest_schema_version": (
                    manifest.schema_version
                ),
                "runtime": manifest.runtime.value,
                "status": manifest.status.value,
                "capabilities": sorted(
                    manifest.capabilities,
                ),
                "tags": sorted(
                    manifest.tags,
                ),
            },
        )

    async def _create_backend(
        self,
        record: _ModelServiceRecord,
    ) -> BaseModelBackend:
        manifest = record.manifest
        provider_type = manifest.provider.type

        provider_config = dict(
            manifest.provider.config,
        )

        provider_config.setdefault(
            "model_id",
            manifest.id,
        )
        provider_config.setdefault(
            "display_name",
            manifest.display_name,
        )

        if manifest.limits.context_window is not None:
            provider_config.setdefault(
                "context_window",
                manifest.limits.context_window,
            )

        dependencies = await self._resolve_dependencies(
            record,
        )

        try:
            return self._provider_registry.create(
                provider_type=provider_type,
                provider_config=provider_config,
                dependencies=dependencies,
            )

        except ModelError:
            raise

        except Exception as exc:
            translated = translate_provider_error(
                exc,
                provider_type=provider_type,
                model_id=manifest.id,
                request_id=(
                    record.last_access_context.request_id
                    if record.last_access_context
                    else None
                ),
            )

            # translated ist bereits ein ModelError (garantiert durch translate_provider_error)
            raise translated from exc

    async def _resolve_dependencies(
        self,
        record: _ModelServiceRecord,
    ) -> dict[str, Any]:
        dependencies = dict(
            self._common_dependencies,
        )

        if self._dependency_provider is not None:
            provided = self._dependency_provider(
                record.loaded_manifest,
                record.last_access_context,
            )

            if inspect.isawaitable(provided):
                provided = await provided

            # Der Provider muss ein Mapping zurückgeben – type-check zur Laufzeit
            if not isinstance(provided, Mapping):  # type: ignore[reportUnnecessaryIsInstance]
                raise ModelProviderCreationError(
                    provider_type=record.provider_type,
                    model_id=record.model_id,
                    reason=(
                        "Der DependencyProvider hat kein Mapping "
                        "zurückgegeben."
                    ),
                )

            dependencies.update(
                dict(provided),
            )

        resolved_secrets = await self._resolve_secrets(
            record,
        )

        dependencies["secrets"] = dict(
            resolved_secrets,
        )

        for secret_name, secret_value in resolved_secrets.items():
            if secret_name not in dependencies:
                dependencies[secret_name] = secret_value

        dependencies.setdefault(
            "manifest",
            record.manifest,
        )
        dependencies.setdefault(
            "loaded_manifest",
            record.loaded_manifest,
        )
        dependencies.setdefault(
            "model_id",
            record.model_id,
        )
        dependencies.setdefault(
            "provider_type",
            record.provider_type,
        )

        return dependencies

    async def _resolve_secrets(
        self,
        record: _ModelServiceRecord,
    ) -> dict[str, Any]:
        resolved: dict[str, Any] = {}

        for secret_name, reference in (
            record.manifest.provider.secrets.items()
        ):
            context = ModelSecretResolutionContext(
                model_id=record.model_id,
                provider_type=record.provider_type,
                manifest_path=(
                    record.loaded_manifest.manifest_path
                ),
                secret_name=secret_name,
                access_context=record.last_access_context,
            )

            try:
                value = self._secret_resolver.resolve(
                    reference,
                    context,
                )

                if inspect.isawaitable(value):
                    value = await value

            except ModelError:
                raise

            except Exception as exc:
                raise ModelProviderDependencyError(
                    provider_type=record.provider_type,
                    model_id=record.model_id,
                    dependency=(
                        f"Secret '{secret_name}'"
                    ),
                    request_id=(
                        record.last_access_context.request_id
                        if record.last_access_context
                        else None
                    ),
                    cause=exc,
                ) from exc

            if value is None and reference.required:
                raise ModelProviderDependencyError(
                    provider_type=record.provider_type,
                    model_id=record.model_id,
                    dependency=(
                        f"Secret '{secret_name}'"
                    ),
                    request_id=(
                        record.last_access_context.request_id
                        if record.last_access_context
                        else None
                    ),
                )

            if value is not None:
                resolved[secret_name] = value

        return resolved

    # ========================================================
    # Capability-Prüfung
    # ========================================================

    def _validate_request_capabilities(
        self,
        record: _ModelServiceRecord,
        request: GenerationRequest,
    ) -> None:
        self._require_capability(
            record,
            ModelManifestCapability.CHAT.value,
            access_context=record.last_access_context,
        )

        tools = getattr(
            request,
            "tools",
            None,
        )

        if tools:
            self._require_capability(
                record,
                ModelManifestCapability.TOOLS.value,
                access_context=record.last_access_context,
            )

        response_format = getattr(
            request,
            "response_format",
            None,
        )

        if response_format is not None:
            self._require_capability(
                record,
                ModelManifestCapability.STRUCTURED_OUTPUT.value,
                access_context=record.last_access_context,
            )

    @staticmethod
    def _require_capability(
        record: _ModelServiceRecord,
        capability: str,
        *,
        access_context: ModelAccessContext | None,
    ) -> None:
        if record.manifest.supports(
            capability,
        ):
            return

        raise ModelCapabilityNotSupportedError(
            model_id=record.model_id,
            capability=capability,
            provider_type=record.provider_type,
            request_id=(
                access_context.request_id
                if access_context
                else None
            ),
        )

    # ========================================================
    # Autorisierung
    # ========================================================

    async def _authorize(
        self,
        *,
        action: ModelServiceAction,
        model_id: str | None,
        provider_type: str | None,
        context: ModelAccessContext | None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        effective_context = (
            context
            or ModelAccessContext()
        )

        request = ModelAuthorizationRequest(
            action=action,
            model_id=model_id,
            provider_type=provider_type,
            context=effective_context,
            metadata=dict(metadata or {}),
        )

        decision = self._authorizer.authorize(
            request,
        )

        if inspect.isawaitable(decision):
            decision = await decision

        if decision:
            return

        raise ModelAccessDeniedError(
            model_id=model_id or "*",
            action=action.value,
            subject_id=effective_context.subject_id,
            request_id=effective_context.request_id,
        )

    async def _is_authorized(
        self,
        *,
        action: ModelServiceAction,
        model_id: str | None,
        provider_type: str | None,
        context: ModelAccessContext | None,
    ) -> bool:
        effective_context = (
            context
            or ModelAccessContext()
        )

        request = ModelAuthorizationRequest(
            action=action,
            model_id=model_id,
            provider_type=provider_type,
            context=effective_context,
        )

        decision = self._authorizer.authorize(
            request,
        )

        if inspect.isawaitable(decision):
            decision = await decision

        return bool(decision)

    # ========================================================
    # Diagnose
    # ========================================================

    def _create_service_info(
        self,
        record: _ModelServiceRecord,
    ) -> ModelServiceInfo:
        lifecycle_snapshot: ModelLifecycleSnapshot | None

        try:
            lifecycle_snapshot = (
                self._lifecycle.get_snapshot(
                    record.model_id,
                )
            )
        except Exception:
            lifecycle_snapshot = None

        manifest = record.manifest

        return ModelServiceInfo(
            model_id=record.model_id,
            display_name=manifest.display_name,
            description=manifest.description,
            provider_type=record.provider_type,
            manifest_enabled=manifest.is_enabled,
            runtime_enabled=record.runtime_enabled,
            effectively_enabled=(
                record.effectively_enabled
            ),
            status=manifest.status.value,
            runtime=manifest.runtime.value,
            capabilities=tuple(
                sorted(manifest.capabilities),
            ),
            tags=tuple(
                sorted(manifest.tags),
            ),
            manifest_path=(
                record.loaded_manifest.manifest_path
            ),
            lifecycle=lifecycle_snapshot,
            metadata={
                "registration_index": (
                    record.registration_index
                ),
                "presentation": (
                    manifest.presentation.model_dump(
                        mode="json",
                        exclude_none=True,
                    )
                ),
                "limits": (
                    manifest.limits.model_dump(
                        mode="json",
                        exclude_none=True,
                    )
                ),
                "manifest_metadata": dict(
                    manifest.metadata,
                ),
            },
        )

    @staticmethod
    def _registration_error_result(
        *,
        path: Path,
        error: BaseException,
    ) -> ModelRegistrationResult:
        model_id: str | None = getattr(
            error,
            "model_id",
            None,
        )
        provider_type: str | None = getattr(
            error,
            "provider_type",
            None,
        )

        return ModelRegistrationResult(
            model_id=model_id,
            manifest_path=path,
            provider_type=provider_type,
            status=ModelRegistrationStatus.FAILED,
            message=str(error),
            error_type=error.__class__.__name__,
            error_code=(
                str(getattr(error, "code"))
                if getattr(error, "code", None)
                is not None
                else None
            ),
        )

    # ========================================================
    # Interne Hilfsmethoden
    # ========================================================

    def _get_record(
        self,
        model_id: str,
    ) -> _ModelServiceRecord:
        normalized = self._normalize_model_id(
            model_id,
        )

        record = self._records.get(
            normalized,
        )

        if record is None:
            raise ModelNotRegisteredError(
                normalized,
            )

        return record

    @staticmethod
    def _ensure_enabled(
        record: _ModelServiceRecord,
        *,
        access_context: ModelAccessContext | None,
    ) -> None:
        if record.effectively_enabled:
            return

        raise ModelDisabledError(
            record.model_id,
            request_id=(
                access_context.request_id
                if access_context
                else None
            ),
        )

    @staticmethod
    def _normalize_model_id(
        model_id: str,
    ) -> str:
        # model_id ist bereits als str annotiert – wir prüfen nur auf Leerheit.
        normalized = model_id.strip().lower()

        if not normalized:
            raise ValueError(
                "model_id darf nicht leer sein.",
            )

        return normalized

    async def __aenter__(
        self,
    ) -> ModelService:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> None:
        del exc_type
        del exc
        del traceback

        await self.shutdown()


__all__ = [
    "AllowAllModelAuthorizer",
    "DependencyProvider",
    "ModelAccessContext",
    "ModelAuthorizationRequest",
    "ModelAuthorizer",
    "ModelDiscoveryReport",
    "ModelRegistrationResult",
    "ModelRegistrationStatus",
    "ModelSecretResolutionContext",
    "ModelSecretResolver",
    "ModelService",
    "ModelServiceAction",
    "ModelServiceInfo",
    "NullModelSecretResolver",
]