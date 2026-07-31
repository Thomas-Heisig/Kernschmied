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
- transportneutrale Chat-Ereignisse
- Abbruchbehandlung
- strukturierte Fehlerübersetzung
- optionale Persistenz über injizierte Repositories

Nicht verantwortlich für:
- HTTP-Response-Objekte
- Authentifizierung
- direkte Datenbankzugriffe
- Provider-spezifische Modelllogik
- Tool-Ausführung
- Prompt-Vererbung
- Berechtigungsentscheidungen

Die eigentliche SSE-Umschlagserialisierung gehört langfristig in die
API-Schicht. `ChatStreamEvent.to_sse()` bleibt vorübergehend für
Abwärtskompatibilität erhalten.
"""

from __future__ import annotations

import asyncio
import inspect
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
from typing import (
    Final,
    Protocol,
    TypeAlias,
    runtime_checkable,
)
from uuid import uuid4

from pydantic import (
    JsonValue,
    TypeAdapter,
)

# Korrekte Imports aus dem stabilen Vertrag
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


# ============================================================
# Konstanten
# ============================================================


SOURCE_FILE: Final[str] = "backend/app/services/chat_service.py"

LOG_AREA: Final[str] = "chat-service"

DEFAULT_CHAT_TEMPERATURE: Final[float] = 0.2

DEFAULT_CHAT_MAX_OUTPUT_TOKENS: Final[int] = 2_048

DEFAULT_CHAT_STREAM_IDLE_TIMEOUT_SECONDS: Final[float] = 120.0

DEFAULT_CHAT_GENERATION_TIMEOUT_SECONDS: Final[float] = 600.0

MAX_CHAT_MESSAGE_LENGTH: Final[int] = 200_000

MAX_CHAT_HISTORY_MESSAGES: Final[int] = 1_000

MAX_CHAT_METADATA_ENTRIES: Final[int] = 128


JsonObject: TypeAlias = dict[
    str,
    JsonValue,
]


_JSON_OBJECT_ADAPTER: Final[TypeAdapter[JsonObject]] = TypeAdapter(
    JsonObject,
)

_JSON_VALUE_ADAPTER: Final[TypeAdapter[JsonValue]] = TypeAdapter(
    JsonValue,
)


# ============================================================
# JSON-Hilfsfunktionen
# ============================================================


def _create_empty_json_object() -> JsonObject:
    return {}


def _normalize_json_object(
    value: object,
) -> JsonObject:
    return _JSON_OBJECT_ADAPTER.validate_python(
        value,
    )


def _normalize_json_value(
    value: object,
) -> JsonValue:
    """Normalisiert einen Wert in einen JSON-kompatiblen Wert."""
    return _JSON_VALUE_ADAPTER.validate_python(
        value,
    )


def _event_type_value(
    event_type: object,
) -> str:
    raw_value = getattr(
        event_type,
        "value",
        event_type,
    )

    return (
        str(
            raw_value,
        )
        .strip()
        .lower()
    )


def _extract_text(
    payload: Mapping[str, JsonValue],
) -> str:
    """Extracts the primary text content from a payload dictionary."""
    # Check common fields first (most direct access)
    for field_name in ("text", "content", "delta"):
        raw_value = payload.get(field_name)
        if isinstance(raw_value, str):
            return raw_value

    # Fallback to 'message' key if common fields fail
    raw_message = payload.get("message")
    if isinstance(raw_message, str):
        return raw_message

    # Handle nested content structure (e.g., in tool results)
    # Ensure the value is a Mapping before calling .get()
    message_value = payload.get("message")
    if isinstance(message_value, Mapping):
        content = message_value.get("content")
        if isinstance(content, str):
            return content

    return ""


def _extract_error_message(
    payload: Mapping[str, JsonValue],
) -> str | None:
    for field_name in (
        "message",
        "detail",
        "error_message",
    ):
        raw_value = payload.get(
            field_name,
        )

        if (
            isinstance(
                raw_value,
                str,
            )
            and raw_value.strip()
        ):
            return raw_value.strip()

    raw_error = payload.get(
        "error",
    )

    if (
        isinstance(
            raw_error,
            str,
        )
        and raw_error.strip()
    ):
        return raw_error.strip()

    if isinstance(
        raw_error,
        Mapping,
    ):
        nested_message = raw_error.get(
            "message",
        )

        if (
            isinstance(
                nested_message,
                str,
            )
            and nested_message.strip()
        ):
            return nested_message.strip()

    return None


# ============================================================
# Logging
# ============================================================


def _log_context(
    **values: object,
) -> dict[str, object]:
    return {
        "source": SOURCE_FILE,
        "area": LOG_AREA,
        **values,
    }


def _log_info(
    message: str,
    **context: object,
) -> None:
    logger.info(
        message,
        extra=_log_context(
            **context,
        ),
    )


def _log_warning(
    message: str,
    **context: object,
) -> None:
    logger.warning(
        message,
        extra=_log_context(
            **context,
        ),
    )


def _log_exception(
    message: str,
    **context: object,
) -> None:
    logger.exception(
        message,
        extra=_log_context(
            **context,
        ),
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
        details: (
            Mapping[
                str,
                JsonValue,
            ]
            | None
        ) = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            message,
        )

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
            "details": dict(
                self.details,
            ),
            "request_id": self.request_id,
        }


class InvalidChatRequestError(
    ChatServiceError,
):
    code = "CHAT_REQUEST_INVALID"
    status_code = 422


class ChatConversationNotFoundError(
    ChatServiceError,
):
    code = "CHAT_CONVERSATION_NOT_FOUND"
    status_code = 404


class ChatAccessDeniedError(
    ChatServiceError,
):
    code = "CHAT_ACCESS_DENIED"
    status_code = 403


class ChatGenerationError(
    ChatServiceError,
):
    code = "CHAT_GENERATION_FAILED"
    status_code = 502


class ChatGenerationCancelledError(
    ChatServiceError,
):
    code = "CHAT_GENERATION_CANCELLED"
    status_code = 499


class ChatPersistenceError(
    ChatServiceError,
):
    code = "CHAT_PERSISTENCE_FAILED"
    status_code = 500


# ============================================================
# Öffentliche Datenmodelle
# ============================================================


class ChatEventType(StrEnum):
    """
    Öffentliche transportneutrale Chat-Ereignistypen.

    Diese Werte entsprechen dem versionierten Frontend- und
    API-Vertrag.
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


@dataclass(
    frozen=True,
    slots=True,
)
class ChatRequest:
    """
    Vollständige Chat-Anfrage an den Service.
    """

    message: str

    model_id: str | None = None
    conversation_id: str | None = None
    parent_message_id: str | None = None

    system_prompt: str | None = None

    history: tuple[
        ChatMessage,
        ...,
    ] = ()

    temperature: float | None = None
    max_output_tokens: int | None = None

    stream: bool = True

    tools: tuple[
        ToolDefinition,
        ...,
    ] = ()

    metadata: Mapping[
        str,
        JsonValue,
    ] = field(
        default_factory=(_create_empty_json_object),
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
                    "maximum_length": (MAX_CHAT_MESSAGE_LENGTH),
                    "actual_length": len(
                        normalized_message,
                    ),
                },
            )

        if len(self.history) > MAX_CHAT_HISTORY_MESSAGES:
            raise InvalidChatRequestError(
                "Der Chat-Verlauf enthält zu viele Nachrichten.",
                details={
                    "maximum_messages": (MAX_CHAT_HISTORY_MESSAGES),
                    "actual_messages": len(
                        self.history,
                    ),
                },
            )

        if len(self.metadata) > MAX_CHAT_METADATA_ENTRIES:
            raise InvalidChatRequestError(
                "Die Chat-Metadaten enthalten zu viele Einträge.",
                details={
                    "maximum_entries": (MAX_CHAT_METADATA_ENTRIES),
                    "actual_entries": len(
                        self.metadata,
                    ),
                },
            )

        if self.temperature is not None and not (0.0 <= self.temperature <= 2.0):
            raise InvalidChatRequestError(
                "temperature muss zwischen 0 und 2 liegen.",
            )

        if self.max_output_tokens is not None and self.max_output_tokens <= 0:
            raise InvalidChatRequestError(
                "max_output_tokens muss größer als 0 sein.",
            )

        normalized_model_id = self.model_id.strip().lower() if self.model_id else None

        normalized_conversation_id = (
            self.conversation_id.strip() if self.conversation_id else None
        )

        normalized_parent_message_id = (
            self.parent_message_id.strip() if self.parent_message_id else None
        )

        normalized_system_prompt = (
            self.system_prompt.strip() if self.system_prompt else None
        )

        object.__setattr__(
            self,
            "message",
            normalized_message,
        )

        object.__setattr__(
            self,
            "model_id",
            normalized_model_id,
        )

        object.__setattr__(
            self,
            "conversation_id",
            normalized_conversation_id,
        )

        object.__setattr__(
            self,
            "parent_message_id",
            normalized_parent_message_id,
        )

        object.__setattr__(
            self,
            "system_prompt",
            normalized_system_prompt,
        )

        object.__setattr__(
            self,
            "history",
            tuple(
                self.history,
            ),
        )

        object.__setattr__(
            self,
            "tools",
            tuple(
                self.tools,
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            _normalize_json_object(
                dict(
                    self.metadata,
                ),
            ),
        )


@dataclass(
    frozen=True,
    slots=True,
)
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

    usage: (
        Mapping[
            str,
            JsonValue,
        ]
        | None
    ) = None

    metadata: Mapping[
        str,
        JsonValue,
    ] = field(
        default_factory=(_create_empty_json_object),
    )


@dataclass(
    frozen=True,
    slots=True,
)
class ChatStreamEvent:
    """
    Transportneutrales Chat-Streaming-Ereignis.
    """

    event: ChatEventType

    request_id: str
    conversation_id: str
    message_id: str

    model_id: str | None = None

    data: Mapping[
        str,
        JsonValue,
    ] = field(
        default_factory=(_create_empty_json_object),
    )

    sequence: int = 0

    # default_factory sorgt für float
    created_at_monotonic: float = field(
        default_factory=time.monotonic,
    )

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError(
                "sequence darf nicht negativ sein.",
            )

        object.__setattr__(
            self,
            "data",
            _normalize_json_object(
                dict(
                    self.data,
                ),
            ),
        )

    def to_dict(self) -> JsonObject:
        return {
            "event": self.event.value,
            "request_id": self.request_id,
            "conversation_id": (self.conversation_id),
            "message_id": self.message_id,
            "model_id": self.model_id,
            "sequence": self.sequence,
            "data": dict(
                self.data,
            ),
        }

    def to_sse(
        self,
        *,
        retry_milliseconds: int | None = None,
    ) -> str:
        """
        Übergangskompatibilität für ältere API-Schichten.

        Neue API-Endpunkte sollten einen eigenen versionierten
        StreamEnvelope erzeugen.
        """

        lines = [
            f"event: {self.event.value}",
            (f"id: {self.message_id}:{self.sequence}"),
        ]

        if retry_milliseconds is not None:
            lines.append(
                f"retry: {retry_milliseconds}",
            )

        payload = json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

        for line in payload.splitlines() or ("",):
            lines.append(
                f"data: {line}",
            )

        lines.extend(
            (
                "",
                "",
            ),
        )

        return "\n".join(
            lines,
        )


@dataclass(
    frozen=True,
    slots=True,
)
class ChatServiceContext:
    """
    Request- und Benutzerkontext des ChatService.
    """

    request_id: str
    access: ModelAccessContext

    tenant_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None

    attributes: Mapping[
        str,
        JsonValue,
    ] = field(
        default_factory=(_create_empty_json_object),
    )

    def __post_init__(self) -> None:
        normalized_request_id = self.request_id.strip()

        if not normalized_request_id:
            raise ValueError(
                "request_id darf nicht leer sein.",
            )

        object.__setattr__(
            self,
            "request_id",
            normalized_request_id,
        )

        object.__setattr__(
            self,
            "attributes",
            _normalize_json_object(
                dict(
                    self.attributes,
                ),
            ),
        )


# ============================================================
# Erweiterungspunkte
# ============================================================


@runtime_checkable
class ChatRepository(Protocol):
    def create_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str | None,
        tenant_id: str | None,
        model_id: str,
        metadata: Mapping[
            str,
            JsonValue,
        ],
    ) -> Awaitable[None] | None: ...

    def append_user_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        parent_message_id: str | None,
        content: str,
        metadata: Mapping[
            str,
            JsonValue,
        ],
    ) -> Awaitable[None] | None: ...

    def append_assistant_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        parent_message_id: str | None,
        model_id: str,
        content: str,
        finish_reason: str | None,
        usage: (
            Mapping[
                str,
                JsonValue,
            ]
            | None
        ),
        metadata: Mapping[
            str,
            JsonValue,
        ],
    ) -> Awaitable[None] | None: ...

    def mark_assistant_message_failed(
        self,
        *,
        conversation_id: str,
        message_id: str,
        error_code: str,
        error_message: str,
        metadata: Mapping[
            str,
            JsonValue,
        ],
    ) -> Awaitable[None] | None: ...


@runtime_checkable
class ChatHistoryProvider(Protocol):
    def get_history(
        self,
        *,
        conversation_id: str,
        context: ChatServiceContext,
    ) -> Sequence[ChatMessage] | Awaitable[Sequence[ChatMessage]]: ...


ModelResolver: TypeAlias = Callable[
    [
        ChatRequest,
        ChatServiceContext,
    ],
    str | Awaitable[str],
]


class NullChatRepository:
    async def create_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str | None,
        tenant_id: str | None,
        model_id: str,
        metadata: Mapping[
            str,
            JsonValue,
        ],
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
        metadata: Mapping[
            str,
            JsonValue,
        ],
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
        usage: (
            Mapping[
                str,
                JsonValue,
            ]
            | None
        ),
        metadata: Mapping[
            str,
            JsonValue,
        ],
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
        metadata: Mapping[
            str,
            JsonValue,
        ],
    ) -> None:
        del conversation_id
        del message_id
        del error_code
        del error_message
        del metadata


class NullChatHistoryProvider:
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
    Zentrale zustandsarme Chat-Orchestrierung.
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
        default_temperature: float = (DEFAULT_CHAT_TEMPERATURE),
        default_max_output_tokens: int = (DEFAULT_CHAT_MAX_OUTPUT_TOKENS),
        stream_idle_timeout_seconds: float = (DEFAULT_CHAT_STREAM_IDLE_TIMEOUT_SECONDS),
        generation_timeout_seconds: float = (DEFAULT_CHAT_GENERATION_TIMEOUT_SECONDS),
    ) -> None:
        if not (0.0 <= default_temperature <= 2.0):
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
                "Es muss entweder default_model_id oder "
                "model_resolver konfiguriert sein.",
            )

        normalized_default_model_id = (
            default_model_id.strip().lower() if default_model_id else None
        )

        if default_model_id is not None and not normalized_default_model_id:
            raise ValueError(
                "default_model_id darf nicht leer sein.",
            )

        self._model_service = model_service

        self._default_model_id = normalized_default_model_id

        self._model_resolver = model_resolver

        self._repository: ChatRepository = (
            repository if repository is not None else NullChatRepository()
        )

        self._history_provider: ChatHistoryProvider = (
            history_provider
            if history_provider is not None
            else NullChatHistoryProvider()
        )

        self._default_system_prompt = (
            default_system_prompt.strip()
            if default_system_prompt and default_system_prompt.strip()
            else None
        )

        self._default_temperature = default_temperature

        self._default_max_output_tokens = default_max_output_tokens

        self._stream_idle_timeout_seconds = stream_idle_timeout_seconds

        self._generation_timeout_seconds = generation_timeout_seconds

    # ========================================================
    # Nicht streamende Generierung
    # ========================================================

    async def generate(
        self,
        request: ChatRequest,
        *,
        context: ChatServiceContext,
    ) -> ChatResponse:
        model_id = await self._resolve_model_id(
            request,
            context,
        )

        conversation_id: str = request.conversation_id or self._new_id(
            "conversation",
        )

        user_message_id: str = self._new_id(
            "message",
        )

        assistant_message_id: str = self._new_id(
            "message",
        )

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

        _log_info(
            "Chat generation started",
            chat_event=("generation-started"),
            request_id=context.request_id,
            conversation_id=conversation_id,
            model_id=model_id,
            streaming=False,
        )

        try:
            model_event: StreamEvent = await self._model_service.generate(
                request=generation_request,
                model_id=model_id,
                timeout_seconds=(self._generation_timeout_seconds),
                access_context=(context.access),
            )

            response: ChatResponse = self._build_chat_response(
                model_event=model_event,
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
            )

            await self._persist_assistant_response(
                request=request,
                response=response,
            )

            _log_info(
                "Chat generation completed",
                chat_event=("generation-completed"),
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
                content_length=len(
                    response.content,
                ),
                streaming=False,
            )

            return response

        except asyncio.CancelledError as exc:
            error = ChatGenerationCancelledError(
                "Die Chat-Generierung wurde abgebrochen.",
                request_id=(context.request_id),
                details={
                    "conversation_id": (conversation_id),
                    "model_id": model_id,
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                error=error,
            )

            raise

        except ModelGenerationCancelledError as exc:
            error = ChatGenerationCancelledError(
                "Die Chat-Generierung wurde abgebrochen.",
                request_id=(context.request_id),
                details={
                    "conversation_id": (conversation_id),
                    "model_id": model_id,
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                error=error,
            )

            raise error from exc

        except ModelError as exc:
            error = self._translate_model_error(
                exc,
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                model_id=model_id,
            )

            await self._persist_failure(
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                error=error,
            )

            raise error from exc

        except ChatServiceError:
            raise

        except Exception as exc:
            error = ChatGenerationError(
                "Die Chat-Antwort konnte nicht erzeugt werden.",
                request_id=(context.request_id),
                details={
                    "conversation_id": (conversation_id),
                    "model_id": model_id,
                    "error_type": (exc.__class__.__name__),
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
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
        # Alle Variablen initialisieren, die später verwendet werden
        authoritative_message_content: str | None = None
        finish_reason: str | None = None
        usage: JsonObject | None = None
        result_metadata: JsonObject = {}
        terminal_event_emitted = False

        model_id = await self._resolve_model_id(
            request,
            context,
        )

        conversation_id: str = request.conversation_id or self._new_id(
            "conversation",
        )

        user_message_id: str = self._new_id(
            "message",
        )

        assistant_message_id: str = self._new_id(
            "message",
        )

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

        token_content_parts: list[str] = []

        _log_info(
            "Chat stream started",
            chat_event="stream-started",
            request_id=context.request_id,
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            model_id=model_id,
            streaming=True,
        )

        yield ChatStreamEvent(
            event=ChatEventType.START,
            request_id=context.request_id,
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            model_id=model_id,
            sequence=sequence,
            data={
                "user_message_id": (user_message_id),
                "parent_message_id": (request.parent_message_id),
            },
        )

        sequence += 1

        try:
            async for model_event in self._model_service.stream(
                request=generation_request,
                model_id=model_id,
                idle_timeout_seconds=(self._stream_idle_timeout_seconds),
                access_context=(context.access),
            ):
                # model_event ist hier garantiert vom Typ StreamEvent
                model_event_type = _event_type_value(
                    model_event.type,
                )

                payload = self._stream_event_payload(
                    model_event,
                )

                raw_finish_reason = payload.get(
                    "finish_reason",
                )

                if isinstance(
                    raw_finish_reason,
                    str,
                ):
                    finish_reason = raw_finish_reason

                raw_usage = payload.get(
                    "usage",
                )

                if isinstance(raw_usage, Mapping):
                    usage = _normalize_json_object(
                        raw_usage,
                    )

                if model_event_type == StreamEventType.ERROR.value:
                    error_message = _extract_error_message(
                        payload,
                    ) or (
                        "Das Modell hat während der Generierung einen Fehler gemeldet."
                    )

                    raise ChatGenerationError(
                        error_message,
                        request_id=(context.request_id),
                        details={
                            "conversation_id": (conversation_id),
                            "model_id": model_id,
                            "model_event": payload,
                        },
                    )

                _log_info(
                    "Model stream event received",
                    chat_event="model-stream-event-received",
                    request_id=context.request_id,
                    conversation_id=conversation_id,
                    message_id=assistant_message_id,
                    model_id=model_id,
                    model_event_type=model_event_type,
                    payload_keys=list(
                        payload.keys(),
                    ),
                )

                mapped_events = self._map_model_stream_event(
                    model_event=model_event,
                    request_id=(context.request_id),
                    conversation_id=(conversation_id),
                    message_id=(assistant_message_id),
                    model_id=model_id,
                    start_sequence=(sequence),
                )

                for chat_event in mapped_events:
                    sequence = chat_event.sequence + 1

                    if chat_event.event == ChatEventType.TOKEN:
                        token_text = _extract_text(
                            chat_event.data,
                        )

                        if token_text:
                            token_content_parts.append(
                                token_text,
                            )

                    elif chat_event.event == ChatEventType.MESSAGE:
                        message_text = _extract_text(
                            chat_event.data,
                        )

                        if message_text:
                            authoritative_message_content = message_text

                    elif chat_event.event == ChatEventType.USAGE:
                        event_usage = chat_event.data.get(
                            "usage",
                        )

                        if event_usage is not None:
                            usage = _normalize_json_object(
                                event_usage,
                            )

                    elif chat_event.event == ChatEventType.REASONING:
                        result_metadata["reasoning_emitted"] = True

                    yield chat_event

            full_content: str = (
                authoritative_message_content
                if (authoritative_message_content is not None)
                else "".join(
                    token_content_parts,
                )
            )

            response = ChatResponse(
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
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

            terminal_event_emitted = True

            yield ChatStreamEvent(
                event=(ChatEventType.COMPLETE),
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
                sequence=sequence,
                data={
                    "content": full_content,
                    "finish_reason": (finish_reason),
                    "content_length": len(
                        full_content,
                    ),
                    "usage": usage,
                },
            )

            _log_info(
                "Chat stream completed",
                chat_event=("stream-completed"),
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
                content_length=len(
                    full_content,
                ),
                finish_reason=(finish_reason),
            )

        except asyncio.CancelledError:
            error = ChatGenerationCancelledError(
                "Der Chat-Stream wurde abgebrochen.",
                request_id=(context.request_id),
                details={
                    "conversation_id": (conversation_id),
                    "model_id": model_id,
                },
            )

            await self._persist_failure(
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                error=error,
            )

            _log_info(
                "Chat stream cancelled",
                chat_event=("stream-cancelled"),
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
            )

            raise

        except ModelStreamCancelledError as exc:
            error = ChatGenerationCancelledError(
                "Der Chat-Stream wurde abgebrochen.",
                request_id=(context.request_id),
                details={
                    "conversation_id": (conversation_id),
                    "model_id": model_id,
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                error=error,
            )

            terminal_event_emitted = True

            yield self._error_event(
                error=error,
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
                sequence=sequence,
            )

        except ModelError as exc:
            error = self._translate_model_error(
                exc,
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                model_id=model_id,
            )

            await self._persist_failure(
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                error=error,
            )

            terminal_event_emitted = True

            yield self._error_event(
                error=error,
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
                sequence=sequence,
            )

        except ChatServiceError as exc:
            await self._persist_failure(
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                error=exc,
            )

            terminal_event_emitted = True

            yield self._error_event(
                error=exc,
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
                sequence=sequence,
            )

        except Exception as exc:
            _log_exception(
                "Unexpected chat stream failure",
                chat_event=("stream-unexpected-failure"),
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
                error_type=(exc.__class__.__name__),
                error_message=str(
                    exc,
                ),
            )

            error = ChatGenerationError(
                "Beim Erzeugen der Chat-Antwort ist ein unerwarteter Fehler aufgetreten.",
                request_id=(context.request_id),
                details={
                    "conversation_id": (conversation_id),
                    "model_id": model_id,
                    "error_type": (exc.__class__.__name__),
                },
                cause=exc,
            )

            await self._persist_failure(
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                error=error,
            )

            terminal_event_emitted = True

            yield self._error_event(
                error=error,
                request_id=(context.request_id),
                conversation_id=(conversation_id),
                message_id=(assistant_message_id),
                model_id=model_id,
                sequence=sequence,
            )

        finally:
            if not terminal_event_emitted:
                _log_warning(
                    "Chat stream ended without terminal event",
                    chat_event=("stream-without-terminal-event"),
                    request_id=(context.request_id),
                    conversation_id=(conversation_id),
                    message_id=(assistant_message_id),
                    model_id=model_id,
                )

    async def stream_sse(
        self,
        request: ChatRequest,
        *,
        context: ChatServiceContext,
    ) -> AsyncIterator[str]:
        """
        Übergangskompatibilität.

        Neue API-Endpunkte sollten `stream()` verwenden und selbst einen
        versionierten SSE-Umschlag erzeugen.
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

        system_prompt = request.system_prompt or self._default_system_prompt

        if system_prompt:
            messages.append(
                ChatMessage(
                    role=(MessageRole.SYSTEM),
                    content=system_prompt,
                ),
            )

        if request.conversation_id is not None:
            history_result = self._history_provider.get_history(
                conversation_id=(conversation_id),
                context=context,
            )

            if inspect.isawaitable(
                history_result,
            ):
                persisted_history = await history_result
            else:
                persisted_history = history_result

            if len(persisted_history) > MAX_CHAT_HISTORY_MESSAGES:
                raise InvalidChatRequestError(
                    "Der gespeicherte Chat-Verlauf enthält zu viele Nachrichten.",
                    request_id=(context.request_id),
                    details={
                        "maximum_messages": (MAX_CHAT_HISTORY_MESSAGES),
                        "actual_messages": len(
                            persisted_history,
                        ),
                    },
                )

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
            if (request.max_output_tokens is not None)
            else (self._default_max_output_tokens)
        )

        metadata: JsonObject = {
            **dict(
                request.metadata,
            ),
            "request_id": (context.request_id),
            "conversation_id": (conversation_id),
            "tenant_id": (context.tenant_id),
            "user_id": context.user_id,
            "session_id": (context.session_id),
        }

        return GenerationRequest(
            model=model_id,
            messages=list(
                messages,
            ),
            temperature=(
                request.temperature
                if (request.temperature is not None)
                else (self._default_temperature)
            ),
            max_tokens=max_tokens,
            tools=list(
                request.tools,
            ),
            metadata=metadata,
        )

    async def _resolve_model_id(
        self,
        request: ChatRequest,
        context: ChatServiceContext,
    ) -> str:
        if request.model_id is not None:
            model_id = request.model_id

        elif self._model_resolver is not None:
            resolver_result = self._model_resolver(
                request,
                context,
            )

            if inspect.isawaitable(
                resolver_result,
            ):
                model_id = await resolver_result
            else:
                model_id = resolver_result

        elif self._default_model_id is not None:
            model_id = self._default_model_id

        else:
            raise InvalidChatRequestError(
                "Für die Chat-Anfrage konnte kein Modell bestimmt werden.",
                request_id=(context.request_id),
            )

        normalized = model_id.strip().lower()

        if not normalized:
            raise InvalidChatRequestError(
                "Die ermittelte Modell-ID ist leer.",
                request_id=(context.request_id),
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
        """
        Übersetzt den stabilen Modell-Stream-Vertrag in Chat-Ereignisse.

        START und COMPLETE werden nicht erneut als Chat-Ereignisse ausgegeben,
        weil der ChatService selbst bereits ein START- und ein abschließendes
        COMPLETE-Ereignis erzeugt.
        """

        event_type_value = _event_type_value(
            model_event.type,
        )

        payload = self._stream_event_payload(
            model_event,
        )

        if event_type_value == StreamEventType.START.value:
            return ()

        if event_type_value == StreamEventType.TOKEN.value:
            text = _extract_text(
                payload,
            )

            safe_payload = {
                key: value
                for key, value in payload.items()
                if key != "created_at_monotonic"
            }

            safe_payload["text"] = text

            return (
                ChatStreamEvent(
                    event=ChatEventType.TOKEN,
                    sequence=start_sequence,
                    data=safe_payload,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                ),
            )

        if event_type_value == StreamEventType.MESSAGE.value:
            text = _extract_text(
                payload,
            )

            safe_payload = {
                key: value
                for key, value in payload.items()
                if key != "created_at_monotonic"
            }

            safe_payload["content"] = text

            return (
                ChatStreamEvent(
                    event=ChatEventType.MESSAGE,
                    sequence=start_sequence,
                    data=safe_payload,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                ),
            )

        if event_type_value == StreamEventType.REASONING.value:
            return (
                ChatStreamEvent(
                    event=ChatEventType.REASONING,
                    sequence=start_sequence,
                    data=payload,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                ),
            )

        if event_type_value == StreamEventType.TOOL_CALL.value:
            return (
                ChatStreamEvent(
                    event=ChatEventType.TOOL_CALL,
                    sequence=start_sequence,
                    data=payload,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                ),
            )

        if event_type_value == StreamEventType.TOOL_RESULT.value:
            return (
                ChatStreamEvent(
                    event=ChatEventType.TOOL_RESULT,
                    sequence=start_sequence,
                    data=payload,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                ),
            )

        if event_type_value == StreamEventType.USAGE.value:
            raw_usage = payload.get(
                "usage",
            )

            if raw_usage is None:
                return ()

            normalized_usage = _normalize_json_object(
                raw_usage,
            )

            return (
                ChatStreamEvent(
                    event=ChatEventType.USAGE,
                    sequence=start_sequence,
                    data={
                        "usage": normalized_usage,
                    },
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                ),
            )

        if event_type_value == StreamEventType.COMPLETE.value:
            # Das öffentliche COMPLETE-Ereignis wird nach Ende des
            # Modellstreams zentral durch ChatService.stream() erzeugt.
            return ()

        if event_type_value == StreamEventType.HEARTBEAT.value:
            return (
                ChatStreamEvent(
                    event=ChatEventType.HEARTBEAT,
                    sequence=start_sequence,
                    data=payload,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    model_id=model_id,
                ),
            )

        if event_type_value == StreamEventType.ERROR.value:
            # ERROR wird bereits vor dem Mapping in stream() behandelt.
            return ()

        _log_warning(
            "Unsupported model stream event ignored",
            chat_event="unsupported-model-event",
            request_id=request_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model_id=model_id,
            model_event_type=event_type_value,
        )

        return ()

    @staticmethod
    def _stream_event_payload(
        model_event: StreamEvent,
    ) -> JsonObject:
        payload: JsonObject = {}

        attribute_names: tuple[
            str,
            ...,
        ] = (
            "text",
            "content",
            "delta",
            "message",
            "finish_reason",
            "usage",
            "metadata",
            "data",
            "error",
            "tool_call",
            "tool_result",
            "reasoning",
        )

        # Use a dictionary comprehension to build the payload from attributes
        payload = {
            attr: _normalize_json_value(getattr(model_event, attr))
            for attr in attribute_names
            if hasattr(model_event, attr) and getattr(model_event, attr) is not None
        }

        # Special handling for nested structures that need explicit normalization/merging
        metadata = getattr(model_event, "metadata", None)
        if metadata is not None:
            payload["metadata"] = _normalize_json_object(metadata)

        data = getattr(model_event, "data", None)
        if data is not None:
            payload["data"] = _normalize_json_object(data)

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

        finish_reason = payload.get("finish_reason")
        if not isinstance(finish_reason, str):
            finish_reason = None

        usage = payload.get("usage")
        if not isinstance(usage, Mapping):
            usage = None

        metadata = payload.get("metadata")
        if not isinstance(metadata, Mapping):
            metadata = {}

        return ChatResponse(
            request_id=request_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model_id=model_id,
            content=_extract_text(payload),
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
            conversation_id=(conversation_id),
            message_id=message_id,
            model_id=model_id,
            sequence=sequence,
            data=error.to_dict(),
        )

    @staticmethod
    def _translate_model_error(
        error: ModelError,
        *,
        request_id: str,
        conversation_id: str,
        model_id: str,
    ) -> ChatGenerationError:
        error_code_value: object = getattr(
            error,
            "code",
            "MODEL_ERROR",
        )

        return ChatGenerationError(
            str(
                error,
            ),
            request_id=request_id,
            details={
                "conversation_id": (conversation_id),
                "model_id": model_id,
                "model_error_code": str(
                    error_code_value,
                ),
            },
            cause=error,
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
                        conversation_id=(conversation_id),
                        user_id=(context.user_id),
                        tenant_id=(context.tenant_id),
                        model_id=model_id,
                        metadata={
                            **dict(
                                request.metadata,
                            ),
                            "request_id": (context.request_id),
                        },
                    ),
                )

            await self._await_if_needed(
                self._repository.append_user_message(
                    conversation_id=(conversation_id),
                    message_id=(user_message_id),
                    parent_message_id=(request.parent_message_id),
                    content=(request.message),
                    metadata={
                        **dict(
                            request.metadata,
                        ),
                        "request_id": (context.request_id),
                    },
                ),
            )

        except ChatServiceError:
            raise

        except Exception as exc:
            raise ChatPersistenceError(
                "Die Benutzeranfrage konnte nicht gespeichert werden.",
                request_id=(context.request_id),
                details={
                    "conversation_id": (conversation_id),
                    "error_type": (exc.__class__.__name__),
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
                    conversation_id=(response.conversation_id),
                    message_id=(response.message_id),
                    parent_message_id=(request.parent_message_id),
                    model_id=(response.model_id),
                    content=(response.content),
                    finish_reason=(response.finish_reason),
                    usage=response.usage,
                    metadata=(response.metadata),
                ),
            )

        except Exception as exc:
            _log_exception(
                "Assistant response persistence failed",
                chat_event=("assistant-persistence-failed"),
                request_id=(response.request_id),
                conversation_id=(response.conversation_id),
                message_id=(response.message_id),
                error_type=(exc.__class__.__name__),
                error_message=str(
                    exc,
                ),
            )

            raise ChatPersistenceError(
                "Die erzeugte Chat-Antwort konnte nicht gespeichert werden.",
                request_id=(response.request_id),
                details={
                    "conversation_id": (response.conversation_id),
                    "message_id": (response.message_id),
                    "error_type": (exc.__class__.__name__),
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
                    conversation_id=(conversation_id),
                    message_id=message_id,
                    error_code=error.code,
                    error_message=(error.message),
                    metadata={
                        "request_id": (error.request_id),
                        "details": dict(
                            error.details,
                        ),
                    },
                ),
            )

        except Exception as exc:
            _log_exception(
                "Could not persist failed assistant message",
                chat_event=("failure-persistence-failed"),
                conversation_id=(conversation_id),
                message_id=message_id,
                error_code=error.code,
                persistence_error_type=(exc.__class__.__name__),
                persistence_error_message=str(
                    exc,
                ),
            )

    # ========================================================
    # Hilfsmethoden
    # ========================================================

    @staticmethod
    async def _await_if_needed(
        value: Awaitable[None] | None,
    ) -> None:
        if value is None:
            return

        if inspect.isawaitable(
            value,
        ):
            await value
            return

        raise TypeError(
            "Die Repository-Methode hat einen ungültigen Rückgabewert geliefert.",
        )

    @staticmethod
    def _new_id(
        prefix: str,
    ) -> str:
        normalized_prefix = prefix.strip().lower()

        if not normalized_prefix:
            raise ValueError(
                "Der ID-Präfix darf nicht leer sein.",
            )

        return f"{normalized_prefix}_{uuid4().hex}"


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
