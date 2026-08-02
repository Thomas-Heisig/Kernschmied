# pyright: reportPrivateUsage=false
import asyncio
import os
from pathlib import Path
from typing import Any, cast

import pytest
from app.core.settings import reload_settings
from app.storage import database as _database_module
from app.storage.database import init_database
from app.storage.models.chat import Chat, Message
from app.storage.models.hierarchy import HierarchyNode
from app.storage.repositories.chat import ChatRepository, InvalidMessageStatusTransition
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite+aiosqlite:///F:/Kernschmied/backend/data/chat.clean-fresh-test.db",
)


@pytest.fixture(scope="module")
async def session_factory() -> async_sessionmaker[AsyncSession]:
    # Prevent init_database from attempting to run Alembic here — we created
    # the fresh test DB via a separate alembic run. Disable automatic upgrades
    # for the test run so metadata.create_all does not override migration state.
    os.environ["DATABASE_MIGRATION_MODE"] = "disabled"
    # Point the test process at the fresh test DB and reload settings so the
    # DatabaseManager will use the correct resolved URL.
    backend_dir = Path(__file__).resolve().parents[1]
    test_db = backend_dir / "data" / "chat.clean-fresh-test.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_db.as_posix()}"

    new_settings = reload_settings()
    _database_module.settings = new_settings

    # Replace the module-level DatabaseManager so it uses the new URL.
    _database_module._database_manager = _database_module.DatabaseManager(
        new_settings.effective_database_url
    )

    sf = await init_database(create_schema=False, echo=False)
    return sf


@pytest.mark.asyncio
async def test_basic_sequence_and_order(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        # Ensure foreign keys are enabled on connection
        await session.execute(text("PRAGMA foreign_keys = ON;"))
        r = await session.execute(text("PRAGMA foreign_keys;"))
        assert int(r.scalar_one()) == 1

        # create hierarchy node via ORM
        node = HierarchyNode(
            node_type="conversation_root",
            name="root",
            prompt=None,
            position=0,
            config={},
            is_active=True,
        )
        session.add(node)
        await session.flush()
        await session.refresh(node)
        await session.commit()

    # create chat and messages in a new session
    async with session_factory() as session:
        repo = ChatRepository(session)
        # create chat without next_message_sequence explicitly
        chat = Chat(node_id=node.id, title="T1")
        created = await repo.add_chat(chat)
        # after flush/refresh, default should be applied
        assert created.next_message_sequence == 0

        # add first message
        msg = Message(conversation_id=created.id, role="user", content="hello")
        stored = await repo.add_message(msg)
        assert stored.sequence_number == 0
        # refresh chat to see updated counter
        await session.refresh(created)
        assert created.next_message_sequence == 1

        # add second message
        msg2 = Message(conversation_id=created.id, role="assistant", content="ok")
        stored2 = await repo.add_message(msg2)
        assert stored2.sequence_number == 1
        await session.refresh(created)
        assert created.next_message_sequence == 2

        # list messages and verify order
        rows = await repo.list_messages(created.id)
        seqs = [m.sequence_number for m in rows]
        assert seqs == [0, 1]
        await session.commit()


@pytest.mark.asyncio
async def test_parallel_inserts(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        # get chat id from DB
        chat: Any = await session.scalar(text("SELECT id FROM chats LIMIT 1"))
        assert chat is not None
        conversation_id: str = cast(str, chat[0] if isinstance(chat, tuple) else chat)

    async def worker(i: int) -> int:
        async with session_factory() as s:
            repo = ChatRepository(s)
            m = Message(conversation_id=conversation_id, role="user", content=f"msg-{i}")
            async with s.begin():
                stored = await repo.add_message(m)
            return stored.sequence_number

    tasks = [asyncio.create_task(worker(i)) for i in range(20)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 20
    assert sorted(results) == list(range(min(results), min(results) + 20))

    # verify next_message_sequence advanced
    async with session_factory() as s2:
        r = await s2.execute(text("SELECT next_message_sequence FROM chats LIMIT 1"))
        next_seq = r.scalar_one()
        assert next_seq >= 20


@pytest.mark.asyncio
async def test_transaction_boundary(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        # prepare chat
        chat: Any = await session.scalar(text("SELECT id FROM chats LIMIT 1"))
        conversation_id: str = cast(str, chat if not isinstance(chat, tuple) else chat[0])

        # create a new message but do not commit outer change
        async def run_test() -> None:
            # mark commit/rollback calls
            orig_commit = session.commit
            orig_rollback = session.rollback
            called = {"commit": False, "rollback": False}

            async def commit_spy() -> None:
                called["commit"] = True
                return await orig_commit()

            async def rollback_spy() -> None:
                called["rollback"] = True
                return await orig_rollback()

            session.commit = commit_spy  # type: ignore[assignment]
            session.rollback = rollback_spy  # type: ignore[assignment]

            # create an unrelated in-memory change via ORM
            node = HierarchyNode(
                node_type="tmp",
                name="tmp",
                prompt=None,
                position=0,
                config={},
                is_active=True,
            )
            session.add(node)
            await session.flush()

            repo = ChatRepository(session)
            m = Message(conversation_id=conversation_id, role="user", content="tx-test")
            _ = await repo.add_message(m)  # unused, but needed to test transaction boundary

            # repository must not have committed or rolled back
            assert called["commit"] is False
            assert called["rollback"] is False

            # now commit explicitly
            await session.commit()
            assert called["commit"] is True

        await run_test()


@pytest.mark.asyncio
async def test_status_transitions(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        # create a fresh message
        chat: Any = await session.scalar(text("SELECT id FROM chats LIMIT 1"))
        conversation_id: str = cast(str, chat if not isinstance(chat, tuple) else chat[0])
        repo = ChatRepository(session)
        m = Message(conversation_id=conversation_id, role="user", content="status-test")
        stored = await repo.add_message(m)

        # pending -> complete
        await repo.mark_message_complete(stored.id)
        msg = await repo.get_message(stored.id)
        assert msg is not None
        assert msg.status == "complete"
        assert msg.completed_at is not None

        # create another and test failed and cancelled transitions
        m2 = Message(conversation_id=conversation_id, role="user", content="status-test2")
        s2 = await repo.add_message(m2)
        await repo.mark_message_failed(s2.id, metadata={"code": "E"})  # type: ignore[arg-type]
        msg2 = await repo.get_message(s2.id)
        assert msg2 is not None
        assert msg2.status == "failed"

        m3 = Message(conversation_id=conversation_id, role="user", content="status-test3")
        s3 = await repo.add_message(m3)
        await repo.mark_message_cancelled(s3.id)
        msg3 = await repo.get_message(s3.id)
        assert msg3 is not None
        assert msg3.status == "cancelled"

        # invalid transitions should raise
        with pytest.raises(InvalidMessageStatusTransition):
            await repo.mark_message_complete(s2.id)
        with pytest.raises(InvalidMessageStatusTransition):
            await repo.mark_message_failed(stored.id)  # type: ignore[arg-type]