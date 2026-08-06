import asyncio
import tempfile
from collections.abc import AsyncIterator

from app.contracts.model_backend import (
    GenerationRequest,
    MessageRole,
    StreamEvent,
    StreamEventType,
)
from app.database.base import Base
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.models.service import ModelAccessContext, ModelService
from app.services.chat_service import ChatRequest, ChatService, ChatServiceContext
from app.storage.adapters.chat_history_provider import ChatHistoryProviderAdapter
from app.storage.adapters.chat_repository_adapter import ChatRepositoryAdapter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _build_hierarchy(session: AsyncSession) -> None:
    nodes = [
        HierarchyNodeModel(
            id="system-root",
            type="system",
            name="System Root",
            parent_id=None,
            system_prompt="Befolge die zentralen Sicherheits- und Systemregeln.",
            prompt_priority=-1000,
            prompt_mode="append",
            is_active=True,
        ),
        HierarchyNodeModel(
            id="user-thomas",
            type="user",
            name="Thomas Heisig",
            parent_id="system-root",
            system_prompt="Der angemeldete Benutzer ist Thomas Heisig.",
            prompt_priority=-100,
            prompt_mode="append",
            is_active=True,
        ),
        HierarchyNodeModel(
            id="workspace-heisig",
            type="workspace",
            name="Heisig Naturstein",
            parent_id="user-thomas",
            system_prompt="Du arbeitest für Heisig Naturstein.",
            prompt_priority=0,
            prompt_mode="append",
            is_active=True,
        ),
        HierarchyNodeModel(
            id="project-angebote",
            type="project",
            name="Angebote",
            parent_id="workspace-heisig",
            system_prompt="Erstelle Angebote nach den Unternehmensregeln.",
            prompt_priority=10,
            prompt_mode="append",
            is_active=True,
        ),
        HierarchyNodeModel(
            id="chat-mueller",
            type="chat",
            name="Angebot Müller",
            parent_id="project-angebote",
            system_prompt="Der aktuelle Vorgang betrifft den Kunden Müller.",
            prompt_priority=20,
            prompt_mode="append",
            is_active=True,
        ),
    ]

    for n in nodes:
        session.add(n)


class RecordingModelService(ModelService):
    def __init__(self) -> None:
        self.last_request: GenerationRequest | None = None

    async def generate(
        self,
        request: GenerationRequest,
        model_id: str | None = None,
        *,
        timeout_seconds: float | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> StreamEvent:
        self.last_request = request

        return StreamEvent(type=StreamEventType.MESSAGE, content="assistant reply")

    async def stream(
        self,
        request: GenerationRequest,
        model_id: str | None = None,
        *,
        idle_timeout_seconds: float | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        self.last_request = request
        # simple async generator that yields one StreamEvent
        yield StreamEvent(type=StreamEventType.MESSAGE, content="assistant reply")


async def _run_in_memory_test():
    tmp = tempfile.TemporaryDirectory()
    url = f"sqlite+aiosqlite:///{tmp.name}/db.sqlite3"
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)

    # seed hierarchy
    async with session_factory() as session:
        _build_hierarchy(session)
        await session.commit()

    model = RecordingModelService()

    chat_repo = ChatRepositoryAdapter(session_factory)
    history_provider = ChatHistoryProviderAdapter(session_factory)

    service = ChatService(
        model_service=model,
        default_model_id="m",
        repository=chat_repo,
        history_provider=history_provider,
        hierarchy_session_factory=session_factory,
    )

    from app.hierarchy.models import HierarchyActor

    actor = HierarchyActor(
        user_id="local-user",
        roles=frozenset({"admin"}),
        permissions=frozenset({"hierarchy.read"}),
    )

    context = ChatServiceContext(
        request_id="r1",
        access=ModelAccessContext(),
        hierarchy_actor=actor,
    )

    req = ChatRequest(
        message="Wer bist du?", conversation_id=None, hierarchy_node_id="chat-mueller"
    )

    # run generate twice to ensure consistent recording
    await service.generate(req, context=context)
    await service.generate(req, context=context)

    # last model request recorded should include system as first message
    assert model.last_request is not None
    msg_roles = [m.role for m in model.last_request.messages]
    assert msg_roles[0].value == MessageRole.SYSTEM.value
    assert any(
        m.content and "Befolge" in m.content for m in model.last_request.messages
    )

    # dispose engine and cleanup temporary directory to release file handles
    try:
        await engine.dispose()
    except Exception:
        pass
    try:
        tmp.cleanup()
    except Exception:
        pass


def test_chat_resolved_prompt_integration():
    asyncio.run(_run_in_memory_test())
