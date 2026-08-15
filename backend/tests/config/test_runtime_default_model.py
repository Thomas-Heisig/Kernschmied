import asyncio
from app.config.service import ConfigService
from app.storage.database import DatabaseManager
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.core.bootstrap import DEFAULT_MODEL_ID
from app.models.service import ModelService, ModelAccessContext
from app.services.chat_service import ChatService, ChatRequest as ServiceChatRequest, ChatServiceContext
import pytest


@pytest.mark.asyncio
async def test_default_model_runtime_switch(tmp_path):
    db_file = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    dbm = DatabaseManager(db_url)
    session_factory = await dbm.initialize(create_schema=True)

    # Provide a minimal ModelRegistry to satisfy ConfigService validation
    class DummyRegistryEntry:
        def __init__(self, model_id: str, provider_type: str):
            self.model_id = model_id
            self.provider_type = provider_type
            self.enabled = True
            class M:
                @staticmethod
                def supports(x):
                    return x == "chat"
            self.manifest = M()

    class DummyModelRegistry:
        async def list_entries(self):
            return [DummyRegistryEntry("model_a", "ollama"), DummyRegistryEntry("model_b", "ollama"), DummyRegistryEntry("model_request", "ollama")]

    cfg = ConfigService(session_factory, model_registry=DummyModelRegistry())
    await cfg.seed_defaults()

    class DummyModelService:
        async def list_model_ids(self):
            return ["ollama-qwen2.5-7b"]

    model_service = DummyModelService()

    chat = ChatService(model_service=model_service, config_service=cfg, default_model_id=DEFAULT_MODEL_ID)

    # set initial default
    await cfg.set("models", "default_model", "model_a", changed_by="test")

    req = ServiceChatRequest(message="hi")
    ctx = ChatServiceContext(request_id="r1", access=ModelAccessContext(request_id="r1"))

    model = await chat._resolve_model_id(req, ctx)
    assert model == "model_a"

    # Change to model_b without restarting chat
    await cfg.set("models", "default_model", "model_b", changed_by="test")

    model2 = await chat._resolve_model_id(req, ctx)
    assert model2 == "model_b"

    # Request override wins
    req2 = ServiceChatRequest(message="hi", model_id="model_request")
    model3 = await chat._resolve_model_id(req2, ctx)
    assert model3 == "model_request"


@pytest.mark.asyncio
async def test_invalid_persisted_default_recovers_to_registered_bootstrap_model():
    class RegistryEntry:
        model_id = DEFAULT_MODEL_ID
        provider_type = "ollama"

        class Manifest:
            class Provider:
                config = {"default_model": "qwen2.5-coder:7b"}

            provider = Provider()

        manifest = Manifest()

    class Registry:
        async def has(self, model_id: str):
            return model_id == DEFAULT_MODEL_ID

        async def list_model_ids(self):
            return [DEFAULT_MODEL_ID]

        async def list_entries(self):
            return [RegistryEntry()]

        async def get_entry(self, model_id: str):
            assert model_id == DEFAULT_MODEL_ID
            return RegistryEntry()

    class ModelServiceStub:
        _model_registry = Registry()

    class ConfigServiceStub:
        def __init__(self):
            self.updates = None

        def get(self, group: str, key: str):
            assert (group, key) == ("models", "default_model")
            return "ollama-qwen2.5-coder-7b"

        async def set_many(self, updates, *, changed_by: str):
            self.updates = updates
            assert changed_by == "system"

    config = ConfigServiceStub()
    chat = ChatService(
        model_service=ModelServiceStub(),
        config_service=config,
        default_model_id=DEFAULT_MODEL_ID,
    )
    request = ServiceChatRequest(message="test")
    context = ChatServiceContext(
        request_id="invalid-default",
        access=ModelAccessContext(request_id="invalid-default"),
    )

    resolved = await chat._resolve_model_id(request, context)

    assert resolved == DEFAULT_MODEL_ID
    assert config.updates == {
        ("models", "default_model"): DEFAULT_MODEL_ID,
        ("models", "default_provider"): "ollama",
    }
