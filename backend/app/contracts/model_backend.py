# F:\Kernschmied\backend\app\contracts\model_backend.py
# Korrigierte Version: JsonValue wird von Pydantic importiert

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

from pydantic import JsonValue


# ==========================================================
# JSON-Vertrag
# ==========================================================


JsonScalar: TypeAlias = str | int | float | bool | None
# JsonValue wird von pydantic importiert – nicht rekursiv definiert
JsonObject: TypeAlias = dict[str, JsonValue]
JsonMapping: TypeAlias = Mapping[str, JsonValue]


def _empty_json_object() -> JsonObject:
    """
    Typisierte Factory für leere JSON-Objekte.

    Eine eigene Factory verhindert, dass Pylance bei
    `default_factory=dict` den Typ `dict[Unknown, Unknown]` ableitet.
    """

    return {}


def _empty_tool_definitions() -> list[ToolDefinition]:
    """
    Typisierte Factory für die Tool-Liste eines GenerationRequest.
    """

    return []


def _empty_capabilities() -> set[ModelCapability]:
    """
    Typisierte Factory für Modellfähigkeiten.
    """

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


# ==========================================================
# Fähigkeiten
# ==========================================================


class ModelCapability(str, Enum):
    CHAT = "chat"
    COMPLETION = "completion"
    TOOLS = "tools"
    VISION = "vision"
    EMBEDDINGS = "embeddings"
    AUDIO_INPUT = "audio_input"
    AUDIO_OUTPUT = "audio_output"
    IMAGE_GENERATION = "image_generation"
    JSON_MODE = "json_mode"
    STREAMING = "streaming"


# ==========================================================
# Rollen
# ==========================================================


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# ==========================================================
# Chat Message
# ==========================================================


@dataclass(slots=True)
class ChatMessage:
    """
    Einheitliche Nachricht innerhalb eines Modellaufrufs.
    """

    role: MessageRole
    content: str

    name: str | None = None
    tool_call_id: str | None = None

    metadata: JsonObject = field(
        default_factory=_empty_json_object,
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
                _copy_json_mapping(metadata)
                if metadata is not None
                else {}
            ),
        )


# ==========================================================
# Tool-Definition für Modellaufrufe
# ==========================================================


@dataclass(slots=True)
class ToolDefinition:
    """
    Modellunabhängige Tool-Beschreibung für Function Calling.

    Dies ist die für Modell-Backends reduzierte Darstellung eines Tools.
    Der vollständige Tool-Vertrag befindet sich in
    `app.contracts.tool`.
    """

    id: str
    name: str
    description: str
    schema: JsonObject

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


# ==========================================================
# Generation Request
# ==========================================================


@dataclass(slots=True)
class GenerationRequest:
    """
    Backendunabhängiger Auftrag zur Text- oder Chat-Generierung.
    """

    model: str
    messages: list[ChatMessage]

    temperature: float = 0.2
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | None = None

    tools: list[ToolDefinition] = field(
        default_factory=_empty_tool_definitions,
    )

    tool_choice: str | None = None
    stream: bool = True

    metadata: JsonObject = field(
        default_factory=_empty_json_object,
    )

    @classmethod
    def create(
        cls,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stop: list[str] | None = None,
        tools: list[ToolDefinition] | None = None,
        tool_choice: str | None = None,
        stream: bool = True,
        metadata: JsonMapping | None = None,
    ) -> GenerationRequest:
        return cls(
            model=model,
            messages=list(
                messages,
            ),
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=(
                list(stop)
                if stop is not None
                else None
            ),
            tools=(
                list(tools)
                if tools is not None
                else []
            ),
            tool_choice=tool_choice,
            stream=stream,
            metadata=(
                _copy_json_mapping(metadata)
                if metadata is not None
                else {}
            ),
        )


# ==========================================================
# Nutzung
# ==========================================================


@dataclass(slots=True)
class Usage:
    """
    Einheitliche Token-Nutzungsdaten eines Modellaufrufs.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self) -> None:
        if self.prompt_tokens < 0:
            raise ValueError(
                "prompt_tokens darf nicht negativ sein.",
            )

        if self.completion_tokens < 0:
            raise ValueError(
                "completion_tokens darf nicht negativ sein.",
            )

        if self.total_tokens < 0:
            raise ValueError(
                "total_tokens darf nicht negativ sein.",
            )


# ==========================================================
# Stream Event
# ==========================================================


class StreamEventType(str, Enum):
    START = "start"
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    INFO = "info"
    ERROR = "error"
    END = "end"


@dataclass(slots=True)
class StreamEvent:
    """
    Einheitliches Ereignis eines Modell-Streams.
    """

    type: StreamEventType
    content: str | None = None
    usage: Usage | None = None

    data: JsonObject = field(
        default_factory=_empty_json_object,
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
            data=(
                _copy_json_mapping(data)
                if data is not None
                else {}
            ),
        )


# ==========================================================
# Modellinformationen
# ==========================================================


@dataclass(slots=True)
class ModelInfo:
    """
    Öffentliche Beschreibung eines verfügbaren Modells.
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

    metadata: JsonObject = field(
        default_factory=_empty_json_object,
    )

    def __post_init__(self) -> None:
        if (
            self.context_window is not None
            and self.context_window <= 0
        ):
            raise ValueError(
                "context_window muss größer als null sein.",
            )

        if (
            self.max_output_tokens is not None
            and self.max_output_tokens <= 0
        ):
            raise ValueError(
                "max_output_tokens muss größer als null sein.",
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
        metadata: JsonMapping | None = None,
    ) -> ModelInfo:
        return cls(
            id=id,
            backend=backend,
            display_name=display_name,
            provider=provider,
            capabilities=(
                set(capabilities)
                if capabilities is not None
                else set()
            ),
            context_window=context_window,
            max_output_tokens=max_output_tokens,
            supports_streaming=supports_streaming,
            supports_tools=supports_tools,
            supports_vision=supports_vision,
            supports_embeddings=supports_embeddings,
            metadata=(
                _copy_json_mapping(metadata)
                if metadata is not None
                else {}
            ),
        )


# ==========================================================
# Base Backend
# ==========================================================


class BaseModelBackend(ABC):
    """
    Einheitlicher Vertrag für alle Modell-Backends.

    Unterstützte Implementierungen können beispielsweise sein:

    - Ollama
    - llama.cpp
    - Transformers
    - OpenAI
    - Gemini
    - Anthropic
    - Azure OpenAI

    Ein Backend darf ausschließlich Modelle seines registrierten
    Provider-Typs verwalten. Auswahl, Freigabe und Autorisierung
    erfolgen außerhalb dieses Vertrags.
    """

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """
        Eindeutiger registrierter Name des Backends.
        """

        raise NotImplementedError

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Prüft, ob das Backend momentan genutzt werden kann.
        """

        raise NotImplementedError

    @abstractmethod
    async def list_models(
        self,
    ) -> list[ModelInfo]:
        """
        Liefert alle aktuell verfügbaren Modelle des Backends.
        """

        raise NotImplementedError

    @abstractmethod
    async def get_model(
        self,
        model_id: str,
    ) -> ModelInfo:
        """
        Liefert Informationen zu einem Modell.

        Implementierungen sollten für unbekannte Modelle einen
        kontrollierten Modellfehler auslösen.
        """

        raise NotImplementedError

    @abstractmethod
    def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        """
        Startet eine Streaming-Ausgabe.

        Konkrete Implementierungen verwenden typischerweise:

        async def stream(
            self,
            request: GenerationRequest,
        ) -> AsyncIterator[StreamEvent]:
            yield StreamEvent(...)

        Wichtig ist, dass der Aufruf von `stream()` unmittelbar einen
        AsyncIterator liefert und keine Coroutine, die zuerst separat
        awaited werden müsste.
        """

        raise NotImplementedError

    async def generate(
        self,
        request: GenerationRequest,
    ) -> str:
        """
        Komfortfunktion für eine vollständige Textantwort.

        Die Methode sammelt ausschließlich TOKEN-Ereignisse. Tool-,
        Informations- und Fehlerereignisse werden nicht als Text
        übernommen.
        """

        parts: list[str] = []

        stream_iterator: AsyncIterator[StreamEvent] = self.stream(
            request,
        )

        async for event in stream_iterator:
            if event.type is not StreamEventType.TOKEN:
                continue

            if event.content is None:
                continue

            parts.append(
                event.content,
            )

        return "".join(
            parts,
        )

    async def shutdown(self) -> None:
        """
        Optionaler Lebenszyklus-Hook zum Freigeben von Ressourcen.

        Backends können beispielsweise HTTP-Clients, Modellinstanzen,
        GPU-Speicher oder Worker-Prozesse schließen.
        """

        return None