import os
from pathlib import Path

import pytest
from app.contracts.hierarchy import HierarchyNodeCreate
from app.core.settings import reload_settings
from app.hierarchy.inheritance import HierarchyInheritanceService
from app.hierarchy.models import HierarchyActor
from app.hierarchy.permissions import HierarchyPermissionService
from app.hierarchy.repository import HierarchyRepository
from app.hierarchy.serializer import HierarchySerializer
from app.hierarchy.service import HierarchyChildTypeNotAllowedError, HierarchyService
from app.storage import database as _database_module
from app.storage.database import init_database
from app.storage.models.chat import Chat
from sqlalchemy import select


async def _create_base_hierarchy(repo: HierarchyRepository) -> None:
    # create minimal system/user/workspace chain
    await repo.create_node(
        HierarchyNodeCreate(
            node_id="system-root",
            type="system",
            name="System",
            parent_id=None,
            tool_policy={},
            config_overrides={},
            metadata={},
        )
    )
    await repo.create_node(
        HierarchyNodeCreate(
            node_id="user-a",
            type="user",
            name="User A",
            parent_id="system-root",
            tool_policy={},
            config_overrides={},
            metadata={},
        )
    )
    await repo.create_node(
        HierarchyNodeCreate(
            node_id="workspace-a",
            type="workspace",
            name="Workspace A",
            parent_id="user-a",
            tool_policy={},
            config_overrides={},
            metadata={},
        )
    )


def _admin_actor() -> HierarchyActor:
    return HierarchyActor(
        user_id="admin",
        roles=frozenset({"admin"}),
        permissions=frozenset({"hierarchy.read", "hierarchy.create_child"}),
    )


@pytest.fixture()
async def session_factory(tmp_path: Path):
    # Use a fresh sqlite file for isolation
    db_file = tmp_path / "kernschmied_test_chat_hierarchy.db"
    os.environ["DATABASE_MIGRATION_MODE"] = "disabled"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    new_settings = reload_settings()
    _database_module.settings = new_settings
    _database_module._database_manager = _database_module.DatabaseManager(
        new_settings.effective_database_url
    )

    sf = await init_database(create_schema=True, echo=False)
    return sf


@pytest.mark.asyncio
async def test_workspace_allows_chat(session_factory):
    async with session_factory() as session:
        repo = HierarchyRepository(session)
        await _create_base_hierarchy(repo)

        # create chat under workspace
        chat = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Chat W",
                parent_id="workspace-a",
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        await session.commit()

        node = await repo.get_node(chat.id)
        assert node is not None
        assert node.node_metadata.get("entity_type") == "conversation"
        assert node.node_metadata.get("entity_id") is not None

        # verify chat record exists
        q = select(Chat).where(Chat.node_id == node.id)
        res = await session.execute(q)
        chat_row = res.scalar_one_or_none()
        assert chat_row is not None


@pytest.mark.asyncio
async def test_chat_allows_child_chat(session_factory):
    async with session_factory() as session:
        repo = HierarchyRepository(session)
        await _create_base_hierarchy(repo)

        parent = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Parent Chat",
                parent_id="workspace-a",
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        child = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Child Chat",
                parent_id=parent.id,
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        await session.commit()

        pnode = await repo.get_node(parent.id)
        cnode = await repo.get_node(child.id)
        assert pnode is not None and cnode is not None
        p_entity = pnode.node_metadata.get("entity_id")
        c_entity = cnode.node_metadata.get("entity_id")
        assert p_entity != c_entity


@pytest.mark.asyncio
async def test_chat_allows_folder_child(session_factory):
    async with session_factory() as session:
        repo = HierarchyRepository(session)
        await _create_base_hierarchy(repo)

        parent = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Parent Chat",
                parent_id="workspace-a",
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        folder = await repo.create_node(
            HierarchyNodeCreate(
                type="folder",
                name="Folder",
                parent_id=parent.id,
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        await session.commit()

        assert (await repo.get_node(folder.id)) is not None


@pytest.mark.asyncio
async def test_chat_rejects_user_child_via_service(session_factory):
    async with session_factory() as session:
        repo = HierarchyRepository(session)
        await _create_base_hierarchy(repo)

        parent = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Parent Chat",
                parent_id="workspace-a",
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        await session.commit()

        perm = HierarchyPermissionService()
        inherit = HierarchyInheritanceService()
        serializer = HierarchySerializer(
            permission_service=perm,
            inheritance_service=inherit,
        )
        service = HierarchyService(
            repository=repo,
            permission_service=perm,
            serializer=serializer,
        )

        with pytest.raises(HierarchyChildTypeNotAllowedError):
            await service.create_node(
                HierarchyNodeCreate(
                    type="user",
                    name="Bad",
                    parent_id=parent.id,
                    tool_policy={},
                    config_overrides={},
                    metadata={},
                ),
                actor=_admin_actor(),
            )


@pytest.mark.asyncio
async def test_child_chat_inherits_prompt(session_factory):
    async with session_factory() as session:
        repo = HierarchyRepository(session)
        await _create_base_hierarchy(repo)

        parent = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Parent Chat",
                parent_id="workspace-a",
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        # set a system_prompt on parent
        parent.system_prompt = "Du bist Experte für Restaurierung."
        await session.flush()

        child = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Child Chat",
                parent_id=parent.id,
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        await session.commit()

        perm = HierarchyPermissionService()
        inherit = HierarchyInheritanceService()
        serializer = HierarchySerializer(
            permission_service=perm,
            inheritance_service=inherit,
        )
        service = HierarchyService(
            repository=repo,
            permission_service=perm,
            serializer=serializer,
        )

        vals = await service.resolve_effective_values(child.id, actor=_admin_actor())
        assert "Restaurierung" in (vals.get("prompt") or "")


@pytest.mark.asyncio
async def test_child_chat_adds_own_prompt(session_factory):
    async with session_factory() as session:
        repo = HierarchyRepository(session)
        await _create_base_hierarchy(repo)

        parent = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Parent Chat",
                parent_id="workspace-a",
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        parent.system_prompt = "Du bist Experte für Restaurierung."
        await session.flush()

        child = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Child Chat",
                parent_id=parent.id,
                system_prompt="Konzentriere dich auf Sandstein.",
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        await session.commit()

        perm = HierarchyPermissionService()
        inherit = HierarchyInheritanceService()
        serializer = HierarchySerializer(
            permission_service=perm,
            inheritance_service=inherit,
        )
        service = HierarchyService(
            repository=repo,
            permission_service=perm,
            serializer=serializer,
        )

        vals = await service.resolve_effective_values(child.id, actor=_admin_actor())
        prompt = vals.get("prompt") or ""
        assert "Restaurierung" in prompt
        assert "Sandstein" in prompt


@pytest.mark.asyncio
async def test_persistence_of_chats_across_sessions(session_factory):
    async with session_factory() as session:
        repo = HierarchyRepository(session)
        await _create_base_hierarchy(repo)

        chat_a = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Chat A",
                parent_id="workspace-a",
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        child = await repo.create_node(
            HierarchyNodeCreate(
                type="chat",
                name="Chat A.1",
                parent_id=chat_a.id,
                tool_policy={},
                config_overrides={},
                metadata={},
            )
        )
        await session.commit()

    # new session to verify persistence
    async with session_factory() as session:
        repo = HierarchyRepository(session)
        assert (await repo.get_node(chat_a.id)) is not None
        assert (await repo.get_node(child.id)) is not None