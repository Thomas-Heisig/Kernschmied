# F:\Kernschmied\backend\app\api\v1\chat.py

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Mapping,
)
from enum import StrEnum
from typing import (
    Literal,
    Protocol,
    cast,
    runtime_checkable,
)
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
)

logger = logging.getLogger(__name__)

router = APIRouter()

CHAT_STREAM_SCHEMA_VERSION = "1.1"
MAX_MESSAGE_LENGTH = 32_000
MAX_TOOL_COUNT = 100
DEFAULT_SSE_RETRY_MILLISECONDS = 3_000

JsonObject = dict[str, JsonValue]


class ChatStreamEventType(StrEnum):
    START = "chat.start"
    TOKEN = "chat.token"
    MESSAGE = "chat.message"
    REASONING = "chat.reasoning"
    TOOL_CALL = "chat.tool_call"
    TOOL_RESULT = "chat.tool_result"
    USAGE = "chat.usage"
    COMPLETE = "chat.complete"
    ERROR = "chat.error"
    HEARTBEAT = "chat.heartbeat"


class ChatFinishReason(StrEnum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALL = "tool_call"
    CANCELLED = "cancelled"
    ERROR = "error"


class InternalChatEventType(StrEnum):
    TOKEN = "token"
    MESSAGE = "message"
    REASONING = "reasoning"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    USAGE = "usage"
    COMPLETE = "complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class ChatRequest(BaseModel):
    """
    Eingabevertrag für eine Chat-Anfrage.

    Modell- und Tool-IDs sind ausschließlich Benutzerwünsche. Auswahl,
    Freigabe und Autorisierung erfolgen serverseitig.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    message: str = Field(
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        description="Nachricht des Benutzers.",
    )

    conversation_id: UUID | None = Field(
        default=None,
        description="Bestehende Unterhaltung, falls vorhanden.",
    )

    hierarchy_node_id: UUID | None = Field(
        default=None,
        description="Aktiver generischer Hierarchieknoten.",
    )

    model_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Optional angefordertes Modell.",
    )

    tool_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_TOOL_COUNT,
        description="Optional angeforderte Tool-IDs.",
    )

    metadata: JsonObject = Field(
        default_factory=dict,
        description="Nicht sicherheitskritische Client-Metadaten.",
    )

    @field_validator("message")
    @classmethod
    def validate_message(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Die Nachricht darf nicht leer sein.",
            )

        return normalized

    @field_validator("model_id")
    @classmethod
    def normalize_model_id(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    @field_validator("tool_ids")
    @classmethod
    def normalize_tool_ids(
        cls,
        values: list[str],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = value.strip()

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(normalized)

        return result


class ChatServiceRequest(BaseModel):
    """
    Interner, API-unabhängiger Eingabevertrag für den ChatService.

    Diese Struktur bildet die stabile Grenze zwischen API und Fachservice.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    message: str
    conversation_id: UUID
    hierarchy_node_id: UUID | None = None
    requested_model_id: str | None = None
    requested_tool_ids: list[str] = Field(
        default_factory=list,
    )
    metadata: JsonObject = Field(
        default_factory=dict,
    )
    request_id: str
    user_id: str | None = None


class StreamContext(BaseModel):
    """
    Serverseitig erzeugter Kontext eines Streaming-Durchlaufs.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    stream_id: UUID
    request_id: str
    conversation_id: UUID
    user_id: str | None = None


class StreamStartData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: str = CHAT_STREAM_SCHEMA_VERSION
    stream_id: UUID
    request_id: str
    conversation_id: UUID
    model_id: str | None = None


class StreamTokenData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    content: str
    index: int = Field(
        ge=0,
    )


class StreamMessageData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    content: str
    role: Literal["assistant"] = "assistant"


class StreamReasoningData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    content: str
    index: int = Field(
        ge=0,
    )


class StreamToolCallData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    call_id: str
    tool_id: str
    arguments: JsonObject = Field(
        default_factory=dict,
    )


class StreamToolResultData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    call_id: str
    tool_id: str
    success: bool
    output: JsonValue = None


class StreamUsageData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    input_tokens: int | None = Field(
        default=None,
        ge=0,
    )
    output_tokens: int | None = Field(
        default=None,
        ge=0,
    )
    total_tokens: int | None = Field(
        default=None,
        ge=0,
    )


class StreamCompleteData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    stream_id: UUID
    request_id: str
    conversation_id: UUID
    token_count: int = Field(
        ge=0,
    )
    finish_reason: ChatFinishReason
    model_id: str | None = None


class StreamErrorData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    code: str
    message: str
    details: JsonObject = Field(
        default_factory=dict,
    )
    request_id: str
    stream_id: UUID
    retryable: bool = False


class StreamHeartbeatData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    stream_id: UUID


class InternalChatEvent(BaseModel):
    """
    Generischer interner Ereignisvertrag.

    Ein zukünftiger ChatService kann direkt diese Ereignisse liefern.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    type: InternalChatEventType
    content: str | None = None
    model_id: str | None = None
    finish_reason: ChatFinishReason | None = None
    call_id: str | None = None
    tool_id: str | None = None
    arguments: JsonObject = Field(
        default_factory=dict,
    )
    output: JsonValue = None
    success: bool | None = None
    usage: StreamUsageData | None = None
    error_code: str | None = None
    error_message: str | None = None
    error_details: JsonObject = Field(
        default_factory=dict,
    )
    retryable: bool = False


@runtime_checkable
class ChatStreamingService(Protocol):
    """
    Minimaler Vertrag für einen zukünftigen produktiven ChatService.
    """

    def stream(
        self,
        request: ChatServiceRequest,
    ) -> AsyncIterator[InternalChatEvent]:
        ...


def require_chat_service(
    request: Request,
) -> object:
    """
    Liefert den registrierten produktiven ChatService.

    Ist kein Service registriert, wird eine strukturierte
    HTTP-503-Antwort ausgelöst.
    """

    service = get_chat_service(
        request,
    )

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "CHAT_SERVICE_UNAVAILABLE",
                "message": (
                    "Der Chat-Dienst ist derzeit nicht verfügbar."
                ),
                "details": {},
                "request_id": get_request_id(
                    request,
                ),
            },
        )

    return service


def get_request_id(
    request: Request,
) -> str:
    """
    Verwendet die Request-ID aus der Middleware oder erzeugt einen
    Ersatzwert.
    """

    request_id: object = getattr(
        request.state,
        "request_id",
        None,
    )

    if request_id is not None:
        normalized = str(request_id).strip()

        if normalized:
            return normalized

    return str(uuid4())


def get_current_user_id(
    request: Request,
) -> str | None:
    """
    Liest die Benutzer-ID aus dem von der Auth-Middleware erzeugten
    Principal.
    """

    principal: object = getattr(
        request.state,
        "user",
        None,
    )

    if principal is None:
        principal = getattr(
            request.state,
            "principal",
            None,
        )

    if principal is None:
        return None

    if isinstance(principal, Mapping):
        typed_principal = cast(
            Mapping[object, object],
            principal,
        )

        raw_user_id = typed_principal.get(
            "id",
        )

        if raw_user_id is None:
            raw_user_id = typed_principal.get(
                "user_id",
            )

        if raw_user_id is None:
            raw_user_id = typed_principal.get(
                "subject",
            )
    else:
        raw_user_id = getattr(
            principal,
            "id",
            None,
        )

        if raw_user_id is None:
            raw_user_id = getattr(
                principal,
                "user_id",
                None,
            )

        if raw_user_id is None:
            raw_user_id = getattr(
                principal,
                "subject",
                None,
            )

    if raw_user_id is None:
        return None

    normalized = str(raw_user_id).strip()

    return normalized or None


def encode_sse(
    event: ChatStreamEventType | str,
    data: BaseModel | JsonObject | None = None,
    *,
    event_id: str | None = None,
    retry: int | None = None,
) -> str:
    """
    Kodiert ein einzelnes Server-Sent Event als JSON.
    """

    lines: list[str] = []

    if event_id is not None:
        lines.append(
            f"id: {event_id}",
        )

    if retry is not None:
        lines.append(
            f"retry: {max(retry, 0)}",
        )

    lines.append(
        f"event: {str(event)}",
    )

    if isinstance(data, BaseModel):
        raw_payload = data.model_dump(
            mode="json",
            exclude_none=True,
        )

        payload = cast(
            JsonObject,
            raw_payload,
        )

    elif data is None:
        payload = {}

    else:
        payload = data

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    serialized_lines = serialized.splitlines()

    if not serialized_lines:
        serialized_lines = [
            "{}",
        ]

    for line in serialized_lines:
        lines.append(
            f"data: {line}",
        )

    return "\n".join(lines) + "\n\n"


def create_stream_context(
    request: Request,
    payload: ChatRequest,
) -> StreamContext:
    return StreamContext(
        stream_id=uuid4(),
        request_id=get_request_id(
            request,
        ),
        conversation_id=(
            payload.conversation_id
            or uuid4()
        ),
        user_id=get_current_user_id(
            request,
        ),
    )


def create_service_request(
    payload: ChatRequest,
    context: StreamContext,
) -> ChatServiceRequest:
    return ChatServiceRequest(
        message=payload.message,
        conversation_id=context.conversation_id,
        hierarchy_node_id=payload.hierarchy_node_id,
        requested_model_id=payload.model_id,
        requested_tool_ids=list(
            payload.tool_ids,
        ),
        metadata=dict(
            payload.metadata,
        ),
        request_id=context.request_id,
        user_id=context.user_id,
    )


def get_chat_service(
    request: Request,
) -> object | None:
    """
    Ermittelt den produktiven ChatService aus dem Application State.

    Ein fehlender Service wird nicht durch einen Demo-Adapter ersetzt.
    """

    service: object = getattr(
        request.app.state,
        "chat_service",
        None,
    )

    return service


async def resolve_maybe_awaitable(
    value: object,
) -> object:
    if inspect.isawaitable(value):
        return await cast(
            Awaitable[object],
            value,
        )

    return value


async def stream_from_service(
    service: object,
    service_request: ChatServiceRequest,
) -> AsyncIterator[InternalChatEvent]:
    """
    Ruft einen registrierten ChatService über seinen stabilen
    `stream()`-Vertrag auf.
    """

    stream_method_value: object = getattr(
        service,
        "stream",
        None,
    )

    if not callable(stream_method_value):
        raise RuntimeError(
            "Der registrierte ChatService besitzt keine "
            "aufrufbare stream()-Methode.",
        )

    raw_stream = stream_method_value(
        service_request,
    )

    resolved_stream = await resolve_maybe_awaitable(
        raw_stream,
    )

    if not hasattr(
        resolved_stream,
        "__aiter__",
    ):
        raise RuntimeError(
            "ChatService.stream() muss einen AsyncIterator liefern.",
        )

    async_iterator = cast(
        AsyncIterator[object],
        resolved_stream,
    )

    async for raw_event in async_iterator:
        if isinstance(
            raw_event,
            InternalChatEvent,
        ):
            yield raw_event
            continue

        if isinstance(
            raw_event,
            str,
        ):
            if raw_event:
                yield InternalChatEvent(
                    type=InternalChatEventType.TOKEN,
                    content=raw_event,
                )
            continue

        if isinstance(
            raw_event,
            BaseModel,
        ):
            event_data = raw_event.model_dump(
                mode="python",
            )

            yield InternalChatEvent.model_validate(
                event_data,
            )
            continue

        if isinstance(
            raw_event,
            Mapping,
        ):
            typed_mapping = cast(
                Mapping[object, object],
                raw_event,
            )

            normalized_mapping: dict[str, object] = {
                str(key): value
                for key, value in typed_mapping.items()
            }

            yield InternalChatEvent.model_validate(
                normalized_mapping,
            )
            continue

        raise TypeError(
            "Der ChatService lieferte einen nicht unterstützten "
            f"Ereignistyp: {type(raw_event).__name__}.",
        )


async def get_internal_chat_events(
    request: Request,
    service_request: ChatServiceRequest,
) -> AsyncIterator[InternalChatEvent]:
    """
    Liefert ausschließlich Ereignisse des produktiven ChatService.

    Ein Demo-Fallback ist bewusst nicht mehr vorgesehen.
    """

    service = require_chat_service(
        request,
    )

    async for event in stream_from_service(
        service,
        service_request,
    ):
        yield event


def create_error_event(
    *,
    context: StreamContext,
    code: str,
    message: str,
    details: JsonObject | None = None,
    retryable: bool = False,
) -> str:
    return encode_sse(
        event=ChatStreamEventType.ERROR,
        data=StreamErrorData(
            code=code,
            message=message,
            details=details or {},
            request_id=context.request_id,
            stream_id=context.stream_id,
            retryable=retryable,
        ),
        event_id=f"{context.stream_id}:error",
    )


async def generate_chat_events(
    request: Request,
    payload: ChatRequest,
    context: StreamContext,
) -> AsyncIterator[str]:
    """
    Übersetzt interne ChatService-Ereignisse in den versionierten
    SSE-Vertrag der HTTP-API.
    """

    token_count = 0
    reasoning_count = 0
    completed = False
    resolved_model_id = payload.model_id

    service_request = create_service_request(
        payload,
        context,
    )

    yield encode_sse(
        event=ChatStreamEventType.START,
        data=StreamStartData(
            stream_id=context.stream_id,
            request_id=context.request_id,
            conversation_id=context.conversation_id,
            model_id=payload.model_id,
        ),
        event_id=f"{context.stream_id}:start",
        retry=DEFAULT_SSE_RETRY_MILLISECONDS,
    )

    try:
        async for event in get_internal_chat_events(
            request,
            service_request,
        ):
            if await request.is_disconnected():
                logger.info(
                    "Chat stream disconnected",
                    extra={
                        "request_id": context.request_id,
                        "stream_id": str(
                            context.stream_id,
                        ),
                        "conversation_id": str(
                            context.conversation_id,
                        ),
                    },
                )
                return

            if event.model_id is not None:
                resolved_model_id = event.model_id

            if event.type == InternalChatEventType.TOKEN:
                content = event.content or ""

                if not content:
                    continue

                yield encode_sse(
                    event=ChatStreamEventType.TOKEN,
                    data=StreamTokenData(
                        content=content,
                        index=token_count,
                    ),
                    event_id=(
                        f"{context.stream_id}:"
                        f"token:{token_count}"
                    ),
                )

                token_count += 1
                continue

            if event.type == InternalChatEventType.MESSAGE:
                content = event.content or ""

                if not content:
                    continue

                yield encode_sse(
                    event=ChatStreamEventType.MESSAGE,
                    data=StreamMessageData(
                        content=content,
                    ),
                    event_id=(
                        f"{context.stream_id}:message"
                    ),
                )
                continue

            if event.type == InternalChatEventType.REASONING:
                content = event.content or ""

                if not content:
                    continue

                yield encode_sse(
                    event=ChatStreamEventType.REASONING,
                    data=StreamReasoningData(
                        content=content,
                        index=reasoning_count,
                    ),
                    event_id=(
                        f"{context.stream_id}:"
                        f"reasoning:{reasoning_count}"
                    ),
                )

                reasoning_count += 1
                continue

            if event.type == InternalChatEventType.TOOL_CALL:
                if (
                    event.call_id is None
                    or event.tool_id is None
                ):
                    logger.warning(
                        "Invalid tool call event",
                        extra={
                            "request_id": context.request_id,
                            "stream_id": str(
                                context.stream_id,
                            ),
                        },
                    )
                    continue

                yield encode_sse(
                    event=ChatStreamEventType.TOOL_CALL,
                    data=StreamToolCallData(
                        call_id=event.call_id,
                        tool_id=event.tool_id,
                        arguments=event.arguments,
                    ),
                    event_id=(
                        f"{context.stream_id}:"
                        f"tool-call:{event.call_id}"
                    ),
                )
                continue

            if event.type == InternalChatEventType.TOOL_RESULT:
                if (
                    event.call_id is None
                    or event.tool_id is None
                ):
                    logger.warning(
                        "Invalid tool result event",
                        extra={
                            "request_id": context.request_id,
                            "stream_id": str(
                                context.stream_id,
                            ),
                        },
                    )
                    continue

                yield encode_sse(
                    event=ChatStreamEventType.TOOL_RESULT,
                    data=StreamToolResultData(
                        call_id=event.call_id,
                        tool_id=event.tool_id,
                        success=bool(
                            event.success,
                        ),
                        output=event.output,
                    ),
                    event_id=(
                        f"{context.stream_id}:"
                        f"tool-result:{event.call_id}"
                    ),
                )
                continue

            if event.type == InternalChatEventType.USAGE:
                if event.usage is None:
                    continue

                yield encode_sse(
                    event=ChatStreamEventType.USAGE,
                    data=event.usage,
                    event_id=(
                        f"{context.stream_id}:usage"
                    ),
                )
                continue

            if event.type == InternalChatEventType.HEARTBEAT:
                yield encode_sse(
                    event=ChatStreamEventType.HEARTBEAT,
                    data=StreamHeartbeatData(
                        stream_id=context.stream_id,
                    ),
                    event_id=(
                        f"{context.stream_id}:heartbeat"
                    ),
                )
                continue

            if event.type == InternalChatEventType.ERROR:
                yield create_error_event(
                    context=context,
                    code=(
                        event.error_code
                        or "CHAT_STREAM_FAILED"
                    ),
                    message=(
                        event.error_message
                        or (
                            "Die Chat-Antwort konnte nicht "
                            "vollständig erzeugt werden."
                        )
                    ),
                    details=event.error_details,
                    retryable=event.retryable,
                )
                return

            if event.type == InternalChatEventType.COMPLETE:
                finish_reason = (
                    event.finish_reason
                    or ChatFinishReason.STOP
                )

                yield encode_sse(
                    event=ChatStreamEventType.COMPLETE,
                    data=StreamCompleteData(
                        stream_id=context.stream_id,
                        request_id=context.request_id,
                        conversation_id=(
                            context.conversation_id
                        ),
                        token_count=token_count,
                        finish_reason=finish_reason,
                        model_id=resolved_model_id,
                    ),
                    event_id=(
                        f"{context.stream_id}:complete"
                    ),
                )

                completed = True
                return

        if not completed:
            yield encode_sse(
                event=ChatStreamEventType.COMPLETE,
                data=StreamCompleteData(
                    stream_id=context.stream_id,
                    request_id=context.request_id,
                    conversation_id=context.conversation_id,
                    token_count=token_count,
                    finish_reason=ChatFinishReason.STOP,
                    model_id=resolved_model_id,
                ),
                event_id=f"{context.stream_id}:complete",
            )

    except asyncio.CancelledError:
        logger.info(
            "Chat stream cancelled",
            extra={
                "request_id": context.request_id,
                "stream_id": str(
                    context.stream_id,
                ),
                "conversation_id": str(
                    context.conversation_id,
                ),
            },
        )
        raise

    except Exception:
        logger.exception(
            "Unhandled chat streaming error",
            extra={
                "request_id": context.request_id,
                "stream_id": str(
                    context.stream_id,
                ),
                "conversation_id": str(
                    context.conversation_id,
                ),
            },
        )

        yield create_error_event(
            context=context,
            code="CHAT_STREAM_FAILED",
            message=(
                "Die Chat-Antwort konnte nicht vollständig "
                "erzeugt werden."
            ),
            details={},
            retryable=False,
        )


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Chat-Antwort streamen",
    description=(
        "Erzeugt eine Chat-Antwort als versionierten "
        "Server-Sent-Events-Datenstrom."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": (
                "SSE-Datenstrom wurde gestartet."
            ),
            "content": {
                "text/event-stream": {
                    "schema": {
                        "type": "string",
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": (
                "Die Chat-Anfrage ist ungültig."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": (
                "Der produktive ChatService ist nicht verfügbar."
            ),
        },
    },
)
async def stream_chat(
    request: Request,
    payload: ChatRequest,
) -> StreamingResponse:
    """
    Startet einen SSE-Chat-Datenstrom.

    Der Endpunkt verwendet den unter
    `request.app.state.chat_service` registrierten produktiven Service.

    Ist kein ChatService registriert, wird der Stream mit einem
    strukturierten Fehlerereignis beziehungsweise HTTP 503 abgelehnt.
    """

    # Frühzeitiger Check – wirft HTTP 503, bevor die StreamingResponse startet
    require_chat_service(
        request,
    )

    context = create_stream_context(
        request=request,
        payload=payload,
    )

    return StreamingResponse(
        generate_chat_events(
            request=request,
            payload=payload,
            context=context,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": (
                "no-cache, no-store, must-revalidate"
            ),
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Request-ID": context.request_id,
            "X-Chat-Stream-ID": str(
                context.stream_id,
            ),
            "X-Chat-Schema-Version": (
                CHAT_STREAM_SCHEMA_VERSION
            ),
        },
    )