"""Testskript: Erzeuge eine Ollama-Payload aus einer GenerationRequest.

Dieses Skript hilft zu überprüfen, ob System-Nachrichten korrekt in
das Ollama-Payload konvertiert werden.
"""

from app.models.providers.ollama import OllamaProvider
from app.contracts.model_backend import (
    ChatMessage,
    GenerationRequest,
    MessageRole,
)


def main() -> None:
    prov = OllamaProvider(config={})

    system = ChatMessage.create(role=MessageRole.SYSTEM, content="System prompt TEST")
    user = ChatMessage.create(role=MessageRole.USER, content="Hello world")

    req = GenerationRequest.create(model=prov._logical_model_id, messages=[system, user])

    payload = prov._create_chat_payload(req)

    print("Payload messages:")
    for m in payload.get("messages", []):
        print(m)


if __name__ == "__main__":
    main()
