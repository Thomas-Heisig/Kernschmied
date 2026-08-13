from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
import traceback
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_session
from app.storage.models import HierarchyNode, WidgetRegistry, WidgetAssignment
from app.widgets.service import WidgetResolverService
import logging

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
    # Delegate to the resolver service to compute effective widgets consistently
    resolver = WidgetResolverService(session)
    user = getattr(request.state, "user", None)
    try:
        # Log actor mapping for diagnostics (id, roles, permissions, is_system_admin)
        if user is not None:
            uid = getattr(user, "id", None)
            roles = getattr(user, "roles", None) or getattr(user, "roles", [])
            perms = getattr(user, "permissions", None) or getattr(user, "permissions", [])
            is_sys_admin = getattr(user, "is_system_admin", False)
            logger.debug("widgets.endpoint: actor id=%s roles=%s permissions=%s is_system_admin=%s", uid, roles, perms, is_sys_admin)
    except Exception:
        logger.debug("widgets.endpoint: failed to introspect actor", exc_info=True)
    try:
        items = await resolver.resolve_effective_widgets(node_id, user)
    except Exception:
        logger.exception("Widget resolution failed for node %s", node_id)
        items = []

    # The resolver is the source of truth for component_type and related
    # metadata. Do not perform additional lookup/enrichment here — return
    # resolver output verbatim so frontend can rely on a consistent API
    # shape. Provide both snake_case and camelCase top-level keys for compatibility.
    return {"schema_version": "1.0", "schemaVersion": "1.0", "node_id": node_id, "items": items}


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

    # Persist assignments to the relational WidgetAssignment table as
    # Source of Truth. Mirror the JSON field on the node for
    # compatibility only after relational changes succeed.
    assigns: list[dict] = payload.assignments or []

    node = await _get_node(session, node_id)

    try:
        # Load existing relational rows for the node
        stmt = select(WidgetAssignment).where(WidgetAssignment.node_id == node.id)
        res = await session.execute(stmt)
        existing_rows = res.scalars().all()

        # Build lookup for existing rows by key (prefer widget_id, fallback to name)
        existing_map: dict[str, WidgetAssignment] = {}
        for r in existing_rows:
            key = str(getattr(r, "widget_id", None) or getattr(r, "name", ""))
            existing_map[key] = r

        # Prepare incoming keys set
        incoming_keys: set[str] = set()

        # Upsert incoming assignments
        for a in assigns:
            if not isinstance(a, dict):
                continue
            widget_id = a.get("id") or a.get("widget_id") or None
            name = a.get("name") or widget_id or None
            key = str(widget_id or name or "")
            incoming_keys.add(key)

            enabled = bool(a.get("enabled", True))
            inherit = bool(a.get("inherit", True))
            try:
                position = int(a.get("position", 1000) or 1000)
            except Exception:
                position = 1000
            configuration = a.get("configuration") or {}
            required_permissions = a.get("required_permissions") or []

            existing = existing_map.get(key)
            if existing is not None:
                # update
                existing.enabled = enabled
                existing.inherit = inherit
                existing.position = position
                existing.configuration = configuration
                existing.required_permissions = required_permissions
                existing.name = name
                if widget_id:
                    existing.widget_id = widget_id
                session.add(existing)
            else:
                # insert
                wa = WidgetAssignment(
                    node_id=node.id,
                    widget_id=widget_id,
                    name=name,
                    enabled=enabled,
                    inherit=inherit,
                    position=position,
                    configuration=configuration,
                    required_permissions=required_permissions,
                )
                session.add(wa)

        # Delete relational rows that are not present in incoming keys
        for r in existing_rows:
            key = str(getattr(r, "widget_id", None) or getattr(r, "name", ""))
            if key not in incoming_keys:
                await session.delete(r)

        # Mirror JSON compatibility field on node
        node.widget_assignments = assigns
        session.add(node)

        # Commit the transaction explicitly. get_session manages the session
        # lifecycle but does not auto-commit — explicit commit ensures atomic
        # persistence while avoiding nested transaction errors.
        await session.commit()
        await session.refresh(node)

        return {"status": "ok", "assignments": node.widget_assignments}
    except Exception:
        logger.exception("Failed to persist node assignments for %s", node_id)
        try:
            await session.rollback()
        except Exception:
            logger.exception("Rollback failed for node %s", node_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
