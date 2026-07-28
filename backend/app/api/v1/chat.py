# F:\Kernschmied\backend\app\api\v1\chat.py

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Mapping
from enum import StrEnum
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator

from app.models.errors import ModelError
from app.models.service import ModelAccessContext
from app.services.chat_service import (
    ChatService,
    ChatRequest as ServiceChatRequest,
    ChatServiceContext,
    ChatStreamEvent,
    ChatEventType,  # <-- NEU: Import für typsichere Event-Vergleiche
)

# Pylance considers this import used
assert ChatStreamEvent

logger = logging.getLogger(__name__)

router = APIRouter()

CHAT_STREAM_SCHEMA_VERSION = "1.1"
MAX_MESSAGE_LENGTH = 32_000
MAX_TOOL_COUNT = 100
DEFAULT_SSE_RETRY_MILLISECONDS = 3_000

JsonScalar = str | int | float | bool | None
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


class ChatRequest(BaseModel):
    """
    Eingabevertrag für eine Chat-Anfrage (API-Ebene).

    Modell- und Tool-IDs sind ausschließlich Benutzerwünsche. Auswahl,
    Freigabe und Autorisierung erfolgen serverseitig.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        description="Nachricht des Benutzers.",
    )

    conversation_id: str | None = Field(
        default=None,
        description="Bestehende Unterhaltung, falls vorhanden.",
    )

    hierarchy_node_id: str | None = Field(
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
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Die Nachricht darf nicht leer sein.")
        return normalized

    @field_validator("model_id")
    @classmethod
    def normalize_model_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("tool_ids")
    @classmethod
    def normalize_tool_ids(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = value.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result


class StreamContext(BaseModel):
    """
    Serverseitig erzeugter Kontext eines Streaming-Durchlaufs.
    """

    model_config = ConfigDict(extra="forbid")

    stream_id: UUID
    request_id: str
    conversation_id: str
    user_id: str | None = None


class StreamStartData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = CHAT_STREAM_SCHEMA_VERSION
    stream_id: UUID
    request_id: str
    conversation_id: str
    model_id: str | None = None


class StreamTokenData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    index: int = Field(ge=0)


class StreamMessageData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    role: Literal["assistant"] = "assistant"


class StreamReasoningData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    index: int = Field(ge=0)


class StreamToolCallData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_id: str
    tool_id: str
    arguments: JsonObject = Field(default_factory=dict)


class StreamToolResultData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_id: str
    tool_id: str
    success: bool
    output: JsonValue = None


class StreamUsageData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class StreamCompleteData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stream_id: UUID
    request_id: str
    conversation_id: str
    token_count: int = Field(ge=0)
    finish_reason: ChatFinishReason
    model_id: str | None = None


class StreamErrorData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: JsonObject = Field(default_factory=dict)
    request_id: str
    stream_id: UUID
    retryable: bool = False


class StreamHeartbeatData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stream_id: UUID


# ============================================================================
# Hilfsfunktionen für Request/Response
# ============================================================================


def get_request_id(request: Request) -> str:
    request_id: object = getattr(request.state, "request_id", None)
    if request_id is not None:
        normalized = str(request_id).strip()
        if normalized:
            return normalized
    return str(uuid4())


def get_current_user_id(request: Request) -> str | None:
    principal: object = getattr(request.state, "user", None)
    if principal is None:
        principal = getattr(request.state, "principal", None)
    if principal is None:
        return None

    if isinstance(principal, Mapping):
        typed = cast(Mapping[object, object], principal)
        raw_user_id = typed.get("id") or typed.get("user_id") or typed.get("subject")
    else:
        raw_user_id = getattr(principal, "id", None) or getattr(
            principal, "user_id", None
        ) or getattr(principal, "subject", None)

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
    """Kodiert ein einzelnes Server-Sent Event als JSON."""
    lines: list[str] = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    if retry is not None:
        lines.append(f"retry: {max(retry, 0)}")
    lines.append(f"event: {str(event)}")

    if isinstance(data, BaseModel):
        payload = cast(JsonObject, data.model_dump(mode="json", exclude_none=True))
    elif data is None:
        payload = {}
    else:
        payload = data

    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    serialized_lines = serialized.splitlines() or ["{}"]
    for line in serialized_lines:
        lines.append(f"data: {line}")

    return "\n".join(lines) + "\n\n"


def create_stream_context(request: Request, payload: ChatRequest) -> StreamContext:
    return StreamContext(
        stream_id=uuid4(),
        request_id=get_request_id(request),
        conversation_id=payload.conversation_id or str(uuid4()),
        user_id=get_current_user_id(request),
    )


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


def get_chat_service(request: Request) -> object | None:
    return getattr(request.app.state, "chat_service", None)


def require_chat_service(request: Request) -> ChatService:
    service = get_chat_service(request)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "CHAT_SERVICE_UNAVAILABLE",
                "message": "Der Chat-Dienst ist derzeit nicht verfügbar.",
                "details": {},
                "request_id": get_request_id(request),
            },
        )
    return cast(ChatService, service)


# ============================================================================
# SSE-Generator
# ============================================================================


async def generate_chat_events(
    request: Request,
    payload: ChatRequest,
    context: StreamContext,
) -> AsyncIterator[str]:
    """
    Übersetzt ChatService-Ereignisse in SSE-Datenströme.
    """
    logger.info(
        "Generating chat events",
        extra={
            "request_id": context.request_id,
            "stream_id": str(context.stream_id),
            "model_id": payload.model_id,
        },
    )

    service = require_chat_service(request)

    # ------------------------------------------------------------
    # API-Request in Service-Request umwandeln
    # Korrektur: conversation_id aus context übernehmen
    # ------------------------------------------------------------
    service_request = ServiceChatRequest(
        message=payload.message,
        model_id=payload.model_id,
        conversation_id=context.conversation_id,  # <-- geändert
        parent_message_id=None,
        system_prompt=None,
        history=(),
        temperature=None,
        max_output_tokens=None,
        stream=True,
        tools=(),
        metadata=dict(payload.metadata),
    )

    service_context = ChatServiceContext(
        request_id=context.request_id,
        access=ModelAccessContext(
            request_id=context.request_id,
            user_id=context.user_id,
        ),
        user_id=context.user_id,
    )

    token_count = 0
    terminal_received = False  # <-- statt completed
    resolved_model_id: str | None = payload.model_id

    try:
        logger.info(
            "Creating service stream",
            extra={
                "request_id": context.request_id,
                "stream_id": str(context.stream_id),
            },
        )

        async for chat_event in service.stream(
            request=service_request,
            context=service_context,
        ):
            logger.debug(
                "Received chat event",
                extra={
                    "request_id": context.request_id,
                    "stream_id": str(context.stream_id),
                    "event_type": chat_event.event,
                    "event_data": chat_event.data,
                },
            )

            if await request.is_disconnected():
                logger.info(
                    "Chat stream disconnected",
                    extra={
                        "request_id": context.request_id,
                        "stream_id": str(context.stream_id),
                        "conversation_id": str(context.conversation_id),
                    },
                )
                return

            # Falls das Modell vom Service mitgeteilt wird, übernehmen wir es
            if chat_event.model_id is not None:
                resolved_model_id = chat_event.model_id

            # Event ausgeben
            yield chat_event.to_sse(retry_milliseconds=DEFAULT_SSE_RETRY_MILLISECONDS)

            # Token-Zählung und terminale Events erkennen
            if chat_event.event == ChatEventType.TOKEN:          # <-- Enum-Vergleich
                token_count += 1

            if chat_event.event in {
                ChatEventType.DONE,
                ChatEventType.ERROR,
            }:                                                 # <-- terminale Events
                terminal_received = True

        # ------------------------------------------------------------
        # Nur wenn kein terminales Event (DONE oder ERROR) kam,
        # senden wir ein COMPLETE-Event.
        # ------------------------------------------------------------
        if not terminal_received:
            logger.info(
                "Sending completion event",
                extra={
                    "request_id": context.request_id,
                    "stream_id": str(context.stream_id),
                },
            )
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
                "stream_id": str(context.stream_id),
                "conversation_id": str(context.conversation_id),
            },
        )
        raise

    except ModelError as exc:
        logger.error(
            f"ModelError: {exc}",
            extra={
                "request_id": context.request_id,
                "stream_id": str(context.stream_id),
                "error_code": getattr(exc, "code", "UNKNOWN"),
                "error_details": getattr(exc, "details", {}),
            },
        )
        yield create_error_event(
            context=context,
            code="CHAT_STREAM_FAILED",
            message=f"Modellfehler: {exc}",
            details={"error_type": type(exc).__name__, "error_message": str(exc)},
            retryable=False,
        )

    except Exception as exc:
        logger.exception(
            "Unhandled chat streaming error",
            extra={
                "request_id": context.request_id,
                "stream_id": str(context.stream_id),
                "conversation_id": str(context.conversation_id),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        yield create_error_event(
            context=context,
            code="CHAT_STREAM_FAILED",
            message=f"Die Chat-Antwort konnte nicht vollständig erzeugt werden: {type(exc).__name__}",
            details={"error_type": type(exc).__name__, "error_message": str(exc)},
            retryable=False,
        )


# ============================================================================
# Endpunkt
# ============================================================================


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Chat-Antwort streamen",
    description="Erzeugt eine Chat-Antwort als versionierten Server-Sent-Events-Datenstrom.",
    responses={
        status.HTTP_200_OK: {
            "description": "SSE-Datenstrom wurde gestartet.",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Die Chat-Anfrage ist ungültig."
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Der produktive ChatService ist nicht verfügbar."
        },
    },
)
async def stream_chat(
    request: Request,
    payload: ChatRequest,
) -> StreamingResponse:
    """
    Startet einen SSE-Chat-Datenstrom.
    """
    require_chat_service(request)
    context = create_stream_context(request=request, payload=payload)

    return StreamingResponse(
        generate_chat_events(request=request, payload=payload, context=context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Request-ID": context.request_id,
            "X-Chat-Stream-ID": str(context.stream_id),
            "X-Chat-Schema-Version": CHAT_STREAM_SCHEMA_VERSION,
        },
    )