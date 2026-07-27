# F:\Kernschmied\backend\app\models\lifecycle.py

"""
Lifecycle-Verwaltung für Modell-Backends.

Dieses Modul verwaltet den kontrollierten Lebenszyklus registrierter
Modelle und Provider-Backends.

Verantwortlichkeiten:

- Lazy-Erzeugung von Backends
- kontrolliertes Laden und Entladen
- parallele Zugriffe synchronisieren
- aktive Generierungen zählen
- Idle-Unload vorbereiten und ausführen
- Fehler in stabile Modellfehler übersetzen
- Shutdown aller Backends
- Lifecycle-Zustände für Diagnose und API bereitstellen

Nicht verantwortlich für:

- Manifest-Discovery
- Modellfreigaben und Autorisierung
- fachliche Modellwahl
- Prompt-Aufbereitung
- Chat-Persistenz
- Tool-Ausführung
- API-Endpunkte

Die ModelRegistry beziehungsweise der ModelService entscheiden, welches
Modell verwendet werden darf. Der Lifecycle verwaltet ausschließlich
bereits freigegebene Modelldefinitionen.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Final

from app.contracts.model_backend import (
    BaseModelBackend,
    GenerationRequest,
    StreamEvent,
)
from app.models.errors import (
    ModelError,
    ModelGenerationCancelledError,
    ModelGenerationTimeoutError,
    ModelLoadError,
    ModelNotReadyError,
    ModelOperationConflictError,
    ModelShutdownError,
    ModelStreamCancelledError,
    ModelStreamTimeoutError,
    ModelUnavailableError,
    ModelUnloadError,
    translate_provider_error,
)


logger = logging.getLogger(__name__)


DEFAULT_GENERATION_TIMEOUT_SECONDS: Final[float] = 600.0
DEFAULT_STREAM_IDLE_TIMEOUT_SECONDS: Final[float] = 600.0
DEFAULT_IDLE_UNLOAD_SECONDS: Final[float | None] = None
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS: Final[float] = 60.0
DEFAULT_MAINTENANCE_INTERVAL_SECONDS: Final[float] = 30.0


# ============================================================
# Typen
# ============================================================


BackendFactory = Callable[
    [],
    BaseModelBackend | Awaitable[BaseModelBackend],
]


class ModelLifecycleState(StrEnum):
    """
    Stabiler Laufzeitzustand eines Modell-Backends.
    """

    REGISTERED = "registered"
    CREATING = "creating"
    CREATED = "created"
    LOADING = "loading"
    READY = "ready"
    BUSY = "busy"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"
    FAILED = "failed"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


@dataclass(frozen=True, slots=True)
class ModelLifecyclePolicy:
    """
    Laufzeitregeln für ein Modell.

    generation_timeout_seconds:
        Maximale Dauer einer nicht streamenden Generierung.

    stream_idle_timeout_seconds:
        Maximale Wartezeit zwischen zwei Stream-Events. Die gesamte
        Streaming-Dauer wird damit nicht pauschal begrenzt.

    idle_unload_seconds:
        Zeit ohne aktive Nutzung, nach der ein unterstütztes lokales
        Backend entladen werden darf. None deaktiviert Idle-Unload.

    unload_when_idle:
        Aktiviert automatisches Entladen durch den Maintenance-Task.

    shutdown_timeout_seconds:
        Maximale Wartezeit auf shutdown() oder unload_model().

    eager_create:
        Erzeugt das Backend beim Registrieren oder Starten des Lifecycles.

    eager_load:
        Ruft load() beim Starten auf, sofern das Backend diese Methode
        besitzt.

    retry_failed_creation:
        Erlaubt nach einem Factory-Fehler einen späteren erneuten Versuch.

    retry_failed_load:
        Erlaubt nach einem Ladefehler einen späteren erneuten Versuch.
    """

    generation_timeout_seconds: float = (
        DEFAULT_GENERATION_TIMEOUT_SECONDS
    )
    stream_idle_timeout_seconds: float = (
        DEFAULT_STREAM_IDLE_TIMEOUT_SECONDS
    )
    idle_unload_seconds: float | None = DEFAULT_IDLE_UNLOAD_SECONDS
    shutdown_timeout_seconds: float = DEFAULT_SHUTDOWN_TIMEOUT_SECONDS

    unload_when_idle: bool = False
    eager_create: bool = False
    eager_load: bool = False

    retry_failed_creation: bool = True
    retry_failed_load: bool = True

    def __post_init__(self) -> None:
        if self.generation_timeout_seconds <= 0:
            raise ValueError(
                "generation_timeout_seconds muss größer als 0 sein.",
            )

        if self.stream_idle_timeout_seconds <= 0:
            raise ValueError(
                "stream_idle_timeout_seconds muss größer als 0 sein.",
            )

        if self.shutdown_timeout_seconds <= 0:
            raise ValueError(
                "shutdown_timeout_seconds muss größer als 0 sein.",
            )

        if (
            self.idle_unload_seconds is not None
            and self.idle_unload_seconds <= 0
        ):
            raise ValueError(
                "idle_unload_seconds muss größer als 0 oder None sein.",
            )

        if self.unload_when_idle and self.idle_unload_seconds is None:
            raise ValueError(
                "unload_when_idle benötigt idle_unload_seconds.",
            )

        if self.eager_load and not self.eager_create:
            object.__setattr__(
                self,
                "eager_create",
                True,
            )


@dataclass(frozen=True, slots=True)
class ModelLifecycleDefinition:
    """
    Serverseitig registrierte Lifecycle-Definition eines Modells.
    """

    model_id: str
    provider_type: str
    factory: BackendFactory
    policy: ModelLifecyclePolicy = field(
        default_factory=ModelLifecyclePolicy,
    )
    metadata: dict[str, Any] = field(
        default_factory=lambda: {},
    )

    def __post_init__(self) -> None:
        model_id = self.model_id.strip()
        provider_type = self.provider_type.strip().lower()

        if not model_id:
            raise ValueError(
                "model_id darf nicht leer sein.",
            )

        if not provider_type:
            raise ValueError(
                "provider_type darf nicht leer sein.",
            )

        if not callable(self.factory):
            raise TypeError(
                "factory muss aufrufbar sein.",
            )

        object.__setattr__(
            self,
            "model_id",
            model_id,
        )
        object.__setattr__(
            self,
            "provider_type",
            provider_type,
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class ModelLifecycleSnapshot:
    """
    Diagnoseansicht eines Modell-Lifecycles.
    """

    model_id: str
    provider_type: str
    state: ModelLifecycleState

    backend_created: bool
    backend_loaded: bool

    active_operations: int
    successful_operations: int
    failed_operations: int

    created_at_monotonic: float | None
    loaded_at_monotonic: float | None
    last_used_at_monotonic: float | None
    failed_at_monotonic: float | None

    last_error_type: str | None
    last_error_message: str | None

    idle_seconds: float | None
    unload_when_idle: bool
    idle_unload_seconds: float | None

    metadata: Mapping[str, Any]


# ============================================================
# Interner Eintrag
# ============================================================


@dataclass(slots=True)
class _ModelLifecycleEntry:
    definition: ModelLifecycleDefinition

    backend: BaseModelBackend | None = None
    state: ModelLifecycleState = ModelLifecycleState.REGISTERED

    active_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0

    created_at_monotonic: float | None = None
    loaded_at_monotonic: float | None = None
    last_used_at_monotonic: float | None = None
    failed_at_monotonic: float | None = None

    last_error: BaseException | None = None

    lifecycle_lock: asyncio.Lock = field(
        default_factory=asyncio.Lock,
    )
    usage_condition: asyncio.Condition = field(
        default_factory=asyncio.Condition,
    )

    @property
    def model_id(self) -> str:
        return self.definition.model_id

    @property
    def provider_type(self) -> str:
        return self.definition.provider_type

    @property
    def policy(self) -> ModelLifecyclePolicy:
        return self.definition.policy


# ============================================================
# Lifecycle Manager
# ============================================================


class ModelLifecycleManager:
    """
    Verwaltet Backends freigegebener Modelle.

    Der Manager ist absichtlich kein globales Singleton. Er wird über den
    Application-Lifecycle erzeugt und per Dependency Injection an Services
    übergeben.
    """

    def __init__(
        self,
        *,
        maintenance_interval_seconds: float = (
            DEFAULT_MAINTENANCE_INTERVAL_SECONDS
        ),
    ) -> None:
        if maintenance_interval_seconds <= 0:
            raise ValueError(
                "maintenance_interval_seconds muss größer als 0 sein.",
            )

        self._maintenance_interval_seconds = (
            maintenance_interval_seconds
        )

        self._entries: dict[str, _ModelLifecycleEntry] = {}
        self._registry_lock = asyncio.Lock()

        self._maintenance_task: asyncio.Task[None] | None = None
        self._started = False
        self._shutdown_requested = False

    # ========================================================
    # Registrierung
    # ========================================================

    async def register(
        self,
        definition: ModelLifecycleDefinition,
    ) -> None:
        """
        Registriert ein Modell für die Lifecycle-Verwaltung.
        """

        async with self._registry_lock:
            if self._shutdown_requested:
                raise ModelOperationConflictError(
                    model_id=definition.model_id,
                    operation="register",
                    lifecycle_state=ModelLifecycleState.SHUTDOWN,
                    reason="Der Lifecycle wurde bereits beendet.",
                )

            if definition.model_id in self._entries:
                raise ModelOperationConflictError(
                    model_id=definition.model_id,
                    operation="register",
                    lifecycle_state=(
                        self._entries[definition.model_id].state
                    ),
                    reason="Das Modell ist bereits registriert.",
                )

            entry = _ModelLifecycleEntry(
                definition=definition,
            )

            self._entries[definition.model_id] = entry

        if self._started and definition.policy.eager_create:
            await self.ensure_ready(
                definition.model_id,
                load=definition.policy.eager_load,
            )

    async def unregister(
        self,
        model_id: str,
        *,
        shutdown_backend: bool = True,
    ) -> bool:
        """
        Entfernt ein Modell aus dem Lifecycle.

        Bei shutdown_backend=True wird das Backend zuvor kontrolliert
        heruntergefahren.
        """

        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        async with self._registry_lock:
            entry = self._entries.get(
                normalized_model_id,
            )

        if entry is None:
            return False

        if shutdown_backend:
            await self.shutdown_model(
                normalized_model_id,
            )

        async with self._registry_lock:
            current_entry = self._entries.get(
                normalized_model_id,
            )

            if current_entry is not entry:
                return False

            del self._entries[
                normalized_model_id
            ]

        return True

    def has(
        self,
        model_id: str,
    ) -> bool:
        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        return normalized_model_id in self._entries

    def list_model_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            sorted(self._entries),
        )

    # ========================================================
    # Start und Maintenance
    # ========================================================

    async def start(self) -> None:
        """
        Startet den Lifecycle und optionales Idle-Unload.
        """

        if self._shutdown_requested:
            raise RuntimeError(
                "Ein bereits beendeter Lifecycle kann nicht neu "
                "gestartet werden.",
            )

        if self._started:
            return

        self._started = True

        eager_entries = [
            entry
            for entry in self._entries.values()
            if entry.policy.eager_create
        ]

        for entry in eager_entries:
            try:
                await self.ensure_ready(
                    entry.model_id,
                    load=entry.policy.eager_load,
                )
            except Exception:
                logger.exception(
                    "Eager model initialization failed",
                    extra={
                        "model_id": entry.model_id,
                        "provider_type": entry.provider_type,
                    },
                )

        if any(
            entry.policy.unload_when_idle
            for entry in self._entries.values()
        ):
            self._maintenance_task = asyncio.create_task(
                self._maintenance_loop(),
                name="model-lifecycle-maintenance",
            )

    async def run_maintenance_once(self) -> tuple[str, ...]:
        """
        Führt einen einzelnen Idle-Unload-Durchlauf aus.

        Rückgabe enthält die erfolgreich entladenen Modell-IDs.
        """

        unloaded_model_ids: list[str] = []
        now = time.monotonic()

        entries = tuple(
            self._entries.values(),
        )

        for entry in entries:
            if not entry.policy.unload_when_idle:
                continue

            idle_unload_seconds = (
                entry.policy.idle_unload_seconds
            )

            if idle_unload_seconds is None:
                continue

            if entry.active_operations > 0:
                continue

            if entry.backend is None:
                continue

            if entry.state not in {
                ModelLifecycleState.CREATED,
                ModelLifecycleState.READY,
                ModelLifecycleState.UNLOADED,
            }:
                continue

            last_activity = (
                entry.last_used_at_monotonic
                or entry.loaded_at_monotonic
                or entry.created_at_monotonic
            )

            if last_activity is None:
                continue

            if now - last_activity < idle_unload_seconds:
                continue

            try:
                unloaded = await self.unload(
                    entry.model_id,
                    wait_for_active_operations=False,
                )
            except Exception:
                logger.exception(
                    "Idle model unload failed",
                    extra={
                        "model_id": entry.model_id,
                        "provider_type": entry.provider_type,
                    },
                )
                continue

            if unloaded:
                unloaded_model_ids.append(
                    entry.model_id,
                )

        return tuple(unloaded_model_ids)

    async def _maintenance_loop(self) -> None:
        try:
            while not self._shutdown_requested:
                await asyncio.sleep(
                    self._maintenance_interval_seconds,
                )

                if self._shutdown_requested:
                    break

                await self.run_maintenance_once()

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception(
                "Model lifecycle maintenance loop failed",
            )

    # ========================================================
    # Backend-Auflösung
    # ========================================================

    async def get_backend(
        self,
        model_id: str,
        *,
        ensure_loaded: bool = True,
    ) -> BaseModelBackend:
        """
        Liefert das Backend eines Modells.

        ensure_loaded=True ruft load() auf, sofern das Backend diese
        Lifecycle-Methode bereitstellt.
        """

        entry = self._get_entry(
            model_id,
        )

        await self._ensure_backend_created(
            entry,
        )

        if ensure_loaded:
            await self._ensure_backend_loaded(
                entry,
            )

        backend = entry.backend

        if backend is None:
            raise ModelNotReadyError(
                entry.model_id,
                lifecycle_state=entry.state,
            )

        return backend

    async def ensure_ready(
        self,
        model_id: str,
        *,
        load: bool = True,
    ) -> BaseModelBackend:
        """
        Stellt sicher, dass das Backend erzeugt und optional geladen ist.
        """

        return await self.get_backend(
            model_id,
            ensure_loaded=load,
        )

    async def _ensure_backend_created(
        self,
        entry: _ModelLifecycleEntry,
    ) -> None:
        if entry.backend is not None:
            return

        async with entry.lifecycle_lock:
            if entry.backend is not None:
                return

            if entry.state == ModelLifecycleState.SHUTDOWN:
                raise ModelNotReadyError(
                    entry.model_id,
                    lifecycle_state=entry.state,
                )

            if (
                entry.state == ModelLifecycleState.FAILED
                and not entry.policy.retry_failed_creation
            ):
                raise ModelNotReadyError(
                    entry.model_id,
                    lifecycle_state=entry.state,
                )

            entry.state = ModelLifecycleState.CREATING

            try:
                backend_or_awaitable = (
                    entry.definition.factory()
                )

                if inspect.isawaitable(
                    backend_or_awaitable,
                ):
                    backend = await backend_or_awaitable
                else:
                    backend = backend_or_awaitable

                # Vertragssicherheit: Die Factory muss ein BaseModelBackend zurückgeben
                # Ein expliziter isinstance-Check ist hier notwendig für Laufzeitsicherheit.
                if not isinstance(backend, BaseModelBackend):  # type: ignore[reportUnnecessaryIsInstance]
                    raise TypeError(
                        "Die Backend-Factory hat keine "
                        "BaseModelBackend-Instanz zurückgegeben.",
                    )

                entry.backend = backend
                entry.created_at_monotonic = (
                    time.monotonic()
                )
                entry.last_used_at_monotonic = (
                    entry.created_at_monotonic
                )
                entry.last_error = None
                entry.failed_at_monotonic = None
                entry.state = ModelLifecycleState.CREATED

            except asyncio.CancelledError:
                entry.state = ModelLifecycleState.REGISTERED
                raise

            except Exception as exc:
                entry.state = ModelLifecycleState.FAILED
                entry.last_error = exc
                entry.failed_at_monotonic = time.monotonic()

                translated = translate_provider_error(
                    exc,
                    provider_type=entry.provider_type,
                    model_id=entry.model_id,
                )

                # translated ist bereits ein ModelError (garantiert durch translate_provider_error)
                raise translated from exc

    async def _ensure_backend_loaded(
        self,
        entry: _ModelLifecycleEntry,
    ) -> None:
        backend = entry.backend

        if backend is None:
            raise ModelNotReadyError(
                entry.model_id,
                lifecycle_state=entry.state,
            )

        load_method = getattr(
            backend,
            "load",
            None,
        )

        if not callable(load_method):
            if entry.state not in {
                ModelLifecycleState.BUSY,
                ModelLifecycleState.SHUTTING_DOWN,
                ModelLifecycleState.SHUTDOWN,
            }:
                entry.state = ModelLifecycleState.READY

            return

        if entry.state in {
            ModelLifecycleState.READY,
            ModelLifecycleState.BUSY,
        }:
            return

        async with entry.lifecycle_lock:
            if entry.state in {
                ModelLifecycleState.READY,
                ModelLifecycleState.BUSY,
            }:
                return

            if entry.state == ModelLifecycleState.SHUTDOWN:
                raise ModelNotReadyError(
                    entry.model_id,
                    lifecycle_state=entry.state,
                )

            if (
                entry.state == ModelLifecycleState.FAILED
                and not entry.policy.retry_failed_load
            ):
                raise ModelNotReadyError(
                    entry.model_id,
                    lifecycle_state=entry.state,
                )

            entry.state = ModelLifecycleState.LOADING

            try:
                result = load_method()

                if inspect.isawaitable(result):
                    await result

                entry.loaded_at_monotonic = (
                    time.monotonic()
                )
                entry.last_used_at_monotonic = (
                    entry.loaded_at_monotonic
                )
                entry.last_error = None
                entry.failed_at_monotonic = None
                entry.state = ModelLifecycleState.READY

            except asyncio.CancelledError:
                entry.state = ModelLifecycleState.CREATED
                raise

            except Exception as exc:
                entry.state = ModelLifecycleState.FAILED
                entry.last_error = exc
                entry.failed_at_monotonic = time.monotonic()

                raise ModelLoadError(
                    entry.model_id,
                    provider_type=entry.provider_type,
                    reason=str(exc),
                    cause=exc,
                ) from exc

    # ========================================================
    # Nutzungskontext
    # ========================================================

    @asynccontextmanager
    async def acquire(
        self,
        model_id: str,
        *,
        ensure_loaded: bool = True,
    ) -> AsyncGenerator[BaseModelBackend, None]:
        """
        Reserviert ein Modell für eine aktive Operation.

        Solange mindestens eine Operation aktiv ist, darf das Modell nicht
        automatisch entladen werden.
        """

        entry = self._get_entry(
            model_id,
        )

        backend = await self.get_backend(
            entry.model_id,
            ensure_loaded=ensure_loaded,
        )

        async with entry.usage_condition:
            if entry.state in {
                ModelLifecycleState.UNLOADING,
                ModelLifecycleState.SHUTTING_DOWN,
                ModelLifecycleState.SHUTDOWN,
            }:
                raise ModelOperationConflictError(
                    model_id=entry.model_id,
                    operation="acquire",
                    lifecycle_state=entry.state,
                    reason=(
                        "Das Modell wird derzeit entladen oder beendet."
                    ),
                )

            entry.active_operations += 1
            entry.last_used_at_monotonic = time.monotonic()
            entry.state = ModelLifecycleState.BUSY

        try:
            yield backend

        except BaseException:
            entry.failed_operations += 1
            raise

        else:
            entry.successful_operations += 1

        finally:
            async with entry.usage_condition:
                entry.active_operations = max(
                    0,
                    entry.active_operations - 1,
                )
                entry.last_used_at_monotonic = (
                    time.monotonic()
                )

                if entry.active_operations == 0:
                    if entry.state == ModelLifecycleState.BUSY:
                        entry.state = ModelLifecycleState.READY

                    entry.usage_condition.notify_all()

    # ========================================================
    # Generierung
    # ========================================================

    async def generate(
        self,
        model_id: str,
        request: GenerationRequest,
        *,
        timeout_seconds: float | None = None,
        request_id: str | None = None,
    ) -> StreamEvent:
        """
        Führt eine vollständige Generierung über den Lifecycle aus.
        """

        entry = self._get_entry(
            model_id,
        )

        effective_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else entry.policy.generation_timeout_seconds
        )

        if effective_timeout <= 0:
            raise ValueError(
                "timeout_seconds muss größer als 0 sein.",
            )

        try:
            async with self.acquire(
                entry.model_id,
                ensure_loaded=True,
            ) as backend:
                result = await asyncio.wait_for(
                    backend.generate(request),
                    timeout=effective_timeout,
                )

                # Der Vertrag von BaseModelBackend garantiert StreamEvent.
                # Pylance kann den Typ nicht immer ableiten – wir helfen mit type: ignore.
                return result  # type: ignore[return-value]

        except asyncio.TimeoutError as exc:
            raise ModelGenerationTimeoutError(
                model_id=entry.model_id,
                provider_type=entry.provider_type,
                timeout_seconds=effective_timeout,
                request_id=request_id,
                cause=exc,
            ) from exc

        except asyncio.CancelledError as exc:
            raise ModelGenerationCancelledError(
                model_id=entry.model_id,
                provider_type=entry.provider_type,
                reason="Die Generierung wurde abgebrochen.",
                request_id=request_id,
                cause=exc,
            ) from exc

        except ModelError:
            raise

        except Exception as exc:
            translated = translate_provider_error(
                exc,
                provider_type=entry.provider_type,
                model_id=entry.model_id,
                request_id=request_id,
            )

            # translated ist bereits ein ModelError
            raise translated from exc
    async def stream(
        self,
        model_id: str,
        request: GenerationRequest,
        *,
        idle_timeout_seconds: float | None = None,
        request_id: str | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """
        Streamt Modellereignisse.

        Der Timeout gilt jeweils zwischen zwei Events. Dadurch können lange
        Generierungen weiterlaufen, solange regelmäßig Daten eintreffen.
        """

        entry = self._get_entry(
            model_id,
        )

        effective_idle_timeout = (
            idle_timeout_seconds
            if idle_timeout_seconds is not None
            else entry.policy.stream_idle_timeout_seconds
        )

        if effective_idle_timeout <= 0:
            raise ValueError(
                "idle_timeout_seconds muss größer als 0 sein.",
            )

        try:
            async with self.acquire(
                entry.model_id,
                ensure_loaded=True,
            ) as backend:
                iterator = backend.stream(request)
                iterator_object = iterator.__aiter__()

                while True:
                    try:
                        event = await asyncio.wait_for(
                            iterator_object.__anext__(),
                            timeout=effective_idle_timeout,
                        )

                    except StopAsyncIteration:
                        break

                    except asyncio.TimeoutError as exc:
                        close_method = getattr(
                            iterator_object,
                            "aclose",
                            None,
                        )

                        if callable(close_method):
                            try:
                                close_result = close_method()

                                if inspect.isawaitable(
                                    close_result,
                                ):
                                    await close_result
                            except Exception:
                                logger.exception(
                                    "Could not close timed-out model stream",
                                    extra={
                                        "model_id": entry.model_id,
                                        "provider_type": (
                                            entry.provider_type
                                        ),
                                    },
                                )

                        raise ModelStreamTimeoutError(
                            model_id=entry.model_id,
                            provider_type=entry.provider_type,
                            timeout_seconds=effective_idle_timeout,
                            request_id=request_id,
                            cause=exc,
                        ) from exc

                    yield event

        except asyncio.CancelledError as exc:
            raise ModelStreamCancelledError(
                model_id=entry.model_id,
                provider_type=entry.provider_type,
                reason="Der Modellstream wurde abgebrochen.",
                request_id=request_id,
                cause=exc,
            ) from exc

        except ModelError:
            raise

        except Exception as exc:
            translated = translate_provider_error(
                exc,
                provider_type=entry.provider_type,
                model_id=entry.model_id,
                request_id=request_id,
            )

            # translated ist bereits ein ModelError
            raise translated from exc

    # ========================================================
    # Entladen
    # ========================================================

    async def unload(
        self,
        model_id: str,
        *,
        wait_for_active_operations: bool = True,
        timeout_seconds: float | None = None,
    ) -> bool:
        """
        Entlädt ein Modell, sofern das Backend dies unterstützt.

        Unterstützte Methoden, in dieser Reihenfolge:

        1. unload_model()
        2. unload()

        Gibt False zurück, wenn das Backend keine Entlademethode besitzt.
        """

        entry = self._get_entry(
            model_id,
        )

        if entry.backend is None:
            return False

        effective_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else entry.policy.shutdown_timeout_seconds
        )

        if wait_for_active_operations:
            await self._wait_until_unused(
                entry,
                timeout_seconds=effective_timeout,
            )
        elif entry.active_operations > 0:
            return False

        async with entry.lifecycle_lock:
            if entry.active_operations > 0:
                if not wait_for_active_operations:
                    return False

                raise ModelOperationConflictError(
                    model_id=entry.model_id,
                    operation="unload",
                    lifecycle_state=entry.state,
                    reason=(
                        "Das Modell besitzt noch aktive Operationen."
                    ),
                )

            backend = entry.backend

            # Hier ist backend garantiert nicht None (siehe Prüfung oben)
            # Der Check ist sicherheitshalber trotzdem drin, aber Pylance
            # würde meckern – deshalb type: ignore.
            if backend is None:  # type: ignore[reportUnnecessaryComparison]
                return False

            unload_method = getattr(
                backend,
                "unload_model",
                None,
            )

            if not callable(unload_method):
                unload_method = getattr(
                    backend,
                    "unload",
                    None,
                )

            if not callable(unload_method):
                return False

            previous_state = entry.state
            entry.state = ModelLifecycleState.UNLOADING

            try:
                result = unload_method()

                if inspect.isawaitable(result):
                    await asyncio.wait_for(
                        result,
                        timeout=effective_timeout,
                    )

                entry.loaded_at_monotonic = None
                entry.last_used_at_monotonic = time.monotonic()
                entry.last_error = None
                entry.failed_at_monotonic = None
                entry.state = ModelLifecycleState.UNLOADED

                return True

            except asyncio.TimeoutError as exc:
                entry.state = ModelLifecycleState.FAILED
                entry.last_error = exc
                entry.failed_at_monotonic = time.monotonic()

                raise ModelUnloadError(
                    entry.model_id,
                    provider_type=entry.provider_type,
                    reason=(
                        "Das Entladen hat das Zeitlimit überschritten."
                    ),
                    cause=exc,
                ) from exc

            except asyncio.CancelledError:
                entry.state = previous_state
                raise

            except Exception as exc:
                entry.state = ModelLifecycleState.FAILED
                entry.last_error = exc
                entry.failed_at_monotonic = time.monotonic()

                raise ModelUnloadError(
                    entry.model_id,
                    provider_type=entry.provider_type,
                    reason=str(exc),
                    cause=exc,
                ) from exc

    async def _wait_until_unused(
        self,
        entry: _ModelLifecycleEntry,
        *,
        timeout_seconds: float,
    ) -> None:
        if entry.active_operations == 0:
            return

        async def wait() -> None:
            async with entry.usage_condition:
                await entry.usage_condition.wait_for(
                    lambda: entry.active_operations == 0,
                )

        try:
            await asyncio.wait_for(
                wait(),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise ModelOperationConflictError(
                model_id=entry.model_id,
                operation="wait_until_unused",
                lifecycle_state=entry.state,
                reason=(
                    "Aktive Modelloperationen wurden nicht rechtzeitig "
                    "beendet."
                ),
            ) from exc

    # ========================================================
    # Shutdown
    # ========================================================

    async def shutdown_model(
        self,
        model_id: str,
        *,
        timeout_seconds: float | None = None,
    ) -> None:
        """
        Beendet genau ein Backend.

        Nach erfolgreichem Shutdown bleibt die Lifecycle-Definition
        registriert, kann aber nicht erneut genutzt werden.
        """

        entry = self._get_entry(
            model_id,
        )

        effective_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else entry.policy.shutdown_timeout_seconds
        )

        await self._wait_until_unused(
            entry,
            timeout_seconds=effective_timeout,
        )

        async with entry.lifecycle_lock:
            if entry.state == ModelLifecycleState.SHUTDOWN:
                return

            backend = entry.backend

            if backend is None:
                entry.state = ModelLifecycleState.SHUTDOWN
                return

            entry.state = ModelLifecycleState.SHUTTING_DOWN

            try:
                await asyncio.wait_for(
                    backend.shutdown(),
                    timeout=effective_timeout,
                )

                entry.backend = None
                entry.loaded_at_monotonic = None
                entry.last_used_at_monotonic = time.monotonic()
                entry.last_error = None
                entry.failed_at_monotonic = None
                entry.state = ModelLifecycleState.SHUTDOWN

            except asyncio.TimeoutError as exc:
                entry.state = ModelLifecycleState.FAILED
                entry.last_error = exc
                entry.failed_at_monotonic = time.monotonic()

                raise ModelShutdownError(
                    entry.model_id,
                    provider_type=entry.provider_type,
                    reason=(
                        "Das Backend-Shutdown hat das Zeitlimit "
                        "überschritten."
                    ),
                    cause=exc,
                ) from exc

            except asyncio.CancelledError:
                entry.state = ModelLifecycleState.FAILED
                raise

            except Exception as exc:
                entry.state = ModelLifecycleState.FAILED
                entry.last_error = exc
                entry.failed_at_monotonic = time.monotonic()

                raise ModelShutdownError(
                    entry.model_id,
                    provider_type=entry.provider_type,
                    reason=str(exc),
                    cause=exc,
                ) from exc

    async def shutdown(
        self,
        *,
        raise_on_error: bool = False,
    ) -> tuple[ModelError, ...]:
        """
        Beendet den vollständigen Lifecycle.

        Fehler einzelner Backends verhindern standardmäßig nicht das
        Herunterfahren der übrigen Backends.
        """

        if self._shutdown_requested:
            return ()

        self._shutdown_requested = True

        maintenance_task = self._maintenance_task
        self._maintenance_task = None

        if maintenance_task is not None:
            maintenance_task.cancel()

            try:
                await maintenance_task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception(
                    "Could not stop model maintenance task cleanly",
                )

        errors: list[ModelError] = []

        entries = tuple(
            self._entries.values(),
        )

        shutdown_tasks = [
            asyncio.create_task(
                self.shutdown_model(
                    entry.model_id,
                ),
                name=f"shutdown-model-{entry.model_id}",
            )
            for entry in entries
        ]

        results = await asyncio.gather(
            *shutdown_tasks,
            return_exceptions=True,
        )

        for entry, result in zip(
            entries,
            results,
            strict=True,
        ):
            if not isinstance(
                result,
                BaseException,
            ):
                continue

            if isinstance(result, ModelError):
                error = result
            else:
                error = ModelShutdownError(
                    entry.model_id,
                    provider_type=entry.provider_type,
                    reason=str(result),
                    cause=result,
                )

            errors.append(error)

            logger.error(
                "Model shutdown failed",
                extra={
                    "model_id": entry.model_id,
                    "provider_type": entry.provider_type,
                    "error_type": (
                        error.__class__.__name__
                    ),
                },
                exc_info=result,
            )

        self._started = False

        if errors and raise_on_error:
            raise ExceptionGroup(
                "Ein oder mehrere Modell-Backends konnten nicht "
                "beendet werden.",
                errors,
            )

        return tuple(errors)

    # ========================================================
    # Diagnose
    # ========================================================

    def get_snapshot(
        self,
        model_id: str,
    ) -> ModelLifecycleSnapshot:
        entry = self._get_entry(
            model_id,
        )

        return self._create_snapshot(
            entry,
        )

    def list_snapshots(
        self,
    ) -> tuple[ModelLifecycleSnapshot, ...]:
        return tuple(
            self._create_snapshot(
                self._entries[model_id],
            )
            for model_id in sorted(self._entries)
        )

    def _create_snapshot(
        self,
        entry: _ModelLifecycleEntry,
    ) -> ModelLifecycleSnapshot:
        now = time.monotonic()

        last_activity = (
            entry.last_used_at_monotonic
            or entry.loaded_at_monotonic
            or entry.created_at_monotonic
        )

        idle_seconds = (
            max(0.0, now - last_activity)
            if last_activity is not None
            else None
        )

        backend_loaded = self._is_backend_loaded(
            entry,
        )

        return ModelLifecycleSnapshot(
            model_id=entry.model_id,
            provider_type=entry.provider_type,
            state=entry.state,
            backend_created=entry.backend is not None,
            backend_loaded=backend_loaded,
            active_operations=entry.active_operations,
            successful_operations=(
                entry.successful_operations
            ),
            failed_operations=entry.failed_operations,
            created_at_monotonic=(
                entry.created_at_monotonic
            ),
            loaded_at_monotonic=(
                entry.loaded_at_monotonic
            ),
            last_used_at_monotonic=(
                entry.last_used_at_monotonic
            ),
            failed_at_monotonic=(
                entry.failed_at_monotonic
            ),
            last_error_type=(
                entry.last_error.__class__.__name__
                if entry.last_error is not None
                else None
            ),
            last_error_message=(
                str(entry.last_error)
                if entry.last_error is not None
                else None
            ),
            idle_seconds=idle_seconds,
            unload_when_idle=(
                entry.policy.unload_when_idle
            ),
            idle_unload_seconds=(
                entry.policy.idle_unload_seconds
            ),
            metadata=dict(entry.definition.metadata),
        )

    @staticmethod
    def _is_backend_loaded(
        entry: _ModelLifecycleEntry,
    ) -> bool:
        backend = entry.backend

        if backend is None:
            return False

        is_loaded = getattr(
            backend,
            "is_loaded",
            None,
        )

        if isinstance(is_loaded, bool):
            return is_loaded

        if callable(is_loaded):
            try:
                result = is_loaded()

                if isinstance(result, bool):
                    return result
            except Exception:
                return False

        return entry.state in {
            ModelLifecycleState.READY,
            ModelLifecycleState.BUSY,
        }

    # ========================================================
    # Hilfsmethoden
    # ========================================================

    def _get_entry(
        self,
        model_id: str,
    ) -> _ModelLifecycleEntry:
        normalized_model_id = self._normalize_model_id(
            model_id,
        )

        entry = self._entries.get(
            normalized_model_id,
        )

        if entry is None:
            raise ModelUnavailableError(
                normalized_model_id,
                reason=(
                    "Das Modell ist nicht im Lifecycle registriert."
                ),
            )

        return entry

    @staticmethod
    def _normalize_model_id(
        model_id: str,
    ) -> str:
        # model_id ist bereits als str typisiert
        normalized = model_id.strip()

        if not normalized:
            raise ValueError(
                "model_id darf nicht leer sein.",
            )

        return normalized

    async def __aenter__(
        self,
    ) -> ModelLifecycleManager:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.shutdown()


__all__ = [
    "BackendFactory",
    "ModelLifecycleDefinition",
    "ModelLifecycleManager",
    "ModelLifecyclePolicy",
    "ModelLifecycleSnapshot",
    "ModelLifecycleState",
]