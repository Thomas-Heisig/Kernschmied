# F:\Kernschmied\backend\app\core\bootstrap.py

from __future__ import annotations

import inspect
import logging
from collections.abc import (
    Awaitable,
    Callable,
    Mapping,
    Sized,
)
from dataclasses import dataclass
from typing import Protocol, TypeVar, cast

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.config.service import ConfigService
from app.registries.model_registry import ModelRegistry
from app.registries.tool_registry import ToolRegistry
from app.storage.database import init_database


logger = logging.getLogger(__name__)


T = TypeVar("T")


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


class ApplicationAlreadyBootstrappedError(BootstrapError):
    """
    Die Anwendung wurde bereits vollständig initialisiert.
    """


class ApplicationNotBootstrappedError(BootstrapError):
    """
    Ein Dienst wurde vor Abschluss des Bootstraps angefordert.
    """


# ============================================================
# Hilfsprotokolle
# ============================================================


class SyncOrAsyncCallableProtocol(Protocol):
    def __call__(self) -> object:
        ...


# ============================================================
# Hierarchie-Verträge und MVP-Implementierung
# ============================================================


HierarchyNode = dict[str, object]


class InMemoryHierarchyRepository:
    """
    Einfache In-Memory-Hierarchie für den MVP.

    Diese Implementierung wird später durch ein persistentes
    SQLAlchemy-Repository ersetzt, ohne den Servicevertrag zu ändern.
    """

    async def get_tree(
        self,
        root_id: str | None = None,
        max_depth: int | None = None,
    ) -> HierarchyNode:
        """
        Liefert die aktuelle MVP-Beispielhierarchie.

        `root_id` und `max_depth` sind bereits Bestandteil des
        Repository-Vertrags, werden von der statischen MVP-
        Implementierung jedoch noch nicht ausgewertet.
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
                    ],
                },
            ],
        }


class MinimalHierarchyService:
    """
    Minimaler Hierarchie-Service für den MVP.

    Der Service kapselt das Repository, damit API-Endpunkte später
    nicht direkt von der konkreten Speicherimplementierung abhängen.
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


# ============================================================
# Bootstrap-Ergebnis
# ============================================================


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """
    Ergebnis eines erfolgreichen Anwendungs-Bootstraps.

    Alle Dienste werden erst nach erfolgreicher Initialisierung
    gemeinsam in `app.state` veröffentlicht.
    """

    session_factory: async_sessionmaker[AsyncSession]
    config_service: ConfigService
    model_registry: ModelRegistry
    tool_registry: ToolRegistry
    hierarchy_repository: InMemoryHierarchyRepository
    hierarchy_service: MinimalHierarchyService


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

    Die Dienste werden erst veröffentlicht, wenn alle erforderlichen
    Bootstrap-Schritte erfolgreich abgeschlossen wurden.
    """

    if is_application_bootstrapped(app):
        if not force:
            raise ApplicationAlreadyBootstrappedError(
                "Die Anwendung wurde bereits initialisiert.",
            )

        await shutdown_application(
            app,
        )

    app.state.bootstrap_complete = False
    app.state.bootstrap_error = None

    session_factory: async_sessionmaker[AsyncSession] | None = None
    config_service: ConfigService | None = None
    model_registry: ModelRegistry | None = None
    tool_registry: ToolRegistry | None = None

    hierarchy_repository: InMemoryHierarchyRepository | None = None
    hierarchy_service: MinimalHierarchyService | None = None

    try:
        # ========================================================
        # 1. Datenbank
        # ========================================================

        session_factory = await _run_bootstrap_step(
            step="database.initialize",
            operation=init_database,
        )

        # ========================================================
        # 2. Hierarchie
        # ========================================================

        hierarchy_repository = InMemoryHierarchyRepository()

        hierarchy_service = MinimalHierarchyService(
            hierarchy_repository,
        )

        # ========================================================
        # 3. Konfiguration
        # ========================================================

        config_service = ConfigService(
            session_factory,
        )

        await _run_bootstrap_step(
            step="configuration.seed_defaults",
            operation=config_service.seed_defaults,
        )

        # ========================================================
        # 4. Modell-Registry
        # ========================================================

        model_registry = ModelRegistry()

        await _run_bootstrap_step(
            step="models.discover",
            operation=model_registry.discover,
        )

        # ========================================================
        # 5. Tool-Registry
        # ========================================================

        tool_registry = ToolRegistry()

        await _run_bootstrap_step(
            step="tools.discover",
            operation=tool_registry.discover,
        )

        # ========================================================
        # 6. Dienste atomar veröffentlichen
        # ========================================================

        result = BootstrapResult(
            session_factory=session_factory,
            config_service=config_service,
            model_registry=model_registry,
            tool_registry=tool_registry,
            hierarchy_repository=hierarchy_repository,
            hierarchy_service=hierarchy_service,
        )

        _publish_services(
            app=app,
            result=result,
        )

        app.state.bootstrap_complete = True
        app.state.bootstrap_error = None

        logger.info(
            "Application bootstrap completed",
            extra={
                "config_revision": config_service.revision,
                "config_definition_count": (
                    config_service.definition_count
                ),
                "config_cache_size": config_service.cache_size,
                "model_count": _registry_item_count(
                    model_registry,
                ),
                "tool_count": _registry_item_count(
                    tool_registry,
                ),
                "hierarchy_service_available": True,
            },
        )

        return result

    except Exception as exc:
        app.state.bootstrap_complete = False
        app.state.bootstrap_error = str(
            exc,
        )

        logger.exception(
            "Application bootstrap failed",
        )

        await _cleanup_partial_bootstrap(
            tool_registry=tool_registry,
            model_registry=model_registry,
            config_service=config_service,
            session_factory=session_factory,
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

    Fehler einzelner Shutdown-Schritte werden protokolliert, verhindern
    aber nicht das Aufräumen der übrigen Ressourcen.
    """

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

    session_factory_value: object = getattr(
        app.state,
        "session_factory",
        None,
    )

    session_factory = _coerce_session_factory(
        session_factory_value,
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

    logger.info(
        "Application shutdown completed",
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


# ============================================================
# Interne Bootstrap-Hilfsfunktionen
# ============================================================


async def _run_bootstrap_step(
    *,
    step: str,
    operation: Callable[[], Awaitable[T]],
) -> T:
    logger.info(
        "Starting bootstrap step",
        extra={
            "bootstrap_step": step,
        },
    )

    try:
        result = await operation()

    except Exception as exc:
        logger.exception(
            "Bootstrap step failed",
            extra={
                "bootstrap_step": step,
            },
        )

        raise BootstrapStepError(
            step=step,
            reason=str(
                exc,
            ),
        ) from exc

    logger.info(
        "Bootstrap step completed",
        extra={
            "bootstrap_step": step,
        },
    )

    return result


def _publish_services(
    *,
    app: FastAPI,
    result: BootstrapResult,
) -> None:
    """
    Veröffentlicht vollständig initialisierte Dienste logisch atomar.

    FastAPI `app.state` bietet keine echte Transaktion. Deshalb werden
    Dienste erst nach Abschluss aller vorbereitenden Schritte gesetzt.
    """

    app.state.session_factory = result.session_factory
    app.state.config_service = result.config_service
    app.state.model_registry = result.model_registry
    app.state.tool_registry = result.tool_registry

    app.state.hierarchy_repository = (
        result.hierarchy_repository
    )

    app.state.hierarchy_service = (
        result.hierarchy_service
    )


def _clear_services(
    app: FastAPI,
) -> None:
    """
    Entfernt veröffentlichte Dienstreferenzen aus `app.state`.
    """

    for attribute in (
        "hierarchy_service",
        "hierarchy_repository",
        "tool_registry",
        "model_registry",
        "config_service",
        "session_factory",
    ):
        if hasattr(
            app.state,
            attribute,
        ):
            delattr(
                app.state,
                attribute,
            )


async def _cleanup_partial_bootstrap(
    *,
    tool_registry: ToolRegistry | None,
    model_registry: ModelRegistry | None,
    config_service: ConfigService | None,
    session_factory: async_sessionmaker[AsyncSession] | None,
) -> None:
    """
    Räumt Ressourcen nach einem fehlgeschlagenen Bootstrap auf.
    """

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


async def _safe_shutdown(
    *,
    name: str,
    resource: object,
) -> None:
    """
    Ruft den ersten verfügbaren Shutdown-Mechanismus einer Ressource auf.

    Unterstützt synchrone und asynchrone Methoden.
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

        try:
            result: object = method()

            if inspect.isawaitable(
                result,
            ):
                await result

        except Exception:
            logger.exception(
                "Resource shutdown failed",
                extra={
                    "resource_name": name,
                    "shutdown_method": method_name,
                },
            )

        return


async def _dispose_session_factory(
    session_factory: (
        async_sessionmaker[AsyncSession] | None
    ),
) -> None:
    """
    Gibt die zugrunde liegende SQLAlchemy-Engine frei.

    `async_sessionmaker` besitzt selbst normalerweise keine
    `dispose()`-Methode. Die Engine ist typischerweise über
    `session_factory.kw["bind"]` erreichbar.
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
        return

    dispose = cast(
        SyncOrAsyncCallableProtocol,
        dispose_value,
    )

    try:
        result: object = dispose()

        if inspect.isawaitable(
            result,
        ):
            await result

    except Exception:
        logger.exception(
            "Database engine disposal failed",
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


def _get_required_state_service(
    *,
    app: FastAPI,
    attribute: str,
) -> object:
    if not is_application_bootstrapped(
        app,
    ):
        raise ApplicationNotBootstrappedError(
            "Die Anwendung wurde noch nicht vollständig initialisiert.",
        )

    service: object = getattr(
        app.state,
        attribute,
        None,
    )

    if service is None:
        raise ApplicationNotBootstrappedError(
            f"Der Anwendungsdienst '{attribute}' ist nicht verfügbar.",
        )

    return service


def _registry_item_count(
    registry: object,
) -> int | None:
    """
    Ermittelt die Anzahl registrierter Elemente, ohne einen bestimmten
    Registry-Vertrag zu erzwingen.

    Unterstützte Formen:

    - registry.count
    - registry.item_count
    - registry.items
    - registry.list()
    - registry.list_models()
    - registry.list_tools()
    """

    for attribute_name in (
        "count",
        "item_count",
    ):
        value: object = getattr(
            registry,
            attribute_name,
            None,
        )

        if isinstance(
            value,
            int,
        ):
            return value

    items: object = getattr(
        registry,
        "items",
        None,
    )

    if isinstance(
        items,
        Mapping,
    ):
        typed_mapping = cast(
            Mapping[object, object],
            items,
        )

        return len(
            typed_mapping,
        )

    if (
        isinstance(
            items,
            Sized,
        )
        and not isinstance(
            items,
            str | bytes | bytearray,
        )
    ):
        return len(
            items,
        )

    for method_name in (
        "list",
        "list_models",
        "list_tools",
    ):
        method_value: object = getattr(
            registry,
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

        try:
            result: object = method()

        except Exception:
            return None

        if inspect.isawaitable(
            result,
        ):
            return None

        if isinstance(
            result,
            Sized,
        ):
            return len(
                result,
            )

        return None

    return None

