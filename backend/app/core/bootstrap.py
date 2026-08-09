# F:\Kernschmied\backend\app\core\bootstrap.py

from __future__ import annotations

import inspect
import logging
from collections.abc import (
    Awaitable,
    Callable,
    Mapping,
)
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, TypeVar, cast

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.config.service import ConfigService
from app.core.settings import settings
from app.hierarchy.repository import HierarchyRepository as CoreHierarchyRepository
from app.models.lifecycle import ModelLifecycleManager
from app.models.providers import ModelProviderRegistry
from app.models.providers.ollama import create_ollama_backend
from app.models.service import ModelService
from app.registries.model_registry import ModelRegistry
from app.registries.tool_registry import ToolRegistry
from app.services.chat_service import (
    ChatService,
)
from app.services.hierarchy_service import create_hierarchy_service
from app.storage.database import init_database

logger = logging.getLogger(__name__)

# ============================================================
# TypeVar für generische Bootstrap-Schritte
# ============================================================

T = TypeVar("T")
R = TypeVar("R")


# ============================================================
# Modulkonfiguration
# ============================================================

SOURCE_FILE = "backend/app/core/bootstrap.py"
LOG_AREA = "application-bootstrap"

BACKEND_ROOT = Path(__file__).resolve().parents[2]

MODEL_MANIFEST_DIRECTORY = (BACKEND_ROOT / "model_paths").resolve()

DEFAULT_MODEL_ID = "ollama-qwen2.5-7b"


# ============================================================
# Fehler
# ============================================================


class BootstrapError(RuntimeError):
    """
    Basisklasse für Fehler beim Start der Anwendung.
    """


class BootstrapStepError(BootstrapError):
    """
    Ein einzelner Bootstrap-Schritt ist fehlgeschlagen.
    """

    def __init__(
        self,
        *,
        step: str,
        reason: str,
    ) -> None:
        self.step = step
        self.reason = reason

        super().__init__(
            f"Bootstrap-Schritt '{step}' fehlgeschlagen: {reason}",
        )


class ApplicationAlreadyBootstrappedError(
    BootstrapError,
):
    """
    Die Anwendung wurde bereits vollständig initialisiert.
    """


class ApplicationNotBootstrappedError(
    BootstrapError,
):
    """
    Ein Dienst wurde vor Abschluss des Bootstraps angefordert.
    """


# ============================================================
# Hilfsprotokolle
# ============================================================


class SyncOrAsyncCallableProtocol(Protocol):
    def __call__(self) -> object: ...


# ============================================================
# Hierarchie-Verträge und MVP-Implementierung
# ============================================================


HierarchyNode = dict[str, object]


class InMemoryHierarchyRepository:
    """
    Einfache In-Memory-Hierarchie für den MVP.

    Diese Implementierung wird später durch ein persistentes
    SQLAlchemy-Repository ersetzt, ohne den Servicevertrag zu
    verändern.
    """

    async def get_tree(
        self,
        root_id: str | None = None,
        max_depth: int | None = None,
    ) -> HierarchyNode:
        """
        Liefert die aktuelle MVP-Beispielhierarchie.

        `root_id` und `max_depth` gehören bereits zum Vertrag,
        werden in dieser statischen MVP-Implementierung jedoch
        noch nicht ausgewertet.
        """

        del root_id
        del max_depth

        return {
            "id": "root",
            "type": "user",
            "name": "Thomas Heisig",
            "parent_id": None,
            "sort_order": 0,
            "selectable": True,
            "disabled": False,
            "status": None,
            "metadata": {},
            "revision": 1,
            "actions": [],
            "children": [
                {
                    "id": "workspace-1",
                    "type": "workspace",
                    "name": "Heisig Naturstein",
                    "parent_id": "root",
                    "sort_order": 0,
                    "selectable": True,
                    "disabled": False,
                    "status": None,
                    "metadata": {},
                    "revision": 1,
                    "actions": [],
                    "children": [
                        {
                            "id": "project-1",
                            "type": "project",
                            "name": "Angebote",
                            "parent_id": "workspace-1",
                            "sort_order": 0,
                            "selectable": True,
                            "disabled": False,
                            "status": None,
                            "metadata": {},
                            "revision": 1,
                            "actions": [],
                            "children": [
                                {
                                    "id": "chat-1",
                                    "type": "chat",
                                    "name": "Angebot Müller",
                                    "parent_id": "project-1",
                                    "sort_order": 0,
                                    "selectable": True,
                                    "disabled": False,
                                    "status": None,
                                    "metadata": {},
                                    "revision": 1,
                                    "actions": [],
                                    "children": [],
                                },
                            ],
                        },
                        {
                            "id": "websites",
                            "type": "website_collection",
                            "name": "Webseiten",
                            "parent_id": "workspace-1",
                            "sort_order": 1,
                            "selectable": True,
                            "disabled": False,
                            "status": None,
                            "metadata": {},
                            "revision": 1,
                            "actions": [],
                            "children": [
                                {
                                    "id": "heisig-naturstein-modern",
                                    "type": "website",
                                    "name": "Heisig Naturstein Modern",
                                    "parent_id": "websites",
                                    "sort_order": 0,
                                    "selectable": True,
                                    "disabled": False,
                                    "status": "available",
                                    "metadata": {
                                        "entry_file": "index.html",
                                        "preview_url": (
                                            "/selfhtml/"
                                            "heisig-naturstein-modern/"
                                            "index.html"
                                        ),
                                        "website_kind": "static",
                                    },
                                    "revision": 1,
                                    "actions": [],
                                    "children": [],
                                },
                            ],
                        },
                    ],
                },
            ],
        }


class MinimalHierarchyService:
    """
    Minimaler Hierarchie-Service für den MVP.

    Der Service kapselt das Repository, sodass API-Endpunkte
    nicht von der konkreten Speicherimplementierung abhängen.
    """

    def __init__(
        self,
        repository: InMemoryHierarchyRepository,
    ) -> None:
        self._repository = repository

    async def get_tree(
        self,
        root_id: str | None = None,
        max_depth: int | None = None,
    ) -> HierarchyNode:
        return await self._repository.get_tree(
            root_id=root_id,
            max_depth=max_depth,
        )


class PersistentHierarchyService:
    """
    Adapter that provides a HierarchyService backed by the database.

    It creates a fresh SQLAlchemy session for each operation using the
    `session_factory` produced by the bootstrap database initialization.
    This keeps the public service contract stable while using persistent
    storage as source of truth.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def _with_service(
        self, func: Callable[..., Awaitable[R]], *args: Any, **kwargs: Any
    ) -> R:
        async with self._session_factory() as session:
            repository = CoreHierarchyRepository(session)
            service = create_hierarchy_service(repository)
            return await func(service, *args, **kwargs)

    async def get_tree(
        self,
        *,
        actor: Any | None = None,
        root_id: str | None = None,
        max_depth: int | None = None,
    ) -> HierarchyNode:
        async def op(s: Any) -> HierarchyNode:
            return await s.get_tree(actor=actor, root_id=root_id, max_depth=max_depth)

        return await self._with_service(op)

    async def get_node(self, node_id: str, actor: Any | None = None) -> dict[str, Any]:
        async def op(s: Any) -> dict[str, Any]:
            return await s.get_node(node_id=node_id, actor=actor)

        return await self._with_service(op)

    async def create_node(
        self, data: dict[str, Any], actor: Any | None = None
    ) -> dict[str, Any]:
        async def op(s: Any) -> dict[str, Any]:
            return await s.create_node(data, actor=actor)

        return await self._with_service(op)

    async def update_node(
        self, node_id: str, data: dict[str, Any], actor: Any | None = None
    ) -> dict[str, Any]:
        async def op(s: Any) -> dict[str, Any]:
            return await s.update_node(node_id=node_id, data=data, actor=actor)

        return await self._with_service(op)

    async def move_node(
        self, node_id: str, new_parent_id: str, actor: Any | None = None
    ) -> dict[str, Any]:
        async def op(s: Any) -> dict[str, Any]:
            return await s.move_node(
                node_id=node_id, new_parent_id=new_parent_id, actor=actor
            )

        return await self._with_service(op)

    async def reorder_nodes(
        self, moves: list[Any], actor: Any | None = None
    ) -> dict[str, Any]:
        async def op(s: Any) -> dict[str, Any]:
            return await s.reorder_nodes(moves=moves, actor=actor)

        return await self._with_service(op)

    async def delete_node(self, node_id: str, actor: Any | None = None) -> Any:
        async def op(s: Any) -> Any:
            return await s.delete_node(node_id=node_id, actor=actor)

        return await self._with_service(op)

    async def resolve_effective_values(
        self, node_id: str, actor: Any | None = None
    ) -> dict[str, Any]:
        async def op(s: Any) -> dict[str, Any]:
            return await s.resolve_effective_values(node_id=node_id, actor=actor)

        return await self._with_service(op)


# ============================================================
# Bootstrap-Ergebnis
# ============================================================


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """
    Ergebnis eines erfolgreichen Anwendungs-Bootstraps.

    Die Dienste werden erst gemeinsam in `app.state`
    veröffentlicht, nachdem alle erforderlichen Schritte
    erfolgreich abgeschlossen wurden.
    """

    session_factory: async_sessionmaker[AsyncSession] | None
    config_service: ConfigService
    model_registry: ModelRegistry
    tool_registry: ToolRegistry
    hierarchy_repository: Any
    hierarchy_service: Any
    model_service: ModelService
    chat_service: ChatService


# ============================================================
# Öffentliche Bootstrap-Funktionen
# ============================================================


async def bootstrap_application(
    app: FastAPI,
    *,
    force: bool = False,
) -> BootstrapResult:
    """
    Initialisiert alle zentralen Anwendungsdienste.

    Dienste werden erst veröffentlicht, wenn alle zwingenden
    Bootstrap-Schritte erfolgreich abgeschlossen wurden.
    """

    _log_info(
        "Application bootstrap requested",
        bootstrap_event="bootstrap-requested",
        force=force,
        already_bootstrapped=is_application_bootstrapped(app),
        model_manifest_directory=str(
            MODEL_MANIFEST_DIRECTORY,
        ),
        default_model_id=DEFAULT_MODEL_ID,
    )

    if is_application_bootstrapped(app):
        if not force:
            raise ApplicationAlreadyBootstrappedError(
                "Die Anwendung wurde bereits initialisiert.",
            )

        _log_warning(
            "Existing application bootstrap will be replaced",
            bootstrap_event="forced-bootstrap-restart",
        )

        await shutdown_application(
            app,
        )

    app.state.bootstrap_complete = False
    app.state.bootstrap_error = None

    # NOTE: Core bootstrap locals below are expected to hold concrete
    # non-None service instances once their respective initialization
    # steps have completed. Do not reintroduce `| None` annotations for
    # these locals — use `_run_bootstrap_step` which returns the proper
    # concrete type or raise a `BootstrapStepError` on failure.
    session_factory: async_sessionmaker[AsyncSession] | None = None

    config_service: ConfigService | None = None
    model_registry: ModelRegistry | None = None
    tool_registry: ToolRegistry | None = None

    hierarchy_repository: Any | None = None

    hierarchy_service: Any | None = None

    model_service: ModelService | None = None
    chat_service: ChatService | None = None

    try:
        # ====================================================
        # 1. Datenbank
        # ====================================================

        session_factory = await _run_bootstrap_step(
            step="database.initialize",
            operation=init_database,
        )

        # ====================================================
        # 2. Hierarchie
        # ====================================================

        async def initialize_hierarchy() -> None:
            nonlocal hierarchy_repository
            nonlocal hierarchy_service

            # Use DB-backed hierarchy service (session_factory is initialized above).
            # Cast session_factory because local variable is Optional for bootstrapping
            # flow, but init_database() returns a concrete session factory.
            assert session_factory is not None
            sf = session_factory
            hierarchy_service = PersistentHierarchyService(sf)
            hierarchy_repository = sf

            # Ensure system root exists in the persistent repository before
            # seeding development data. This bootstrap step is idempotent.
            try:
                from app.core.hierarchy_bootstrap import ensure_system_root
                from app.hierarchy.repository import HierarchyRepository

                async with sf() as session:
                    repo = HierarchyRepository(session)
                    await ensure_system_root(repo)
            except Exception:
                # Let bootstrap step wrapper transform this into a BootstrapStepError
                raise

            # run development seed only in development environment
            try:
                from app.core.dev_seed import seed_development_hierarchy
                from app.core.settings import AppEnvironment

                if settings.app_environment == AppEnvironment.DEVELOPMENT:
                    await seed_development_hierarchy(sf)
            except Exception:
                # Let bootstrap step wrapper transform this into a BootstrapStepError
                raise

        await _run_bootstrap_step(
            step="hierarchy.initialize",
            operation=initialize_hierarchy,
        )

        if hierarchy_repository is None or hierarchy_service is None:
            raise BootstrapStepError(
                step="hierarchy.initialize",
                reason="Hierarchy initialization failed: repository or service is None",
            )
        # ====================================================
        # 3. Konfiguration
        # ====================================================

        async def initialize_config() -> None:
            nonlocal config_service

            assert session_factory is not None
            # Create ConfigService and ensure defaults are seeded
            cs = ConfigService(session_factory)
            await cs.seed_defaults()
            config_service = cs

        await _run_bootstrap_step(
            step="config.initialize",
            operation=initialize_config,
        )

        # ====================================================
        # 4. Modellkatalog
        # ====================================================

        model_registry = ModelRegistry()
        # Make model registry available to the already-created config_service
        from contextlib import suppress

        with suppress(Exception):
            cast(Any, config_service)._model_registry = model_registry

        await _run_bootstrap_step(
            step="models.discover_catalog",
            operation=model_registry.discover,
        )

        # ====================================================
        # 5. Tool-Registry
        # ====================================================

        tool_registry = ToolRegistry()

        await _run_bootstrap_step(
            step="tools.discover",
            operation=tool_registry.discover,
        )

        # ====================================================
        # 6. ModelService und Provider
        # ====================================================

        provider_registry = ModelProviderRegistry()

        await _run_bootstrap_step(
            step="models.register_providers",
            operation=lambda: _register_model_providers(
                provider_registry,
            ),
        )

        lifecycle = ModelLifecycleManager()

        model_service = ModelService(
            provider_registry=provider_registry,
            lifecycle=lifecycle,
            allowed_manifest_directories=[
                str(
                    MODEL_MANIFEST_DIRECTORY,
                ),
            ],
            default_model_id=DEFAULT_MODEL_ID,
        )

        # If model_registry exists, register an availability checker so the
        # registry can surface runtime availability/selectability.
        try:
            # model_service types may be opaque to the type checker; cast to Any
            model_registry.set_availability_checker(
                cast(Any, model_service).is_model_available,
                ttl=30.0,
            )
        except Exception:
            # non-fatal if model_registry does not expose the setter
            pass
        # Start des ModelService (Methode muss in ModelService existieren)
        await _run_bootstrap_step(
            step="models.start_service",
            operation=model_service.start,  # type: ignore[attr-defined]
        )

        # ====================================================
        # 7. Modellmanifeste laden
        # ====================================================

        async def load_manifests() -> None:
            if model_service is None:  # type: ignore
                raise RuntimeError(
                    "Der ModelService wurde noch nicht erstellt.",
                )

            if not MODEL_MANIFEST_DIRECTORY.exists():
                raise RuntimeError(
                    "Das Modellmanifest-Verzeichnis existiert "
                    f"nicht: {MODEL_MANIFEST_DIRECTORY}",
                )

            if not MODEL_MANIFEST_DIRECTORY.is_dir():
                raise RuntimeError(
                    "Der Modellmanifest-Pfad ist kein "
                    f"Verzeichnis: {MODEL_MANIFEST_DIRECTORY}",
                )

            _log_info(
                "Starting model manifest discovery",
                bootstrap_event="model-discovery-started",
                manifest_directory=str(
                    MODEL_MANIFEST_DIRECTORY,
                ),
                default_model_id=DEFAULT_MODEL_ID,
            )

            report = await model_service.discover_and_register(
                base_directories=[
                    str(
                        MODEL_MANIFEST_DIRECTORY,
                    ),
                ],
                replace=True,
                continue_on_error=True,
            )

            _log_info(
                "Model manifest discovery completed",
                bootstrap_event="model-discovery-completed",
                registered_count=report.registered_count,
                failed_count=report.failed_count,
                skipped_count=report.skipped_count,
            )

            if report.failed_count > 0:
                _log_warning(
                    "Some model manifests could not be registered",
                    bootstrap_event=("model-discovery-partial-failure"),
                    registered_count=report.registered_count,
                    failed_count=report.failed_count,
                    skipped_count=report.skipped_count,
                )

            has_default = await model_service.has_model(
                DEFAULT_MODEL_ID,
            )
            if not has_default:
                model_ids = await model_service.list_model_ids()

                _log_error(
                    "Default model is unavailable after discovery",
                    bootstrap_event="default-model-missing",
                    default_model_id=DEFAULT_MODEL_ID,
                    registered_model_ids=model_ids,
                )

                raise RuntimeError(
                    "Das Standardmodell "
                    f"'{DEFAULT_MODEL_ID}' konnte nicht "
                    "registriert werden."
                )

            model_ids = await model_service.list_model_ids()

            _log_info(
                "Models available in ModelService",
                bootstrap_event="models-available",
                model_count=len(model_ids),
                model_ids=model_ids,
                default_model_id=DEFAULT_MODEL_ID,
            )

        await _run_bootstrap_step(
            step="models.load_manifests",
            operation=load_manifests,
        )

        # ====================================================
        # 8. ChatService
        # ====================================================

        async def initialize_chat_service() -> None:
            nonlocal chat_service

            if model_service is None:  # type: ignore
                raise RuntimeError(
                    "Der ModelService ist nicht verfügbar.",
                )

            # Use DB-backed chat repository adapter so ChatService persists messages
            from app.storage.adapters.chat_history_provider import (
                ChatHistoryProviderAdapter,
            )
            from app.storage.adapters.chat_repository_adapter import (
                ChatRepositoryAdapter,
            )

            chat_repo_adapter = ChatRepositoryAdapter(session_factory)
            chat_history_provider = ChatHistoryProviderAdapter(session_factory)

            chat_service = ChatService(
                model_service=model_service,
                default_model_id=DEFAULT_MODEL_ID,
                repository=chat_repo_adapter,
                history_provider=chat_history_provider,
                hierarchy_session_factory=session_factory,
                prompt_config_reader=(
                    # small adapter to expose get_system_prompt() used by ChatService
                    type(
                        "_ConfigPromptReader",
                        (),
                        {
                            "get_system_prompt": staticmethod(
                                lambda: (
                                    cast(Any, config_service).get_required(
                                        "chat", "system_prompt"
                                    ),
                                    getattr(
                                        cast(Any, config_service), "revision", None
                                    ),
                                )
                            )
                        },
                    )()
                ),
            )

        await _run_bootstrap_step(
            step="chat.initialize_service",
            operation=initialize_chat_service,
        )

        if chat_service is None:
            raise BootstrapStepError(
                step="chat.initialize_service",
                reason=("Der ChatService wurde nicht vollständig initialisiert."),
            )

        # ====================================================
        # 9. Dienste atomar veröffentlichen
        # ====================================================

        # At this point bootstrap steps either raised or populated the
        # `config_service` variable — assert to inform static checkers
        # that it is non-None for subsequent attribute access.
        assert config_service is not None

        result = BootstrapResult(
            session_factory=session_factory,
            config_service=config_service,
            model_registry=model_registry,
            tool_registry=tool_registry,
            hierarchy_repository=hierarchy_repository,
            hierarchy_service=hierarchy_service,
            model_service=model_service,
            chat_service=chat_service,
        )

        _publish_services(
            app=app,
            result=result,
        )
        # Initialize optional post-commit projection service and publish to app.state
        try:
            from app.core.settings import settings as _settings
            from app.workspace_projection.post_commit import PostCommitProjectionService
            from app.workspace_projection.contracts import ProjectionConfig

            proj_config = ProjectionConfig(enabled=bool(getattr(_settings, "data_projection_enabled", False)), root_path=str(getattr(_settings, "data_projection_path", "./data")))
            post_commit = PostCommitProjectionService(session_factory=session_factory, config=proj_config)
            app.state.post_commit_projection = post_commit
        except Exception:
            # If projection initialization fails, log but continue bootstrapping without projection
            logger.exception("Failed to initialize PostCommitProjectionService; continuing without workspace projection")

        app.state.bootstrap_complete = True
        app.state.bootstrap_error = None

        model_ids = await model_service.list_model_ids()
        _log_info(
            "Application bootstrap completed",
            bootstrap_event="bootstrap-completed",
            config_revision=config_service.revision,
            config_definition_count=(config_service.definition_count),
            config_cache_size=config_service.cache_size,
            model_registry_count=_registry_item_count(
                model_registry,
            ),
            tool_registry_count=_registry_item_count(
                tool_registry,
            ),
            model_service_count=len(model_ids),
            hierarchy_service_available=True,
            model_service_available=True,
            chat_service_available=True,
        )

        return result

    except Exception as exc:
        app.state.bootstrap_complete = False
        app.state.bootstrap_error = str(
            exc,
        )

        _log_exception(
            "Application bootstrap failed",
            bootstrap_event="bootstrap-failed",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

        await _cleanup_partial_bootstrap(
            tool_registry=tool_registry,
            model_registry=model_registry,
            config_service=config_service,
            session_factory=session_factory,  # type: ignore
            model_service=model_service,
            chat_service=chat_service,
        )

        _clear_services(
            app,
        )

        if isinstance(
            exc,
            BootstrapError,
        ):
            raise

        raise BootstrapError(
            "Die Anwendung konnte nicht vollständig initialisiert werden.",
        ) from exc


async def shutdown_application(
    app: FastAPI,
) -> None:
    """
    Beendet zentrale Anwendungsdienste in umgekehrter Reihenfolge.

    Fehler einzelner Shutdown-Schritte werden protokolliert,
    verhindern jedoch nicht das Aufräumen der übrigen Ressourcen.
    """

    _log_info(
        "Application shutdown started",
        bootstrap_event="shutdown-started",
        was_bootstrapped=is_application_bootstrapped(app),
    )

    tool_registry: object = getattr(
        app.state,
        "tool_registry",
        None,
    )

    model_registry: object = getattr(
        app.state,
        "model_registry",
        None,
    )

    config_service: object = getattr(
        app.state,
        "config_service",
        None,
    )

    hierarchy_service: object = getattr(
        app.state,
        "hierarchy_service",
        None,
    )

    hierarchy_repository: object = getattr(
        app.state,
        "hierarchy_repository",
        None,
    )

    model_service_value: object = getattr(
        app.state,
        "model_service",
        None,
    )

    chat_service: object = getattr(
        app.state,
        "chat_service",
        None,
    )

    session_factory_value: object = getattr(
        app.state,
        "session_factory",
        None,
    )

    session_factory = _coerce_session_factory(
        session_factory_value,
    )

    model_service = _coerce_model_service(
        model_service_value,
    )

    await _safe_shutdown(
        name="chat_service",
        resource=chat_service,
    )

    await _shutdown_model_service(
        model_service,
    )

    await _safe_shutdown(
        name="tool_registry",
        resource=tool_registry,
    )

    await _safe_shutdown(
        name="model_registry",
        resource=model_registry,
    )

    await _safe_shutdown(
        name="config_service",
        resource=config_service,
    )

    await _safe_shutdown(
        name="hierarchy_service",
        resource=hierarchy_service,
    )

    await _safe_shutdown(
        name="hierarchy_repository",
        resource=hierarchy_repository,
    )

    await _dispose_session_factory(
        session_factory,
    )

    _clear_services(
        app,
    )

    app.state.bootstrap_complete = False
    app.state.bootstrap_error = None

    _log_info(
        "Application shutdown completed",
        bootstrap_event="shutdown-completed",
    )


def is_application_bootstrapped(
    app: FastAPI,
) -> bool:
    """
    Prüft, ob der Bootstrap vollständig abgeschlossen wurde.
    """

    value: object = getattr(
        app.state,
        "bootstrap_complete",
        False,
    )

    return bool(
        value,
    )


# ============================================================
# Öffentliche Dienstzugriffe
# ============================================================


def get_session_factory(
    app: FastAPI,
) -> async_sessionmaker[AsyncSession]:
    """
    Liefert die initialisierte Session-Factory.
    """

    service = _get_required_state_service(
        app=app,
        attribute="session_factory",
    )

    return cast(
        async_sessionmaker[AsyncSession],
        service,
    )


def get_config_service(
    app: FastAPI,
) -> ConfigService:
    """
    Liefert den initialisierten ConfigService.
    """

    service = _get_required_state_service(
        app=app,
        attribute="config_service",
    )

    return cast(
        ConfigService,
        service,
    )


def get_model_registry(
    app: FastAPI,
) -> ModelRegistry:
    """
    Liefert die initialisierte ModelRegistry.
    """

    service = _get_required_state_service(
        app=app,
        attribute="model_registry",
    )

    return cast(
        ModelRegistry,
        service,
    )


def get_tool_registry(
    app: FastAPI,
) -> ToolRegistry:
    """
    Liefert die initialisierte ToolRegistry.
    """

    service = _get_required_state_service(
        app=app,
        attribute="tool_registry",
    )

    return cast(
        ToolRegistry,
        service,
    )


def get_hierarchy_repository(
    app: FastAPI,
) -> InMemoryHierarchyRepository:
    """
    Liefert das initialisierte Hierarchie-Repository.
    """

    service = _get_required_state_service(
        app=app,
        attribute="hierarchy_repository",
    )

    return cast(
        InMemoryHierarchyRepository,
        service,
    )


def get_hierarchy_service(
    app: FastAPI,
) -> MinimalHierarchyService:
    """
    Liefert den initialisierten Hierarchie-Service.
    """

    service = _get_required_state_service(
        app=app,
        attribute="hierarchy_service",
    )

    return cast(
        MinimalHierarchyService,
        service,
    )


def get_model_service(
    app: FastAPI,
) -> ModelService:
    """
    Liefert den initialisierten ModelService.
    """

    service = _get_required_state_service(
        app=app,
        attribute="model_service",
    )

    return cast(
        ModelService,
        service,
    )


def get_chat_service(
    app: FastAPI,
) -> ChatService:
    """
    Liefert den initialisierten ChatService.
    """

    service = _get_required_state_service(
        app=app,
        attribute="chat_service",
    )

    return cast(
        ChatService,
        service,
    )


# ============================================================
# Modell-Provider
# ============================================================


async def _register_model_providers(
    provider_registry: ModelProviderRegistry,
) -> None:
    """
    Registriert die fest freigegebenen Modell-Provider.

    Dynamische Erkennung führt nicht zu einer automatischen
    Freigabe unbekannter Provider.
    """

    _log_info(
        "Registering model provider",
        bootstrap_event="provider-registration-started",
        provider_type="ollama",
    )

    provider_registry.register(
        provider_type="ollama",
        factory=create_ollama_backend,
    )

    if not provider_registry.has(
        "ollama",
    ):
        raise RuntimeError(
            "Der Ollama-Provider wurde nach der Registrierung "
            "nicht in der Provider-Registry gefunden."
        )

    _log_info(
        "Model provider registered",
        bootstrap_event="provider-registration-completed",
        provider_type="ollama",
    )


# ============================================================
# Interne Bootstrap-Hilfsfunktionen
# ============================================================


async def _run_bootstrap_step(
    *,
    step: str,
    operation: Callable[[], Awaitable[T]],
) -> T:
    """
    Führt einen einzelnen Bootstrap-Schritt aus und wandelt
    dessen Fehler in einen strukturierten BootstrapStepError um.
    """

    _log_info(
        "Starting bootstrap step",
        bootstrap_event="bootstrap-step-started",
        bootstrap_step=step,
    )

    try:
        result = await operation()

    except Exception as exc:
        _log_exception(
            "Bootstrap step failed",
            bootstrap_event="bootstrap-step-failed",
            bootstrap_step=step,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

        raise BootstrapStepError(
            step=step,
            reason=str(
                exc,
            ),
        ) from exc

    _log_info(
        "Bootstrap step completed",
        bootstrap_event="bootstrap-step-completed",
        bootstrap_step=step,
    )

    return result


def _publish_services(
    *,
    app: FastAPI,
    result: BootstrapResult,
) -> None:
    """
    Veröffentlicht vollständig initialisierte Dienste logisch atomar.

    `app.state` bietet keine echte Transaktion. Deshalb werden
    alle Referenzen erst nach Abschluss der vorbereitenden
    Bootstrap-Schritte gesetzt.
    """

    app.state.session_factory = result.session_factory

    app.state.config_service = result.config_service

    app.state.model_registry = result.model_registry

    app.state.tool_registry = result.tool_registry

    app.state.hierarchy_repository = result.hierarchy_repository

    app.state.hierarchy_service = result.hierarchy_service

    app.state.model_service = result.model_service

    app.state.chat_service = result.chat_service

    _log_info(
        "Application services published",
        bootstrap_event="services-published",
        published_services=[
            "session_factory",
            "config_service",
            "model_registry",
            "tool_registry",
            "hierarchy_repository",
            "hierarchy_service",
            "model_service",
            "chat_service",
        ],
    )


def _clear_services(
    app: FastAPI,
) -> None:
    """
    Entfernt veröffentlichte Dienstreferenzen aus `app.state`.
    """

    removed_services: list[str] = []

    for attribute in (
        "chat_service",
        "model_service",
        "hierarchy_service",
        "hierarchy_repository",
        "tool_registry",
        "model_registry",
        "config_service",
        "session_factory",
        "shutdown_callbacks",
    ):
        if not hasattr(
            app.state,
            attribute,
        ):
            continue

        delattr(
            app.state,
            attribute,
        )

        removed_services.append(
            attribute,
        )

    _log_debug(
        "Application service references cleared",
        bootstrap_event="services-cleared",
        removed_services=removed_services,
    )


async def _cleanup_partial_bootstrap(
    *,
    tool_registry: ToolRegistry | None,
    model_registry: ModelRegistry | None,
    config_service: ConfigService | None,
    session_factory: async_sessionmaker[AsyncSession] | None,
    model_service: ModelService | None,
    chat_service: ChatService | None,
) -> None:
    """
    Räumt Ressourcen nach einem fehlgeschlagenen Bootstrap auf.
    """

    _log_warning(
        "Partial bootstrap cleanup started",
        bootstrap_event="partial-cleanup-started",
    )

    await _safe_shutdown(
        name="chat_service",
        resource=chat_service,
    )

    await _shutdown_model_service(
        model_service,
    )

    await _safe_shutdown(
        name="tool_registry",
        resource=tool_registry,
    )

    await _safe_shutdown(
        name="model_registry",
        resource=model_registry,
    )

    await _safe_shutdown(
        name="config_service",
        resource=config_service,
    )

    await _dispose_session_factory(
        session_factory,
    )

    _log_info(
        "Partial bootstrap cleanup completed",
        bootstrap_event="partial-cleanup-completed",
    )


async def _shutdown_model_service(
    model_service: ModelService | None,
) -> None:
    """
    Beendet den ModelService mit seinem konkreten Vertrag.

    Die generische Shutdown-Funktion kann keine Argumente an
    `ModelService.shutdown()` übergeben. Deshalb wird der
    ModelService ausdrücklich behandelt.
    """

    if model_service is None:
        return

    _log_debug(
        "Resource shutdown started",
        bootstrap_event="resource-shutdown-started",
        resource_name="model_service",
        shutdown_method="shutdown",
    )

    try:
        await model_service.shutdown(  # type: ignore[attr-defined]
            raise_on_error=False,
        )

    except Exception as exc:
        _log_exception(
            "Model service shutdown failed",
            bootstrap_event="resource-shutdown-failed",
            resource_name="model_service",
            shutdown_method="shutdown",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

        return

    _log_debug(
        "Resource shutdown completed",
        bootstrap_event="resource-shutdown-completed",
        resource_name="model_service",
        shutdown_method="shutdown",
    )


async def _safe_shutdown(
    *,
    name: str,
    resource: object,
) -> None:
    """
    Ruft den ersten verfügbaren Shutdown-Mechanismus einer
    Ressource auf.

    Unterstützt synchrone und asynchrone Methoden ohne
    erforderliche Argumente.
    """

    if resource is None:
        return

    for method_name in (
        "shutdown",
        "close",
        "dispose",
    ):
        method_value: object = getattr(
            resource,
            method_name,
            None,
        )

        if not callable(
            method_value,
        ):
            continue

        method = cast(
            SyncOrAsyncCallableProtocol,
            method_value,
        )

        _log_debug(
            "Resource shutdown started",
            bootstrap_event="resource-shutdown-started",
            resource_name=name,
            shutdown_method=method_name,
        )

        try:
            result: object = method()

            if inspect.isawaitable(result):
                await result

        except Exception as exc:
            _log_exception(
                "Resource shutdown failed",
                bootstrap_event="resource-shutdown-failed",
                resource_name=name,
                shutdown_method=method_name,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

            return

        _log_debug(
            "Resource shutdown completed",
            bootstrap_event="resource-shutdown-completed",
            resource_name=name,
            shutdown_method=method_name,
        )

        return


async def _dispose_session_factory(
    session_factory: async_sessionmaker[AsyncSession] | None,
) -> None:
    """
    Gibt die zugrunde liegende SQLAlchemy-Engine frei.

    `async_sessionmaker` besitzt normalerweise keine eigene
    `dispose()`-Methode. Die Engine wird deshalb über das
    gebundene SQLAlchemy-Objekt ermittelt.
    """

    if session_factory is None:
        return

    bind: object = getattr(
        session_factory,
        "bind",
        None,
    )

    if bind is None:
        kw_value: object = getattr(
            session_factory,
            "kw",
            None,
        )

        if isinstance(
            kw_value,
            Mapping,
        ):
            typed_kw = cast(
                Mapping[object, object],
                kw_value,
            )

            bind = typed_kw.get(
                "bind",
            )

    dispose_value: object = getattr(
        bind,
        "dispose",
        None,
    )

    if not callable(
        dispose_value,
    ):
        _log_debug(
            "Database engine has no dispose method",
            bootstrap_event="database-dispose-skipped",
        )

        return

    dispose = cast(
        SyncOrAsyncCallableProtocol,
        dispose_value,
    )

    _log_debug(
        "Database engine disposal started",
        bootstrap_event="database-dispose-started",
    )

    try:
        result: object = dispose()

        if inspect.isawaitable(
            result,
        ):
            await result

    except Exception as exc:
        _log_exception(
            "Database engine disposal failed",
            bootstrap_event="database-dispose-failed",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

        return

    _log_debug(
        "Database engine disposal completed",
        bootstrap_event="database-dispose-completed",
    )


def _coerce_session_factory(
    value: object,
) -> async_sessionmaker[AsyncSession] | None:
    if value is None:
        return None

    return cast(
        async_sessionmaker[AsyncSession],
        value,
    )


def _coerce_model_service(
    value: object,
) -> ModelService | None:
    if value is None:
        return None

    return cast(
        ModelService,
        value,
    )


def _get_required_state_service(
    *,
    app: FastAPI,
    attribute: str,
) -> object:
    if not is_application_bootstrapped(
        app,
    ):
        _log_warning(
            "Service requested before bootstrap completion",
            bootstrap_event="service-access-rejected",
            requested_service=attribute,
            reason="application-not-bootstrapped",
        )

        raise ApplicationNotBootstrappedError(
            "Die Anwendung wurde noch nicht vollständig initialisiert.",
        )

    service: object = getattr(
        app.state,
        attribute,
        None,
    )

    if service is None:
        _log_error(
            "Published application service is unavailable",
            bootstrap_event="service-access-failed",
            requested_service=attribute,
        )

        raise ApplicationNotBootstrappedError(
            f"Der Anwendungsdienst '{attribute}' ist nicht verfügbar.",
        )

    return service


def _registry_item_count(
    registry: object,
) -> int | None:
    """
    Ermittelt die Anzahl registrierter Elemente ausschließlich über
    synchron verfügbare Zustände.

    Asynchrone Registry-Methoden dürfen hier nicht aufgerufen werden,
    weil dadurch nicht erwartete Coroutine-Objekte entstehen.
    """

    for attribute_name in (
        "count",
        "item_count",
    ):
        value = getattr(
            registry,
            attribute_name,
            None,
        )

        if isinstance(value, int):
            return value

    items = getattr(
        registry,
        "items",
        None,
    )

    if isinstance(items, Mapping):
        typed_items = cast(
            Mapping[object, object],
            items,
        )

        return len(typed_items)

    return None


# ============================================================
# Strukturierte Logging-Hilfsfunktionen
# ============================================================


def _log_context(
    **values: object,
) -> dict[str, object]:
    """
    Ergänzt jedes Log um stabile Kontextfelder.
    """

    return {
        "source": SOURCE_FILE,
        "area": LOG_AREA,
        **values,
    }


def _log_debug(
    message: str,
    **context: object,
) -> None:
    logger.debug(
        message,
        extra=_log_context(
            **context,
        ),
    )


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
    **context: object,
) -> None:
    logger.warning(
        message,
        extra=_log_context(
            **context,
        ),
    )


def _log_error(
    message: str,
    **context: object,
) -> None:
    logger.error(
        message,
        extra=_log_context(
            **context,
        ),
    )


def _log_exception(
    message: str,
    **context: object,
) -> None:
    logger.exception(
        message,
        extra=_log_context(
            **context,
        ),
    )
