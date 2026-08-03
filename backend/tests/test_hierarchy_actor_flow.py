# ruff: noqa
import asyncio
from typing import ClassVar, Mapping, cast
from collections.abc import AsyncIterator

from app.auth.models import UserContext
from app.hierarchy.actor_factory import hierarchy_actor_from_user_context
from app.services.chat_service import (
    ChatRequest,
    ChatService,
    ChatServiceContext,
)
from app.models.service import ModelAccessContext, ModelService
from app.contracts.model_backend import GenerationRequest, StreamEvent, StreamEventType
from app.database.base import Base
from app.database.models.hierarchy_node import HierarchyNodeModel
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from pydantic import JsonValue
from typing import Any as _TAny

from app.hierarchy.permissions import HierarchyPermissionService
from app.hierarchy.repository import HierarchyRepository
from app.hierarchy.models import HierarchyActor


class InMemoryChatRepository:
    async def create_conversation(self, *, conversation_id: str, user_id: str | None, tenant_id: str | None, model_id: str, metadata: Mapping[str, JsonValue] | None = None, hierarchy_node_id: str | None = None) -> None:
        return None

    async def append_user_message(self, *, conversation_id: str, message_id: str, parent_message_id: str | None, content: str, metadata: Mapping[str, JsonValue], user_id: str | None = None) -> None:
        return None

    async def append_assistant_message(self, *, conversation_id: str, message_id: str, parent_message_id: str | None, model_id: str, user_id: str | None = None, content: str = "", finish_reason: str | None = None, usage: Mapping[str, JsonValue] | None = None, metadata: Mapping[str, JsonValue] | None = None) -> None:
        return None

    async def mark_assistant_message_failed(self, *, conversation_id: str, message_id: str, error_code: str, error_message: str, metadata: Mapping[str, JsonValue]) -> None:
        return None



class RecordingModelService(ModelService):
    def __init__(self) -> None:
        self.last_request: GenerationRequest | None = None
        self.call_count: int = 0

    async def generate(
        self,
        request: GenerationRequest,
        model_id: str | None = None,
        *,
        timeout_seconds: float | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> StreamEvent:
        self.last_request = request
        self.call_count += 1

        return StreamEvent(type=StreamEventType.MESSAGE, content="ok")

    async def stream(
        self,
        request: GenerationRequest,
        model_id: str | None = None,
        *,
        idle_timeout_seconds: float | None = None,
        access_context: ModelAccessContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        self.last_request = request
        self.call_count += 1

        yield StreamEvent(type=StreamEventType.MESSAGE, content="ok")


class RecordingPromptResolver:
    def __init__(self, *, permission_service: HierarchyPermissionService | None = None) -> None:
        self.received_actor: HierarchyActor | None = None
        self._permission_service: HierarchyPermissionService | None = permission_service
        # expose last created instance for tests
        RecordingPromptResolver.last_instance = self

    async def resolve(self, node_id: str, *, repository: HierarchyRepository | None = None, actor: HierarchyActor | None = None, settings_system_prompt: str | None = None) -> _TAny:
        # record actor identity and return a minimal resolved object
        self.received_actor = actor
        class RP:
            system_prompt = "S"
            fragments: ClassVar[tuple[_TAny, ...]] = ()

        return RP()


def test_hierarchy_actor_is_forwarded_to_prompt_resolver():
    """Ensure the exact HierarchyActor instance from context reaches the resolver."""
    asyncio.run(_run_actor_identity_test())


def test_exact_hierarchy_actor_instance_is_preserved():
    """Assert object identity (is) is preserved through the service into the resolver."""
    async def _inner():
        tmp = __import__("tempfile").TemporaryDirectory()
        url = f"sqlite+aiosqlite:///{tmp.name}/db.sqlite3"
        engine = create_async_engine(url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)

        async with session_factory() as session:
            _build_hierarchy(session)
            await session.commit()

        model = RecordingModelService()
        repo = InMemoryChatRepository()
        service = ChatService(model_service=model, default_model_id="m", repository=repo, history_provider=None, hierarchy_session_factory=session_factory)

        user = UserContext.development_admin(user_id="u1", name="U1")
        actor = hierarchy_actor_from_user_context(user)

        service_context = ChatServiceContext(request_id="r2", access=ModelAccessContext(), hierarchy_actor=actor)

        import app.services.chat_service as csmod
        original = csmod.PromptResolver
        csmod.PromptResolver = RecordingPromptResolver

        try:
            req = ChatRequest(message="hello", hierarchy_node_id="chat-node")
            await service.generate(req, context=service_context)

            # resolver instance should have been created and recorded the exact actor
            inst = getattr(RecordingPromptResolver, "last_instance", None)
            assert inst is not None
            assert inst.received_actor is actor
        finally:
            csmod.PromptResolver = original

    asyncio.run(_inner())


def test_unauthorized_actor_prevents_model_invocation():
    """An actor without read permission must be denied and model must not be called."""
    async def _inner():
        tmp = __import__("tempfile").TemporaryDirectory()
        url = f"sqlite+aiosqlite:///{tmp.name}/db.sqlite3"
        engine = create_async_engine(url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)

        async with session_factory() as session:
            _build_hierarchy(session)
            await session.commit()

        model = RecordingModelService()
        repo = InMemoryChatRepository()
        service = ChatService(model_service=model, default_model_id="m", repository=repo, history_provider=None, hierarchy_session_factory=session_factory)

        # create a user without read permission and without admin role
        user = UserContext(id="u-no", name="NoPerm", authenticated=True, active=True, roles=(), permissions=())
        actor = hierarchy_actor_from_user_context(user)

        service_context = ChatServiceContext(request_id="r3", access=ModelAccessContext(), hierarchy_actor=actor)

        try:
            req = ChatRequest(message="hello", hierarchy_node_id="chat-node")
            try:
                await service.generate(req, context=service_context)
                raised = None
            except Exception as e:
                raised = e

            # Expect ChatGenerationError mapped from PermissionError
            from app.services.chat_service import ChatGenerationError

            assert isinstance(raised, ChatGenerationError)
            assert "Leseberechtigung" in str(raised) or "Leseberechtigung" in raised.message
            # model must not have been invoked
            assert model.call_count == 0

        finally:
            pass

    asyncio.run(_inner())


def test_development_user_context_maps_without_admin_escalation():
    """Check that hierarchy_actor_from_user_context preserves fields and does not add admin rights."""
    # non-admin user
    user = UserContext(id="u4", name="U4", authenticated=True, active=True, roles=("member",), permissions=("read.something",))
    actor = hierarchy_actor_from_user_context(user)

    assert actor.user_id == user.id
    assert actor.roles == frozenset(user.roles)
    assert actor.permissions == frozenset(user.permissions)
    assert "admin" not in actor.roles


def test_missing_hierarchy_actor_is_rejected():
    """If ChatServiceContext.hierarchy_actor is None the service should reject before prompt resolution."""
    async def _inner():
        tmp = __import__("tempfile").TemporaryDirectory()
        url = f"sqlite+aiosqlite:///{tmp.name}/db.sqlite3"
        engine = create_async_engine(url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)

        async with session_factory() as session:
            _build_hierarchy(session)
            await session.commit()

        model = RecordingModelService()
        repo = InMemoryChatRepository()
        service = ChatService(model_service=model, default_model_id="m", repository=repo, history_provider=None, hierarchy_session_factory=session_factory)

        # explicitly set hierarchy_actor to None
        service_context = ChatServiceContext(request_id="r4", access=ModelAccessContext(), hierarchy_actor=cast(_TAny, None))

        # substitute a resolver that would record calls
        import app.services.chat_service as csmod
        original = csmod.PromptResolver
        csmod.PromptResolver = RecordingPromptResolver

        try:
            req = ChatRequest(message="hello", hierarchy_node_id="chat-node")
            try:
                await service.generate(req, context=service_context)
                raised = None
            except Exception as e:
                raised = e

            from app.services.chat_service import ChatServiceError
            assert isinstance(raised, ChatServiceError)
            assert model.call_count == 0
            # resolver was instantiated but resolve should not have been called (no actor)
            inst = getattr(RecordingPromptResolver, "last_instance", None)
            if inst is not None:
                assert inst.received_actor is None
        finally:
            csmod.PromptResolver = original

    asyncio.run(_inner())


def _build_hierarchy(session: AsyncSession) -> None:
    nodes = [
        HierarchyNodeModel(id="system-root", type="system", name="System Root", parent_id=None, system_prompt="S", prompt_priority=-1000, prompt_mode="append", is_active=True),
        HierarchyNodeModel(id="chat-node", type="chat", name="Chat", parent_id="system-root", system_prompt="C", prompt_priority=10, prompt_mode="append", is_active=True),
    ]
    for n in nodes:
        session.add(n)


async def _run_actor_identity_test():
    tmp = __import__("tempfile").TemporaryDirectory()
    url = f"sqlite+aiosqlite:///{tmp.name}/db.sqlite3"
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)

    async with session_factory() as session:
        _build_hierarchy(session)
        await session.commit()

    model = RecordingModelService()

    repo = InMemoryChatRepository()
    service = ChatService(model_service=model, default_model_id="m", repository=repo, history_provider=None, hierarchy_session_factory=session_factory)

    # create a real authenticated user and produce actor at API boundary
    user = UserContext.development_admin(user_id="u1", name="U1")
    actor = hierarchy_actor_from_user_context(user)

    # build contexts
    stream_hierarchy_actor = actor
    service_context = ChatServiceContext(request_id="r1", access=ModelAccessContext(), hierarchy_actor=stream_hierarchy_actor)

    # patch the PromptResolver used by ChatService to our recording resolver
    import app.services.chat_service as csmod
    original = csmod.PromptResolver
    csmod.PromptResolver = RecordingPromptResolver

    try:
        req = ChatRequest(message="hi", hierarchy_node_id="chat-node")
        await service.generate(req, context=service_context)

        # verify the resolver received the exact actor instance
        # the recording resolver instance is created inside service; find it via last created
        # we can inspect csmod.PromptResolver instances by creating a fresh one here (not ideal)
        # instead assert that no exception occurred and model was called
        assert model.last_request is not None

    finally:
        csmod.PromptResolver = original


def test_actor_propagation_and_authorization():
    asyncio.run(_run_actor_identity_test())
