import pytest
from unittest.mock import MagicMock
from app.models.providers.ollama import OllamaProvider
from app.contracts.model_backend import GenerationRequest, ChatMessage, MessageRole


def test_ollama_payload_includes_system_message(monkeypatch):
    # create a minimal GenerationRequest with a system message
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content="GLOBAL_MARKER_2026\nPARENT_MARKER_2026\nCHAT_MARKER_2026"),
        ChatMessage(role=MessageRole.USER, content="Hello"),
    ]

    req = GenerationRequest(model="test-model", messages=messages)

    provider = OllamaProvider(config={})

    payload = provider._create_chat_payload(req)

    msgs = payload.get("messages", [])

    assert len(msgs) >= 1
    assert msgs[0]["role"] == "system"
    # Ensure markers present in first system message
    assert "GLOBAL_MARKER_2026" in msgs[0]["content"]
    assert "PARENT_MARKER_2026" in msgs[0]["content"]
    assert "CHAT_MARKER_2026" in msgs[0]["content"]
