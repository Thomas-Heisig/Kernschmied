from typing import Any, cast

from app.contracts.model_backend import ChatMessage, GenerationRequest, MessageRole
from app.models.service import ModelAccessContext, ModelService
from app.services.chat_service import (
    ChatHistoryProvider,
    ChatRequest,
    ChatService,
    ChatServiceContext,
)


def test_history_loaded_and_deduplicated(tmp_path: Any, monkeypatch: Any) -> None:
    # This test is a high-level integration-style unit that ensures persisted messages
    # are loaded and the current user message is not duplicated when building the
    # GenerationRequest. It uses the real adapters but a transient SQLite DB would
    # normally be used; here we patch the history provider to return a crafted list.

    # minimal ChatService instance with a recording model_service and injected history provider
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
        ):
            # capture the prepared GenerationRequest for assertions
            self.last_request = request
            from app.contracts.model_backend import StreamEvent, StreamEventType

            return StreamEvent(type=StreamEventType.MESSAGE, content="ok")

    recording_model = RecordingModelService()

    # Create a fake persisted history with a message that matches the user_message_id
    persisted = [
        ChatMessage.create(
            role=MessageRole.USER,
            content="old message",
            metadata={"message_id": "m1", "sequence_number": 1},
        ),
        ChatMessage.create(
            role=MessageRole.ASSISTANT,
            content="reply",
            metadata={"message_id": "m2", "sequence_number": 2},
        ),
    ]

    class H:
        async def get_history(
            self, *, conversation_id: str, context: ChatServiceContext
        ) -> list[ChatMessage]:
            del conversation_id
            del context

            return persisted

    # inject provider via constructor to avoid using protected members
    service = ChatService(
        model_service=recording_model,
        default_model_id="m",
        history_provider=cast(ChatHistoryProvider, H()),
    )

    req = ChatRequest(
        message="new message", conversation_id=None, history=(), system_prompt=None
    )

    # emulate service flow
    context = ChatServiceContext(request_id="r1", access=ModelAccessContext())

    import asyncio

    # run through the public `generate` path to build the GenerationRequest
    asyncio.run(service.generate(req, context=context))

    gen_req = recording_model.last_request
    assert gen_req is not None

    # messages should include system (none), persisted except m1, and current user message once
    texts = [m.content for m in gen_req.messages]
    assert "old message" not in texts
    assert "reply" in texts
    assert "new message" in texts
    assert texts.count("new message") == 1
