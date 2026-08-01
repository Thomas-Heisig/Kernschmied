# F:\Kernschmied\backend\app\models\service.py

"""
Zentrale Anwendungsschicht des Kernschmied-Modellsystems.

Der ModelService verbindet:

- validierte model.json-Manifeste über die ModelRegistry,
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
5. Jede Benutzeraktion wird serverseitig autorisiert.
6. Providerfehler werden in stabile Modellfehler übersetzt.
7. Der Service ist kein globales Singleton.
8. Runtime-Aktivierung ersetzt keine persistente Konfiguration.
9. Provider werden erst bei tatsächlicher Verwendung erzeugt.
10. Das Herunterfahren eines Providers darf andere Provider nicht blockieren.
11. Request-Kontext wird niemals in gemeinsam genutzten Modelleinträgen gespeichert.
12. Ein Standardmodell wird ausschließlich explizit konfiguriert.
13. Provider-Erzeugung und Secret-Auflösung sind systembezogene Vorgänge.
14. Autorisierung und Provider-Lifecycle bleiben getrennte Verantwortlichkeiten.
15. Registry und Fallback-Speicher werden niemals gleichzeitig als Wahrheitsquelle verwendet.
16. Bei einer Ersetzung wird zuerst der alte Lifecycle entfernt und danach der neue registriert.
17. Fehlgeschlagene Ersetzungen stellen den vorherigen Zustand bestmöglich wieder her.

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
from types import MappingProxyType
from typing import Any, Final, Protocol, TypeAlias, runtime_checkable
from app.registries.model_registry import ModelRegistryEntry

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
from app.registries.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


SOURCE_FILE: Final[str] = "backend/app/models/service.py"
LOG_AREA: Final[str] = "model-service"

DEFAULT_DISCOVERY_RECURSIVE: Final[bool] = True
DEFAULT_DISCOVERY_FOLLOW_SYMLINKS: Final[bool] = False


# ============================================================
# Typisierte Default-Factorys
# ============================================================


def _empty_string_frozenset() -> frozenset[str]:
    """
    Liefert ein vollständig typisiertes leeres String-Frozenset.

    Die explizite Factory verhindert teilweise unbekannte Typen bei
    strikter Pylance-/Pyright-Prüfung.
    """

    return frozenset()


def _empty_string_any_mapping() -> dict[str, Any]:
    """
    Liefert ein vollständig typisiertes leeres Mapping.
    """

    return {}


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

    Dieser Kontext ist requestbezogen und darf nicht in gemeinsam
    genutzten Modelleinträgen gespeichert werden.
    """

    subject_id: str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None

    roles: frozenset[str] = field(
        default_factory=_empty_string_frozenset,
    )
    permissions: frozenset[str] = field(
        default_factory=_empty_string_frozenset,
    )
    attributes: Mapping[str, Any] = field(
        default_factory=_empty_string_any_mapping,
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "subject_id",
            self._normalize_optional_identifier(
                self.subject_id,
            ),
        )
        object.__setattr__(
            self,
            "tenant_id",
            self._normalize_optional_identifier(
                self.tenant_id,
            ),
        )
        object.__setattr__(
            self,
            "user_id",
            self._normalize_optional_identifier(
                self.user_id,
            ),
        )
        object.__setattr__(
            self,
            "session_id",
            self._normalize_optional_identifier(
                self.session_id,
            ),
        )
        object.__setattr__(
            self,
            "request_id",
            self._normalize_optional_identifier(
                self.request_id,
            ),
        )

        normalized_roles: frozenset[str] = frozenset(
            normalized
            for role in self.roles
            if (
                normalized := str(
                    role,
                ).strip()
            )
        )

        normalized_permissions: frozenset[str] = frozenset(
            normalized
            for permission in self.permissions
            if (
                normalized := str(
                    permission,
                ).strip()
            )
        )

        normalized_attributes: dict[str, Any] = dict(
            self.attributes,
        )

        object.__setattr__(
            self,
            "roles",
            normalized_roles,
        )
        object.__setattr__(
            self,
            "permissions",
            normalized_permissions,
        )
        object.__setattr__(
            self,
            "attributes",
            MappingProxyType(
                normalized_attributes,
            ),
        )

    @staticmethod
    def _normalize_optional_identifier(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None


@dataclass(frozen=True, slots=True)
class ModelAuthorizationRequest:
    """
    Vollständige Anfrage an den ModelAuthorizer.
    """

    action: ModelServiceAction
    model_id: str | None
    provider_type: str | None
    context: ModelAccessContext
    metadata: Mapping[str, Any] = field(
        default_factory=_empty_string_any_mapping,
    )

    def __post_init__(self) -> None:
        normalized_metadata: dict[str, Any] = dict(
            self.metadata,
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                normalized_metadata,
            ),
        )


@runtime_checkable
class ModelAuthorizer(Protocol):
    """
    Schnittstelle für serverseitige Modellautorisierung.
    """

    def authorize(
        self,
        request: ModelAuthorizationRequest,
    ) -> bool | Awaitable[bool]: ...


@dataclass(frozen=True, slots=True)
class ModelSecretResolutionContext:
    """
    Kontext für die systemseitige Auflösung einer Secret-Referenz.

    Der Benutzerkontext wird absichtlich nicht an den systemweiten
    Provider-Lifecycle gebunden.
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
    ) -> Any | Awaitable[Any]: ...


DependencyProvider: TypeAlias = Callable[
    [
        LoadedModelManifest,
        ModelAccessContext | None,
    ],
    Mapping[str, Any] | Awaitable[Mapping[str, Any]],
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
            result.status == ModelRegistrationStatus.FAILED for result in self.results
        )

    @property
    def skipped_count(self) -> int:
        return sum(
            result.status == ModelRegistrationStatus.SKIPPED for result in self.results
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

    def __post_init__(self) -> None:
        normalized_metadata: dict[str, Any] = dict(
            self.metadata,
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                normalized_metadata,
            ),
        )


@dataclass(slots=True)
class _ModelServiceRecord:
    """
    Interner ModelService-Eintrag.

    Der Eintrag enthält ausschließlich systemweiten Zustand.
    Requestbezogene Zugriffskontexte dürfen hier nicht gespeichert werden.
    """

    loaded_manifest: LoadedModelManifest
    runtime_enabled: bool
    registration_index: int
    registered_at_loop_time: float

    @property
    def manifest(self) -> ModelManifest:
        return self.loaded_manifest.manifest

    @property
    def model_id(self) -> str:
        return self.manifest.id.strip().lower()

    @property
    def provider_type(self) -> str:
        return self.manifest.provider.type.strip().lower()

    @property
    def effectively_enabled(self) -> bool:
        return self.manifest.is_enabled and self.runtime_enabled


# ============================================================
# Standardimplementierungen
# ============================================================


class AllowAllModelAuthorizer:
    """
    Authorizer ausschließlich für lokale Entwicklung.
    """

    def authorize(
        self,
        request: ModelAuthorizationRequest,
    ) -> bool:
        return True


class NullModelSecretResolver:
    """
    Resolver, der keine Secrets bereitstellt.
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
                dependency=(f"Secret-Resolver für '{context.secret_name}'"),
            )

        return None


# ============================================================
# ModelService
# ============================================================


class ModelService:
    """
    Zentrale Anwendungsschicht für registrierte Modelle.

    Der Service besitzt keine globale Instanz. Er wird im
    Application-Lifespan erzeugt und per Dependency Injection
    bereitgestellt.
    """

    def __init__(
        self,
        *,
        provider_registry: ModelProviderRegistry,
        lifecycle: ModelLifecycleManager,
        model_registry: ModelRegistry | None = None,
        secret_resolver: ModelSecretResolver | None = None,
        authorizer: ModelAuthorizer | None = None,
        common_dependencies: Mapping[str, Any] | None = None,
        dependency_provider: DependencyProvider | None = None,
        allowed_manifest_directories: Sequence[str | Path] = (),
        default_model_id: str | None = None,
    ) -> None:
        self._provider_registry = provider_registry
        self._lifecycle = lifecycle
        self._model_registry = model_registry

        self._secret_resolver = (
            secret_resolver
            if secret_resolver is not None
            else NullModelSecretResolver()
        )

        self._authorizer = (
            authorizer if authorizer is not None else AllowAllModelAuthorizer()
        )

        self._common_dependencies = dict(
            common_dependencies or {},
        )
        self._dependency_provider = dependency_provider

        self._allowed_manifest_directories = tuple(
            Path(
                directory,
            )
            .expanduser()
            .resolve()
            for directory in allowed_manifest_directories
        )

        self._records: dict[
            str,
            _ModelServiceRecord,
        ] = {}

        self._runtime_enabled: dict[
            str,
            bool,
        ] = {}

        self._registry_lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()

        self._registration_locks: dict[
            str,
            asyncio.Lock,
        ] = {}

        self._registration_counter = 0
        self._started = False
        self._shutdown_requested = False

        self._default_model_id = (
            self._normalize_model_id(
                default_model_id,
            )
            if default_model_id is not None
            else None
        )

    # ========================================================
    # Eigenschaften
    # ========================================================

    @property
    def provider_registry(
        self,
    ) -> ModelProviderRegistry:
        return self._provider_registry

    @property
    def lifecycle(
        self,
    ) -> ModelLifecycleManager:
        return self._lifecycle

    @property
    def count(self) -> int:
        """
        Liefert eine synchrone Diagnosezahl.

        Für eine garantiert aktuelle Anzahl sollte get_count()
        verwendet werden.
        """

        if self._model_registry is not None:
            return len(
                self._runtime_enabled,
            )

        return len(
            self._records,
        )

    @property
    def started(self) -> bool:
        return self._started

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    # ========================================================
    # Service-Lifecycle
    # ========================================================

    async def start(self) -> None:
        """
        Startet den ModelService.

        Provider werden dadurch nicht automatisch erzeugt.
        """

        async with self._state_lock:
            if self._started:
                return

            if self._shutdown_requested:
                raise ModelUnavailableError(
                    model_id="*",
                    provider_type=None,
                    reason=(
                        "Der ModelService wurde bereits "
                        "heruntergefahren und kann nicht "
                        "erneut gestartet werden."
                    ),
                    request_id=None,
                )

            self._started = True

        _log_info(
            "ModelService started",
            model_step="service-started",
            default_model_id=self._default_model_id,
        )

    async def shutdown(
        self,
        *,
        raise_on_error: bool = True,
        access_context: ModelAccessContext | None = None,
    ) -> None:
        """
        Fährt den ModelService und den ModelLifecycleManager herunter.
        """

        await self._authorize(
            action=ModelServiceAction.SHUTDOWN,
            model_id=None,
            provider_type=None,
            context=access_context,
        )

        async with self._state_lock:
            if self._shutdown_requested:
                return

            self._shutdown_requested = True
            self._started = False

        try:
            await self._lifecycle.shutdown()

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            _log_warning(
                "Model lifecycle shutdown failed",
                model_step="lifecycle-shutdown-failed",
                error_type=exc.__class__.__name__,
                error_message=str(
                    exc,
                ),
                exc_info=True,
            )

            if raise_on_error:
                raise

        finally:
            _log_info(
                "ModelService stopped",
                model_step="service-stopped",
            )

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
        await self.shutdown(
            raise_on_error=False,
        )

    # ========================================================
    # Registrierung und Discovery
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
        Registriert ein validiertes Modellmanifest.

        Bei einer Ersetzung wird der alte Lifecycle-Eintrag zuerst
        entfernt. Erst danach wird die neue Definition registriert.

        Schlägt die Ersetzung fehl, wird der vorherige Zustand
        bestmöglich wiederhergestellt.
        """

        model_id = self._normalize_model_id(
            loaded_manifest.model_id,
        )
        provider_type = self._normalize_provider_type(
            loaded_manifest.manifest.provider.type,
        )
        manifest_path = loaded_manifest.manifest_path.expanduser().resolve()

        await self._authorize(
            action=ModelServiceAction.REGISTER,
            model_id=model_id,
            provider_type=provider_type,
            context=access_context,
            metadata={
                "manifest_path": str(
                    manifest_path,
                ),
                "replace": replace,
            },
        )

        self._ensure_service_not_shutdown(
            model_id=model_id,
            provider_type=provider_type,
            access_context=access_context,
        )

        if not self._provider_registry.has(
            provider_type,
        ):
            raise InvalidModelProviderConfigurationError(
                provider_type=provider_type,
                model_id=model_id,
                field="provider.type",
                reason=(
                    "Der Provider ist nicht in der "
                    "serverseitigen Freigabeliste registriert."
                ),
                request_id=self._request_id(
                    access_context,
                ),
            )

        registration_lock = await self._get_registration_lock(
            model_id,
        )

        async with registration_lock:
            existing_record = await self._find_model_record(
                model_id,
            )

            if existing_record is not None and not replace:
                raise DuplicateModelRegistrationError(
                    model_id,
                    request_id=self._request_id(
                        access_context,
                    ),
                )

            effective_runtime_enabled = (
                runtime_enabled
                if runtime_enabled is not None
                else loaded_manifest.manifest.is_enabled
            )

            registration_index = await self._next_registration_index()

            loop = asyncio.get_running_loop()

            new_record = _ModelServiceRecord(
                loaded_manifest=loaded_manifest,
                runtime_enabled=effective_runtime_enabled,
                registration_index=registration_index,
                registered_at_loop_time=loop.time(),
            )

            new_lifecycle_definition = self._create_lifecycle_definition(
                new_record,
            )

            old_lifecycle_definition = (
                self._create_lifecycle_definition(
                    existing_record,
                )
                if existing_record is not None
                else None
            )

            old_runtime_enabled = (
                existing_record.runtime_enabled if existing_record is not None else None
            )

            old_lifecycle_removed = False
            new_lifecycle_registered = False
            registry_updated = False

            try:
                if existing_record is not None:
                    old_lifecycle_removed = await self._lifecycle.unregister(
                        model_id,
                        shutdown_backend=True,
                    )

                    _log_info(
                        "Previous lifecycle definition removed",
                        model_step="previous-lifecycle-removed",
                        model_id=model_id,
                        provider_type=provider_type,
                        removed=old_lifecycle_removed,
                    )

                await self._lifecycle.register(
                    new_lifecycle_definition,
                )
                new_lifecycle_registered = True

                await self._store_record(
                    new_record,
                    replace=replace,
                )
                registry_updated = True

                self._runtime_enabled[model_id] = effective_runtime_enabled

            except asyncio.CancelledError:
                await self._rollback_registration(
                    model_id=model_id,
                    existing_record=existing_record,
                    old_lifecycle_definition=old_lifecycle_definition,
                    old_runtime_enabled=old_runtime_enabled,
                    old_lifecycle_removed=old_lifecycle_removed,
                    new_lifecycle_registered=new_lifecycle_registered,
                    registry_updated=registry_updated,
                )
                raise

            except Exception:
                await self._rollback_registration(
                    model_id=model_id,
                    existing_record=existing_record,
                    old_lifecycle_definition=old_lifecycle_definition,
                    old_runtime_enabled=old_runtime_enabled,
                    old_lifecycle_removed=old_lifecycle_removed,
                    new_lifecycle_registered=new_lifecycle_registered,
                    registry_updated=registry_updated,
                )
                raise

            status = (
                ModelRegistrationStatus.REPLACED
                if existing_record is not None
                else ModelRegistrationStatus.REGISTERED
            )

            _log_info(
                "Model manifest registered",
                model_step="manifest-registered",
                model_id=model_id,
                provider_type=provider_type,
                registration_status=status.value,
                runtime_enabled=effective_runtime_enabled,
                manifest_enabled=loaded_manifest.manifest.is_enabled,
                manifest_path=str(
                    manifest_path,
                ),
            )

            return ModelRegistrationResult(
                model_id=model_id,
                manifest_path=manifest_path,
                provider_type=provider_type,
                status=status,
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
            allowed_base_directories=(self._allowed_manifest_directories or None),
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
        Findet model.json-Dateien und registriert sie kontrolliert.
        """

        directories = tuple(
            Path(
                directory,
            )
            .expanduser()
            .resolve()
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

        model_paths: dict[
            str,
            list[Path],
        ] = {}

        for path in paths:
            try:
                loaded_manifest = load_model_manifest(
                    path,
                    allowed_base_directories=(directories or None),
                )

                model_id = self._normalize_model_id(
                    loaded_manifest.model_id,
                )

                known_paths = model_paths.setdefault(
                    model_id,
                    [],
                )
                known_paths.append(
                    path,
                )

                if (
                    len(
                        known_paths,
                    )
                    > 1
                    and not replace
                ):
                    raise DuplicateModelManifestError(
                        model_id,
                        manifest_paths=[
                            str(
                                known_path,
                            )
                            for known_path in known_paths
                        ],
                        request_id=self._request_id(
                            access_context,
                        ),
                    )

                result = await self.register_manifest(
                    loaded_manifest,
                    replace=replace,
                    access_context=access_context,
                )

                results.append(
                    result,
                )

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                result = self._registration_error_result(
                    path=path,
                    error=exc,
                )

                results.append(
                    result,
                )

                _log_warning(
                    "Model manifest registration failed",
                    model_step="manifest-registration-failed",
                    manifest_path=str(
                        path,
                    ),
                    error_type=exc.__class__.__name__,
                    error_code=getattr(
                        exc,
                        "code",
                        None,
                    ),
                    error_message=str(
                        exc,
                    ),
                    exc_info=True,
                )

                if not continue_on_error:
                    raise

        return ModelDiscoveryReport(
            discovered_paths=paths,
            results=tuple(
                results,
            ),
        )

    async def unregister_model(
        self,
        model_id: str,
        *,
        access_context: ModelAccessContext | None = None,
    ) -> bool:
        """
        Entfernt ein Modell aus Lifecycle und Registry.
        """

        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        record = await self._find_model_record(
            normalized_model_id,
        )

        if record is None:
            return False

        await self._authorize(
            action=ModelServiceAction.UNREGISTER,
            model_id=normalized_model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        registration_lock = await self._get_registration_lock(
            normalized_model_id,
        )

        async with registration_lock:
            record = await self._find_model_record(
                normalized_model_id,
            )

            if record is None:
                return False

            lifecycle_removed = await self._lifecycle.unregister(
                normalized_model_id,
                shutdown_backend=True,
            )

            try:
                await self._remove_record(
                    normalized_model_id,
                )

            except asyncio.CancelledError:
                if lifecycle_removed:
                    await self._restore_lifecycle_definition(
                        self._create_lifecycle_definition(
                            record,
                        ),
                    )
                raise

            except Exception:
                if lifecycle_removed:
                    await self._restore_lifecycle_definition(
                        self._create_lifecycle_definition(
                            record,
                        ),
                    )
                raise

            self._runtime_enabled.pop(
                normalized_model_id,
                None,
            )

            if self._default_model_id == normalized_model_id:
                _log_warning(
                    "Configured default model was unregistered",
                    model_step="default-model-unregistered",
                    model_id=normalized_model_id,
                    provider_type=record.provider_type,
                )

            _log_info(
                "Model unregistered",
                model_step="model-unregistered",
                model_id=normalized_model_id,
                provider_type=record.provider_type,
                lifecycle_removed=lifecycle_removed,
            )

            return True

    async def reload_manifest(
        self,
        model_id: str,
        *,
        access_context: ModelAccessContext | None = None,
    ) -> ModelRegistrationResult:
        """
        Lädt das Manifest eines registrierten Modells erneut.
        """

        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        record = await self._require_model_record(
            normalized_model_id,
            access_context=access_context,
        )

        await self._authorize(
            action=ModelServiceAction.RELOAD,
            model_id=normalized_model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        loaded_manifest = load_model_manifest(
            record.loaded_manifest.manifest_path,
            allowed_base_directories=(self._allowed_manifest_directories or None),
        )

        reloaded_model_id = self._normalize_model_id(
            loaded_manifest.model_id,
        )

        if reloaded_model_id != normalized_model_id:
            raise InvalidModelProviderConfigurationError(
                provider_type=record.provider_type,
                model_id=normalized_model_id,
                field="id",
                reason=(
                    "Die Modell-ID darf bei einem "
                    "Manifest-Reload nicht geändert werden. "
                    f"Erwartet wurde '{normalized_model_id}', "
                    f"gefunden wurde '{reloaded_model_id}'."
                ),
                request_id=self._request_id(
                    access_context,
                ),
            )

        return await self.register_manifest(
            loaded_manifest,
            replace=True,
            runtime_enabled=record.runtime_enabled,
            access_context=access_context,
        )

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
        Aktiviert ein persistiert freigegebenes Modell zur Laufzeit.
        """

        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        record = await self._require_model_record(
            normalized_model_id,
            access_context=access_context,
        )

        await self._authorize(
            action=ModelServiceAction.ENABLE,
            model_id=normalized_model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        if not record.manifest.is_enabled:
            raise ModelDisabledError(
                normalized_model_id,
                request_id=self._request_id(
                    access_context,
                ),
            )

        self._runtime_enabled[normalized_model_id] = True

        if self._model_registry is None:
            async with self._registry_lock:
                fallback_record = self._records.get(
                    normalized_model_id,
                )

                if fallback_record is not None:
                    fallback_record.runtime_enabled = True

        _log_info(
            "Model enabled at runtime",
            model_step="runtime-enabled",
            model_id=normalized_model_id,
            provider_type=record.provider_type,
        )

    async def disable_model(
        self,
        model_id: str,
        *,
        unload: bool = False,
        access_context: ModelAccessContext | None = None,
    ) -> None:
        """
        Deaktiviert ein Modell zur Laufzeit.

        Optional wird ein bereits erzeugtes Backend entladen.
        """

        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        record = await self._require_model_record(
            normalized_model_id,
            access_context=access_context,
        )

        await self._authorize(
            action=ModelServiceAction.DISABLE,
            model_id=normalized_model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        self._runtime_enabled[normalized_model_id] = False

        if self._model_registry is None:
            async with self._registry_lock:
                fallback_record = self._records.get(
                    normalized_model_id,
                )

                if fallback_record is not None:
                    fallback_record.runtime_enabled = False

        if unload:
            await self._lifecycle.unload(
                normalized_model_id,
                wait_for_active_operations=True,
            )

        _log_info(
            "Model disabled at runtime",
            model_step="runtime-disabled",
            model_id=normalized_model_id,
            provider_type=record.provider_type,
            unloaded=unload,
        )

    # ========================================================
    # Abfragen
    # ========================================================

    async def get_count(self) -> int:
        """
        Liefert die aktuelle Anzahl registrierter Modelle.
        """

        return len(
            await self.list_model_ids(),
        )

    async def has_model(
        self,
        model_id: str,
    ) -> bool:
        """
        Prüft, ob ein Modell registriert ist.
        """

        record = await self._find_model_record(
            self._normalize_model_id(
                model_id,
            ),
        )

        return record is not None

    async def get_manifest(
        self,
        model_id: str,
    ) -> ModelManifest:
        """
        Liefert das validierte Manifest eines Modells.
        """

        record = await self._require_model_record(
            model_id,
        )

        return record.manifest

    async def get_loaded_manifest(
        self,
        model_id: str,
    ) -> LoadedModelManifest:
        """
        Liefert Manifest und Quelldateiinformationen.
        """

        record = await self._require_model_record(
            model_id,
        )

        return record.loaded_manifest

    async def list_model_ids(
        self,
        *,
        enabled_only: bool = False,
    ) -> tuple[str, ...]:
        """
        Liefert registrierte Modell-IDs.

        enabled_only berücksichtigt sowohl den persistenten
        Manifest-Zustand als auch die Runtime-Aktivierung.
        """

        records = await self._list_records()

        return tuple(
            sorted(
                record.model_id
                for record in records
                if (not enabled_only or record.effectively_enabled)
            ),
        )

    async def list_models(
        self,
        *,
        enabled_only: bool = False,
        access_context: ModelAccessContext | None = None,
    ) -> tuple[ModelServiceInfo, ...]:
        """
        Liefert alle für den Benutzer sichtbaren Modelle.
        """

        await self._authorize(
            action=ModelServiceAction.LIST,
            model_id=None,
            provider_type=None,
            context=access_context,
        )

        records = await self._list_records()

        if enabled_only:
            records = [record for record in records if record.effectively_enabled]

        sorted_records = sorted(
            records,
            key=lambda record: (
                record.manifest.presentation.sort_order,
                record.manifest.display_name.lower(),
                record.model_id,
            ),
        )

        result: list[ModelServiceInfo] = []

        for record in sorted_records:
            authorized = await self._is_authorized(
                action=ModelServiceAction.READ,
                model_id=record.model_id,
                provider_type=record.provider_type,
                context=access_context,
            )

            if not authorized:
                continue

            result.append(
                self._create_service_info(
                    record,
                ),
            )

        return tuple(
            result,
        )

    async def get_model_info(
        self,
        model_id: str | None = None,
        *,
        include_provider_info: bool = False,
        access_context: ModelAccessContext | None = None,
    ) -> (
        ModelServiceInfo
        | tuple[
            ModelServiceInfo,
            ModelInfo,
        ]
    ):
        """
        Liefert Service- und optional Providerinformationen.
        """

        resolved_model_id = await self._resolve_model_id(
            model_id,
            access_context=access_context,
        )

        record = await self._require_model_record(
            resolved_model_id,
            access_context=access_context,
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

        self._ensure_service_available(
            model_id=record.model_id,
            provider_type=record.provider_type,
            access_context=access_context,
        )
        self._ensure_enabled(
            record,
            access_context=access_context,
        )

        backend = await self._lifecycle.ensure_ready(
            record.model_id,
            load=True,
        )

        provider_info = backend.get_model_info()

        return (
            service_info,
            provider_info,
        )

    # ========================================================
    # Lifecycle-Aktionen
    # ========================================================

    async def load_model(
        self,
        model_id: str | None = None,
        *,
        access_context: ModelAccessContext | None = None,
    ) -> BaseModelBackend:
        """
        Erzeugt beziehungsweise lädt das Backend eines Modells.
        """

        resolved_model_id = await self._resolve_model_id(
            model_id,
            access_context=access_context,
        )

        record = await self._require_model_record(
            resolved_model_id,
            access_context=access_context,
        )

        await self._authorize(
            action=ModelServiceAction.LOAD,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        self._ensure_service_available(
            model_id=record.model_id,
            provider_type=record.provider_type,
            access_context=access_context,
        )
        self._ensure_enabled(
            record,
            access_context=access_context,
        )

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
        """
        Entlädt ein erzeugtes Backend, ohne das Modell zu deregistrieren.
        """

        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        record = await self._require_model_record(
            normalized_model_id,
            access_context=access_context,
        )

        await self._authorize(
            action=ModelServiceAction.UNLOAD,
            model_id=normalized_model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        self._ensure_service_available(
            model_id=normalized_model_id,
            provider_type=record.provider_type,
            access_context=access_context,
        )

        return await self._lifecycle.unload(
            normalized_model_id,
            wait_for_active_operations=wait_for_active_operations,
        )

    # ========================================================
    # Generierung
    # ========================================================

    async def generate(
        self,
        request: GenerationRequest,
        model_id: str | None = None,
        *,
        timeout_seconds: float | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> StreamEvent:
        """
        Führt eine nicht-streamende Modellgenerierung aus.
        """

        resolved_model_id = await self._resolve_model_id(
            model_id,
            access_context=access_context,
        )

        record = await self._require_model_record(
            resolved_model_id,
            access_context=access_context,
        )

        await self._authorize(
            action=ModelServiceAction.USE,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        self._ensure_service_available(
            model_id=record.model_id,
            provider_type=record.provider_type,
            access_context=access_context,
        )
        self._ensure_enabled(
            record,
            access_context=access_context,
        )
        self._validate_request_capabilities(
            record,
            request,
            access_context=access_context,
        )
        self._validate_request_model(
            record,
            request,
            access_context=access_context,
        )

        request_id = self._request_id(
            access_context,
        )

        _log_info(
            "Model generation started",
            model_step="generation-started",
            model_id=record.model_id,
            provider_type=record.provider_type,
            request_id=request_id,
        )

        try:
            result = await self._lifecycle.generate(
                record.model_id,
                request,
                timeout_seconds=timeout_seconds,
                request_id=request_id,
            )

        except asyncio.CancelledError:
            raise

        except ModelError:
            raise

        except Exception as exc:
            _log_warning(
                "Model generation failed",
                model_step="generation-failed",
                model_id=record.model_id,
                provider_type=record.provider_type,
                request_id=request_id,
                error_type=exc.__class__.__name__,
                error_message=str(
                    exc,
                ),
                exc_info=True,
            )

            raise translate_provider_error(
                exc,
                provider_type=record.provider_type,
                model_id=record.model_id,
                request_id=request_id,
            ) from exc

        _log_info(
            "Model generation completed",
            model_step="generation-completed",
            model_id=record.model_id,
            provider_type=record.provider_type,
            request_id=request_id,
        )

        return result

    async def stream(
        self,
        request: GenerationRequest,
        model_id: str | None = None,
        *,
        idle_timeout_seconds: float | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """
        Führt eine streamende Modellgenerierung aus.
        """

        resolved_model_id = await self._resolve_model_id(
            model_id,
            access_context=access_context,
        )

        record = await self._require_model_record(
            resolved_model_id,
            access_context=access_context,
        )

        await self._authorize(
            action=ModelServiceAction.STREAM,
            model_id=record.model_id,
            provider_type=record.provider_type,
            context=access_context,
        )

        self._ensure_service_available(
            model_id=record.model_id,
            provider_type=record.provider_type,
            access_context=access_context,
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
            access_context=access_context,
        )
        self._validate_request_model(
            record,
            request,
            access_context=access_context,
        )

        request_id = self._request_id(
            access_context,
        )

        _log_info(
            "Model stream started",
            model_step="stream-started",
            model_id=record.model_id,
            provider_type=record.provider_type,
            request_id=request_id,
            request_model=request.model,
        )

        try:
            async for event in self._lifecycle.stream(
                record.model_id,
                request,
                idle_timeout_seconds=idle_timeout_seconds,
                request_id=request_id,
            ):
                yield event

        except asyncio.CancelledError:
            raise

        except ModelError:
            raise

        except Exception as exc:
            _log_warning(
                "Model stream failed",
                model_step="stream-failed",
                model_id=record.model_id,
                provider_type=record.provider_type,
                request_id=request_id,
                request_model=request.model,
                error_type=exc.__class__.__name__,
                error_message=str(
                    exc,
                ),
                exc_info=True,
            )

            raise translate_provider_error(
                exc,
                provider_type=record.provider_type,
                model_id=record.model_id,
                request_id=request_id,
            ) from exc

        finally:
            _log_info(
                "Model stream finished",
                model_step="stream-finished",
                model_id=record.model_id,
                provider_type=record.provider_type,
                request_id=request_id,
            )

    # ========================================================
    # Factory und Abhängigkeiten
    # ========================================================

    def _create_lifecycle_definition(
        self,
        record: _ModelServiceRecord,
    ) -> ModelLifecycleDefinition:
        """
        Erstellt eine unveränderliche Lifecycle-Definition.
        """

        manifest = record.manifest
        lifecycle_manifest = manifest.lifecycle
        policy_defaults = ModelLifecyclePolicy()

        policy = ModelLifecyclePolicy(
            generation_timeout_seconds=(
                lifecycle_manifest.generation_timeout_seconds
                if lifecycle_manifest.generation_timeout_seconds is not None
                else policy_defaults.generation_timeout_seconds
            ),
            stream_idle_timeout_seconds=(
                lifecycle_manifest.stream_idle_timeout_seconds
                if lifecycle_manifest.stream_idle_timeout_seconds is not None
                else policy_defaults.stream_idle_timeout_seconds
            ),
            idle_unload_seconds=lifecycle_manifest.idle_unload_seconds,
            shutdown_timeout_seconds=(
                lifecycle_manifest.shutdown_timeout_seconds
                if lifecycle_manifest.shutdown_timeout_seconds is not None
                else policy_defaults.shutdown_timeout_seconds
            ),
            unload_when_idle=lifecycle_manifest.unload_when_idle,
            eager_create=lifecycle_manifest.eager_create,
            eager_load=lifecycle_manifest.eager_load,
        )

        async def backend_factory(
            record_snapshot: _ModelServiceRecord = record,
        ) -> BaseModelBackend:
            return await self._create_backend(
                record_snapshot,
            )

        return ModelLifecycleDefinition(
            model_id=record.model_id,
            provider_type=record.provider_type,
            factory=backend_factory,
            policy=policy,
            metadata={
                "manifest_path": str(
                    record.loaded_manifest.manifest_path,
                ),
                "manifest_schema_version": manifest.schema_version,
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
        """
        Erzeugt das konkrete Provider-Backend.

        Die logische Kernschmied-ID bleibt vom providerinternen
        Modellnamen getrennt.
        """

        manifest = record.manifest
        provider_type = record.provider_type

        provider_config = dict(
            manifest.provider.config,
        )

        provider_config.pop(
            "model_id",
            None,
        )
        provider_config.pop(
            "logical_model_id",
            None,
        )
        provider_config.pop(
            "display_name",
            None,
        )

        provider_config["logical_model_id"] = record.model_id

        provider_config["display_name"] = manifest.display_name

        if manifest.limits.context_window is not None:
            provider_config.setdefault(
                "context_window",
                manifest.limits.context_window,
            )

        dependencies = await self._resolve_dependencies(
            record,
        )

        _log_info(
            "Creating model backend",
            model_step="backend-create-started",
            model_id=record.model_id,
            provider_type=provider_type,
            provider_model=provider_config.get(
                "model",
            ),
            logical_model_id=provider_config.get(
                "logical_model_id",
            ),
            base_url=provider_config.get(
                "base_url",
            ),
        )

        try:
            backend = await self._provider_registry.create(
                provider_type=provider_type,
                provider_config=provider_config,
                dependencies=dependencies,
            )

        except asyncio.CancelledError:
            raise

        except ModelError:
            raise

        except Exception as exc:
            _log_warning(
                "Model backend creation failed",
                model_step="backend-create-failed",
                model_id=record.model_id,
                provider_type=provider_type,
                provider_model=provider_config.get(
                    "model",
                ),
                logical_model_id=provider_config.get(
                    "logical_model_id",
                ),
                base_url=provider_config.get(
                    "base_url",
                ),
                error_type=exc.__class__.__name__,
                error_message=str(
                    exc,
                ),
                exc_info=True,
            )
            raise

        _log_info(
            "Model backend created",
            model_step="backend-created",
            model_id=record.model_id,
            provider_type=provider_type,
            backend_type=backend.__class__.__name__,
        )

        return backend

    async def _resolve_dependencies(
        self,
        record: _ModelServiceRecord,
    ) -> dict[str, Any]:
        """
        Löst statische, dynamische und geheime Abhängigkeiten auf.
        """

        dependencies: dict[str, Any] = dict(
            self._common_dependencies,
        )

        if self._dependency_provider is not None:
            provided = self._dependency_provider(
                record.loaded_manifest,
                None,
            )

            if inspect.isawaitable(
                provided,
            ):
                provided = await provided

            dependencies.update(
                dict(
                    provided,
                ),
            )

        resolved_secrets = await self._resolve_secrets(
            record,
        )

        dependencies["secrets"] = dict(
            resolved_secrets,
        )

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
        """
        Löst Secret-Referenzen serverseitig auf.
        """

        resolved: dict[
            str,
            Any,
        ] = {}

        for (
            secret_name,
            reference,
        ) in record.manifest.provider.secrets.items():
            context = ModelSecretResolutionContext(
                model_id=record.model_id,
                provider_type=record.provider_type,
                manifest_path=record.loaded_manifest.manifest_path,
                secret_name=secret_name,
                access_context=None,
            )

            try:
                value = self._secret_resolver.resolve(
                    reference,
                    context,
                )

                if inspect.isawaitable(
                    value,
                ):
                    value = await value

            except asyncio.CancelledError:
                raise

            except ModelError:
                raise

            except Exception as exc:
                raise ModelProviderDependencyError(
                    provider_type=record.provider_type,
                    model_id=record.model_id,
                    dependency=(f"Secret '{secret_name}'"),
                    request_id=None,
                    cause=exc,
                ) from exc

            if value is None and reference.required:
                raise ModelProviderDependencyError(
                    provider_type=record.provider_type,
                    model_id=record.model_id,
                    dependency=(f"Secret '{secret_name}'"),
                    request_id=None,
                )

            if value is not None:
                resolved[secret_name] = value

        return resolved

    # ========================================================
    # Capability- und Request-Prüfung
    # ========================================================

    def _validate_request_capabilities(
        self,
        record: _ModelServiceRecord,
        request: GenerationRequest,
        *,
        access_context: ModelAccessContext | None,
    ) -> None:
        self._require_capability(
            record,
            ModelManifestCapability.CHAT.value,
            access_context=access_context,
        )

        if request.tools or request.tool_choice is not None:
            self._require_capability(
                record,
                ModelManifestCapability.TOOLS.value,
                access_context=access_context,
            )

        if (
            request.response_format is not None
            and request.response_format.type != "text"
        ):
            self._require_capability(
                record,
                ModelManifestCapability.STRUCTURED_OUTPUT.value,
                access_context=access_context,
            )

    def _validate_request_model(
        self,
        record: _ModelServiceRecord,
        request: GenerationRequest,
        *,
        access_context: ModelAccessContext | None,
    ) -> None:
        """
        Stellt sicher, dass GenerationRequest.model die logische
        Kernschmied-Modell-ID enthält.
        """

        requested_model_id = self._normalize_model_id(
            request.model,
        )

        if requested_model_id == record.model_id:
            return

        raise InvalidModelProviderConfigurationError(
            provider_type=record.provider_type,
            model_id=record.model_id,
            field="request.model",
            reason=(
                "Der GenerationRequest verwendet die "
                f"logische Modell-ID '{requested_model_id}', "
                "ausgewählt wurde jedoch "
                f"'{record.model_id}'. Der Ollama-Modellname "
                "darf an dieser Stelle nicht direkt verwendet "
                "werden."
            ),
            request_id=self._request_id(
                access_context,
            ),
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
                access_context.request_id if access_context is not None else None
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
        effective_context = context if context is not None else ModelAccessContext()

        authorization_request = ModelAuthorizationRequest(
            action=action,
            model_id=model_id,
            provider_type=provider_type,
            context=effective_context,
            metadata=dict(
                metadata or {},
            ),
        )

        decision = self._authorizer.authorize(
            authorization_request,
        )

        if inspect.isawaitable(
            decision,
        ):
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
        effective_context = context if context is not None else ModelAccessContext()

        authorization_request = ModelAuthorizationRequest(
            action=action,
            model_id=model_id,
            provider_type=provider_type,
            context=effective_context,
        )

        decision = self._authorizer.authorize(
            authorization_request,
        )

        if inspect.isawaitable(
            decision,
        ):
            decision = await decision

        return bool(
            decision,
        )

    # ========================================================
    # Registry- und Record-Helfer
    # ========================================================

    async def _find_model_record(
        self,
        model_id: str,
    ) -> _ModelServiceRecord | None:
        """
        Sucht einen ModelService-Record.

        Ist eine ModelRegistry injiziert, ist ausschließlich diese
        Registry die Wahrheitsquelle.
        """

        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        if self._model_registry is not None:
            try:
                entry = await self._model_registry.get_entry(
                    normalized_model_id,
                )

            except ModelNotRegisteredError:
                return None

            runtime_enabled = self._runtime_enabled.get(
                normalized_model_id,
                entry.enabled,
            )

            return _ModelServiceRecord(
                loaded_manifest=entry.loaded_manifest,
                runtime_enabled=runtime_enabled,
                registration_index=entry.registration_index,
                registered_at_loop_time=entry.registered_at_monotonic,
            )

        async with self._registry_lock:
            return self._records.get(
                normalized_model_id,
            )

    async def _require_model_record(
        self,
        model_id: str,
        *,
        access_context: ModelAccessContext | None = None,
    ) -> _ModelServiceRecord:
        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        record = await self._find_model_record(
            normalized_model_id,
        )

        if record is None:
            raise ModelNotRegisteredError(
                normalized_model_id,
                request_id=self._request_id(
                    access_context,
                ),
            )

        return record

    async def _list_records(
        self,
    ) -> list[_ModelServiceRecord]:
        """
        Liefert alle Records aus der aktiven Wahrheitsquelle.
        """

        if self._model_registry is not None:
            entries = await self._model_registry.list_entries(
                enabled_only=False,
            )

            return [
                _ModelServiceRecord(
                    loaded_manifest=entry.loaded_manifest,
                    runtime_enabled=self._runtime_enabled.get(
                        entry.model_id,
                        entry.enabled,
                    ),
                    registration_index=entry.registration_index,
                    registered_at_loop_time=entry.registered_at_monotonic,
                )
                for entry in entries
            ]

        async with self._registry_lock:
            return list(
                self._records.values(),
            )

    async def _store_record(
        self,
        record: _ModelServiceRecord,
        *,
        replace: bool,
    ) -> None:
        """
        Speichert einen Record in der aktiven Wahrheitsquelle.
        """

        if self._model_registry is not None:
            await self._model_registry.register(
                record.loaded_manifest,
                replace=replace,
            )
            return

        async with self._registry_lock:
            if record.model_id in self._records and not replace:
                raise DuplicateModelRegistrationError(
                    record.model_id,
                )

            self._records[record.model_id] = record

    async def _remove_record(
        self,
        model_id: str,
    ) -> bool:
        """
        Entfernt einen Record aus der aktiven Wahrheitsquelle.
        """

        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        if self._model_registry is not None:
            return await self._model_registry.unregister(
                normalized_model_id,
            )

        async with self._registry_lock:
            return (
                self._records.pop(
                    normalized_model_id,
                    None,
                )
                is not None
            )

    async def _restore_record(
        self,
        record: _ModelServiceRecord,
    ) -> None:
        """
        Stellt einen vorherigen Registry-Zustand wieder her.
        """

        try:
            if self._model_registry is not None:
                await self._model_registry.register(
                    record.loaded_manifest,
                    replace=True,
                )
            else:
                async with self._registry_lock:
                    self._records[record.model_id] = record

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            _log_warning(
                "Previous model record could not be restored",
                model_step="record-rollback-failed",
                model_id=record.model_id,
                provider_type=record.provider_type,
                error_type=exc.__class__.__name__,
                error_message=str(
                    exc,
                ),
                exc_info=True,
            )

    async def _rollback_registration(
        self,
        *,
        model_id: str,
        existing_record: _ModelServiceRecord | None,
        old_lifecycle_definition: ModelLifecycleDefinition | None,
        old_runtime_enabled: bool | None,
        old_lifecycle_removed: bool,
        new_lifecycle_registered: bool,
        registry_updated: bool,
    ) -> None:
        """
        Stellt nach einer fehlgeschlagenen Registrierung den vorherigen
        Zustand bestmöglich wieder her.
        """

        if new_lifecycle_registered:
            try:
                await self._lifecycle.unregister(
                    model_id,
                    shutdown_backend=True,
                )

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                _log_warning(
                    "New lifecycle could not be removed during rollback",
                    model_step="new-lifecycle-rollback-failed",
                    model_id=model_id,
                    error_type=exc.__class__.__name__,
                    error_message=str(
                        exc,
                    ),
                    exc_info=True,
                )

        if registry_updated:
            try:
                await self._remove_record(
                    model_id,
                )

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                _log_warning(
                    "New model record could not be removed during rollback",
                    model_step="new-record-rollback-failed",
                    model_id=model_id,
                    error_type=exc.__class__.__name__,
                    error_message=str(
                        exc,
                    ),
                    exc_info=True,
                )

        if existing_record is not None:
            await self._restore_record(
                existing_record,
            )

            if old_runtime_enabled is not None:
                self._runtime_enabled[model_id] = old_runtime_enabled

        else:
            self._runtime_enabled.pop(
                model_id,
                None,
            )

        if old_lifecycle_definition is not None and old_lifecycle_removed:
            await self._restore_lifecycle_definition(
                old_lifecycle_definition,
            )

    async def _restore_lifecycle_definition(
        self,
        definition: ModelLifecycleDefinition,
    ) -> None:
        """
        Stellt eine vorherige Lifecycle-Definition bestmöglich wieder her.
        """

        try:
            await self._lifecycle.register(
                definition,
            )

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            _log_warning(
                "Previous lifecycle definition could not be restored",
                model_step="lifecycle-rollback-failed",
                model_id=definition.model_id,
                provider_type=definition.provider_type,
                error_type=exc.__class__.__name__,
                error_message=str(
                    exc,
                ),
                exc_info=True,
            )

    async def _next_registration_index(
        self,
    ) -> int:
        async with self._registry_lock:
            self._registration_counter += 1

            return self._registration_counter

    async def _get_registration_lock(
        self,
        model_id: str,
    ) -> asyncio.Lock:
        """
        Holt oder erstellt ein Lock für eine Modell-ID.
        """

        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        async with self._registry_lock:
            lock = self._registration_locks.get(
                normalized_model_id,
            )

            if lock is None:
                lock = asyncio.Lock()

                self._registration_locks[normalized_model_id] = lock

            return lock

    # ========================================================
    # Modellauflösung
    # ========================================================

    async def _resolve_model_id(
        self,
        model_id: str | None,
        *,
        access_context: ModelAccessContext | None = None,
    ) -> str:
        """
        Löst eine explizite oder konfigurierte Standardmodell-ID auf.
        """

        if model_id is not None:
            normalized_model_id = self._normalize_model_id(
                model_id,
            )

            await self._require_model_record(
                normalized_model_id,
                access_context=access_context,
            )

            return normalized_model_id

        if self._default_model_id is None:
            raise ModelNotRegisteredError(
                "<default>",
                request_id=self._request_id(
                    access_context,
                ),
            )

        await self._require_model_record(
            self._default_model_id,
            access_context=access_context,
        )

        return self._default_model_id

    # ========================================================
    # Diagnose
    # ========================================================

    def _create_service_info(
        self,
        record: _ModelServiceRecord,
    ) -> ModelServiceInfo:
        try:
            lifecycle_snapshot = self._lifecycle.get_snapshot(
                record.model_id,
            )

        except Exception as exc:
            lifecycle_snapshot = None

            _log_warning(
                "Lifecycle snapshot could not be read",
                model_step="lifecycle-snapshot-failed",
                model_id=record.model_id,
                provider_type=record.provider_type,
                error_type=exc.__class__.__name__,
                error_message=str(
                    exc,
                ),
            )

        manifest = record.manifest

        return ModelServiceInfo(
            model_id=record.model_id,
            display_name=manifest.display_name,
            description=manifest.description,
            provider_type=record.provider_type,
            manifest_enabled=manifest.is_enabled,
            runtime_enabled=record.runtime_enabled,
            effectively_enabled=record.effectively_enabled,
            status=manifest.status.value,
            runtime=manifest.runtime.value,
            capabilities=tuple(
                sorted(
                    manifest.capabilities,
                ),
            ),
            tags=tuple(
                sorted(
                    manifest.tags,
                ),
            ),
            manifest_path=record.loaded_manifest.manifest_path,
            lifecycle=lifecycle_snapshot,
            metadata={
                "registration_index": record.registration_index,
                "registered_at_loop_time": record.registered_at_loop_time,
                "presentation": manifest.presentation.model_dump(
                    mode="json",
                    exclude_none=True,
                ),
                "limits": manifest.limits.model_dump(
                    mode="json",
                    exclude_none=True,
                ),
                "manifest_metadata": dict(
                    manifest.metadata,
                ),
                "is_default": (self._default_model_id == record.model_id),
            },
        )

    @staticmethod
    def _registration_error_result(
        *,
        path: Path,
        error: BaseException,
    ) -> ModelRegistrationResult:
        model_id = getattr(
            error,
            "model_id",
            None,
        )
        provider_type = getattr(
            error,
            "provider_type",
            None,
        )
        error_code = getattr(
            error,
            "code",
            None,
        )

        return ModelRegistrationResult(
            model_id=(
                str(
                    model_id,
                )
                if model_id is not None
                else None
            ),
            manifest_path=path,
            provider_type=(
                str(
                    provider_type,
                )
                if provider_type is not None
                else None
            ),
            status=ModelRegistrationStatus.FAILED,
            message=str(
                error,
            ),
            error_type=error.__class__.__name__,
            error_code=(
                str(
                    error_code,
                )
                if error_code is not None
                else None
            ),
        )

    # ========================================================
    # Zustandsprüfungen
    # ========================================================

    def _ensure_service_not_shutdown(
        self,
        *,
        model_id: str,
        provider_type: str | None,
        access_context: ModelAccessContext | None,
    ) -> None:
        if not self._shutdown_requested:
            return

        raise ModelUnavailableError(
            model_id=model_id,
            provider_type=provider_type,
            reason=("Der ModelService wurde bereits beendet."),
            request_id=self._request_id(
                access_context,
            ),
        )

    def _ensure_service_available(
        self,
        *,
        model_id: str,
        provider_type: str | None,
        access_context: ModelAccessContext | None,
    ) -> None:
        request_id = self._request_id(
            access_context,
        )

        if self._shutdown_requested:
            raise ModelUnavailableError(
                model_id=model_id,
                provider_type=provider_type,
                reason=("Der ModelService wurde bereits beendet."),
                request_id=request_id,
            )

        if not self._started:
            raise ModelUnavailableError(
                model_id=model_id,
                provider_type=provider_type,
                reason=("Der ModelService wurde noch nicht gestartet."),
                request_id=request_id,
            )

    @staticmethod
    def _ensure_enabled(
        record: _ModelServiceRecord,
        *,
        access_context: ModelAccessContext | None,
    ) -> None:
        if record.effectively_enabled:
            return

        async def is_model_available(
            self,
            *,
            entry: ModelRegistryEntry,
        ) -> tuple[bool, bool]:
            """
            Probe whether a model (registry entry) is available and selectable at runtime.

            Returns (available, selectable). This implementation tries to create
            a provider backend via the configured `ModelProviderRegistry` and
            calls `is_available()` / `is_selectable()` if present. Any error yields
            (False, False) conservatively.
            """
            manifest = entry.manifest

            provider_type = entry.provider_type

            try:
                provider_config = dict(manifest.provider.config)
                provider_config.pop("model_id", None)
                provider_config.pop("logical_model_id", None)
                provider_config.pop("display_name", None)

                provider_config["logical_model_id"] = entry.model_id
                provider_config["display_name"] = manifest.display_name

                # Create backend instance (may be async-heavy). Pass no dependencies.
                backend = await self._provider_registry.create(
                    provider_type=provider_type,
                    provider_config=provider_config,
                    dependencies=None,
                )

                available = True
                selectable = True

                is_avail = getattr(backend, "is_available", None)
                if callable(is_avail):
                    try:
                        avail_res = is_avail()
                        if asyncio.iscoroutine(avail_res):
                            available = await avail_res
                        else:
                            available = bool(avail_res)
                    except Exception:
                        available = False

                is_sel = getattr(backend, "is_selectable", None)
                if callable(is_sel):
                    try:
                        sel_res = is_sel()
                        if asyncio.iscoroutine(sel_res):
                            selectable = await sel_res
                        else:
                            selectable = bool(sel_res)
                    except Exception:
                        selectable = False

                # Try to close/unload backend if it exposes a cleanup method
                cleanup = getattr(backend, "close", None) or getattr(backend, "shutdown", None)
                if callable(cleanup):
                    try:
                        res = cleanup()
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception:
                        pass

                return bool(available), bool(selectable)

            except Exception:
                return False, False

        raise ModelDisabledError(
            record.model_id,
            request_id=(
                access_context.request_id if access_context is not None else None
            ),
        )

    # ========================================================
    # Normalisierung
    # ========================================================

    @staticmethod
    def _request_id(
        access_context: ModelAccessContext | None,
    ) -> str | None:
        if access_context is None:
            return None

        return access_context.request_id

    @staticmethod
    def _normalize_model_id(
        model_id: str,
    ) -> str:
        normalized = model_id.strip().lower()

        if not normalized:
            raise ValueError(
                "model_id darf nicht leer sein.",
            )

        return normalized

    @staticmethod
    def _normalize_provider_type(
        provider_type: str,
    ) -> str:
        normalized = provider_type.strip().lower()

        if not normalized:
            raise ValueError(
                "provider_type darf nicht leer sein.",
            )

        return normalized


# ============================================================
# Logging
# ============================================================


def _log_context(
    **values: object,
) -> dict[str, object]:
    return {
        "source": SOURCE_FILE,
        "area": LOG_AREA,
        **values,
    }


def _log_info(
    message: str,
    **context: object,
) -> None:
    logger.info(
        message,
        extra=_log_context(
            **context,
        ),
    )


def _log_warning(
    message: str,
    *,
    exc_info: bool = False,
    **context: object,
) -> None:
    logger.warning(
        message,
        extra=_log_context(
            **context,
        ),
        exc_info=exc_info,
    )


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
