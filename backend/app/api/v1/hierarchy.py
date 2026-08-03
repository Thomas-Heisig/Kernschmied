# F:\Kernschmied\backend\app\api\v1\hierarchy.py

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Mapping, Sequence
from typing import Protocol, cast, runtime_checkable, Any, Optional
from typing import List

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
from app.hierarchy.repository import HierarchyParentNotFoundError
from app.hierarchy.service import HierarchyChildTypeNotAllowedError
from app.services.hierarchy_service import create_hierarchy_service

router = APIRouter()

HIERARCHY_SCHEMA_VERSION = "1.0"


# Keine eigene rekursive JsonValue-Definition – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]
JSONDict = dict[str, Any]


@runtime_checkable
class HierarchyServiceProtocol(Protocol):
    async def get_tree(
        self,
        *,
        actor: object | None = None,
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


def _map_backend_tree_to_frontend(value: JSONDict | List[Any]) -> JSONDict | List[Any]:
    """Map backend HierarchyTree (config_revision + roots) to frontend root shape.

    The serializer/service may return a model or dict with
    `config_revision` and `roots`. The frontend expects a single
    `root` node. This helper is a minimal, defensive mapping layer
    used by the API surface to keep the internal contract stable.
    """
    # If it's a pydantic model, prefer its model_dump representation
    model_dump = getattr(value, "model_dump", None)

    if callable(model_dump):
        try:
            as_dict_any: Any = model_dump()
        except Exception:
            as_dict_any = value
    else:
        as_dict_any = value

    if not isinstance(as_dict_any, dict):
        return value

    as_dict = cast(JSONDict, as_dict_any)

    # Detect legacy backend tree shape: has `config_revision` and `roots`
    if "roots" in as_dict and ("config_revision" in as_dict or "roots" in as_dict):
        roots_raw: Any = as_dict.get("roots")
        if isinstance(roots_raw, list):
            roots = cast(List[Any], roots_raw)
        else:
            roots = []

        root_node: Optional[Any] = None

        if len(roots) > 0:
            root_node = roots[0]

        # Defensive: if no root available, return an empty dict so the
        # normalizer can fail loudly or the caller can handle it.
        if root_node is None:
            return {}

        return root_node

    return value


def _publicize_node(node: object) -> object:
    """Recursively normalize a node to the public API shape.

    - Rename `available_actions` -> `actions`
    - Ensure `children` is always a list (empty if missing)
    - Ensure `actions` is always a list (empty if missing)
    - Avoid returning ORM/Pydantic internals by working on plain dicts
    """
    # Convert pydantic models to dicts if possible
    model_dump = getattr(node, "model_dump", None)
    if callable(model_dump):
        try:
            obj_any: Any = model_dump()
        except Exception:
            obj_any = node
    else:
        obj_any = node

    if not isinstance(obj_any, dict):
        return obj_any

    obj: JSONDict = cast(JSONDict, obj_any)

    # Prepare a shallow copy to avoid mutating originals
    out: dict[str, Any] = {}

    # Copy known scalar/string fields directly
    for key in (
        "id",
        "type",
        "name",
        "parent_id",
        "sort_order",
        "selectable",
        "disabled",
        "status",
        "metadata",
        "revision",
        "system_prompt",
    ):
        if key in obj:
            out[key] = obj[key]

    # Actions: map available_actions -> actions
    actions_any: Any = obj.get("actions")
    if actions_any is None:
        actions_any = obj.get("available_actions")

    if actions_any is None or not isinstance(actions_any, list):
        out["actions"] = []
    else:
        actions_list = cast(List[Any], actions_any)
        out["actions"] = [a for a in actions_list]

    # Children: ensure list and recursively publicize
    raw_children_any: Any = obj.get("children")
    if raw_children_any is None or not isinstance(raw_children_any, list):
        out["children"] = []
    else:
        raw_children = cast(List[Any], raw_children_any)
        children: List[object] = []
        for child_any in raw_children:
            try:
                children.append(_publicize_node(child_any))
            except Exception:
                # If a child cannot be serialized, skip it
                continue

        out["children"] = children

    # Preserve additional safe fields that frontend may rely on
    for optional in (
        "tool_policy",
        "config_overrides",
        "metadata",
        "effective_prompt",
        "effective_tools",
        "effective_config",
        "system_prompt",
    ):
        if optional in obj and obj[optional] is not None:
            out[optional] = obj[optional]

    return out


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
    include_system_nodes: bool = Query(
        default=False,
        description="Wenn true und der Aufrufer Admin ist, werden system-interne Knoten (z.B. system-root) im Ergebnis belassen.",
    ),
) -> HierarchyTreeResponse:
    service = get_hierarchy_service(request)

    actor = build_actor_from_request(request)

    try:
        raw_tree_any = await service.get_tree(
                actor=actor,
                root_id=root_id,
                max_depth=max_depth,
            )

        # Type: service implementations may return pydantic/ORM models or
        # plain dicts. Cast to a JSON-shaped dict or list for downstream
        # processing so the type checker can reason about `.get()` and
        # indexing operations.
        raw_tree = cast(JSONDict | List[Any], raw_tree_any)

        # Map internal backend tree shape (config_revision + roots)
        # to the frontend-expected single `root` node shape.
        raw_tree = _map_backend_tree_to_frontend(raw_tree)

        # Defensive: never return a non-user root for normal callers.
        # Forbid returning certain technical/structural types as the visible
        # root for non-admin callers.
        forbidden_root_types = {"chat", "project", "workspace", "folder"}
        if isinstance(raw_tree, dict):
            rt = raw_tree.get("type")
            if rt in forbidden_root_types and not getattr(actor, "is_admin", False):
                # Do not silently fall back to arbitrary nodes — return a structured error.
                raise structured_http_error(
                    request=request,
                    status_code=status.HTTP_404_NOT_FOUND,
                    code="HIERARCHY_USER_ROOT_NOT_FOUND",
                    message=(
                        "Für den angemeldeten Benutzer wurde kein gültiger Hierarchie-Root gefunden."
                    ),
                    details={"invalid_root_type": rt},
                )

        # Projection: keep `system-root` internal by default. If the
        # backend returns the technical `system-root` as top-level node
        # we project it to a visible user root for normal callers.
        if isinstance(raw_tree, dict):
            raw_tree_dict: JSONDict = raw_tree

            if raw_tree_dict.get("id") == "system-root":
                # Admins may request the system nodes explicitly
                if include_system_nodes:
                    if not getattr(actor, "is_admin", False):
                        raise PermissionError("Nur Administratoren dürfen system-interne Knoten anfordern.")
                    # leave system-root as-is for admins
                else:
                    # Try to pick the caller's user node if available
                    selected: JSONDict | None = None
                    children_any = raw_tree_dict.get("children", [])
                    if not isinstance(children_any, list):
                        children: List[Any] = []
                    else:
                        children = cast(List[Any], children_any)

                    if getattr(actor, "user_id", None) is not None:
                        for c in children:
                            if isinstance(c, dict):
                                c_dict = cast(JSONDict, c)
                                if c_dict.get("id") == actor.user_id:
                                    selected = c_dict
                                    break

                    # Fallback: first child of type 'user'
                    if selected is None:
                        for c in children:
                            if isinstance(c, dict):
                                c_dict = cast(JSONDict, c)
                                if c_dict.get("type") == "user":
                                    selected = c_dict
                                    break

                    # Final fallback: pick the first non-chat child (never project a chat node)
                    if selected is None and children:
                        for c in children:
                            if isinstance(c, dict):
                                c_dict = cast(JSONDict, c)
                                if c_dict.get("type") != "chat":
                                    selected = c_dict
                                    break

                    # If still not found, return a structured error instead of silently
                    # projecting a technical chat node.
                    if selected is None:
                        raise structured_http_error(
                            request=request,
                            status_code=status.HTTP_404_NOT_FOUND,
                            code="HIERARCHY_USER_ROOT_NOT_FOUND",
                            message="Kein benutzerbezogener Root-Knoten gefunden.",
                        )

                    raw_tree = selected

        # Ensure node fields match the public contract (rename actions,
        # enforce arrays for children/actions, recurse).
        raw_tree = _publicize_node(raw_tree)
    except PermissionError as exc:
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_403_FORBIDDEN,
            code="HIERARCHY_READ_FORBIDDEN",
            message=str(exc),
        ) from exc

    tree = normalize_hierarchy(raw_tree)

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
        except HierarchyChildTypeNotAllowedError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=getattr(exc, "code", "HIERARCHY_CHILD_TYPE_NOT_ALLOWED"),
                message=str(exc),
            ) from exc
        except ValueError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_HIERARCHY_NODE",
                message=str(exc),
            ) from exc
        except HierarchyParentNotFoundError as exc:
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="HIERARCHY_PARENT_REQUIRED",
                message="Für den neuen Hierarchieknoten ist ein übergeordneter Knoten erforderlich.",
                details={"node_type": payload.type if hasattr(payload, "type") else "unknown"},
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
