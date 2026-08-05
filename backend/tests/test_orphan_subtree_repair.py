import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.engine import Result

import pytest
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import reload_settings
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.maintenance.orphan_hierarchy_repair import (
    apply_orphan_repair,
    build_orphan_repair_plan,
)
from app.storage.database import init_database
from app.storage.models.chat import Chat as ChatModel
from app.storage.models.chat import Message as MessageModel


@pytest.fixture()
async def session_factory(tmp_path: Path, monkeypatch: MonkeyPatch) -> async_sessionmaker[AsyncSession]:
    # Use a temporary sqlite file for isolation
    db_file = tmp_path / "test.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    reload_settings()
    sf = await init_database(create_schema=True)
    return sf  # type: ignore


def test_build_plan_blocks_on_children(session_factory: async_sessionmaker[AsyncSession]):
    async def _run():
        async with session_factory() as s:  # type: ignore
            # create target parent and target chat
            root = HierarchyNodeModel(id="root", type="user", name="Root")
            chat_node = HierarchyNodeModel(id="chat-1", type="chat", name="Chat 1")
            await s.merge(root)  # type: ignore
            await s.merge(chat_node)  # type: ignore
            # orphan with a child
            orphan = HierarchyNodeModel(id="orphan-1", type="chat", name="Conversation conversation_x")
            child = HierarchyNodeModel(id="child-1", type="folder", name="Public", parent_id="orphan-1")
            await s.merge(orphan)  # type: ignore
            await s.merge(child)  # type: ignore
            await s.commit()  # type: ignore

            plan = await build_orphan_repair_plan(s, orphan_node_id="orphan-1", target_parent_id="root", target_chat_node_id="chat-1")  # type: ignore
            assert plan.can_apply is False
            assert "orphan_has_children" in plan.blockers

    asyncio.run(_run())


def test_plan_rejects_non_chat_orphan(session_factory: async_sessionmaker[AsyncSession]):
    async def _run():
        async with session_factory() as s:  # type: ignore
            user = HierarchyNodeModel(id="root", type="user", name="Root")
            await s.merge(user)  # type: ignore
            non_chat = HierarchyNodeModel(id="n1", type="project", name="Project X")
            await s.merge(non_chat)  # type: ignore
            chat_node = HierarchyNodeModel(id="chat-1", type="chat", name="Chat 1")
            await s.merge(chat_node)  # type: ignore
            await s.commit()  # type: ignore

            plan = await build_orphan_repair_plan(s, orphan_node_id="n1", target_parent_id="root", target_chat_node_id="chat-1")  # type: ignore
            assert plan.can_apply is False
            assert "orphan_not_chat_type" in plan.blockers

    asyncio.run(_run())


def test_plan_rejects_non_root_orphan(session_factory: async_sessionmaker[AsyncSession]):
    async def _run():
        async with session_factory() as s:  # type: ignore
            root = HierarchyNodeModel(id="root", type="user", name="Root")
            child_parent = HierarchyNodeModel(id="p1", type="workspace", name="WS", parent_id="root")
            await s.merge(root)  # type: ignore
            await s.merge(child_parent)  # type: ignore
            orphan = HierarchyNodeModel(id="orphan-2", type="chat", name="Conversation conversation_y", parent_id="p1")
            chat_node = HierarchyNodeModel(id="chat-1", type="chat", name="Chat 1")
            await s.merge(orphan)  # type: ignore
            await s.merge(chat_node)  # type: ignore
            await s.commit()  # type: ignore

            plan = await build_orphan_repair_plan(s, orphan_node_id="orphan-2", target_parent_id="root", target_chat_node_id="chat-1")  # type: ignore
            assert plan.can_apply is False
            assert "orphan_not_root" in plan.blockers

    asyncio.run(_run())


def test_plan_rejects_missing_target_parent(session_factory: async_sessionmaker[AsyncSession]):
    async def _run():
        async with session_factory() as s:  # type: ignore
            orphan = HierarchyNodeModel(id="o3", type="chat", name="Conversation conversation_z")
            chat_node = HierarchyNodeModel(id="chat-1", type="chat", name="Chat 1")
            await s.merge(orphan)  # type: ignore
            await s.merge(chat_node)  # type: ignore
            await s.commit()  # type: ignore

            plan = await build_orphan_repair_plan(s, orphan_node_id="o3", target_parent_id="missing", target_chat_node_id="chat-1")  # type: ignore
            assert plan.can_apply is False
            assert "target_parent_not_found" in plan.blockers

    asyncio.run(_run())


def test_plan_rejects_invalid_target_chat(session_factory: async_sessionmaker[AsyncSession]):
    async def _run():
        async with session_factory() as s:  # type: ignore
            orphan = HierarchyNodeModel(id="o4", type="chat", name="Conversation conversation_a")
            await s.merge(orphan)  # type: ignore
            parent = HierarchyNodeModel(id="root", type="user", name="Root")
            non_chat = HierarchyNodeModel(id="notchat", type="workspace", name="WS")
            await s.merge(parent)  # type: ignore
            await s.merge(non_chat)  # type: ignore
            await s.commit()  # type: ignore

            plan = await build_orphan_repair_plan(s, orphan_node_id="o4", target_parent_id="root", target_chat_node_id="notchat")  # type: ignore
            assert plan.can_apply is False
            assert "target_chat_not_type_chat" in plan.blockers or "target_chat_not_found" in plan.blockers

    asyncio.run(_run())


def test_detects_cycle(session_factory: async_sessionmaker[AsyncSession]):
    async def _run():
        async with session_factory() as s:  # type: ignore
            # orphan -> a -> b ; target parent = b (descendant)
            orphan = HierarchyNodeModel(id="orp-c", type="chat", name="Conversation conversation_c")
            a = HierarchyNodeModel(id="a", type="folder", name="A", parent_id="orp-c")
            b = HierarchyNodeModel(id="b", type="folder", name="B", parent_id="a")
            target_chat = HierarchyNodeModel(id="chat-1", type="chat", name="Chat 1")
            await s.merge(orphan)  # type: ignore
            await s.merge(a)  # type: ignore
            await s.merge(b)  # type: ignore
            await s.merge(target_chat)  # type: ignore
            await s.commit()  # type: ignore

            plan = await build_orphan_repair_plan(s, orphan_node_id="orp-c", target_parent_id="b", target_chat_node_id="chat-1")  # type: ignore
            assert plan.can_apply is False
            assert "target_parent_is_descendant" in plan.blockers

    asyncio.run(_run())


def test_apply_reassigns_chats_and_deletes_orphan(session_factory: async_sessionmaker[AsyncSession]):
    async def _run():
        async with session_factory() as s:  # type: ignore
            # setup: root, target_chat, orphan (no children), chat referencing orphan, message
            root = HierarchyNodeModel(id="root", type="user", name="Root")
            target_chat = HierarchyNodeModel(id="chat-1", type="chat", name="Chat Target")
            orphan = HierarchyNodeModel(id="orp-d", type="chat", name="Conversation conversation_d")
            await s.merge(root)  # type: ignore
            await s.merge(target_chat)  # type: ignore
            await s.merge(orphan)  # type: ignore
            await s.commit()  # type: ignore

            # create chat record and message (updated to current Chat model fields)
            chat = ChatModel(id="conv-d", node_id="orp-d", title="Conversation conversation_d")
            msg = MessageModel(id="m1", conversation_id="conv-d", sequence_number=1, role="user", content="hi", message_type="text", status="ok")  # type: ignore[arg-type]
            await s.merge(chat)  # type: ignore
            await s.merge(msg)  # type: ignore
            await s.commit()  # type: ignore

            plan = await build_orphan_repair_plan(s, orphan_node_id="orp-d", target_parent_id="root", target_chat_node_id="chat-1")  # type: ignore
            assert plan.can_apply is True

            # apply using a nested transaction so this works even if a transaction
            # was started during plan building.
            async with s.begin_nested():  # type: ignore
                await apply_orphan_repair(s, plan=plan)  # type: ignore

            # assert chat reassigned and orphan deleted
            c = await s.get(ChatModel, "conv-d")  # type: ignore
            assert c is not None
            node_id = c.node_id
            assert node_id == "chat-1"

            orphan_after = await s.get(HierarchyNodeModel, "orp-d")  # type: ignore
            assert orphan_after is None

            # messages preserved
            from sqlalchemy import func, select

            mq: Result[tuple[int]] = await s.execute(select(func.count()).select_from(MessageModel).where(MessageModel.conversation_id == "conv-d"))
            cnt = mq.scalar_one()  # type: ignore
            assert int(cnt) == 1

    asyncio.run(_run())
    