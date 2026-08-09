from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_session
from app.storage.models import HierarchyNode, WidgetRegistry
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()


class WidgetRegistryIn(BaseModel):
    name: str
    type: str | None = None
    metadata: dict = {}
    default_config: dict = {}
    required_permissions: list[str] = []
    status: str = "active"
    version: str | None = None
    interaction_mode: str | None = None


class WidgetRegistryOut(WidgetRegistryIn):
    id: str
    created_at: datetime
    updated_at: datetime


class WidgetAssignmentIn(BaseModel):
    assignments: list[dict]


@router.get("/", response_model=list[WidgetRegistryOut])
async def list_registry(session: AsyncSession = Depends(get_session)):
    try:
        stmt = select(WidgetRegistry)
        result = await session.execute(stmt)
        items = result.scalars().all()
        return [
            WidgetRegistryOut(
                id=i.id,
                name=i.name,
                type=i.type,
                metadata=i.widget_metadata,
                default_config=i.default_config,
                required_permissions=i.required_permissions,
                status=i.status,
                version=i.version,
                interaction_mode=i.interaction_mode,
                created_at=i.created_at,
                updated_at=i.updated_at,
            )
            for i in items
        ]
    except Exception as e:
        # Log full traceback for debugging purposes
        logger.exception("Failed in list_registry: %s", e)
        tb = traceback.format_exc()
        logger.error("Traceback: %s", tb)
        # Re-raise to allow FastAPI to return a 500
        raise


@router.post("/", response_model=WidgetRegistryOut, status_code=status.HTTP_201_CREATED)
async def create_registry(payload: WidgetRegistryIn = Body(...), session: AsyncSession = Depends(get_session)):
    obj = WidgetRegistry(
        name=payload.name,
        type=payload.type,
        widget_metadata=payload.metadata,
        default_config=payload.default_config,
        required_permissions=payload.required_permissions,
        status=payload.status,
        version=payload.version,
        interaction_mode=payload.interaction_mode,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return WidgetRegistryOut(
        id=obj.id,
        name=obj.name,
        type=obj.type,
        metadata=obj.widget_metadata,
        default_config=obj.default_config,
        required_permissions=obj.required_permissions,
        status=obj.status,
        version=obj.version,
        interaction_mode=obj.interaction_mode,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


async def _get_node(session: AsyncSession, node_id: str) -> HierarchyNode:
    stmt = select(HierarchyNode).where(HierarchyNode.id == node_id)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return obj


@router.get("/nodes/{node_id}/effective")
async def get_effective_widgets(node_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    # Resolve effective widgets by traversing ancestors and merging widget_assignments
    node = await _get_node(session, node_id)

    # auth info
    user = getattr(request.state, "user", None)

    def is_admin(u) -> bool:
        if u is None:
            return False
        roles = getattr(u, "roles", ()) or ()
        perms = getattr(u, "permissions", ()) or ()
        return "admin" in roles or "*" in perms

    # If this or any ancestor is a system node, only admin may view
    # collect chain temporarily to inspect is_system
    temp_chain: list[HierarchyNode] = []
    cur = node
    while cur is not None:
        temp_chain.append(cur)
        if not cur.parent_id:
            break
        stmt = select(HierarchyNode).where(HierarchyNode.id == cur.parent_id)
        res = await session.execute(stmt)
        cur = res.scalar_one_or_none()

    if any(getattr(n, "is_system", False) for n in temp_chain) and not is_admin(user):
        return {"items": []}

    # collect chain from root -> node
    chain: list[HierarchyNode] = []
    cur = node
    while cur is not None:
        chain.append(cur)
        if not cur.parent_id:
            break
        stmt = select(HierarchyNode).where(HierarchyNode.id == cur.parent_id)
        res = await session.execute(stmt)
        cur = res.scalar_one_or_none()

    # reverse chain to go from root to node
    chain = list(reversed(chain))

    effective: list[dict] = []
    names_seen: set = set()

    # include registry defaults for each node type if present
    for n in chain:
        # registry defaults by node type
        stmt = select(WidgetRegistry).where(WidgetRegistry.name == n.type)
        res = await session.execute(stmt)
        reg = res.scalar_one_or_none()
        if reg and isinstance(reg.default_config, dict):
            # skip deprecated registry entries
            if getattr(reg, "status", "active") == "deprecated":
                defaults = None
            else:
                defaults = reg.default_config.get("default_widgets")
            if isinstance(defaults, list):
                for w in defaults:
                    name = w.get("name") if isinstance(w, dict) else None
                    # permission check: registry-level required_permissions
                    required = getattr(reg, "required_permissions", []) or []
                    if required and user is not None:
                        user_perms = set(getattr(user, "permissions", ())) | set(getattr(user, "roles", ()))
                        if not any(r in user_perms for r in required):
                            continue

                    if name and name in names_seen:
                        continue
                    effective.append(w)
                    if name:
                        names_seen.add(name)

        # now include explicit widget_assignments on the node
        assigns = getattr(n, "widget_assignments", None) or []
        if isinstance(assigns, list):
            for w in assigns:
                if not isinstance(w, dict):
                    continue
                name = w.get("name")
                # assignment-level visibility check
                vis = w.get("visible_to") or w.get("visible")
                if vis:
                    # allow boolean true => visible to all
                    if isinstance(vis, list):
                        user_perms = set(getattr(user, "permissions", ())) | set(getattr(user, "roles", ()))
                        if not any(v in user_perms for v in vis):
                            continue
                    elif vis is False:
                        continue
                # override if same name seen before
                if name and name in names_seen:
                    # replace previous
                    for idx, ex in enumerate(effective):
                        if isinstance(ex, dict) and ex.get("name") == name:
                            effective[idx] = w
                            break
                else:
                    effective.append(w)
                    if name:
                        names_seen.add(name)

    return {"items": effective}


@router.post("/nodes/{node_id}/assignments", status_code=status.HTTP_200_OK)
async def set_node_assignments(
    node_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    payload: WidgetAssignmentIn = Body(...),
):
    # Basic auth check: ensure user present
    if request is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    obj = await _get_node(session, node_id)
    obj.widget_assignments = payload.assignments or []
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return {"status": "ok", "assignments": obj.widget_assignments}
