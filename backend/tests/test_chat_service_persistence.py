import asyncio
from typing import Any, List

import pytest

from app.services.chat_service import (
    ChatService,
    ChatRequest,
    ChatServiceContext,
    ChatEventType,
)
from app.contracts.model_backend import (
    StreamEvent,
    StreamEventType,
    Usage,
)


class FakeRepo:
    def __init__(self) -> None:
        self.user_calls: List[dict[str, Any]] = []
        self.assistant_calls: List[dict[str, Any]] = []
        self.failed_calls: List[dict[str, Any]] = []

    async def create_conversation(self, **kwargs) -> None:
        self.conversation = kwargs

    async def append_user_message(self, **kwargs) -> None:
        self.user_calls.append(dict(kwargs))

    async def append_assistant_message(self, **kwargs) -> None:
        self.assistant_calls.append(dict(kwargs))

    async def mark_assistant_message_failed(self, **kwargs) -> None:
        self.failed_calls.append(dict(kwargs))


class FakeModelService:
    def __init__(self, *, content: str = "ok") -> None:
        self.content = content

    async def generate(self, *, request, model_id, timeout_seconds, access_context):
        # non-streaming: return a COMPLETE event (usage allowed) and put
        # the textual result into data['content'] to respect the contract
        return StreamEvent(type=StreamEventType.COMPLETE, content=None, usage=Usage(1, 1), data={"content": self.content})

    async def stream(self, *, request, model_id, idle_timeout_seconds, access_context):
        # streaming generator that yields one MESSAGE then COMPLETE
        yield StreamEvent(type=StreamEventType.MESSAGE, content=self.content)
        yield StreamEvent(type=StreamEventType.COMPLETE, content=None, usage=Usage(1, 1))


@pytest.mark.asyncio
async def test_user_message_is_persisted_once() -> None:
    repo = FakeRepo()
    model = FakeModelService(content="persisted text")
    service = ChatService(model_service=model, repository=repo, default_model_id="m")

    context = ChatServiceContext(request_id="r1", access=None, user_id="u1")
    req = ChatRequest(message="hello", stream=False)

    resp = await service.generate(req, context=context)

    # user message persisted once
    assert len(repo.user_calls) == 1
    # assistant persisted once
    assert len(repo.assistant_calls) == 1
    # content matches
    assert repo.assistant_calls[0]["content"] == "persisted text"


@pytest.mark.asyncio
async def test_successful_stream_marks_message_complete() -> None:
    repo = FakeRepo()
    model = FakeModelService(content="streamed full")
    service = ChatService(model_service=model, repository=repo, default_model_id="m")

    context = ChatServiceContext(request_id="r2", access=None, user_id="u2")
    req = ChatRequest(message="hi", stream=True)

    events = []
    async for e in service.stream(req, context=context):
        events.append(e)

    # ensure we saw a COMPLETE event
    assert any(e.event == ChatEventType.COMPLETE for e in events)
    # assistant persisted once with final content
    assert len(repo.assistant_calls) == 1
    assert repo.assistant_calls[0]["content"] == "streamed full"
