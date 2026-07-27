# F:\Kernschmied\backend\app\services\chat_service.py

"""
Anwendungsschicht für Chat-Generierungen.

Der ChatService orchestriert:

- Eingabevalidierung
- Modellauflösung
- serverseitigen Zugriffskontext
- Erzeugung von GenerationRequest
- nicht streamende Antworten
- streamende Antworten
- SSE-freundliche Chat-Events
- Abbruchbehandlung
- strukturierte Fehlerübersetzung
- optionale Persistenz über injizierte Repositories

Nicht verantwortlich für:

- HTTP- oder SSE-Response-Objekte
- Authentifizierung
- direkte Datenbankzugriffe
- Provider-spezifische Modelllogik
- Tool-Ausführung
- Prompt-Vererbung
- Berechtigungsentscheidungen

Diese Aufgaben werden über klar definierte Abhängigkeiten injiziert.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final, Protocol, TypeAlias, runtime_checkable
from uuid import uuid4

from pydantic import JsonValue, TypeAdapter

from app.contracts.model_backend import (
    ChatMessage,
    GenerationRequest,
    MessageRole,
    StreamEvent,
    StreamEventType,
    ToolDefinition,
)
from app.models.errors import (
    ModelError,
    ModelGenerationCancelledError,
    ModelStreamCancelledError,
)
from app.models.service import (
    ModelAccessContext,
    ModelService,
)


logger = logging.getLogger(__name__)


DEFAULT_CHAT_TEMPERATURE: Final[float] = 0.2
DEFAULT_CHAT_MAX_OUTPUT_TOKENS: Final[int] = 2_048
DEFAULT_CHAT_STREAM_IDLE_TIMEOUT_SECONDS: Final[float] = 120.0
DEFAULT_CHAT_GENERATION_TIMEOUT_SECONDS: Final[float] = 600.0

MAX_CHAT_MESSAGE_LENGTH: Final[int] = 200_000
MAX_CHAT_HISTORY_MESSAGES: Final[int] = 1_000
MAX_CHAT_METADATA_ENTRIES: Final[int] = 128


# Keine eigene rekursive JsonValue-Definition – importiert aus pydantic
JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonObject: TypeAlias = dict[str, JsonValue]


_JSON_OBJECT_ADAPTER: Final[TypeAdapter[JsonObject]] = TypeAdapter(
    JsonObject,
)

_JSON_VALUE_ADAPTER: Final[TypeAdapter[JsonValue]] = TypeAdapter(
    JsonValue,
)


def _create_empty_json_object() -> JsonObject:
    """Erzeugt ein neues leeres JSON-Objekt."""

    return {}


def _normalize_json_object(
    value: object,
) -> JsonObject:
    """Validiert und normalisiert einen Wert als JSON-Objekt."""

    return _JSON_OBJECT_ADAPTER.validate_python(
        value,
    )


def _normalize_json_value(
    value: object,
) -> JsonValue:
    """Validiert und normalisiert einen beliebigen JSON-Wert."""

    return _JSON_VALUE_ADAPTER.validate_python(
        value,
    )


# ============================================================
# Fehler
# ============================================================


class ChatServiceError(RuntimeError):
    """
    Basisklasse stabiler Chat-Service-Fehler.
    """

    code = "CHAT_SERVICE_ERROR"
    status_code = 500

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, JsonValue] | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.details: JsonObject = dict(
            details or {},
        )
        self.request_id = request_id
        self.cause = cause

    def to_dict(self) -> JsonObject:
        return {
            "code": self.code,
            "message": self.message,
            "details": dict(self.details),
            "request_id": self.request_id,
        }


class InvalidChatRequestError(ChatServiceError):
    code = "CHAT_REQUEST_INVALID"
    status_code = 422


class ChatConversationNotFoundError(ChatServiceError):
    code = "CHAT_CONVERSATION_NOT_FOUND"
    status_code = 404


class ChatAccessDeniedError(ChatServiceError):
    code = "CHAT_ACCESS_DENIED"
    status_code = 403


class ChatGenerationError(ChatServiceError):
    code = "CHAT_GENERATION_FAILED"
    status_code = 502


class ChatGenerationCancelledError(ChatServiceError):
    code = "CHAT_GENERATION_CANCELLED"
    status_code = 499


class ChatPersistenceError(ChatServiceError):
    code = "CHAT_PERSISTENCE_FAILED"
    status_code = 500


# ============================================================
# Öffentliche Datenmodelle
# ============================================================


class ChatEventType(StrEnum):
    """
    Transportneutrale Ereignistypen für Chat-Streaming.
    """

    START = "start"
    MESSAGE = "message"
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    USAGE = "usage"
    METADATA = "metadata"
    DONE = "done"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


@dataclass(frozen=True, slots=True)
class ChatRequest:
    """
    Vollständige Chat-Anfrage an den Service.
    """

    message: str

    model_id: str | None = None
    conversation_id: str | None = None
    parent_message_id: str | None = None

    system_prompt: str | None = None
    history: tuple[ChatMessage, ...] = ()

    temperature: float | None = None
    max_output_tokens: int | None = None

    stream: bool = True
    tools: tuple[ToolDefinition, ...] = ()

    metadata: Mapping[str, JsonValue] = field(
        default_factory=_create_empty_json_object,
    )

    def __post_init__(self) -> None:
        normalized_message = self.message.strip()

        if not normalized_message:
            raise InvalidChatRequestError(
                "Die Chat-Nachricht darf nicht leer sein.",
            )

        if len(normalized_message) > MAX_CHAT_MESSAGE_LENGTH:
            raise InvalidChatRequestError(
                "Die Chat-Nachricht überschreitet die erlaubte Länge.",
                details={
                    "maximum_length": MAX_CHAT_MESSAGE_LENGTH,
                    "actual_length": len(normalized_message),
                },
            )

        if len(self.history) > MAX_CHAT_HISTORY_MESSAGES:
            raise InvalidChatRequestError(
                "Der Chat-Verlauf enthält zu viele Nachrichten.",
                details={
                    "maximum_messages": MAX_CHAT_HISTORY_MESSAGES,
                    "actual_messages": len(self.history),
                },
            )

        if len(self.metadata) > MAX_CHAT_METADATA_ENTRIES:
            raise InvalidChatRequestError(
                "Die Chat-Metadaten enthalten zu viele Einträge.",
                details={
                    "maximum_entries": MAX_CHAT_METADATA_ENTRIES,
                    "actual_entries": len(self.metadata),
                },
            )

        if self.temperature is not None and not (
            0.0 <= self.temperature <= 2.0
        ):
            raise InvalidChatRequestError(
                "temperature muss zwischen 0 und 2 liegen.",
            )

        if (
            self.max_output_tokens is not None
            and self.max_output_tokens <= 0
        ):
            raise InvalidChatRequestError(
                "max_output_tokens muss größer als 0 sein.",
            )

        object.__setattr__(
            self,
            "message",
            normalized_message,
        )
        object.__setattr__(
            self,
            "history",
            tuple(self.history),
        )
        object.__setattr__(
            self,
            "tools",
            tuple(self.tools),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """
    Ergebnis einer nicht streamenden Chat-Anfrage.
    """

    request_id: str
    conversation_id: str
    message_id: str
    model_id: str

    content: str
    finish_reason: str | None = None

    usage: Mapping[str, JsonValue] | None = None
    metadata: Mapping[str, JsonValue] = field(
        default_factory=_create_empty_json_object,
    )


@dataclass(frozen=True, slots=True)
class ChatStreamEvent:
    """
    Transportneutrales Chat-Streaming-Ereignis.

    Die API-Schicht kann dieses Objekt in SSE, WebSocket-Nachrichten oder
    andere Transportformate umwandeln.
    """

    event: ChatEventType
    request_id: str
    conversation_id: str
    message_id: str

    model_id: str | None = None
    data: Mapping[str, JsonValue] = field(
        default_factory=_create_empty_json_object,
    )

    sequence: int = 0
    created_at_monotonic: float = field(
        default_factory=time.monotonic,
    )

    def to_dict(self) -> JsonObject:
        return {
            "event": self.event.value,
            "request_id": self.request_id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "model_id": self.model_id,
            "sequence": self.sequence,
            "data": dict(self.data),
        }

    def to_sse(
        self,
        *,
        retry_milliseconds: int | None = None,
    ) -> str:
        """
        Serialisiert das Ereignis als vollständigen SSE-Datenblock.
        """

        lines = [
            f"event: {self.event.value}",
            f"id: {self.message_id}:{self.sequence}",
        ]

        if retry_milliseconds is not None:
            lines.append(
                f"retry: {retry_milliseconds}",
            )

        payload = json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
        )

        for line in payload.splitlines() or ("",):
            lines.append(
                f"data: {line}",
            )

        lines.extend(
            ("", ""),
        )

        return "\n".join(
            lines,
        )


@dataclass(frozen=True, slots=True)
class ChatServiceContext:
    """
    Request- und Benutzerkontext des ChatService.
    """

    request_id: str
    access: ModelAccessContext

    tenant_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None

    attributes: Mapping[str, JsonValue] = field(
        default_factory=_create_empty_json_object,
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "attributes",
            dict(self.attributes),
        )


# ============================================================
# Erweiterungspunkte
# ============================================================


@runtime_checkable
class ChatRepository(Protocol):
    """
    Optionale Persistenzschnittstelle.

    Eine SQLAlchemy-Implementierung kann diese Methoden später umsetzen.
    """

    def create_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str | None,
        tenant_id: str | None,
        model_id: str,
        metadata: Mapping[str, JsonValue],
    ) -> None | Awaitable[None]:
        ...

    def append_user_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        parent_message_id: str | None,
        content: str,
        metadata: Mapping[str, JsonValue],
    ) -> None | Awaitable[None]:
        ...

    def append_assistant_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        parent_message_id: str | None,
        model_id: str,
        content: str,
        finish_reason: str | None,
        usage: Mapping[str, JsonValue] | None,
        metadata: Mapping[str, JsonValue],
    ) -> None | Awaitable[None]:
        ...

    def mark_assistant_message_failed(
        self,
        *,
        conversation_id: str,
        message_id: str,
        error_code: str,
        error_message: str,
        metadata: Mapping[str, JsonValue],
    ) -> None | Awaitable[None]:
        ...


@runtime_checkable
class ChatHistoryProvider(Protocol):
    """
    Lädt serverseitig autorisierten Gesprächsverlauf.
    """

    def get_history(
        self,
        *,
        conversation_id: str,
        context: ChatServiceContext,
    ) -> Sequence[ChatMessage] | Awaitable[Sequence[ChatMessage]]:
        ...


ModelResolver: TypeAlias = Callable[
    [ChatRequest, ChatServiceContext],
    str | Awaitable[str],
]


class NullChatRepository:
    """
    No-op-Repository für den Betrieb ohne Chat-Persistenz.
    """

    async def create_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str | None,
        tenant_id: str | None,
        model_id: str,
        metadata: Mapping[str, JsonValue],
    ) -> None:
        del conversation_id
        del user_id
        del tenant_id
        del model_id
        del metadata

    async def append_user_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        parent_message_id: str | None,
        content: str,
        metadata: Mapping[str, JsonValue],
    ) -> None:
        del conversation_id
        del message_id
        del parent_message_id
        del content
        del metadata

    async def append_assistant_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        parent_message_id: str | None,
        model_id: str,
        content: str,
        finish_reason: str | None,
        usage: Mapping[str, JsonValue] | None,
        metadata: Mapping[str, JsonValue],
    ) -> None:
        del conversation_id
        del message_id
        del parent_message_id
        del model_id
        del content
        del finish_reason
        del usage
        del metadata

    async def mark_assistant_message_failed(
        self,
        *,
        conversation_id: str,
        message_id: str,
        error_code: str,
        error_message: str,
        metadata: Mapping[str, JsonValue],
    ) -> None:
        del conversation_id
        del message_id
        del error_code
        del error_message
        del metadata


class NullChatHistoryProvider:
    """
    Leerer Verlaufsanbieter für neue oder nicht persistierte Chats.
    """

    async def get_history(
        self,
        *,
        conversation_id: str,
        context: ChatServiceContext,
    ) -> Sequence[ChatMessage]:
        del conversation_id
        del context

        return ()


# ============================================================
# ChatService
# ============================================================


class ChatService:
    """
    Zentrale Chat-Orchestrierung.

    Die Klasse ist zustandsarm und kann als Application-Service über
    Dependency Injection bereitgestellt werden.
    """

    def __init__(
        self,
        *,
        model_service: ModelService,
        default_model_id: str | None = None,
        model_resolver: ModelResolver | None = None,
        repository: ChatRepository | None = None,
        history_provider: ChatHistoryProvider | None = None,
        default_system_prompt: str | None = None,
        default_temperature: float = DEFAULT_CHAT_TEMPERATURE,
        default_max_output_tokens: int = DEFAULT_CHAT_MAX_OUTPUT_TOKENS,
        stream_idle_timeout_seconds: float = (
            DEFAULT_CHAT_STREAM_IDLE_TIMEOUT_SECONDS
        ),
        generation_timeout_seconds: float = (
            DEFAULT_CHAT_GENERATION_TIMEOUT_SECONDS
        ),
    ) -> None:
        if not 0.0 <= default_temperature <= 2.0:
            raise ValueError(
                "default_temperature muss zwischen 0 und 2 liegen.",
            )

        if default_max_output_tokens <= 0:
            raise ValueError(
                "default_max_output_tokens muss größer als 0 sein.",
            )

        if stream_idle_timeout_seconds <= 0:
            raise ValueError(
                "stream_idle_timeout_seconds muss größer als 0 sein.",
            )

        if generation_timeout_seconds <= 0:
            raise ValueError(
                "generation_timeout_seconds muss größer als 0 sein.",
            )

        if default_model_id is None and model_resolver is None:
            raise ValueError(
                "Es muss entweder default_model_id oder model_resolver "
                "konfiguriert sein.",
            )

        self._model_service = model_service
        self._default_model_id = (
            default_model_id.strip().lower()
            if default_model_id
            else None
        )
        self._model_resolver = model_resolver

        self._repository: ChatRepository = (
            repository
            if repository is not None
            else NullChatRepository()
        )
        self._history_provider: ChatHistoryProvider = (
            history_provider
            if history_provider is not None
            else NullChatHistoryProvider()
        )

        self._default_system_prompt = (
            default_system_prompt.strip()
            if default_system_prompt
            else None
        )
        self._default_temperature = default_temperature
        self._default_max_output_tokens = (
            default_max_output_tokens
        )
        self._stream_idle_timeout_seconds = (
            stream_idle_timeout_seconds
        )
        self._generation_timeout_seconds = (
            generation_timeout_seconds
        )

    # ========================================================
    # Nicht streamende Generierung
    # ========================================================

    async def generate(
        self,
        request: ChatRequest,
        *,
        context: ChatServiceContext,
    ) -> ChatResponse:
        """
        Erzeugt eine vollständige Chat-Antwort.
        """

        model_id = await self._resolve_model_id(
            request,
            context,
        )

        conversation_id = (
            request.conversation_id
            or self._new_id("conversation")
        )
        user_message_id = self._new_id("message")
        assistant_message_id = self._new_id("message")

        await self._prepare_persistence(
            request=request,
            context=context,
            model_id=model_id,
            conversation_id=conversation_id,
            user_message_id=user_message_id,
        )

        generation_request = await self._create_generation_request(
            request=request,
            context=context,
            conversation_id=conversation_id,
            model_id=model_id,
        )

        try:
            model_event = await self._model_service.generate(
                model_id,
                generation_request,
                timeout_seconds=self._generation_timeout_seconds,
                access_context=context.access,
            )

            response = self._build_chat_response(
                model_event=model_event,
                request_id=context.request_id,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                model_id=model_id,
            )

            await self._persist_assistant_response(
                request=request,
                response=response,
            )

            return response

        except asyncio.CancelledError as exc:
            error = ChatGenerationCancelledError(
                "Die Chat-Generierung wurde abgebrochen.",
                request_id=context.request_id,
                details={
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                error=error,
            )

            raise

        except ModelGenerationCancelledError as exc:
            error = ChatGenerationCancelledError(
                "Die Chat-Generierung wurde abgebrochen.",
                request_id=context.request_id,
                details={
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                error=error,
            )

            raise error from exc

        except ModelError as exc:
            error_code_value: object = getattr(
                exc,
                "code",
                "MODEL_ERROR",
            )

            error = ChatGenerationError(
                str(exc),
                request_id=context.request_id,
                details={
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                    "model_error_code": str(error_code_value),
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                error=error,
            )

            raise error from exc

        except ChatServiceError:
            raise

        except Exception as exc:
            error = ChatGenerationError(
                "Die Chat-Antwort konnte nicht erzeugt werden.",
                request_id=context.request_id,
                details={
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                    "error_type": exc.__class__.__name__,
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                error=error,
            )

            raise error from exc

    # ========================================================
    # Streaming
    # ========================================================

    async def stream(
        self,
        request: ChatRequest,
        *,
        context: ChatServiceContext,
    ) -> AsyncIterator[ChatStreamEvent]:
        """
        Streamt eine Chat-Antwort als transportneutrale Ereignisse.
        """

        model_id = await self._resolve_model_id(
            request,
            context,
        )

        conversation_id = (
            request.conversation_id
            or self._new_id("conversation")
        )
        user_message_id = self._new_id("message")
        assistant_message_id = self._new_id("message")

        await self._prepare_persistence(
            request=request,
            context=context,
            model_id=model_id,
            conversation_id=conversation_id,
            user_message_id=user_message_id,
        )

        generation_request = await self._create_generation_request(
            request=request,
            context=context,
            conversation_id=conversation_id,
            model_id=model_id,
        )

        sequence = 0
        content_parts: list[str] = []
        finish_reason: str | None = None
        usage: JsonObject | None = None
        result_metadata: JsonObject = {}

        yield ChatStreamEvent(
            event=ChatEventType.START,
            request_id=context.request_id,
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            model_id=model_id,
            sequence=sequence,
            data={
                "user_message_id": user_message_id,
                "parent_message_id": request.parent_message_id,
            },
        )
        sequence += 1

        try:
            async for model_event in self._model_service.stream(
                model_id,
                generation_request,
                idle_timeout_seconds=self._stream_idle_timeout_seconds,
                access_context=context.access,
            ):
                mapped_events = self._map_model_stream_event(
                    model_event=model_event,
                    request_id=context.request_id,
                    conversation_id=conversation_id,
                    message_id=assistant_message_id,
                    model_id=model_id,
                    start_sequence=sequence,
                )

                for chat_event in mapped_events:
                    sequence = chat_event.sequence + 1

                    if chat_event.event in {
                        ChatEventType.TOKEN,
                        ChatEventType.MESSAGE,
                    }:
                        raw_text = chat_event.data.get(
                            "text",
                        )

                        if isinstance(raw_text, str):
                            content_parts.append(
                                raw_text,
                            )

                    elif chat_event.event == ChatEventType.USAGE:
                        raw_usage = chat_event.data.get(
                            "usage",
                        )

                        if raw_usage is not None:
                            usage = _normalize_json_object(
                                raw_usage,
                            )

                    elif chat_event.event == ChatEventType.METADATA:
                        result_metadata.update(
                            dict(chat_event.data),
                        )

                    raw_finish_reason = chat_event.data.get(
                        "finish_reason",
                    )

                    if isinstance(raw_finish_reason, str):
                        finish_reason = raw_finish_reason

                    yield chat_event

            full_content = "".join(
                content_parts,
            )

            response = ChatResponse(
                request_id=context.request_id,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                model_id=model_id,
                content=full_content,
                finish_reason=finish_reason,
                usage=usage,
                metadata=result_metadata,
            )

            await self._persist_assistant_response(
                request=request,
                response=response,
            )

            yield ChatStreamEvent(
                event=ChatEventType.DONE,
                request_id=context.request_id,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                model_id=model_id,
                sequence=sequence,
                data={
                    "finish_reason": finish_reason,
                    "content_length": len(full_content),
                    "usage": usage,
                },
            )

        except asyncio.CancelledError:
            error = ChatGenerationCancelledError(
                "Der Chat-Stream wurde abgebrochen.",
                request_id=context.request_id,
                details={
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                },
            )

            await self._persist_failure(
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                error=error,
            )

            raise

        except ModelStreamCancelledError as exc:
            error = ChatGenerationCancelledError(
                "Der Chat-Stream wurde abgebrochen.",
                request_id=context.request_id,
                details={
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                error=error,
            )

            yield self._error_event(
                error=error,
                request_id=context.request_id,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                model_id=model_id,
                sequence=sequence,
            )

        except ModelError as exc:
            error_code_value: object = getattr(
                exc,
                "code",
                "MODEL_ERROR",
            )

            error = ChatGenerationError(
                str(exc),
                request_id=context.request_id,
                details={
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                    "model_error_code": str(error_code_value),
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                error=error,
            )

            yield self._error_event(
                error=error,
                request_id=context.request_id,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                model_id=model_id,
                sequence=sequence,
            )

        except ChatServiceError as exc:
            await self._persist_failure(
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                error=exc,
            )

            yield self._error_event(
                error=exc,
                request_id=context.request_id,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                model_id=model_id,
                sequence=sequence,
            )

        except Exception as exc:
            logger.exception(
                "Unexpected chat stream failure",
                extra={
                    "request_id": context.request_id,
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                },
            )

            error = ChatGenerationError(
                "Beim Erzeugen der Chat-Antwort ist ein unerwarteter "
                "Fehler aufgetreten.",
                request_id=context.request_id,
                details={
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                    "error_type": exc.__class__.__name__,
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                error=error,
            )

            yield self._error_event(
                error=error,
                request_id=context.request_id,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                model_id=model_id,
                sequence=sequence,
            )

    async def stream_sse(
        self,
        request: ChatRequest,
        *,
        context: ChatServiceContext,
    ) -> AsyncIterator[str]:
        """
        Convenience-Methode für FastAPI StreamingResponse.
        """

        async for event in self.stream(
            request,
            context=context,
        ):
            yield event.to_sse()

    # ========================================================
    # Request-Aufbereitung
    # ========================================================

    async def _create_generation_request(
        self,
        *,
        request: ChatRequest,
        context: ChatServiceContext,
        conversation_id: str,
        model_id: str,
    ) -> GenerationRequest:
        messages: list[ChatMessage] = []

        system_prompt = (
            request.system_prompt
            or self._default_system_prompt
        )

        if system_prompt:
            messages.append(
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=system_prompt,
                ),
            )

        if request.conversation_id is not None:
            history_result = self._history_provider.get_history(
                conversation_id=conversation_id,
                context=context,
            )

            if isinstance(
                history_result,
                Awaitable,
            ):
                persisted_history = await history_result
            else:
                persisted_history = history_result

            messages.extend(
                persisted_history,
            )

        messages.extend(
            request.history,
        )

        messages.append(
            ChatMessage(
                role=MessageRole.USER,
                content=request.message,
            ),
        )

        max_tokens = (
            request.max_output_tokens
            if request.max_output_tokens is not None
            else self._default_max_output_tokens
        )

        metadata: JsonObject = {
            **dict(request.metadata),
            "request_id": context.request_id,
            "conversation_id": conversation_id,
            "tenant_id": context.tenant_id,
            "user_id": context.user_id,
            "session_id": context.session_id,
        }

        return GenerationRequest(
            model=model_id,
            messages=list(messages),
            temperature=(
                request.temperature
                if request.temperature is not None
                else self._default_temperature
            ),
            max_tokens=max_tokens,
            tools=list(request.tools),
            metadata=metadata,
        )

    async def _resolve_model_id(
        self,
        request: ChatRequest,
        context: ChatServiceContext,
    ) -> str:
        model_id: str

        if request.model_id is not None:
            model_id = request.model_id

        elif self._model_resolver is not None:
            resolver_result = self._model_resolver(
                request,
                context,
            )

            if isinstance(
                resolver_result,
                Awaitable,
            ):
                model_id = await resolver_result
            else:
                model_id = resolver_result

        elif self._default_model_id is not None:
            model_id = self._default_model_id

        else:
            raise InvalidChatRequestError(
                "Für die Chat-Anfrage konnte kein Modell bestimmt werden.",
                request_id=context.request_id,
            )

        normalized = model_id.strip().lower()

        if not normalized:
            raise InvalidChatRequestError(
                "Die ermittelte Modell-ID ist leer.",
                request_id=context.request_id,
            )

        return normalized

    # ========================================================
    # Modell-Event-Mapping
    # ========================================================

    def _map_model_stream_event(
        self,
        *,
        model_event: StreamEvent,
        request_id: str,
        conversation_id: str,
        message_id: str,
        model_id: str,
        start_sequence: int,
    ) -> tuple[ChatStreamEvent, ...]:
        event_type = model_event.type
        payload = self._stream_event_payload(
            model_event,
        )

        if event_type == StreamEventType.TOKEN:
            raw_text = payload.get(
                "text",
            )

            text = (
                raw_text
                if isinstance(raw_text, str)
                else ""
            )

            return (
                ChatStreamEvent(
                    event=ChatEventType.TOKEN,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                    sequence=start_sequence,
                    data={
                        **payload,
                        "text": text,
                    },
                ),
            )

        if event_type == StreamEventType.TOOL_CALL:
            return (
                ChatStreamEvent(
                    event=ChatEventType.TOOL_CALL,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                    sequence=start_sequence,
                    data=payload,
                ),
            )

        if event_type == StreamEventType.TOOL_RESULT:
            return (
                ChatStreamEvent(
                    event=ChatEventType.TOOL_RESULT,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                    sequence=start_sequence,
                    data=payload,
                ),
            )

        if event_type == StreamEventType.ERROR:
            return (
                ChatStreamEvent(
                    event=ChatEventType.ERROR,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                    sequence=start_sequence,
                    data=payload,
                ),
            )

        if event_type == StreamEventType.END:
            end_events: list[ChatStreamEvent] = []
            next_sequence = start_sequence

            raw_usage = payload.get(
                "usage",
            )

            if raw_usage is not None:
                usage = _normalize_json_object(
                    raw_usage,
                )

                end_events.append(
                    ChatStreamEvent(
                        event=ChatEventType.USAGE,
                        request_id=request_id,
                        conversation_id=conversation_id,
                        message_id=message_id,
                        model_id=model_id,
                        sequence=next_sequence,
                        data={
                            "usage": usage,
                        },
                    ),
                )
                next_sequence += 1

            raw_finish_reason = payload.get(
                "finish_reason",
            )

            if isinstance(raw_finish_reason, str):
                end_events.append(
                    ChatStreamEvent(
                        event=ChatEventType.METADATA,
                        request_id=request_id,
                        conversation_id=conversation_id,
                        message_id=message_id,
                        model_id=model_id,
                        sequence=next_sequence,
                        data={
                            "finish_reason": raw_finish_reason,
                        },
                    ),
                )

            return tuple(
                end_events,
            )

        return (
            ChatStreamEvent(
                event=ChatEventType.METADATA,
                request_id=request_id,
                conversation_id=conversation_id,
                message_id=message_id,
                model_id=model_id,
                sequence=start_sequence,
                data={
                    "model_event_type": event_type.value,
                    **payload,
                },
            ),
        )

    @staticmethod
    def _stream_event_payload(
        model_event: StreamEvent,
    ) -> JsonObject:
        """
        Überführt bekannte StreamEvent-Felder in ein JSON-Objekt.

        Es wird bewusst weder model_dump() noch vars() verwendet, weil
        StreamEvent nicht zwingend ein Pydantic-Modell sein muss.
        """

        payload: JsonObject = {}

        attribute_names: tuple[str, ...] = (
            "text",
            "content",
            "delta",
            "finish_reason",
            "usage",
            "metadata",
            "data",
            "error",
            "tool_call",
            "tool_result",
        )

        for attribute_name in attribute_names:
            raw_value: object = getattr(
                model_event,
                attribute_name,
                None,
            )

            if raw_value is None:
                continue

            if attribute_name in {
                "metadata",
                "data",
            }:
                nested_payload = _normalize_json_object(
                    raw_value,
                )

                payload.update(
                    nested_payload,
                )
                continue

            payload[attribute_name] = _normalize_json_value(
                raw_value,
            )

        return payload

    # ========================================================
    # Response-Aufbereitung
    # ========================================================

    def _build_chat_response(
        self,
        *,
        model_event: StreamEvent,
        request_id: str,
        conversation_id: str,
        message_id: str,
        model_id: str,
    ) -> ChatResponse:
        payload = self._stream_event_payload(
            model_event,
        )

        raw_text = payload.get(
            "text",
        )
        raw_content = payload.get(
            "content",
        )
        raw_delta = payload.get(
            "delta",
        )

        if isinstance(raw_text, str):
            content = raw_text
        elif isinstance(raw_content, str):
            content = raw_content
        elif isinstance(raw_delta, str):
            content = raw_delta
        else:
            content = ""

        raw_finish_reason = payload.get(
            "finish_reason",
        )

        finish_reason = (
            raw_finish_reason
            if isinstance(raw_finish_reason, str)
            else None
        )

        raw_usage = payload.get(
            "usage",
        )

        usage = (
            _normalize_json_object(raw_usage)
            if raw_usage is not None
            else None
        )

        metadata: JsonObject = {
            key: value
            for key, value in payload.items()
            if key
            not in {
                "text",
                "content",
                "delta",
                "finish_reason",
                "usage",
            }
        }

        return ChatResponse(
            request_id=request_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model_id=model_id,
            content=content,
            finish_reason=finish_reason,
            usage=usage,
            metadata=metadata,
        )

    @staticmethod
    def _error_event(
        *,
        error: ChatServiceError,
        request_id: str,
        conversation_id: str,
        message_id: str,
        model_id: str,
        sequence: int,
    ) -> ChatStreamEvent:
        return ChatStreamEvent(
            event=ChatEventType.ERROR,
            request_id=request_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model_id=model_id,
            sequence=sequence,
            data=error.to_dict(),
        )

    # ========================================================
    # Persistenz
    # ========================================================

    async def _prepare_persistence(
        self,
        *,
        request: ChatRequest,
        context: ChatServiceContext,
        model_id: str,
        conversation_id: str,
        user_message_id: str,
    ) -> None:
        try:
            if request.conversation_id is None:
                await self._await_if_needed(
                    self._repository.create_conversation(
                        conversation_id=conversation_id,
                        user_id=context.user_id,
                        tenant_id=context.tenant_id,
                        model_id=model_id,
                        metadata={
                            **dict(request.metadata),
                            "request_id": context.request_id,
                        },
                    ),
                )

            await self._await_if_needed(
                self._repository.append_user_message(
                    conversation_id=conversation_id,
                    message_id=user_message_id,
                    parent_message_id=request.parent_message_id,
                    content=request.message,
                    metadata={
                        **dict(request.metadata),
                        "request_id": context.request_id,
                    },
                ),
            )

        except ChatServiceError:
            raise

        except Exception as exc:
            raise ChatPersistenceError(
                "Die Benutzeranfrage konnte nicht gespeichert werden.",
                request_id=context.request_id,
                details={
                    "conversation_id": conversation_id,
                    "error_type": exc.__class__.__name__,
                },
                cause=exc,
            ) from exc

    async def _persist_assistant_response(
        self,
        *,
        request: ChatRequest,
        response: ChatResponse,
    ) -> None:
        try:
            await self._await_if_needed(
                self._repository.append_assistant_message(
                    conversation_id=response.conversation_id,
                    message_id=response.message_id,
                    parent_message_id=request.parent_message_id,
                    model_id=response.model_id,
                    content=response.content,
                    finish_reason=response.finish_reason,
                    usage=response.usage,
                    metadata=response.metadata,
                ),
            )

        except Exception as exc:
            logger.exception(
                "Assistant response persistence failed",
                extra={
                    "request_id": response.request_id,
                    "conversation_id": response.conversation_id,
                    "message_id": response.message_id,
                },
            )

            raise ChatPersistenceError(
                "Die erzeugte Chat-Antwort konnte nicht gespeichert "
                "werden.",
                request_id=response.request_id,
                details={
                    "conversation_id": response.conversation_id,
                    "message_id": response.message_id,
                    "error_type": exc.__class__.__name__,
                },
                cause=exc,
            ) from exc

    async def _persist_failure(
        self,
        *,
        conversation_id: str,
        message_id: str,
        error: ChatServiceError,
    ) -> None:
        try:
            await self._await_if_needed(
                self._repository.mark_assistant_message_failed(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    error_code=error.code,
                    error_message=error.message,
                    metadata={
                        "request_id": error.request_id,
                        "details": dict(error.details),
                    },
                ),
            )

        except Exception:
            logger.exception(
                "Could not persist failed assistant message",
                extra={
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "error_code": error.code,
                },
            )

    # ========================================================
    # Hilfsmethoden
    # ========================================================

    @staticmethod
    async def _await_if_needed(
        value: None | Awaitable[None],
    ) -> None:
        if value is not None:
            await value

    @staticmethod
    def _new_id(
        prefix: str,
    ) -> str:
        return f"{prefix}_{uuid4().hex}"


__all__ = [
    "ChatAccessDeniedError",
    "ChatConversationNotFoundError",
    "ChatEventType",
    "ChatGenerationCancelledError",
    "ChatGenerationError",
    "ChatHistoryProvider",
    "ChatPersistenceError",
    "ChatRepository",
    "ChatRequest",
    "ChatResponse",
    "ChatService",
    "ChatServiceContext",
    "ChatServiceError",
    "ChatStreamEvent",
    "InvalidChatRequestError",
    "ModelResolver",
    "NullChatHistoryProvider",
    "NullChatRepository",
]