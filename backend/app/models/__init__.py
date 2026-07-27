# F:\Kernschmied\backend\app\models\__init__.py

"""
Modell-Subsystem von Kernschmied.

Dieses Paket enthält die technische Anbindung von Modell-Providern und
deren Laufzeitimplementierungen.

Architekturregeln:

- Modell-Metadaten stammen primär aus versionierten `model.json`-Manifesten.
- Provider werden ausschließlich über die ModelRegistry ausgewählt.
- Der Import dieses Pakets führt keine Discovery aus.
- Der Import dieses Pakets erzeugt keine globalen Provider-Instanzen.
- Provider erhalten ihre Abhängigkeiten über Dependency Injection.
- Unbekannte Provider-Typen werden nicht automatisch ausgeführt.
- Beliebiger Python-Code aus unkontrollierten Verzeichnissen wird nicht
  importiert.
- Fachliche Modellkonfiguration wird nicht in diesem Paket gespeichert.
"""

from __future__ import annotations

from app.contracts.model_backend import (
    BaseModelBackend,
    ChatMessage,
    GenerationRequest,
    MessageRole,
    ModelCapability,
    ModelInfo,
    StreamEvent,
    StreamEventType,
    ToolDefinition,
    Usage,
)

__all__ = [
    "BaseModelBackend",
    "ChatMessage",
    "GenerationRequest",
    "MessageRole",
    "ModelCapability",
    "ModelInfo",
    "StreamEvent",
    "StreamEventType",
    "ToolDefinition",
    "Usage",
]