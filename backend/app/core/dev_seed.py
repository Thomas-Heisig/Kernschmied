from __future__ import annotations

import logging
from typing import Any, Dict, List, cast

from sqlalchemy import select
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.auth.password_service import PasswordService
from app.contracts.hierarchy import HierarchyNodeCreate
from app.core.settings import settings
from app.database.models.user import UserModel
from app.database.models.user_role import RoleModel, UserRoleModel
from app.hierarchy.repository import HierarchyRepository
from app.services.mailbox_service import ensure_user_mailbox
from app.storage.models import WidgetAssignment, WidgetRegistry
from app.storage.repositories.user import UserRepository

logger = logging.getLogger(__name__)


async def seed_development_hierarchy(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """
    Idempotenter Development-Seed für die Hierarchie.

    Erstellt nur fehlende Knoten und überschreibt keine vorhandenen Daten.
    """
    if settings.app_environment.name.lower() != "development":
        logger.debug("Skipping dev seed: not in development environment")
        return

    # Break the seed into multiple independent transactional steps. Each step
    # uses a fresh session/transaction so a failure in one step will not leave
    # the session in a closed/invalid state for subsequent steps.
    # Step 1: ensure system-root and bootstrap-admin nodes
    try:
        async with session_factory() as s1:
            async with s1.begin():
                repo = HierarchyRepository(s1)
                # Ensure system-root exists and protective flags are correct
                system_root = await repo.get_node("system-root")
                if system_root is None:
                    await repo.create_node(
                        HierarchyNodeCreate(
                            node_id="system-root",
                            type="system",
                            name="System Root",
                            parent_id=None,
                            system_prompt=None,
                            tool_policy={},
                            config_overrides={},
                            metadata={},
                        )
                    )
                else:
                    changed = False
                    if not getattr(system_root, "is_system", False):
                        system_root.is_system = True
                        changed = True
                    if getattr(system_root, "is_movable", True):
                        system_root.is_movable = False
                        changed = True
                    if getattr(system_root, "is_deletable", True):
                        system_root.is_deletable = False
                        changed = True

                    if changed:
                        await repo._session.flush()  # type: ignore[attr-defined]

                # Bootstrap administrator node
                admin_node = await repo.get_node("bootstrap-admin")
                if admin_node is None:
                    await repo.create_node(
                        HierarchyNodeCreate(
                            node_id="bootstrap-admin",
                            type="user",
                            name="Administrator",
                            parent_id="system-root",
                            system_prompt=None,
                            tool_policy={},
                            config_overrides={},
                            metadata={
                                "bootstrap_admin": True,
                                "user_id": "local-development-admin",
                                "display_name": "Administrator",
                            },
                        )
                    )
                else:
                    repaired = False
                    if admin_node.type != "user":
                        admin_node.type = "user"
                        repaired = True
                    if admin_node.name != "Administrator":
                        admin_node.name = "Administrator"
                        repaired = True
                    if admin_node.parent_id != "system-root":
                        await repo.move_node(admin_node, new_parent_id="system-root")

                    if repaired:
                        await repo._session.flush()  # type: ignore[attr-defined]
        logger.info("Development minimal hierarchy seed applied (idempotent)")
    except Exception:
        logger.exception("Development hierarchy seed failed; continuing")

    # Step 2: ensure admin user, roles and basic system children
    try:
        async with session_factory() as s2:
            async with s2.begin():
                repo = HierarchyRepository(s2)
                if settings.app_environment.name.lower() == "development":
                    user_repo = UserRepository(s2)
                    pwd = PasswordService()

                    admin: UserModel | None = await user_repo.get_by_id(
                        settings.development_admin_user_id
                    )
                    if admin is None:
                        admin = await user_repo.get_by_username(
                            settings.development_admin_username
                        )

                    if admin is None:
                        user_data: dict[str, object | None] = {
                            "id": settings.development_admin_user_id,
                            "username": settings.development_admin_username,
                            "display_name": settings.development_admin_display_name,
                            "email": None,
                            "password_hash": pwd.hash_password(
                                settings.development_admin_password
                            ),
                            "is_active": True,
                            "is_system_admin": True,
                            "is_system_user": True,
                        }
                        admin = await user_repo.create(user_data)
                    else:
                        updated = False
                        if getattr(admin, "username", None) != settings.development_admin_username:
                            conflict = await user_repo.get_by_username(
                                settings.development_admin_username
                            )
                            if conflict is None or conflict.id == admin.id:
                                admin.username = settings.development_admin_username
                                updated = True
                            else:
                                logger.warning(
                                    "Cannot rename existing dev admin to %s: username conflict",
                                    settings.development_admin_username,
                                )

                        if getattr(admin, "display_name", None) != settings.development_admin_display_name:
                            admin.display_name = settings.development_admin_display_name
                            updated = True

                        if getattr(admin, "password_hash", None) is None:
                            admin.password_hash = pwd.hash_password(
                                settings.development_admin_password
                            )
                            updated = True

                        if not getattr(admin, "is_system_admin", False):
                            admin.is_system_admin = True
                            updated = True
                        if not getattr(admin, "is_system_user", False):
                            admin.is_system_user = True
                            updated = True

                        if updated:
                            await user_repo.update(admin, {})

                    await ensure_user_mailbox(
                        s2,
                        admin.id,
                        external_email=admin.email,
                        sync_external_email=True,
                    )

                    q = select(RoleModel).where(RoleModel.name == "admin")
                    result = await s2.execute(q)
                    admin_role = result.scalar_one_or_none()
                    if admin_role is None:
                        admin_role = RoleModel(
                            name="admin",
                            display_name="Administrator",
                            is_system=True,
                            assignable=True,
                        )
                        s2.add(admin_role)
                        await s2.flush()

                    q2 = select(UserRoleModel).where(
                        UserRoleModel.user_id == admin.id,
                        UserRoleModel.role_id == admin_role.id,
                    )
                    res2 = await s2.execute(q2)
                    mapping = res2.scalar_one_or_none()
                    if mapping is None:
                        ur = UserRoleModel(user_id=admin.id, role_id=admin_role.id)
                        s2.add(ur)
                        await s2.flush()

                    # Ensure standard root nodes under system-root
                    users_root = await repo.get_node("users-root")
                    if users_root is None:
                        await repo.create_node(
                            HierarchyNodeCreate(
                                node_id="users-root",
                                type="users-root",
                                name="Users",
                                parent_id="system-root",
                                system_prompt=None,
                                tool_policy={},
                                config_overrides={},
                                metadata={"system_managed": True},
                            )
                        )
                    elif users_root.type != "users-root":
                        users_root.type = "users-root"
                        await repo._session.flush()  # type: ignore[attr-defined]

                    workspaces_root = await repo.get_node("workspaces-root")
                    if workspaces_root is None:
                        await repo.create_node(
                            HierarchyNodeCreate(
                                node_id="workspaces-root",
                                type="workspaces-root",
                                name="Workspaces",
                                parent_id="system-root",
                                system_prompt=None,
                                tool_policy={},
                                config_overrides={},
                                metadata={"system_managed": True},
                            )
                        )
                    elif workspaces_root.type != "workspaces-root":
                        workspaces_root.type = "workspaces-root"
                        await repo._session.flush()  # type: ignore[attr-defined]

                    chats_root = await repo.get_node("chats-root")
                    if chats_root is None:
                        await repo.create_node(
                            HierarchyNodeCreate(
                                node_id="chats-root",
                                type="chats-root",
                                name="Chats",
                                parent_id="system-root",
                                system_prompt=None,
                                tool_policy={},
                                config_overrides={},
                                metadata={"system_managed": True},
                            )
                        )
                    elif chats_root.type != "chats-root":
                        chats_root.type = "chats-root"
                        await repo._session.flush()  # type: ignore[attr-defined]

                    # Ensure admin has a dedicated user node under users-root
                    admin_node_id = f"user-{admin.id}"
                    existing_admin_node = await repo.get_node(admin_node_id)
                    if existing_admin_node is None:
                        await repo.create_node(
                            HierarchyNodeCreate(
                                node_id=admin_node_id,
                                type="user",
                                name=admin.display_name or admin.username,
                                parent_id="users-root",
                                system_prompt=None,
                                tool_policy={},
                                config_overrides={},
                                metadata={
                                    "entity_type": "user",
                                    "entity_id": admin.id,
                                    "display_name": admin.display_name,
                                },
                            )
                        )

                    # Repair: create user nodes for all active users missing them
                    stmt = select(UserModel).where(UserModel.is_active.is_(True))
                    res = await s2.execute(stmt)
                    users = res.scalars().all()

                    children = await repo.list_children("users-root")
                    existing_entity_ids = {
                        str(n.node_metadata.get("entity_id"))
                        for n in children
                        if n.node_metadata and n.node_metadata.get("entity_type") == "user"
                    }

                    for u in users:
                        if str(u.id) in existing_entity_ids:
                            continue
                        node_id = f"user-{u.id}"
                        await repo.create_node(
                            HierarchyNodeCreate(
                                node_id=node_id,
                                type="user",
                                name=u.display_name or u.username,
                                parent_id="users-root",
                                system_prompt=None,
                                tool_policy={},
                                config_overrides={},
                                metadata={
                                    "entity_type": "user",
                                    "entity_id": u.id,
                                    "display_name": u.display_name,
                                },
                            )
                        )
        logger.info("Development admin user and role ensured (idempotent)")
    except Exception:
        logger.exception("Development admin seed failed; continuing")

    # Step 3: ensure widget registry entries (canonical pool)
    try:
        async with session_factory() as s3:
            async with s3.begin():
                widget_pool: List[Dict[str, Any]] = [
                    {
                        "name": "system_health",
                        "type": "system_health_widget",
                        "widget_metadata": {"component_type": "system_health_widget", "supported_node_types": ["system"]},
                    },
                    {
                        "name": "audit_log",
                        "type": "audit_log_widget",
                        "widget_metadata": {"component_type": "audit_log_widget", "supported_node_types": ["system"]},
                    },
                    {
                        "name": "registry_editor",
                        "type": "registry_editor_widget",
                        "widget_metadata": {"component_type": "registry_editor_widget", "supported_node_types": ["system"]},
                    },
                    {
                        "name": "calendar",
                        "type": "calendar_widget",
                        "widget_metadata": {"component_type": "calendar_widget"},
                    },
                    {
                        "name": "files",
                        "type": "files_widget",
                        "widget_metadata": {"component_type": "files_widget", "supported_node_types": ["workspace", "project", "chat", "user", "folder"]},
                    },
                    {
                        "name": "chat",
                        "type": "chat_widget",
                        "widget_metadata": {"component_type": "chat_widget", "supported_node_types": ["chat", "user", "workspace"]},
                    },
                ]

                for sw in widget_pool:
                    # Find all registry rows with this logical name
                    q = select(WidgetRegistry).where(WidgetRegistry.name == sw["name"])
                    try:
                        resw = await s3.execute(q)
                        rows = cast(List[WidgetRegistry], resw.scalars().all())
                    except Exception:
                        logger.warning("Dev seed: failed to query registry rows for %s; skipping", sw["name"])
                        rows = []

                    # Prefer an existing row whose id equals the stable name
                    canonical: WidgetRegistry | None = None
                    for r in rows:
                        if getattr(r, "id", None) == sw["name"]:
                            canonical = r
                            break

                    # If no canonical row with id==name exists, create one by copying fields
                    if canonical is None:
                        # Create new canonical registry entry with stable id == name
                        wr = WidgetRegistry(
                            id=sw["name"],
                            name=sw["name"],
                            type=sw.get("type"),
                            widget_metadata=sw.get("widget_metadata", {}),
                            default_config=sw.get("default_config", {}),
                            required_permissions=sw.get("required_permissions", []),
                            status=sw.get("status", "active"),
                            version=sw.get("version", "1.0"),
                            interaction_mode=sw.get("interaction_mode", "panel"),
                        )
                        s3.add(wr)
                        await s3.flush()
                        canonical = wr

                    # Ensure canonical has required fields set and preserve useful
                    # metadata from legacy duplicate rows before deprecating them.
                    updated = False
                    # Narrow type for static analysis: canonical should exist here
                    assert canonical is not None
                    c: WidgetRegistry = canonical
                    if getattr(c, "type", None) != sw.get("type") and sw.get("type"):
                        c.type = sw.get("type")
                        updated = True

                    canonical_metadata = getattr(c, "widget_metadata", {}) or {}
                    if isinstance(canonical_metadata, str):
                        try:
                            import json as _json

                            canonical_metadata = _json.loads(canonical_metadata)
                        except Exception:
                            canonical_metadata = {}
                    merged_metadata = dict(canonical_metadata)
                    for key, value in cast(Dict[str, Any], sw.get("widget_metadata") or {}).items():
                        merged_metadata.setdefault(key, value)

                    supported_node_types = set(merged_metadata.get("supported_node_types") or [])
                    for row in rows:
                        duplicate_metadata = getattr(row, "widget_metadata", {}) or {}
                        if isinstance(duplicate_metadata, str):
                            try:
                                import json as _json

                                duplicate_metadata = _json.loads(duplicate_metadata)
                            except Exception:
                                duplicate_metadata = {}
                        for key, value in duplicate_metadata.items():
                            if key != "supported_node_types":
                                merged_metadata.setdefault(key, value)
                        supported_node_types.update(duplicate_metadata.get("supported_node_types") or [])
                    if supported_node_types:
                        merged_metadata["supported_node_types"] = sorted(supported_node_types)

                    if merged_metadata != canonical_metadata:
                        c.widget_metadata = merged_metadata
                        updated = True
                    if not getattr(c, "default_config", None) and sw.get("default_config"):
                        c.default_config = cast(Dict[str, Any], sw.get("default_config") or {})
                        updated = True
                    if updated:
                        s3.add(c)
                        await s3.flush()

                    # Deprecate other rows after their metadata has been merged into
                    # the canonical entry, avoiding ambiguous active registry rows.
                    try:
                        canonical_id = getattr(canonical, "id", None)
                        for r in rows:
                            if getattr(r, "id", None) == canonical_id:
                                continue
                            try:
                                r.status = "deprecated"
                                s3.add(r)
                            except Exception:
                                logger.debug(
                                    "Failed to mark duplicate registry row %s as deprecated",
                                    getattr(r, "id", None),
                                )
                    except Exception:
                        logger.debug("Dev seed: error while evaluating duplicate deprecation", exc_info=True)
                    await s3.flush()
        logger.info("Development widget registry entries ensured")
    except Exception:
        logger.exception("Failed to ensure system widget registry entries; continuing")

    # Step 4: ensure node-level assignments (JSON legacy + relational rows)
    try:
        async with session_factory() as s4:
            async with s4.begin():
                repo = HierarchyRepository(s4)
                sys_node = await repo.get_node("system-root")
                if sys_node is not None:
                    assigns: List[Dict[str, Any]] = getattr(sys_node, "widget_assignments", None) or []
                    names = {str(a.get("id") or a.get("widget_id") or a.get("name")) for a in assigns if (a.get("id") or a.get("name") or a.get("widget_id"))}
                    additions: List[Dict[str, Any]] = []
                    for core_name in ("system_health", "audit_log", "registry_editor"):
                        if core_name not in names:
                            additions.append({
                                "id": core_name,
                                "name": core_name,
                                "component_type": core_name + "_widget",
                                "position": 10,
                                "configuration": {},
                                "enabled": True,
                                "inherit": False,
                            })
                    if additions:
                        sys_node.widget_assignments = assigns + additions
                        s4.add(sys_node)
                        await s4.flush()

                    # relational rows for additions
                    try:
                        for add in additions:
                            q = select(WidgetAssignment).where(
                                WidgetAssignment.node_id == sys_node.id,
                                (WidgetAssignment.widget_id == add.get("id")) | (WidgetAssignment.name == add.get("name")),
                            )
                            resw = await s4.execute(q)
                            exists_row = resw.scalar_one_or_none()
                            if exists_row is None:
                                wa = WidgetAssignment(
                                    node_id=sys_node.id,
                                    widget_id=add.get("id"),
                                    name=add.get("name"),
                                    enabled=add.get("enabled", True),
                                    inherit=add.get("inherit", False),
                                    position=add.get("position", 10),
                                    configuration=add.get("configuration", {}),
                                    required_permissions=add.get("required_permissions", []),
                                )
                                s4.add(wa)
                                await s4.flush()
                    except Exception as _exc:
                        if isinstance(_exc, InvalidRequestError):
                            raise
                        logger.debug("Relational widget_assignment insertion skipped or failed")

                # bootstrap-admin calendar assignment
                try:
                    admin_node = await repo.get_node("bootstrap-admin")
                    if admin_node is not None:
                        a_assigns: List[Dict[str, Any]] = getattr(admin_node, "widget_assignments", None) or []
                        a_names = {str(a.get("id") or a.get("name")) for a in a_assigns if (a.get("id") or a.get("name"))}
                        if "calendar" not in a_names:
                            ca: Dict[str, Any] = {
                                "id": "calendar",
                                "name": "calendar",
                                "component_type": "calendar_widget",
                                "position": 20,
                                "configuration": {"view": "month"},
                                "enabled": True,
                                "inherit": True,
                            }
                            admin_node.widget_assignments = a_assigns + [ca]
                            s4.add(admin_node)
                            await s4.flush()

                        q2 = select(WidgetAssignment).where(
                            WidgetAssignment.node_id == admin_node.id,
                            (WidgetAssignment.widget_id == "calendar") | (WidgetAssignment.name == "calendar"),
                        )
                        res2 = await s4.execute(q2)
                        exists_row2 = res2.scalar_one_or_none()
                        if exists_row2 is None:
                            wa2 = WidgetAssignment(
                                node_id=admin_node.id,
                                widget_id="calendar",
                                name="calendar",
                                enabled=True,
                                inherit=True,
                                position=20,
                                configuration={"view": "month"},
                                required_permissions=[],
                            )
                            s4.add(wa2)
                            await s4.flush()
                except Exception as _exc:
                    if isinstance(_exc, InvalidRequestError):
                        raise
                    logger.debug("Relational calendar assignment insertion skipped or failed")

                # Ensure standard system nodes and their default widget assignments
                try:
                    standard_nodes: Dict[str, Dict[str, Any]] = {
                        "system-root": {
                            "type": "system",
                            "parent": None,
                            "widgets": [
                                {"name": "system_health", "inherit": False, "position": 10},
                                {"name": "audit_log", "inherit": False, "position": 20},
                                {"name": "registry_editor", "inherit": False, "position": 30},
                            ],
                        },
                        "bootstrap-admin": {
                            "type": "user",
                            "parent": "system-root",
                            "widgets": [
                                {"name": "calendar", "inherit": True, "position": 10, "configuration": {"view": "month"}},
                                {"name": "files", "inherit": True, "position": 20},
                                {"name": "chat", "inherit": True, "position": 30},
                            ],
                        },
                        "workspaces-root": {
                            "type": "workspaces-root",
                            "parent": "system-root",
                            "widgets": [
                                {"name": "files", "inherit": False, "position": 10},
                            ],
                        },
                    }

                    for node_id, spec in standard_nodes.items():
                        spec: Dict[str, Any]
                        node = await repo.get_node(node_id)
                        if node is None:
                            await repo.create_node(
                                HierarchyNodeCreate(
                                    node_id=node_id,
                                    type=spec.get("type", "folder"),
                                    name=(node_id.replace("-", " ").title()),
                                    parent_id=spec.get("parent"),
                                    system_prompt=None,
                                    tool_policy={},
                                    config_overrides={},
                                    metadata={"system_managed": True},
                                )
                            )
                            node = await repo.get_node(node_id)

                        if node is not None:
                            existing: List[Dict[str, Any]] = getattr(node, "widget_assignments", None) or []
                            existing_names = {str(a.get("id") or a.get("name")) for a in existing}
                            additions: List[Dict[str, Any]] = []
                            for w in spec.get("widgets", []):
                                if w["name"] not in existing_names:
                                    additions.append(
                                        {
                                            "id": w["name"],
                                            "name": w["name"],
                                            "component_type": (w.get("component_type") or (w["name"] + "_widget")),
                                            "position": w.get("position", 100),
                                            "configuration": w.get("configuration", {}),
                                            "enabled": True,
                                            "inherit": w.get("inherit", False),
                                        }
                                    )
                            if additions:
                                node.widget_assignments = existing + additions
                                s4.add(node)
                                await s4.flush()

                            try:
                                for w in spec.get("widgets", []):
                                    q = select(WidgetAssignment).where(
                                        WidgetAssignment.node_id == node.id,
                                        (WidgetAssignment.widget_id == w["name"]) | (WidgetAssignment.name == w["name"]),
                                    )
                                    res = await s4.execute(q)
                                    exists_row = res.scalar_one_or_none()
                                    if exists_row is None:
                                        wa = WidgetAssignment(
                                            node_id=node.id,
                                            widget_id=w["name"],
                                            name=w["name"],
                                            enabled=True,
                                            inherit=w.get("inherit", False),
                                            position=w.get("position", 100),
                                            configuration=w.get("configuration", {}),
                                            required_permissions=[],
                                        )
                                        s4.add(wa)
                                        await s4.flush()
                            except Exception as _exc:
                                if isinstance(_exc, InvalidRequestError):
                                    raise
                                logger.debug("Relational widget_assignment insertion skipped or failed for %s", node_id)
                    logger.info("Development node widget assignments ensured")
                except Exception as _exc:
                    if isinstance(_exc, InvalidRequestError):
                        raise
                    logger.debug("Failed to ensure standard node widget assignments; continuing")
        logger.info("Development node widget assignments ensured")
    except Exception:
        logger.exception("Failed to ensure standard node widget assignments; continuing")

    # All done
    return
