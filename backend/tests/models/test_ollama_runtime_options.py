import pytest
from app.contracts.model_backend import GenerationRequest, ChatMessage, MessageRole
from app.models.providers.ollama import OllamaProvider

@pytest.mark.asyncio
async def test_ollama_payload_options_num_predict():
    # build GenerationRequest
    gen = GenerationRequest(
        model="ollama-qwen2.5-7b",
        messages=[ChatMessage(role=MessageRole.SYSTEM, content="SYSTEM_MARKER"), ChatMessage(role=MessageRole.USER, content="Hallo")],
        temperature=0.2,
        max_tokens=1111,
    )

    # instantiate provider with default config (no overrides)
    prov = OllamaProvider({}, dependencies=None)

    payload = prov._create_chat_payload(gen)

    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][0]["content"] == "SYSTEM_MARKER"
    assert payload["options"]["num_predict"] == 1111

    # change to 2222
    gen.max_tokens = 2222
    payload2 = prov._create_chat_payload(gen)
    assert payload2["options"]["num_predict"] == 2222
