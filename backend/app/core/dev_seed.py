from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contracts.hierarchy import HierarchyNodeCreate
from app.core.settings import settings
from app.database.models.user import UserModel
from app.database.models.user_role import RoleModel, UserRoleModel
from app.hierarchy.repository import HierarchyRepository
from app.storage.repositories.user import UserRepository
from app.auth.password_service import PasswordService

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

    async with session_factory() as session:
        # Run the minimal seed inside a single transaction for atomicity.
        async with session.begin():
            repo = HierarchyRepository(session)

            try:
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
                    # Repair protective attributes
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

                # Bootstrap administrator (neutral).
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
                    # Repair admin node attributes conservatively
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
                # session.begin() will rollback on exception
                logger.exception("Development hierarchy seed failed")
                raise

            # Idempotent creation of a development administrator user and role.
            try:
                # Only in development environment
                if settings.app_environment.name.lower() == "development":
                    user_repo = UserRepository(session)
                    pwd = PasswordService()

                    # Try find by configured id or username
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
                            # For development only: seed a reproducible password
                            # using the dedicated development password setting.
                            "password_hash": pwd.hash_password(
                                settings.development_admin_password
                            ),
                            "is_active": True,
                            "is_system_admin": True,
                            "is_system_user": True,
                        }
                        admin = await user_repo.create(user_data)
                    else:
                        # If an admin row exists, ensure it has the configured
                        # username/display_name and a development password hash
                        updated = False
                        # If existing username differs, attempt to rename if free
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

                        # Ensure system flags are set for the development admin
                        if not getattr(admin, "is_system_admin", False):
                            admin.is_system_admin = True
                            updated = True
                        if not getattr(admin, "is_system_user", False):
                            admin.is_system_user = True
                            updated = True

                        if updated:
                            await user_repo.update(admin, {})

                    # Ensure admin role exists
                    q = select(RoleModel).where(RoleModel.name == "admin")
                    result = await session.execute(q)
                    admin_role = result.scalar_one_or_none()
                    if admin_role is None:
                        admin_role = RoleModel(
                            name="admin",
                            display_name="Administrator",
                            is_system=True,
                            assignable=True,
                        )
                        session.add(admin_role)
                        await session.flush()

                    # Ensure user_roles mapping exists
                    # Check existing mapping
                    q2 = select(UserRoleModel).where(
                        UserRoleModel.user_id == admin.id,
                        UserRoleModel.role_id == admin_role.id,
                    )
                    res2 = await session.execute(q2)
                    mapping = res2.scalar_one_or_none()
                    if mapping is None:
                        ur = UserRoleModel(user_id=admin.id, role_id=admin_role.id)
                        session.add(ur)
                        await session.flush()

                    logger.info("Development admin user and role ensured (idempotent)")
                    # Ensure standard root nodes under system-root
                    users_root = await repo.get_node("users-root")
                    if users_root is None:
                        await repo.create_node(
                            HierarchyNodeCreate(
                                node_id="users-root",
                                type="folder",
                                name="Users",
                                parent_id="system-root",
                                system_prompt=None,
                                tool_policy={},
                                config_overrides={},
                                metadata={"system_managed": True},
                            )
                        )

                    workspaces_root = await repo.get_node("workspaces-root")
                    if workspaces_root is None:
                        await repo.create_node(
                            HierarchyNodeCreate(
                                node_id="workspaces-root",
                                type="folder",
                                name="Workspaces",
                                parent_id="system-root",
                                system_prompt=None,
                                tool_policy={},
                                config_overrides={},
                                metadata={"system_managed": True},
                            )
                        )

                    chats_root = await repo.get_node("chats-root")
                    if chats_root is None:
                        await repo.create_node(
                            HierarchyNodeCreate(
                                node_id="chats-root",
                                type="folder",
                                name="Chats",
                                parent_id="system-root",
                                system_prompt=None,
                                tool_policy={},
                                config_overrides={},
                                metadata={"system_managed": True},
                            )
                        )

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
                    res = await session.execute(stmt)
                    users = res.scalars().all()

                    # Collect existing user-linked entity_ids under users-root
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
            except Exception:
                logger.exception("Development admin seed failed")
                raise
