from app.models.providers.ollama import OllamaProvider
from app.contracts.model_backend import ChatMessage, GenerationRequest, MessageRole


def test_ollama_payload_contains_full_conversation_history() -> None:
    # Configure provider with logical model id matching the request
    cfg = {
        "model": "qwen-ollama-server-model",
        "logical_model_id": "ollama-qwen",
    }

    provider = OllamaProvider(cfg)

    request = GenerationRequest(
        model="ollama-qwen",
        messages=[
            ChatMessage(role=MessageRole.USER, content="Mein Name ist Thomas Heisig."),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hallo Thomas Heisig."),
            ChatMessage(role=MessageRole.USER, content="Wer bin ich?"),
        ],
    )

    payload = provider._create_chat_payload(request)

    assert payload["messages"] == [
        {"role": "user", "content": "Mein Name ist Thomas Heisig."},
        {"role": "assistant", "content": "Hallo Thomas Heisig."},
        {"role": "user", "content": "Wer bin ich?"},
    ]
