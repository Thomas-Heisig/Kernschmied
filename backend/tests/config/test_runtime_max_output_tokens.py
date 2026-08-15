import pytest
from app.storage.database import DatabaseManager
from app.config.service import ConfigService
from app.services.chat_service import ChatService, ChatRequest as ServiceChatRequest, ChatServiceContext
from app.models.service import ModelAccessContext

@pytest.mark.asyncio
async def test_max_output_tokens_runtime_switch(tmp_path):
    db_file = tmp_path / "test2.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    dbm = DatabaseManager(db_url)
    session_factory = await dbm.initialize(create_schema=True)

    cfg = ConfigService(session_factory)
    await cfg.seed_defaults()

    class DummyModelService:
        async def list_model_ids(self):
            return ["ollama-qwen2.5-7b"]

    model_service = DummyModelService()
    chat = ChatService(model_service=model_service, config_service=cfg, default_model_id="ollama-qwen2.5-7b")

    # set global
    await cfg.set("models", "max_output_tokens", 1111, changed_by="test")

    req = ServiceChatRequest(message="hello")
    ctx = ChatServiceContext(request_id="r1", access=ModelAccessContext(request_id="r1"))

    gen = await chat._create_generation_request(request=req, context=ctx, conversation_id="c1", model_id="ollama-qwen2.5-7b", user_message_id="m1")
    assert gen.max_tokens == 1111

    # change to 2222 and ensure new request picks it up
    await cfg.set("models", "max_output_tokens", 2222, changed_by="test")
    gen2 = await chat._create_generation_request(request=req, context=ctx, conversation_id="c1", model_id="ollama-qwen2.5-7b", user_message_id="m1")
    assert gen2.max_tokens == 2222

    # request override wins
    req3 = ServiceChatRequest(message="hello", max_output_tokens=3333)
    gen3 = await chat._create_generation_request(request=req3, context=ctx, conversation_id="c1", model_id="ollama-qwen2.5-7b", user_message_id="m1")
    assert gen3.max_tokens == 3333
