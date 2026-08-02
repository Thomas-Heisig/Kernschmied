from typing import Any, cast

from app.services.chat_service import ChatService, ChatServiceContext, ChatRequest, ChatHistoryProvider
from app.models.service import ModelAccessContext, ModelService
from app.contracts.model_backend import MessageRole, ChatMessage


def test_history_loaded_and_deduplicated(tmp_path: Any, monkeypatch: Any) -> None:
    # This test is a high-level integration-style unit that ensures persisted messages
    # are loaded and the current user message is not duplicated when building the
    # GenerationRequest. It uses the real adapters but a transient SQLite DB would
    # normally be used; here we patch the history provider to return a crafted list.

    # minimal ChatService instance with a dummy model_service and default_model_id
    dummy_model_service = cast(ModelService, type("M", (), {})())
    service = ChatService(model_service=dummy_model_service, default_model_id="m")

    # Create a fake persisted history with a message that matches the user_message_id
    persisted = [
        ChatMessage.create(role=MessageRole.USER, content="old message", metadata={"message_id": "m1", "sequence_number": 1}),
        ChatMessage.create(role=MessageRole.ASSISTANT, content="reply", metadata={"message_id": "m2", "sequence_number": 2}),
    ]

    class H:
        async def get_history(self, *, conversation_id: str, context: ChatServiceContext) -> list[ChatMessage]:
            del conversation_id
            del context

            return persisted

    # assign provider via setattr with a cast to satisfy static typing
    setattr(service, "_history_provider", cast(ChatHistoryProvider, H()))

    req = ChatRequest(message="new message", conversation_id=None, history=(), system_prompt=None)

    # emulate service flow
    conversation_id = "c1"
    user_message_id = "m1"  # same as first persisted message to trigger dedupe

    context = ChatServiceContext(request_id="r1", access=ModelAccessContext())

    import asyncio

    coro = getattr(service, "_create_generation_request")(
        request=req,
        context=context,
        conversation_id=conversation_id,
        model_id="m",
        user_message_id=user_message_id,
    )

    gen_req = asyncio.run(coro)

    # messages should include system (none), persisted except m1, and current user message once
    texts = [m.content for m in gen_req.messages]
    assert "old message" not in texts
    assert "reply" in texts
    assert "new message" in texts
    assert texts.count("new message") == 1
