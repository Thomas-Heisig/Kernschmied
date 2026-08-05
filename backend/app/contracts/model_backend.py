# F:\Kernschmied\backend\app\contracts\model_backend.py

"""
Stabile backendunabhängige Verträge des Kernschmied-Modellsystems.

Diese Datei definiert ausschließlich providerunabhängige Datentypen und
den gemeinsamen Vertrag aller Modell-Backends.

Architekturregeln:

1. Provider-spezifische SDK-Typen dürfen diese Systemgrenze nicht
   überschreiten.
2. Alle Metadaten müssen JSON-kompatibel sein.
3. Streaming und nicht streamende Generierung verwenden denselben
   StreamEvent-Vertrag.
4. Providerfehler werden außerhalb dieses Vertrags in stabile
   ModelError-Typen übersetzt.
5. Ein Stream-Aufruf liefert unmittelbar einen AsyncIterator.
6. Abbruch und Cancellation dürfen nicht verschluckt werden.
7. Unbekannte Event- oder Capability-Typen werden nicht still akzeptiert.
8. Multimodale Inhalte werden erst mit einer versionierten Erweiterung
   des Nachrichtenvertrags eingeführt.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias, Any, AsyncIterator

from pydantic import JsonValue

# ============================================================
# JSON-Vertrag
# ============================================================


JsonScalar: TypeAlias = str | int | float | bool | None

JsonObject: TypeAlias = dict[
    str,
    JsonValue,
]

JsonMapping: TypeAlias = Mapping[
    str,
    JsonValue,
]


def _empty_json_object() -> JsonObject:
    return {}


def _empty_chat_messages() -> list[ChatMessage]:
    return []


def _empty_tool_definitions() -> list[ToolDefinition]:
    return []


def _empty_capabilities() -> set[ModelCapability]:
    return set()


def _copy_json_mapping(
    value: JsonMapping,
) -> JsonObject:
    """
    Erzeugt eine tiefe, veränderbare Kopie eines JSON-Mappings.
    """

    return deepcopy(
        dict(value),
    )


def _normalize_required_identifier(
    value: str,
    *,
    field_name: str,
) -> str:
    """Normalisiert einen erforderlichen Identifier (z.B. ID)."""
    normalized = value.strip()
    if not normalized:
        raise ValueError(
            f"{field_name} darf nicht leer sein.",
        )
    return normalized


def _normalize_optional_identifier(
    value: str | None,
    *,
    field_name: str,
) -> str | None:
    """Normalisiert einen optionalen Identifier."""
    if value is None:
        return None
    return _normalize_required_identifier(
        value,
        field_name=field_name,
    )


# ============================================================
# Fähigkeiten
# ============================================================


class ModelCapability(StrEnum):
    """
    Stabile Fähigkeiten eines Modell-Backends.

    Die Werte müssen mit den Capability-Werten der Modellmanifeste
    übereinstimmen.
    """

    CHAT = "chat"
    COMPLETION = "completion"

    TOOLS = "tools"
    STREAMING = "streaming"
    STRUCTURED_OUTPUT = "structured_output"

    VISION = "vision"
    EMBEDDINGS = "embeddings"

    AUDIO_INPUT = "audio_input"
    AUDIO_OUTPUT = "audio_output"

    IMAGE_GENERATION = "image_generation"

    # Kompatibilitätsalias für ältere Provider.
    JSON_MODE = "structured_output"


# ============================================================
# Rollen
# ============================================================


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# ============================================================
# Chat-Nachricht
# ============================================================


@dataclass(slots=True)
class ChatMessage:
    """
    Einheitliche Textnachricht innerhalb eines Modellaufrufs.

    Der aktuelle Vertragsstand unterstützt ausschließlich Textinhalte.
    Vision-, Audio- und andere multimodale Inhalte benötigen künftig
    einen versionierten MessageContentPart-Vertrag.
    """

    role: MessageRole
    content: str

    name: str | None = None
    tool_call_id: str | None = None

    metadata: JsonObject = field(
        default_factory=_empty_json_object,
    )

    def __post_init__(self) -> None:
        # `role` ist bereits vom Typ MessageRole, daher keine Konvertierung nötig.
        self.name = _normalize_optional_identifier(
            self.name,
            field_name="name",
        )
        self.tool_call_id = _normalize_optional_identifier(
            self.tool_call_id,
            field_name="tool_call_id",
        )
        self.metadata = _copy_json_mapping(
            self.metadata,
        )

        if self.role is MessageRole.TOOL and self.tool_call_id is None:
            raise ValueError(
                "Nachrichten mit role='tool' benötigen eine tool_call_id.",
            )

    @classmethod
    def create(
        cls,
        *,
        role: MessageRole,
        content: str,
        name: str | None = None,
        tool_call_id: str | None = None,
        metadata: JsonMapping | None = None,
    ) -> ChatMessage:
        return cls(
            role=role,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            metadata=(
                _copy_json_mapping(
                    metadata,
                )
                if metadata is not None
                else {}
            ),
        )


# ============================================================
# Tool-Definition
# ============================================================


@dataclass(slots=True)
class ToolDefinition:
    """
    Modellunabhängige Tool-Beschreibung für Function Calling.

    Dies ist die reduzierte Provideransicht eines bereits serverseitig
    registrierten und autorisierten Tools.
    """

    id: str
    name: str
    description: str
    schema: JsonObject

    def __post_init__(self) -> None:
        self.id = _normalize_required_identifier(
            self.id,
            field_name="id",
        )
        self.name = _normalize_required_identifier(
            self.name,
            field_name="name",
        )
        self.description = self.description.strip()
        self.schema = _copy_json_mapping(
            self.schema,
        )

    @classmethod
    def create(
        cls,
        *,
        id: str,
        name: str,
        description: str,
        schema: JsonMapping,
    ) -> ToolDefinition:
        return cls(
            id=id,
            name=name,
            description=description,
            schema=_copy_json_mapping(
                schema,
            ),
        )


# ============================================================
# Structured Output
# ============================================================


@dataclass(slots=True)
class ResponseFormat:
    """
    Providerunabhängige Anforderung an ein strukturiertes Ergebnis.

    type:

    - text
    - json_object
    - json_schema
    """

    type: str = "text"
    schema: JsonObject | None = None
    name: str | None = None
    strict: bool = False

    def __post_init__(self) -> None:
        normalized_type = _normalize_required_identifier(
            self.type,
            field_name="response_format.type",
        ).lower()

        allowed_types = {
            "text",
            "json_object",
            "json_schema",
        }

        if normalized_type not in allowed_types:
            raise ValueError(
                "response_format.type muss 'text', "
                "'json_object' oder 'json_schema' sein.",
            )

        self.type = normalized_type

        self.name = _normalize_optional_identifier(
            self.name,
            field_name="response_format.name",
        )

        if self.schema is not None:
            self.schema = _copy_json_mapping(
                self.schema,
            )

        if self.type == "json_schema" and self.schema is None:
            raise ValueError(
                "response_format.schema ist bei type='json_schema' erforderlich.",
            )

        if self.type != "json_schema" and self.schema is not None:
            raise ValueError(
                "response_format.schema ist nur bei type='json_schema' erlaubt.",
            )


# ============================================================
# Usage
# ============================================================


@dataclass(slots=True)
class Usage:
    """
    Verbrauchsinformationen einer Modellgenerierung.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Optional: zusätzliche Metadaten
    metadata: JsonObject = field(
        default_factory=_empty_json_object,
    )

    def __post_init__(self) -> None:
        if self.input_tokens < 0:
            raise ValueError("input_tokens darf nicht negativ sein.")
        if self.output_tokens < 0:
            raise ValueError("output_tokens darf nicht negativ sein.")
        self.total_tokens = self.input_tokens + self.output_tokens

        self.metadata = _copy_json_mapping(self.metadata)


# ============================================================
# Generation Request
# ============================================================


@dataclass(slots=True)
class GenerationRequest:
    """
    Backendunabhängiger Auftrag zur Modellgenerierung.

    `model` bezeichnet die providerseitige Modellkennung. Die logische
    Kernschmied-Modell-ID wird außerhalb dieses Vertrags durch Registry,
    Service und Lifecycle verwaltet.
    """

    model: str

    messages: list[ChatMessage] = field(
        default_factory=_empty_chat_messages,
    )

    temperature: float = 0.2
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | None = None

    tools: list[ToolDefinition] = field(
        default_factory=_empty_tool_definitions,
    )

    tool_choice: str | None = None
    response_format: ResponseFormat | None = None

    stream: bool = True

    metadata: JsonObject = field(
        default_factory=_empty_json_object,
    )

    def __post_init__(self) -> None:
        self.model = _normalize_required_identifier(
            self.model,
            field_name="model",
        )

        # messages sind bereits list[ChatMessage] – keine Prüfung nötig

        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(
                "temperature muss zwischen 0.0 und 2.0 liegen.",
            )

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError(
                "max_tokens muss größer als null sein.",
            )

        if self.top_p is not None and not 0.0 < self.top_p <= 1.0:
            raise ValueError(
                "top_p muss größer als 0.0 und höchstens 1.0 sein.",
            )

        if self.stop is not None:
            normalized_stop: list[str] = []
            for index, stop_value in enumerate(self.stop):
                normalized_stop.append(
                    _normalize_required_identifier(
                        stop_value,
                        field_name=f"stop[{index}]",
                    ),
                )
            self.stop = normalized_stop

        self.tool_choice = _normalize_optional_identifier(
            self.tool_choice,
            field_name="tool_choice",
        )

        if self.tool_choice is not None and not self.tools:
            raise ValueError(
                "tool_choice darf nur gesetzt werden, wenn Tools übergeben wurden.",
            )

        # response_format ist bereits ResponseFormat oder None

        # stream ist bereits bool

        self.metadata = _copy_json_mapping(
            self.metadata,
        )

    @classmethod
    def create(
        cls,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stop: Sequence[str] | None = None,
        tools: Sequence[ToolDefinition] | None = None,
        tool_choice: str | None = None,
        response_format: ResponseFormat | None = None,
        stream: bool = True,
        metadata: JsonMapping | None = None,
    ) -> GenerationRequest:
        return cls(
            model=model,
            messages=list(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=(list(stop) if stop is not None else None),
            tools=(list(tools) if tools is not None else []),
            tool_choice=tool_choice,
            response_format=response_format,
            stream=stream,
            metadata=(_copy_json_mapping(metadata) if metadata is not None else {}),
        )


# ============================================================
# Stream Event
# ============================================================


class StreamEventType(StrEnum):
    """
    Interner und providerunabhängiger Stream-Vertrag.

    Die Werte stimmen mit dem vorgesehenen SSE-Vertrag überein.
    """

    START = "start"
    TOKEN = "token"
    MESSAGE = "message"
    REASONING = "reasoning"

    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

    USAGE = "usage"
    COMPLETE = "complete"

    ERROR = "error"
    HEARTBEAT = "heartbeat"


@dataclass(slots=True)
class StreamEvent:
    """
    Einheitliches Ereignis einer Modellgenerierung.

    Regeln:

    - TOKEN, MESSAGE und REASONING dürfen `content` enthalten.
    - USAGE und COMPLETE dürfen `usage` enthalten.
    - Providerfehler sollten vorzugsweise als Exception ausgelöst werden.
    - ERROR bleibt für kontrollierte, bereits normalisierte Streamfehler
      verfügbar.
    """

    type: StreamEventType

    content: str | None = None
    usage: Usage | None = None

    data: JsonObject = field(
        default_factory=_empty_json_object,
    )

    def __post_init__(self) -> None:
        # `type` ist bereits StreamEventType, daher keine Konvertierung nötig
        self.data = _copy_json_mapping(
            self.data,
        )

        content_event_types = {
            StreamEventType.TOKEN,
            StreamEventType.MESSAGE,
            StreamEventType.REASONING,
            StreamEventType.ERROR,
        }

        if self.content is not None and self.type not in content_event_types:
            raise ValueError(
                f"Das Event '{self.type.value}' darf keinen content-Wert enthalten.",
            )

        usage_event_types = {
            StreamEventType.USAGE,
            StreamEventType.COMPLETE,
        }

        if self.usage is not None and self.type not in usage_event_types:
            raise ValueError(
                f"Das Event '{self.type.value}' darf keine Usage-Daten enthalten.",
            )

    @classmethod
    def create(
        cls,
        *,
        type: StreamEventType,
        content: str | None = None,
        usage: Usage | None = None,
        data: JsonMapping | None = None,
    ) -> StreamEvent:
        return cls(
            type=type,
            content=content,
            usage=usage,
            data=(_copy_json_mapping(data) if data is not None else {}),
        )


# ============================================================
# Modellinformationen
# ============================================================


@dataclass(slots=True)
class ModelInfo:
    """
    Providerunabhängige Beschreibung eines verfügbaren Modells.

    `capabilities` ist die maßgebliche Quelle. Die supports_*-Felder
    bleiben als kompatible, daraus abgeleitete Diagnosewerte erhalten.
    """

    id: str
    backend: str
    display_name: str
    provider: str

    capabilities: set[ModelCapability] = field(
        default_factory=_empty_capabilities,
    )

    context_window: int | None = None
    max_output_tokens: int | None = None

    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False
    supports_embeddings: bool = False
    supports_structured_output: bool = False

    metadata: JsonObject = field(
        default_factory=_empty_json_object,
    )

    def __post_init__(self) -> None:
        self.id = _normalize_required_identifier(
            self.id,
            field_name="id",
        )
        self.backend = _normalize_required_identifier(
            self.backend,
            field_name="backend",
        )
        self.display_name = _normalize_required_identifier(
            self.display_name,
            field_name="display_name",
        )
        self.provider = _normalize_required_identifier(
            self.provider,
            field_name="provider",
        ).lower()

        # `capabilities` ist bereits set[ModelCapability], daher keine Konvertierung nötig

        if self.context_window is not None and self.context_window <= 0:
            raise ValueError("context_window muss größer als null sein.")

        if self.max_output_tokens is not None and self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens muss größer als null sein.")

        self.supports_streaming = ModelCapability.STREAMING in self.capabilities
        self.supports_tools = ModelCapability.TOOLS in self.capabilities
        self.supports_vision = ModelCapability.VISION in self.capabilities
        self.supports_embeddings = ModelCapability.EMBEDDINGS in self.capabilities
        self.supports_structured_output = (
            ModelCapability.STRUCTURED_OUTPUT in self.capabilities
        )

        self.metadata = _copy_json_mapping(
            self.metadata,
        )

    @classmethod
    def create(
        cls,
        *,
        id: str,
        backend: str,
        display_name: str,
        provider: str,
        capabilities: set[ModelCapability] | None = None,
        context_window: int | None = None,
        max_output_tokens: int | None = None,
        supports_streaming: bool = True,
        supports_tools: bool = False,
        supports_vision: bool = False,
        supports_embeddings: bool = False,
        supports_structured_output: bool = False,
        metadata: JsonMapping | None = None,
    ) -> ModelInfo:
        return cls(
            id=id,
            backend=backend,
            display_name=display_name,
            provider=provider,
            capabilities=(set(capabilities) if capabilities is not None else set()),
            context_window=context_window,
            max_output_tokens=max_output_tokens,
            supports_streaming=supports_streaming,
            supports_tools=supports_tools,
            supports_vision=supports_vision,
            supports_embeddings=supports_embeddings,
            supports_structured_output=supports_structured_output,
            metadata=(_copy_json_mapping(metadata) if metadata is not None else {}),
        )


# ============================================================
# Base Backend
# ============================================================


class BaseModelBackend(ABC):
    """
    Einheitlicher Vertrag aller Modell-Backends.

    Ein Backend darf ausschließlich Modelle seines registrierten
    Provider-Typs verwalten. Auswahl, Freigabe, Autorisierung und
    Lifecycle-Verwaltung müssen über diesen Vertrag erfolgen.
    """

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Gibt die Modellinformationen des Backends zurück."""
        pass

    # Optional runtime methods that some backends provide. Declared here
    # so static type checkers (mypy) accept dynamic backends that may
    # implement these operations. Default implementations raise
    # NotImplementedError to preserve existing runtime behavior.

    async def generate(self, request: GenerationRequest) -> StreamEvent:
        """Optional: vollständige Generierung ausführen (nicht streaming)."""
        raise NotImplementedError()

    def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        """Optional: Streaming-Interface zurückgeben (AsyncIterator of StreamEvent)."""
        raise NotImplementedError()

    async def shutdown(self) -> None:
        """Optional: sauber herunterfahren; default: not implemented."""
        raise NotImplementedError()

    def unload_model(self, *args: Any, **kwargs: Any) -> Any:
        """Optional: provider-specific model unload hook."""
        raise NotImplementedError()

    def unload(self, *args: Any, **kwargs: Any) -> Any:
        """Optional: legacy provider unload hook."""
        raise NotImplementedError()


__all__ = [
    "BaseModelBackend",
    "ChatMessage",
    "GenerationRequest",
    "JsonMapping",
    "JsonObject",
    "JsonScalar",
    "MessageRole",
    "ModelCapability",
    "ModelInfo",
    "ResponseFormat",
    "StreamEvent",
    "StreamEventType",
    "ToolDefinition",
    "Usage",
]
