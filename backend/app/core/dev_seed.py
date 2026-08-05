from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.hierarchy.repository import HierarchyRepository
from app.contracts.hierarchy import HierarchyNodeCreate
from app.core.settings import settings
import logging
from sqlalchemy import select
from app.storage.repositories.user import UserRepository
from app.database.models.user import UserModel
from app.database.models.user_role import RoleModel, UserRoleModel

logger = logging.getLogger(__name__)


async def seed_development_hierarchy(session_factory: async_sessionmaker[AsyncSession]) -> None:
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

                    # Try find by configured id or username
                    admin: UserModel | None = await user_repo.get_by_id(settings.development_admin_user_id)
                    if admin is None:
                        admin = await user_repo.get_by_username(settings.development_admin_username)

                    if admin is None:
                        user_data: dict[str, object | None] = {
                            "id": settings.development_admin_user_id,
                            "username": settings.development_admin_username,
                            "display_name": settings.development_admin_display_name,
                            "email": None,
                            "password_hash": None,
                            "is_active": True,
                            "is_system_admin": True,
                        }
                        admin = await user_repo.create(user_data)

                    # Ensure admin role exists
                    q = select(RoleModel).where(RoleModel.name == "admin")
                    result = await session.execute(q)
                    admin_role = result.scalar_one_or_none()
                    if admin_role is None:
                        admin_role = RoleModel(name="admin", display_name="Administrator")
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
            except Exception:
                logger.exception("Development admin seed failed")
                raise
