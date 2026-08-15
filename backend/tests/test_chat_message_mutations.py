from collections.abc import AsyncIterator

import httpx
import pytest
from app.api.v1 import chats as chats_api
from app.auth.dependencies import require_authenticated_user
from app.auth.models import UserContext
from app.storage.database import get_session
from app.storage.database import DatabaseManager
from app.storage.models.chat import Chat, Message
from app.storage.models.hierarchy import HierarchyNode
from app.storage.repositories.chat import ChatRepository
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi import FastAPI, Request


@pytest.fixture
async def session_factory(
    tmp_path,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    manager = DatabaseManager(f"sqlite+aiosqlite:///{(tmp_path / 'chat-mutations.db').as_posix()}")
    factory = await manager.initialize(create_schema=True)
    yield factory
    await manager.dispose()


async def create_conversation(
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[str, tuple[str, str, str]]:
    async with session_factory() as session:
        node = HierarchyNode(
            node_type="chat",
            name="Mutation test",
            prompt=None,
            position=0,
            config={},
            is_active=True,
        )
        session.add(node)
        await session.flush()

        repository = ChatRepository(session)
        chat = await repository.add_chat(Chat(node_id=node.id, title="Mutation test"))
        first = await repository.add_message(
            Message(conversation_id=chat.id, role="user", content="first")
        )
        second = await repository.add_message(
            Message(
                conversation_id=chat.id,
                role="assistant",
                content="second",
                parent_message_id=first.id,
            )
        )
        third = await repository.add_message(
            Message(
                conversation_id=chat.id,
                role="user",
                content="third",
                parent_message_id=second.id,
            )
        )
        await session.commit()
        return chat.id, (first.id, second.id, third.id)


@pytest.mark.asyncio
async def test_delete_message_keeps_replies_and_sequence_monotonic(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id, (first_id, second_id, third_id) = await create_conversation(
        session_factory
    )

    async with session_factory() as session:
        repository = ChatRepository(session)
        assert await repository.delete_message(conversation_id, second_id) is True
        await session.commit()

        remaining = list(await repository.list_messages(conversation_id))
        assert [message.id for message in remaining] == [first_id, third_id]
        assert remaining[1].parent_message_id is None

        next_message = await repository.add_message(
            Message(conversation_id=conversation_id, role="assistant", content="next")
        )
        assert next_message.sequence_number == 3


@pytest.mark.asyncio
async def test_truncate_and_clear_conversation_messages(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id, (first_id, _, _) = await create_conversation(session_factory)

    async with session_factory() as session:
        repository = ChatRepository(session)
        assert await repository.delete_messages_after(conversation_id, first_id) == 2
        assert await repository.delete_messages_after(conversation_id, "missing") is None
        assert [message.id for message in await repository.list_messages(conversation_id)] == [
            first_id
        ]

        next_message = await repository.add_message(
            Message(conversation_id=conversation_id, role="user", content="continued")
        )
        assert next_message.sequence_number == 3
        assert await repository.clear_messages(conversation_id) == 2
        assert list(await repository.list_messages(conversation_id)) == []
        await session.commit()


@pytest.mark.asyncio
async def test_message_mutation_endpoints(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id, (first_id, second_id, _) = await create_conversation(
        session_factory
    )
    actor = UserContext(
        id="admin-user",
        name="Administrator",
        authenticated=True,
        active=True,
        roles=("admin",),
        permissions=(),
    )
    app = FastAPI()

    @app.middleware("http")
    async def attach_actor(request: Request, call_next):
        request.state.user = actor
        return await call_next(request)

    async def test_session():
        async with session_factory() as session:
            yield session

    async def test_user() -> UserContext:
        return actor

    app.dependency_overrides[get_session] = test_session
    app.dependency_overrides[require_authenticated_user] = test_user
    app.include_router(chats_api.router, prefix="/chats")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        deleted = await client.delete(
            f"/chats/{conversation_id}/messages/{second_id}"
        )
        assert deleted.status_code == 200
        assert deleted.json()["affected_messages"] == 1

        truncated = await client.delete(
            f"/chats/{conversation_id}/messages",
            params={"after_message_id": first_id},
        )
        assert truncated.status_code == 200
        assert truncated.json()["action"] == "truncate_after"
        assert truncated.json()["affected_messages"] == 1

        missing = await client.delete(
            f"/chats/{conversation_id}/messages/missing"
        )
        assert missing.status_code == 404

        cleared = await client.delete(f"/chats/{conversation_id}/messages")
        assert cleared.status_code == 200
        assert cleared.json()["action"] == "clear"
        assert cleared.json()["affected_messages"] == 1