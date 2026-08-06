# pyright: reportPrivateUsage=false
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

import pytest
from app.contracts.model_backend import GenerationRequest, StreamEvent, StreamEventType
from app.core.settings import reload_settings
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.models.service import ModelAccessContext, ModelService
from app.services.chat_service import ChatRequest, ChatService, ChatServiceContext
from app.storage import database as _database_module
from app.storage.adapters.chat_history_provider import ChatHistoryProviderAdapter
from app.storage.adapters.chat_repository_adapter import ChatRepositoryAdapter
from app.storage.database import init_database
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.fixture(scope="module")
async def session_factory() -> async_sessionmaker[AsyncSession]:
    # Prevent init_database from attempting to run Alembic here
    os.environ["DATABASE_MIGRATION_MODE"] = "disabled"
    backend_dir = Path(__file__).resolve().parents[1]
    test_db = backend_dir / "data" / "chat.clean-fresh-test.db"
    # Ensure a fresh DB file so ORM create_all produces the canonical schema
    try:
        if test_db.exists():
            test_db.unlink()
    except Exception:
        pass

    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_db.as_posix()}"

    new_settings = reload_settings()
    _database_module.settings = new_settings

    _database_module._database_manager = _database_module.DatabaseManager(
        new_settings.effective_database_url
    )

    # Create the schema from current ORM models to ensure columns match.
    sf = await init_database(create_schema=True, echo=False)
    return sf


class RecordingModelService(ModelService):
    def __init__(self) -> None:
        self.requests: list[GenerationRequest] = []
        self.first_response = "Antwort vom Modell"

    async def stream(
        self,
        request: GenerationRequest,
        model_id: str | None = None,
        *,
        idle_timeout_seconds: float | None = None,
        access_context: Any | None = None,
    ) -> AsyncIterator[StreamEvent]:
        # record the request
        self.requests.append(request)

        # yield a single message event and then a complete event
        yield StreamEvent.create(
            type=StreamEventType.MESSAGE, content=self.first_response
        )
        yield StreamEvent.create(type=StreamEventType.COMPLETE)


async def collect_stream(it: AsyncIterator[Any]) -> list[Any]:
    events: list[Any] = []
    async for e in it:
        events.append(e)
    return events


@pytest.mark.asyncio
async def test_second_request_contains_previous_conversation_history(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # prepare adapters using real session factory
    repo_adapter = ChatRepositoryAdapter(session_factory)
    history_provider = ChatHistoryProviderAdapter(session_factory)

    # recording model service
    model_service = RecordingModelService()

    # create service (cast recording service to ModelService for the test)
    service = ChatService(
        model_service=cast(ModelService, model_service),
        default_model_id="m",
        repository=repo_adapter,
        history_provider=history_provider,
    )

    # create a chat hierarchy node and pass its id in request metadata
    async with session_factory() as session:
        node = HierarchyNodeModel(
            id="node-1", parent_id=None, type="chat", name="Node 1"
        )
        session.add(node)
        await session.flush()
        await session.commit()

    # first user message: let the service create the conversation id
    req1 = ChatRequest(
        message="Mein Name ist Thomas Heisig.",
        conversation_id=None,
        history=(),
        system_prompt=None,
        hierarchy_node_id="node-1",
    )
    ctx = ChatServiceContext(request_id="r1", access=ModelAccessContext())
    events = await collect_stream(service.stream(req1, context=ctx))

    # extract conversation_id from START event
    conv_id = None
    for e in events:
        if getattr(e, "event", None) is not None and e.event.name == "START":
            conv_id = e.conversation_id
            break
    assert conv_id is not None

    # second user message uses same conversation id
    req2 = ChatRequest(
        message="Wer bin ich?", conversation_id=conv_id, history=(), system_prompt=None
    )
    ctx2 = ChatServiceContext(request_id="r2", access=ModelAccessContext())

    await collect_stream(service.stream(req2, context=ctx2))

    # ensure the model received two requests and the second contains history
    assert len(model_service.requests) >= 2

    second = model_service.requests[1]
    seq = [(m.role.value, m.content) for m in second.messages]

    assert ("user", "Mein Name ist Thomas Heisig.") in seq
    assert ("assistant", model_service.first_response) in seq
    assert ("user", "Wer bin ich?") in seq
