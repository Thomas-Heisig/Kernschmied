from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.hierarchy.repository import HierarchyRepository
from app.contracts.hierarchy import HierarchyNodeCreate
from app.core.settings import settings
import logging

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
                admin = await repo.get_node("bootstrap-admin")
                if admin is None:
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
                    if admin.type != "user":
                        admin.type = "user"
                        repaired = True
                    if admin.name != "Administrator":
                        admin.name = "Administrator"
                        repaired = True
                    if admin.parent_id != "system-root":
                        await repo.move_node(admin, new_parent_id="system-root")

                    if repaired:
                        await repo._session.flush()  # type: ignore[attr-defined]

                logger.info("Development minimal hierarchy seed applied (idempotent)")
            except Exception:
                # session.begin() will rollback on exception
                logger.exception("Development hierarchy seed failed")
                raise
