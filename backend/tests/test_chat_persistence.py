import asyncio
import os
import tempfile
from typing import Any

from app.storage.models.base import Base
from app.storage.models.chat import Chat, Message
from app.storage.repositories.chat import ChatRepository
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def test_append_and_list_messages() -> None:
    async def _run() -> None:
        # use a temporary file-backed sqlite DB so multiple connections share state
        db_file = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        try:
            url = f"sqlite+aiosqlite:///{db_file.name}"
            engine = create_async_engine(url, echo=False)

            # enable foreign keys for SQLite
            @event.listens_for(engine.sync_engine, "connect")
            def _enable_fk(dbapi_connection: Any, connection_record: Any) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            session_factory = async_sessionmaker(engine, expire_on_commit=False)

            async with session_factory() as session:
                repo = ChatRepository(session)

                # create a hierarchy node first (foreign key)
                from app.storage.models.hierarchy import HierarchyNode

                node = HierarchyNode(id="node-1", node_type="chat", name="Node 1", config={})
                session.add(node)
                await session.flush()
                await session.commit()

                # create a chat
                chat = Chat(id="conv-1", node_id="node-1", title="Conv 1", config={})
                await repo.add_chat(chat)
                await session.commit()

            # append messages concurrently using separate sessions to simulate contention
            async def append_message(msg_id: str, role: str, content: str) -> Message:
                async with session_factory() as session:
                    repo = ChatRepository(session)
                    msg = Message(
                        id=msg_id,
                        conversation_id="conv-1",
                        user_id=None,
                        role=role,
                        content=content,
                        ui_context={}
                    )
                    await repo.add_message(msg)
                    await session.commit()
                    return msg

            _results = await asyncio.gather(
                *[append_message(f"m{i}", "user" if i % 2 == 0 else "assistant", f"msg{i}") for i in range(6)]
            )

            async with session_factory() as session:
                repo = ChatRepository(session)
                msgs = await repo.list_messages("conv-1")
                assert len(msgs) == 6
                seqs = [m.sequence_number for m in msgs]
                # sequence numbers must be unique and 0..5
                assert sorted(seqs) == list(range(6))

                # test get_message and status transitions
                some_id = msgs[2].id
                await repo.mark_message_complete(some_id)
                m = await repo.get_message(some_id)
                assert m is not None and m.status == "complete"

                # fail a message – type ignore due to partial unknown in repository signature
                await repo.mark_message_failed(msgs[3].id, metadata={"code": "E_TEST", "message": "fail"})  # type: ignore[arg-type]
                m3 = await repo.get_message(msgs[3].id)
                assert m3 is not None and m3.status == "failed"
        finally:
            try:
                db_file.close()
                os.unlink(db_file.name)
            except Exception:
                pass

    asyncio.run(_run())