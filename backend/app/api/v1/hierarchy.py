# F:\Kernschmied\backend\app\api\v1\hierarchy.py

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Mapping, Sequence
from typing import Protocol, cast, runtime_checkable

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
)

from app.auth.models import UserContext
from app.contracts.hierarchy import (
    HierarchyNode,
    HierarchyNodeCreate,
    HierarchyNodeUpdate,
)
from app.hierarchy.models import HierarchyActor
from app.hierarchy.repository import HierarchyRepository
from app.services.hierarchy_service import create_hierarchy_service

router = APIRouter()

HIERARCHY_SCHEMA_VERSION = "1.0"


# Keine eigene rekursive JsonValue-Definition – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


@runtime_checkable
class HierarchyServiceProtocol(Protocol):
    async def get_tree(
        self,
        *,
        root_id: str | None = None,
        max_depth: int | None = None,
    ) -> object: ...


# NEU: Frontend-kompatibler Response-Vertrag
class HierarchyTreeResponse(BaseModel):
    """
    API-Vertrag für die Hierarchie – kompatibel mit Frontend-HierarchyTree.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: str = HIERARCHY_SCHEMA_VERSION
    root: JsonObject
    revision: int | None = Field(
        default=None,
        ge=0,
        description="Optionale globale Revision für Cache-Invalidierung.",
    )


def get_request_id(
    request: Request,
) -> str | None:
    raw_request_id: object = getattr(
        request.state,
        "request_id",
        None,
    )

    if raw_request_id is None:
        return None

    value = str(raw_request_id).strip()

    return value or None


def structured_http_error(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Mapping[str, object] | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "details": dict(details or {}),
            "request_id": get_request_id(request),
        },
    )


async def resolve_maybe_awaitable(
    value: object,
) -> object:
    if inspect.isawaitable(value):
        return await cast(
            Awaitable[object],
            value,
        )

    return value


def normalize_non_negative_int(
    value: object,
    *,
    default: int = 0,
) -> int:
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return max(value, 0)

    if isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            return default

        try:
            return max(int(normalized), 0)
        except ValueError:
            return default

    if isinstance(value, float):
        if not value.is_integer():
            return default

        return max(int(value), 0)

    return default


async def get_config_revision(
    request: Request,
) -> int:
    service: object = getattr(
        request.app.state,
        "config_service",
        None,
    )

    if service is None:
        return 0

    revision_getter: object = getattr(
        service,
        "get_revision",
        None,
    )

    if callable(revision_getter):
        try:
            revision = await resolve_maybe_awaitable(
                revision_getter(),
            )

            return normalize_non_negative_int(
                revision,
            )

        except Exception:
            return 0

    revision = getattr(
        service,
        "revision",
        0,
    )

    revision = await resolve_maybe_awaitable(
        revision,
    )

    return normalize_non_negative_int(
        revision,
    )


def normalize_json_value(
    value: object,
) -> JsonValue:
    if value is None:
        return None

    if isinstance(
        value,
        str | int | float | bool,
    ):
        return value

    if isinstance(
        value,
        Mapping,
    ):
        mapping = cast(
            Mapping[object, object],
            value,
        )

        result: JsonObject = {}

        for raw_key, raw_value in mapping.items():
            if not isinstance(raw_key, str):
                raise TypeError("Hierarchieschlüssel müssen Strings sein.")

            result[raw_key] = normalize_json_value(
                raw_value,
            )

        return result

    if isinstance(
        value,
        Sequence,
    ):
        if isinstance(
            value,
            bytes | bytearray,
        ):
            raise TypeError("Binärdaten sind nicht zulässig.")

        sequence = cast(
            Sequence[object],
            value,
        )

        return [normalize_json_value(item) for item in sequence]

    if isinstance(
        value,
        set | frozenset,
    ):
        values = cast(
            set[object] | frozenset[object],
            value,
        )

        return [normalize_json_value(item) for item in values]

    model_dump = getattr(
        value,
        "model_dump",
        None,
    )

    if callable(model_dump):
        return normalize_json_value(
            model_dump(
                mode="json",
            )
        )

    raise TypeError(f"Nicht unterstützter Typ '{type(value).__name__}'.")


def normalize_hierarchy(
    value: object,
) -> JsonObject:
    normalized = normalize_json_value(
        value,
    )

    if not isinstance(
        normalized,
        dict,
    ):
        raise TypeError("Die Hierarchie muss ein JSON-Objekt sein.")

    return normalized


def build_actor_from_request(request: Request) -> HierarchyActor:
    principal: object | None = getattr(request.state, "user", None)

    if principal is None:
        return HierarchyActor()

    if isinstance(principal, UserContext):
        user = principal
    else:
        try:
            user = UserContext.from_principal(principal)
        except Exception:
            return HierarchyActor()

    return HierarchyActor(
        user_id=user.id,
        roles=frozenset(user.roles),
        permissions=frozenset(user.permissions),
    )


def get_hierarchy_service(
    request: Request,
) -> HierarchyServiceProtocol:
    service: object = getattr(
        request.app.state,
        "hierarchy_service",
        None,
    )

    if service is None:
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="HIERARCHY_SERVICE_UNAVAILABLE",
            message="Der Hierarchiedienst ist nicht verfügbar.",
        )

    if not isinstance(
        service,
        HierarchyServiceProtocol,
    ):
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="HIERARCHY_SERVICE_CONTRACT_UNSUPPORTED",
            message="Der registrierte Hierarchiedienst erfüllt den erforderlichen Vertrag nicht.",
            details={
                "required_method": "get_tree",
            },
        )

    return service


@router.get(
    "",
    response_model=HierarchyTreeResponse,  # geändert!
    response_model_exclude_none=True,
    summary="Hierarchie laden",
    description=(
        "Liefert die generische Projekt-/Mandanten-/Objekthierarchie "
        "für das schema-gesteuerte Frontend."
    ),
)
async def hierarchy(
    request: Request,
    response: Response,
    root_id: str | None = Query(
        default=None,
        description="Optionaler Startknoten.",
    ),
    max_depth: int | None = Query(
        default=None,
        ge=1,
        le=32,
        description="Optionale maximale Rekursionstiefe.",
    ),
) -> HierarchyTreeResponse:
    service = get_hierarchy_service(
        request,
    )

    raw_tree = await service.get_tree(
        root_id=root_id,
        max_depth=max_depth,
    )

    tree = normalize_hierarchy(
        raw_tree,
    )

    revision = await get_config_revision(
        request,
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Hierarchy-Schema-Version"] = HIERARCHY_SCHEMA_VERSION

    return HierarchyTreeResponse(
        root=tree,
        schema_version=HIERARCHY_SCHEMA_VERSION,
        revision=revision,
    )


class _MovePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_parent_id: str | None = Field(
        default=None,
        description="Neuer Elternknoten oder null für Root",
    )


class _ReorderItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(...)
    new_parent_id: str | None = Field(default=None)
    new_position: int = Field(..., ge=0)


class _ReorderPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[_ReorderItem]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=HierarchyNode,
    summary="Hierarchieknoten erstellen",
)
async def create_hierarchy_node(
    request: Request,
    payload: HierarchyNodeCreate,
) -> HierarchyNode:
    actor = build_actor_from_request(request)

    session_factory = getattr(request.app.state, "session_factory", None)

    if session_factory is None:
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="HIERARCHY_PERSISTENCE_UNAVAILABLE",
            message="Die Persistenz für Hierarchie ist nicht verfügbar.",
        )

    async with session_factory() as session:  # type: ignore[arg-type]
        repository = HierarchyRepository(session)  # type: ignore[arg-type]
        service = create_hierarchy_service(repository)

        try:
            node = await service.create_node(payload, actor=actor)
            return node
        except PermissionError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code="PERMISSION_DENIED",
                message=str(exc),
            )


@router.patch(
    "/{node_id}",
    response_model=HierarchyNode,
    summary="Hierarchieknoten aktualisieren",
)
async def update_hierarchy_node(
    request: Request,
    node_id: str,
    payload: HierarchyNodeUpdate,
) -> HierarchyNode:
    actor = build_actor_from_request(request)

    session_factory = getattr(request.app.state, "session_factory", None)

    if session_factory is None:
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="HIERARCHY_PERSISTENCE_UNAVAILABLE",
            message="Die Persistenz für Hierarchie ist nicht verfügbar.",
        )

    async with session_factory() as session:  # type: ignore[arg-type]
        repository = HierarchyRepository(session)  # type: ignore[arg-type]
        service = create_hierarchy_service(repository)

        try:
            node = await service.update_node(node_id, payload, actor=actor)
            return node
        except LookupError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_404_NOT_FOUND,
                code="HIERARCHY_NODE_NOT_FOUND",
                message=str(exc),
            )
        except PermissionError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code="PERMISSION_DENIED",
                message=str(exc),
            )


@router.post(
    "/{node_id}/move",
    response_model=HierarchyNode,
    summary="Hierarchieknoten verschieben",
)
async def move_hierarchy_node(
    request: Request,
    node_id: str,
    payload: _MovePayload,
) -> HierarchyNode:
    actor = build_actor_from_request(request)

    session_factory = getattr(request.app.state, "session_factory", None)

    if session_factory is None:
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="HIERARCHY_PERSISTENCE_UNAVAILABLE",
            message="Die Persistenz für Hierarchie ist nicht verfügbar.",
        )

    async with session_factory() as session:  # type: ignore[arg-type]
        repository = HierarchyRepository(session)  # type: ignore[arg-type]
        service = create_hierarchy_service(repository)

        try:
            node = await service.move_node(
                node_id, new_parent_id=payload.new_parent_id, actor=actor
            )
            return node
        except LookupError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_404_NOT_FOUND,
                code="HIERARCHY_NODE_NOT_FOUND",
                message=str(exc),
            )
        except PermissionError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code="PERMISSION_DENIED",
                message=str(exc),
            )


@router.post(
    "/reorder",
    response_class=Response,
    summary="Mehrere Knoten atomar neu anordnen",
)
async def reorder_hierarchy_nodes(
    request: Request,
    payload: _ReorderPayload,
) -> Response:
    actor = build_actor_from_request(request)

    session_factory = getattr(request.app.state, "session_factory", None)

    if session_factory is None:
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="HIERARCHY_PERSISTENCE_UNAVAILABLE",
            message="Die Persistenz für Hierarchie ist nicht verfügbar.",
        )

    async with session_factory() as session:  # type: ignore[arg-type]
        repository = HierarchyRepository(session)  # type: ignore[arg-type]
        service = create_hierarchy_service(repository)

        try:
            moves = [(it.id, it.new_parent_id, it.new_position) for it in payload.items]
            await service.reorder_nodes(moves, actor=actor)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except LookupError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_404_NOT_FOUND,
                code="HIERARCHY_NODE_NOT_FOUND",
                message=str(exc),
            )
        except PermissionError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code="PERMISSION_DENIED",
                message=str(exc),
            )
        except ValueError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_400_BAD_REQUEST,
                code="HIERARCHY_INVALID_REORDER",
                message=str(exc),
            )


@router.delete(
    "/{node_id}",
    response_class=Response,
    summary="Hierarchieknoten löschen",
)
async def delete_hierarchy_node(
    request: Request,
    node_id: str,
) -> Response:
    actor = build_actor_from_request(request)

    session_factory = getattr(request.app.state, "session_factory", None)

    if session_factory is None:
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="HIERARCHY_PERSISTENCE_UNAVAILABLE",
            message="Die Persistenz für Hierarchie ist nicht verfügbar.",
        )

    async with session_factory() as session:  # type: ignore[arg-type]
        repository = HierarchyRepository(session)  # type: ignore[arg-type]
        service = create_hierarchy_service(repository)

        try:
            await service.delete_node(node_id, actor=actor)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except LookupError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_404_NOT_FOUND,
                code="HIERARCHY_NODE_NOT_FOUND",
                message=str(exc),
            )
        except PermissionError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code="PERMISSION_DENIED",
                message=str(exc),
            )
