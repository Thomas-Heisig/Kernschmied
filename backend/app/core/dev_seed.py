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
        # Run the entire seed inside a single transaction for atomicity.
        async with session.begin():
            repo = HierarchyRepository(session)

            try:
                # root
                root = await repo.get_node("root")
                if root is None:
                    await repo.create_node(
                        HierarchyNodeCreate(
                            node_id="root",
                            type="user",
                            name="Thomas Heisig",
                            parent_id=None,
                            system_prompt=None,
                            tool_policy={},
                            config_overrides={},
                            metadata={},
                        )
                    )
                else:
                    # repair existing node attributes to canonical values
                    if root.type != "user":
                        root.type = "user"
                    if root.name != "Thomas Heisig":
                        root.name = "Thomas Heisig"
                    # ensure parent is system-root
                    if root.parent_id is not None:
                        await repo.move_node(root, new_parent_id=None)

                # workspace-1
                ws = await repo.get_node("workspace-1")
                if ws is None:
                    await repo.create_node(
                        HierarchyNodeCreate(
                            node_id="workspace-1",
                            type="workspace",
                            name="Heisig Naturstein",
                            parent_id="root",
                            system_prompt=None,
                            tool_policy={},
                            config_overrides={},
                            metadata={},
                        )
                    )
                else:
                    if ws.type != "workspace":
                        ws.type = "workspace"
                    if ws.name != "Heisig Naturstein":
                        ws.name = "Heisig Naturstein"
                    if ws.parent_id != "root":
                        await repo.move_node(ws, new_parent_id="root")

                # project-1
                proj = await repo.get_node("project-1")
                if proj is None:
                    await repo.create_node(
                        HierarchyNodeCreate(
                            node_id="project-1",
                            type="project",
                            name="Angebote",
                            parent_id="workspace-1",
                            system_prompt=None,
                            tool_policy={},
                            config_overrides={},
                            metadata={},
                        )
                    )
                else:
                    if proj.type != "project":
                        proj.type = "project"
                    if proj.name != "Angebote":
                        proj.name = "Angebote"
                    if proj.parent_id != "workspace-1":
                        await repo.move_node(proj, new_parent_id="workspace-1")

                # chat-1
                chat = await repo.get_node("chat-1")
                if chat is None:
                    await repo.create_node(
                        HierarchyNodeCreate(
                            node_id="chat-1",
                            type="chat",
                            name="Angebot Müller",
                            parent_id="project-1",
                            system_prompt=None,
                            tool_policy={},
                            config_overrides={},
                            metadata={},
                        )
                    )
                else:
                    if chat.type != "chat":
                        chat.type = "chat"
                    if chat.name != "Angebot Müller":
                        chat.name = "Angebot Müller"
                    if chat.parent_id != "project-1":
                        await repo.move_node(chat, new_parent_id="project-1")

                logger.info("Development hierarchy seed applied (idempotent)")
            except Exception:
                # session.begin() will rollback on exception
                logger.exception("Development hierarchy seed failed")
                raise
