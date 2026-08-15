import pytest
from app.storage.database import DatabaseManager
from app.config.service import ConfigService
from app.services.chat_service import ChatService, ChatRequest as ServiceChatRequest, ChatServiceContext
from app.models.service import ModelAccessContext
from app.hierarchy.repository import HierarchyRepository
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.contracts.hierarchy import HierarchyNodeCreate
from app.hierarchy.models import HierarchyActor

@pytest.mark.asyncio
async def test_generation_request_token_priority(tmp_path):
    db_file = tmp_path / "test3.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    dbm = DatabaseManager(db_url)
    session_factory = await dbm.initialize(create_schema=True)

    cfg = ConfigService(session_factory)
    await cfg.seed_defaults()

    class DummyModelService:
        async def list_model_ids(self):
            return ["ollama-qwen2.5-7b"]

    model_service = DummyModelService()
    chat = ChatService(model_service=model_service, config_service=cfg, default_model_id="ollama-qwen2.5-7b", hierarchy_session_factory=session_factory)

    # set global to 1000
    await cfg.set("models", "max_output_tokens", 1000, changed_by="test")

    # create a hierarchy node with config_overrides models.max_output_tokens = 1500
    async with session_factory() as s:
        repo = HierarchyRepository(s)
        node_data = HierarchyNodeCreate(
            node_id=None,
            parent_id=None,
            type="chat",
            name="h1",
            system_prompt=None,
            tool_policy={},
            config_overrides={"models": {"max_output_tokens": 1500}},
            metadata={},
        )
        node = await repo.create_node(node_data)
        node_id = node.id
        await s.commit()

    req = ServiceChatRequest(message="hello", hierarchy_node_id=node_id)
    actor = HierarchyActor(user_id=None, roles=frozenset(), permissions=frozenset({"hierarchy.read"}))
    ctx = ChatServiceContext(request_id="r1", access=ModelAccessContext(request_id="r1"), hierarchy_actor=actor)

    gen = await chat._create_generation_request(request=req, context=ctx, conversation_id="c1", model_id="ollama-qwen2.5-7b", user_message_id="m1")
    assert gen.max_tokens == 1500

    # request override 2000
    req2 = ServiceChatRequest(message="hello", hierarchy_node_id=node_id, max_output_tokens=2000)
    gen2 = await chat._create_generation_request(request=req2, context=ctx, conversation_id="c1", model_id="ollama-qwen2.5-7b", user_message_id="m1")
    assert gen2.max_tokens == 2000

    # remove hierarchy by using no hierarchy_node_id and expect global 1000
    req3 = ServiceChatRequest(message="hello")
    gen3 = await chat._create_generation_request(request=req3, context=ctx, conversation_id="c1", model_id="ollama-qwen2.5-7b", user_message_id="m1")
    assert gen3.max_tokens == 1000

    # no config and no hierarchy -> fallback to service default
    await cfg.reset_to_default("models", "max_output_tokens", changed_by="test")
    gen4 = await chat._create_generation_request(request=req3, context=ctx, conversation_id="c1", model_id="ollama-qwen2.5-7b", user_message_id="m1")
    assert gen4.max_tokens > 0
