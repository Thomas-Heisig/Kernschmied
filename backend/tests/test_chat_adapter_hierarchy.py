import asyncio
import os
import tempfile
from typing import Any

from app.database.models.hierarchy_node import HierarchyNodeModel
from app.services.chat_service import (
    ChatHierarchyNodeNotFoundError,
    ChatHierarchyNodeRequiredError,
)
from app.storage.adapters.chat_repository_adapter import ChatRepositoryAdapter
from app.storage.models.base import Base as StorageBase
from app.storage.models.chat import Chat as ChatModel
from app.storage.models.chat import Message as MessageModel
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def test_chat_adapter_hierarchy_behaviour() -> None:
    async def _run() -> None:
        fd, db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        engine: AsyncEngine | None = None
        try:
            url = f"sqlite+aiosqlite:///{db_path}"
            engine = create_async_engine(url, echo=False)

            # enable foreign keys for SQLite
            @event.listens_for(engine.sync_engine, "connect")
            def _enable_fk(dbapi_connection: Any, connection_record: Any) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

            async with engine.begin() as conn:
                await conn.run_sync(StorageBase.metadata.create_all)

            session_factory = async_sessionmaker[AsyncSession](
                engine,
                expire_on_commit=False,
            )

            adapter = ChatRepositoryAdapter(session_factory)

            # 1) Missing hierarchy_node_id -> ChatHierarchyNodeRequiredError
            try:
                await adapter.create_conversation(
                    conversation_id="conv-missing",
                    user_id=None,
                    tenant_id=None,
                    model_id="m",
                    metadata=None,
                )
                raise AssertionError("Expected ChatHierarchyNodeRequiredError")
            except ChatHierarchyNodeRequiredError:
                pass

            # 2) Provided unknown hierarchy_node_id -> ChatHierarchyNodeNotFoundError
            try:
                await adapter.create_conversation(
                    conversation_id="conv-unknown",
                    user_id=None,
                    tenant_id=None,
                    model_id="m",
                    metadata=None,
                    hierarchy_node_id="does-not-exist",
                )
                raise AssertionError("Expected ChatHierarchyNodeNotFoundError")
            except ChatHierarchyNodeNotFoundError:
                pass

            # 3) Provided existing hierarchy_node -> chat created and no extra hierarchy node created
            async with session_factory() as session:
                node = HierarchyNodeModel(
                    id="node-1",
                    parent_id=None,
                    type="chat",
                    name="Node 1",
                )
                session.add(node)
                await session.flush()
                await session.commit()

            await adapter.create_conversation(
                conversation_id="conv-ok",
                user_id=None,
                tenant_id=None,
                model_id="m",
                metadata=None,
                hierarchy_node_id="node-1",
            )

            # verify chat exists and references node-1
            async with session_factory() as session:
                q = select(ChatModel).where(ChatModel.id == "conv-ok")
                res = (await session.execute(q)).scalars().first()
                assert res is not None and res.node_id == "node-1"

                # ensure no hierarchy node named 'Conversation conv-ok' exists
                q2 = select(HierarchyNodeModel).where(
                    HierarchyNodeModel.name.like("Conversation conv-ok%")
                )
                res2 = (await session.execute(q2)).scalars().all()
                assert len(res2) == 0

            await adapter.append_user_message(
                conversation_id="conv-ok",
                message_id="message-user",
                parent_message_id=None,
                content="Hallo",
                metadata={},
                hierarchy_node_id="node-1",
            )
            await adapter.append_assistant_message(
                conversation_id="conv-ok",
                message_id="message-assistant",
                parent_message_id="message-user",
                model_id="m",
                content="Antwort",
                finish_reason="stop",
                usage=None,
                metadata={},
            )

            async with session_factory() as session:
                messages = (
                    await session.scalars(
                        select(MessageModel).where(
                            MessageModel.conversation_id == "conv-ok"
                        )
                    )
                ).all()
                assert {message.status for message in messages} == {"complete"}

        finally:
            if engine is not None:
                import contextlib

                with contextlib.suppress(Exception):
                    await engine.dispose()

            try:
                os.remove(db_path)
            except Exception:
                pass

    asyncio.run(_run())
