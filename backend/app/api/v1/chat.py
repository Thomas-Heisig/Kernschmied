# F:\Kernschmied\backend\app\api\v1\chat.py

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import (
    AsyncIterator,
    Mapping,
    Sequence,
)
from enum import Enum, StrEnum
from typing import (
    Literal,
    TypeAlias,
    cast,
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

from app.models.errors import ModelError
from app.models.service import ModelAccessContext
from app.services.chat_service import (
    ChatRequest as ServiceChatRequest,
)
from app.services.chat_service import (
    ChatService,
    ChatServiceContext,
    ChatServiceError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Modulkonfiguration
# ============================================================


SOURCE_FILE = "backend/app/api/v1/chat.py"
LOG_AREA = "chat-api"

CHAT_REQUEST_SCHEMA_VERSION = "1.0"
CHAT_STREAM_SCHEMA_VERSION = "1.0"

MAX_MESSAGE_LENGTH = 50_000
MAX_IDENTIFIER_LENGTH = 255
MAX_REQUEST_ID_LENGTH = 128
MAX_TOOL_COUNT = 100
MAX_METADATA_ENTRIES = 128

DEFAULT_SSE_RETRY_MILLISECONDS = 3_000

CLIENT_REQUEST_ID_HEADER = "X-Client-Request-ID"
SERVER_REQUEST_ID_HEADER = "X-Request-ID"

JsonObject: TypeAlias = dict[str, JsonValue]


# ============================================================
# Öffentliche Chat-Verträge
# ============================================================


class ChatStreamEventType(StrEnum):
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


class ChatFinishReason(StrEnum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALL = "tool_call"
    CANCELLED = "cancelled"
    ERROR = "error"
    UNKNOWN = "unknown"


class ChatRequest(BaseModel):
    """
    Öffentlicher, versionierter Chat-Request.

    Zusätzliche Felder werden bewusst abgelehnt. Neue öffentliche Felder
    müssen explizit und versioniert ergänzt werden.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    schema_version: Literal["1.0"] = Field(
        default=CHAT_REQUEST_SCHEMA_VERSION,
        description="Version des öffentlichen Chat-Request-Schemas.",
    )

    message: str = Field(
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        description="Nachricht des Benutzers.",
    )

    conversation_id: str | None = Field(
        default=None,
        max_length=MAX_IDENTIFIER_LENGTH,
        description="Bestehende Unterhaltung, falls vorhanden.",
    )

    hierarchy_node_id: str | None = Field(
        default=None,
        max_length=MAX_IDENTIFIER_LENGTH,
        description="Aktiver generischer Hierarchieknoten.",
    )

    model_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_IDENTIFIER_LENGTH,
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

    @field_validator(
        "conversation_id",
        "hierarchy_node_id",
        "model_id",
    )
    @classmethod
    def normalize_optional_identifier(
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

            if len(normalized) > MAX_IDENTIFIER_LENGTH:
                raise ValueError(
                    "Eine Tool-ID darf höchstens "
                    f"{MAX_IDENTIFIER_LENGTH} Zeichen enthalten.",
                )

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(normalized)

        return result

    @field_validator("metadata")
    @classmethod
    def validate_metadata(
        cls,
        value: JsonObject,
    ) -> JsonObject:
        if len(value) > MAX_METADATA_ENTRIES:
            raise ValueError(
                "Die Chat-Metadaten dürfen höchstens "
                f"{MAX_METADATA_ENTRIES} Einträge enthalten.",
            )

        return dict(value)


class StreamContext(BaseModel):
    """
    Transportkontext des öffentlichen SSE-Streams.

    Die Conversation-ID wird nicht vorab erzeugt. Für neue Unterhaltungen
    bleibt sie zunächst `None` und wird vom ChatService übernommen.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    stream_id: UUID
    request_id: str
    client_request_id: str | None = None
    requested_conversation_id: str | None = None
    user_id: str | None = None


class StreamEnvelope(BaseModel):
    """
    Stabiler öffentlicher Ereignisumschlag.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: Literal["1.0"] = CHAT_STREAM_SCHEMA_VERSION

    event: ChatStreamEventType
    sequence: int = Field(ge=0)

    request_id: str
    conversation_id: str | None = None
    message_id: str | None = None

    data: JsonObject = Field(
        default_factory=dict,
    )


# ============================================================
# Request- und Benutzerkontext
# ============================================================


def _normalize_request_id(
    value: object,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    if not normalized:
        return None

    if len(normalized) > MAX_REQUEST_ID_LENGTH:
        return None

    if not all(character.isalnum() or character in "._-" for character in normalized):
        return None

    return normalized


def get_request_id(
    request: Request,
) -> str:
    """
    Liefert ausschließlich eine serverseitige Request-ID.

    Eine vom Client gelieferte Korrelations-ID darf die Server-ID nicht
    ersetzen.
    """

    state_request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    normalized_state_id = _normalize_request_id(
        state_request_id,
    )

    if normalized_state_id is not None:
        return normalized_state_id

    generated_request_id = str(uuid4())

    request.state.request_id = generated_request_id

    return generated_request_id


def get_client_request_id(
    request: Request,
) -> str | None:
    state_client_request_id = getattr(
        request.state,
        "client_request_id",
        None,
    )

    normalized_state_id = _normalize_request_id(
        state_client_request_id,
    )

    if normalized_state_id is not None:
        return normalized_state_id

    return _normalize_request_id(
        request.headers.get(
            CLIENT_REQUEST_ID_HEADER,
        ),
    )


def get_current_user_id(
    request: Request,
) -> str | None:
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

    raw_user_id: object

    if isinstance(principal, Mapping):
        typed_principal = cast(
            Mapping[object, object],
            principal,
        )

        raw_user_id = (
            typed_principal.get("id")
            or typed_principal.get("user_id")
            or typed_principal.get("subject")
        )

    else:
        raw_user_id = (
            getattr(principal, "id", None)
            or getattr(principal, "user_id", None)
            or getattr(principal, "subject", None)
        )

    if raw_user_id is None:
        return None

    normalized = str(raw_user_id).strip()

    return normalized or None


def create_stream_context(
    request: Request,
    payload: ChatRequest,
) -> StreamContext:
    context = StreamContext(
        stream_id=uuid4(),
        request_id=get_request_id(request),
        client_request_id=get_client_request_id(request),
        requested_conversation_id=payload.conversation_id,
        user_id=get_current_user_id(request),
    )

    _log_info(
        "Chat stream context created",
        chat_step="stream-context-created",
        request_id=context.request_id,
        client_request_id=context.client_request_id,
        stream_id=str(context.stream_id),
        requested_conversation_id=(context.requested_conversation_id),
        user_id=context.user_id,
        requested_model_id=payload.model_id,
        requested_tool_count=len(payload.tool_ids),
        hierarchy_node_id=payload.hierarchy_node_id,
        message_length=len(payload.message),
        request_schema_version=payload.schema_version,
    )

    return context


# ============================================================
# ChatService-Zugriff
# ============================================================


def get_chat_service(
    request: Request,
) -> object | None:
    return getattr(
        request.app.state,
        "chat_service",
        None,
    )


def require_chat_service(
    request: Request,
) -> ChatService:
    service = get_chat_service(request)

    if service is None:
        request_id = get_request_id(request)

        _log_error(
            "Chat service is unavailable",
            chat_step="chat-service-unavailable",
            request_id=request_id,
            client_request_id=get_client_request_id(request),
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "CHAT_SERVICE_UNAVAILABLE",
                "message": ("Der Chat-Dienst ist derzeit nicht verfügbar."),
                "details": {},
                "request_id": request_id,
            },
        )

    if not isinstance(service, ChatService):
        request_id = get_request_id(request)

        _log_error(
            "Configured chat service has an invalid type",
            chat_step="chat-service-invalid",
            request_id=request_id,
            service_type=type(service).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "CHAT_SERVICE_INVALID",
                "message": ("Der Chat-Dienst ist fehlerhaft konfiguriert."),
                "details": {
                    "service_type": type(service).__name__,
                },
                "request_id": request_id,
            },
        )

    return service


# ============================================================
# Autorisierung
# ============================================================


async def authorize_chat_request(
    *,
    request: Request,
    payload: ChatRequest,
    context: StreamContext,
) -> None:
    """
    Autorisiert die vollständige Benutzeraktion vor Öffnung des Streams.

    Diese Funktion darf nicht erst innerhalb des Streaming-Generators
    aufgerufen werden, da zu diesem Zeitpunkt der HTTP-Status bereits
    gesendet sein kann.
    """

    del request

    if context.user_id is None:
        _log_warning(
            "Chat request without user ID",
            chat_step="authorization-missing-user",
            request_id=context.request_id,
            client_request_id=context.client_request_id,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AUTHENTICATION_REQUIRED",
                "message": (
                    "Für Chat-Anfragen ist eine Authentifizierung erforderlich."
                ),
                "details": {},
                "request_id": context.request_id,
            },
        )

    _log_info(
        "Chat request authorized",
        chat_step="authorization-success",
        request_id=context.request_id,
        client_request_id=context.client_request_id,
        user_id=context.user_id,
        hierarchy_node_id=payload.hierarchy_node_id,
        requested_model_id=payload.model_id,
        requested_tool_count=len(payload.tool_ids),
    )


# ============================================================
# SSE-Kodierung
# ============================================================


def encode_sse(
    envelope: StreamEnvelope,
    *,
    event_id: str | None = None,
    retry: int | None = None,
) -> str:
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
        f"event: {envelope.event.value}",
    )

    payload = envelope.model_dump(
        mode="json",
        exclude_none=False,
    )

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    for line in serialized.splitlines() or ["{}"]:
        lines.append(
            f"data: {line}",
        )

    return "\n".join(lines) + "\n\n"


def create_stream_envelope(
    *,
    context: StreamContext,
    event: ChatStreamEventType,
    sequence: int,
    data: JsonObject | None = None,
    conversation_id: str | None = None,
    message_id: str | None = None,
) -> StreamEnvelope:
    return StreamEnvelope(
        event=event,
        sequence=sequence,
        request_id=context.request_id,
        conversation_id=conversation_id,
        message_id=message_id,
        data=data or {},
    )


def encode_stream_event(
    *,
    context: StreamContext,
    event: ChatStreamEventType,
    sequence: int,
    data: JsonObject | None = None,
    conversation_id: str | None = None,
    message_id: str | None = None,
    retry: int | None = None,
) -> str:
    envelope = create_stream_envelope(
        context=context,
        event=event,
        sequence=sequence,
        data=data,
        conversation_id=conversation_id,
        message_id=message_id,
    )

    return encode_sse(
        envelope,
        event_id=f"{context.stream_id}:{sequence}",
        retry=retry,
    )


def create_error_event(
    *,
    context: StreamContext,
    sequence: int,
    code: str,
    message: str,
    details: JsonObject | None = None,
    retryable: bool = False,
    conversation_id: str | None = None,
    message_id: str | None = None,
) -> str:
    return encode_stream_event(
        context=context,
        event=ChatStreamEventType.ERROR,
        sequence=sequence,
        conversation_id=conversation_id,
        message_id=message_id,
        data={
            "code": code,
            "message": message,
            "details": details or {},
            "retryable": retryable,
        },
    )


# ============================================================
# Service-Ereignisse normalisieren
# ============================================================


def normalize_service_event_type(
    event: object,
) -> ChatStreamEventType | None:
    raw_values: list[str] = []

    if isinstance(event, Enum):
        raw_values.append(
            str(event.value),
        )
        raw_values.append(
            event.name,
        )

    raw_values.append(
        str(event),
    )

    aliases = {
        "start": ChatStreamEventType.START,
        "token": ChatStreamEventType.TOKEN,
        "message": ChatStreamEventType.MESSAGE,
        "reasoning": ChatStreamEventType.REASONING,
        "tool_call": ChatStreamEventType.TOOL_CALL,
        "tool.call": ChatStreamEventType.TOOL_CALL,
        "tool_result": ChatStreamEventType.TOOL_RESULT,
        "tool.result": ChatStreamEventType.TOOL_RESULT,
        "usage": ChatStreamEventType.USAGE,
        "complete": ChatStreamEventType.COMPLETE,
        "done": ChatStreamEventType.COMPLETE,
        "error": ChatStreamEventType.ERROR,
        "heartbeat": ChatStreamEventType.HEARTBEAT,
    }

    for raw_value in raw_values:
        normalized = raw_value.strip().lower().replace("-", "_")

        if normalized.startswith("chat."):
            normalized = normalized.removeprefix(
                "chat.",
            )

        mapped = aliases.get(normalized)

        if mapped is not None:
            return mapped

    return None


def normalize_service_event_data(
    event_type: ChatStreamEventType,
    raw_data: object,
    *,
    token_index: int,
    resolved_model_id: str | None,
    requested_tool_ids: Sequence[str],
) -> JsonObject:
    safe_data = _to_json_value(
        raw_data,
    )

    if isinstance(safe_data, dict):
        source = cast(
            JsonObject,
            safe_data,
        )
    else:
        source = {
            "value": safe_data,
        }

    if event_type is ChatStreamEventType.START:
        result: JsonObject = dict(source)

        if resolved_model_id is not None:
            result["model_id"] = resolved_model_id

        # Die Toolauflösung ist im aktuellen MVP noch nicht angebunden.
        result["accepted_tool_ids"] = []
        result["rejected_tool_ids"] = list(
            requested_tool_ids,
        )

        return result

    if event_type is ChatStreamEventType.TOKEN:
        return {
            "content": _extract_text_content(
                raw_data,
            ),
            "index": token_index,
        }

    if event_type is ChatStreamEventType.MESSAGE:
        return {
            "role": "assistant",
            "content": _extract_text_content(
                raw_data,
            ),
            "replace": True,
        }

    if event_type is ChatStreamEventType.REASONING:
        return {
            "content": _extract_text_content(
                raw_data,
            ),
            "visible": bool(
                source.get(
                    "visible",
                    False,
                ),
            ),
        }

    if event_type is ChatStreamEventType.COMPLETE:
        raw_finish_reason = source.get(
            "finish_reason",
            ChatFinishReason.STOP.value,
        )

        finish_reason = (
            raw_finish_reason
            if isinstance(raw_finish_reason, str)
            else ChatFinishReason.UNKNOWN.value
        )

        result = {
            "finish_reason": finish_reason,
        }

        usage = source.get("usage")

        if isinstance(usage, dict):
            result["usage"] = cast(
                JsonObject,
                usage,
            )

        content = source.get("content")

        if isinstance(content, str):
            result["content"] = content

        content_length = source.get(
            "content_length",
        )

        if isinstance(content_length, int):
            result["content_length"] = content_length

        if resolved_model_id is not None:
            result["model_id"] = resolved_model_id

        return result

    if event_type is ChatStreamEventType.ERROR:
        raw_code = source.get(
            "code",
            "CHAT_STREAM_FAILED",
        )

        raw_message = source.get(
            "message",
            "Die Chat-Antwort konnte nicht erzeugt werden.",
        )

        # Typwarnung unterdrücken, da source JsonObject ist
        raw_details = source.get("details", {})  # type: ignore[arg-type]

        code = raw_code if isinstance(raw_code, str) else "CHAT_STREAM_FAILED"

        message = (
            raw_message
            if isinstance(raw_message, str)
            else ("Die Chat-Antwort konnte nicht erzeugt werden.")
        )

        details: JsonObject

        if isinstance(raw_details, dict):
            details = cast(
                JsonObject,
                raw_details,
            )
        else:
            details = {
                "value": raw_details,
            }

        return {
            "code": code,
            "message": message,
            "details": details,
            "retryable": bool(
                source.get(
                    "retryable",
                    False,
                ),
            ),
        }

    return dict(source)


def _extract_text_content(
    value: object,
) -> str:
    if isinstance(value, str):
        return value

    if isinstance(value, Mapping):
        typed_value = cast(
            Mapping[object, object],
            value,
        )

        for key in (
            "content",
            "text",
            "token",
            "delta",
            "message",
        ):
            candidate = typed_value.get(
                key,
            )

            if isinstance(candidate, str):
                return candidate

            # Falls candidate selbst ein Mapping ist, darin weiter suchen
            if isinstance(candidate, Mapping):
                candidate_mapping = cast(
                    Mapping[object, object],
                    candidate,
                )
                nested_content = candidate_mapping.get(
                    "content",
                )
                if isinstance(nested_content, str):
                    return nested_content

                nested_text = candidate_mapping.get(
                    "text",
                )
                if isinstance(nested_text, str):
                    return nested_text

    for attribute_name in (
        "content",
        "text",
        "token",
        "delta",
        "message",
    ):
        candidate = getattr(
            cast(object, value),
            attribute_name,
            None,
        )

        if isinstance(candidate, str):
            return candidate

    return ""


def _to_json_value(
    value: object,
) -> JsonValue:
    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(value, BaseModel):
        return cast(
            JsonValue,
            value.model_dump(
                mode="json",
                exclude_none=True,
            ),
        )

    if isinstance(value, Mapping):
        typed_mapping = cast(
            Mapping[object, object],
            value,
        )

        result: JsonObject = {}

        for key, item in typed_mapping.items():
            result[str(key)] = _to_json_value(
                item,
            )

        return result

    if isinstance(value, Sequence) and not isinstance(
        value,
        (
            str,
            bytes,
            bytearray,
        ),
    ):
        typed_sequence = cast(
            Sequence[object],
            value,
        )

        return [_to_json_value(item) for item in typed_sequence]

    if isinstance(value, Enum):
        return _to_json_value(
            value.value,
        )

    return str(value)


# ============================================================
# Service-Kontext
# ============================================================


def create_service_request(
    payload: ChatRequest,
) -> ServiceChatRequest:
    """
    Die Conversation-ID des Clients wird unverändert weitergereicht.

    Bei `None` erzeugt ausschließlich der ChatService eine neue ID und
    legt die Unterhaltung über das Repository an.
    """

    return ServiceChatRequest(
        message=payload.message,
        model_id=payload.model_id,
        conversation_id=payload.conversation_id,
        parent_message_id=None,
        system_prompt=None,
        history=(),
        temperature=None,
        max_output_tokens=None,
        stream=True,
        tools=(),
        metadata={
            **dict(payload.metadata),
            "hierarchy_node_id": (payload.hierarchy_node_id),
            "requested_tool_ids": list(
                payload.tool_ids,
            ),
            "request_schema_version": (payload.schema_version),
        },
    )


def create_service_context(
    context: StreamContext,
) -> ChatServiceContext:
    return ChatServiceContext(
        request_id=context.request_id,
        access=ModelAccessContext(
            request_id=context.request_id,
            user_id=context.user_id,
        ),
        user_id=context.user_id,
        attributes={
            "client_request_id": (context.client_request_id),
            "stream_id": str(
                context.stream_id,
            ),
        },
    )


# ============================================================
# SSE-Generator
# ============================================================


async def generate_chat_events(
    request: Request,
    payload: ChatRequest,
    context: StreamContext,
    service: ChatService,
) -> AsyncIterator[str]:
    service_request = create_service_request(
        payload,
    )

    service_context = create_service_context(
        context,
    )

    sequence = 0
    token_count = 0
    terminal_received = False
    first_event = True

    resolved_model_id: str | None = payload.model_id

    resolved_conversation_id: str | None = payload.conversation_id

    resolved_message_id: str | None = None

    _log_info(
        "Chat stream generation started",
        chat_step="stream-generation-started",
        request_id=context.request_id,
        client_request_id=context.client_request_id,
        stream_id=str(context.stream_id),
        requested_conversation_id=(payload.conversation_id),
        requested_model_id=payload.model_id,
        requested_tool_count=len(payload.tool_ids),
        message_length=len(payload.message),
    )

    try:
        async for chat_event in service.stream(
            request=service_request,
            context=service_context,
        ):
            if await request.is_disconnected():
                _log_info(
                    "Chat stream client disconnected",
                    chat_step="client-disconnected",
                    request_id=context.request_id,
                    client_request_id=(context.client_request_id),
                    stream_id=str(context.stream_id),
                    conversation_id=(resolved_conversation_id),
                    sequence=sequence,
                    token_count=token_count,
                )

                return

            service_event_type = getattr(
                chat_event,
                "event",
                None,
            )  # type: ignore[arg-type]

            api_event_type = normalize_service_event_type(
                service_event_type,
            )

            if api_event_type is None:
                _log_warning(
                    "Unsupported service event rejected",
                    chat_step="service-event-rejected",
                    request_id=context.request_id,
                    client_request_id=(context.client_request_id),
                    stream_id=str(context.stream_id),
                    service_event_type=str(
                        service_event_type,
                    ),
                )

                continue

            event_model_id = getattr(
                chat_event,
                "model_id",
                None,
            )

            if isinstance(event_model_id, str) and event_model_id.strip():
                resolved_model_id = event_model_id.strip()

            event_conversation_id = getattr(
                chat_event,
                "conversation_id",
                None,
            )

            if (
                isinstance(
                    event_conversation_id,
                    str,
                )
                and event_conversation_id.strip()
            ):
                resolved_conversation_id = event_conversation_id.strip()

            event_message_id = getattr(
                chat_event,
                "message_id",
                None,
            )

            if isinstance(event_message_id, str) and event_message_id.strip():
                resolved_message_id = event_message_id.strip()

            raw_event_data = getattr(
                chat_event,
                "data",
                {},
            )

            if api_event_type is ChatStreamEventType.TOKEN:
                token_count += 1

            normalized_data = normalize_service_event_data(
                api_event_type,
                raw_event_data,
                token_index=max(
                    token_count - 1,
                    0,
                ),
                resolved_model_id=(resolved_model_id),
                requested_tool_ids=(payload.tool_ids),
            )

            _log_debug(
                "Chat service event translated",
                chat_step="service-event-translated",
                request_id=context.request_id,
                client_request_id=(context.client_request_id),
                stream_id=str(context.stream_id),
                sequence=sequence,
                event_type=api_event_type.value,
                service_sequence=getattr(
                    chat_event,
                    "sequence",
                    None,
                ),
                token_count=token_count,
                conversation_id=(resolved_conversation_id),
                message_id=(resolved_message_id),
                data_keys=list(
                    normalized_data.keys(),
                ),
            )

            yield encode_stream_event(
                context=context,
                event=api_event_type,
                sequence=sequence,
                data=normalized_data,
                conversation_id=(resolved_conversation_id),
                message_id=(resolved_message_id),
                retry=(DEFAULT_SSE_RETRY_MILLISECONDS if first_event else None),
            )

            first_event = False
            sequence += 1

            if api_event_type in {
                ChatStreamEventType.COMPLETE,
                ChatStreamEventType.ERROR,
            }:
                terminal_received = True

                _log_info(
                    "Terminal chat event received",
                    chat_step="terminal-event-received",
                    request_id=context.request_id,
                    client_request_id=(context.client_request_id),
                    stream_id=str(context.stream_id),
                    sequence=sequence - 1,
                    event_type=api_event_type.value,
                    token_count=token_count,
                    conversation_id=(resolved_conversation_id),
                    message_id=(resolved_message_id),
                )

                break

        if not terminal_received:
            _log_error(
                "Chat service ended without terminal event",
                chat_step="missing-terminal-event",
                request_id=context.request_id,
                client_request_id=(context.client_request_id),
                stream_id=str(context.stream_id),
                sequence=sequence,
                token_count=token_count,
                conversation_id=(resolved_conversation_id),
                message_id=resolved_message_id,
            )

            yield create_error_event(
                context=context,
                sequence=sequence,
                code="CHAT_STREAM_PROTOCOL_ERROR",
                message=(
                    "Der Chat-Dienst hat den Datenstrom "
                    "nicht ordnungsgemäß abgeschlossen."
                ),
                details={
                    "token_count": token_count,
                    "terminal_event_received": False,
                },
                retryable=False,
                conversation_id=(resolved_conversation_id),
                message_id=resolved_message_id,
            )

            terminal_received = True
            sequence += 1

    except asyncio.CancelledError:
        _log_info(
            "Chat stream cancelled",
            chat_step="stream-cancelled",
            request_id=context.request_id,
            client_request_id=(context.client_request_id),
            stream_id=str(context.stream_id),
            conversation_id=(resolved_conversation_id),
            message_id=resolved_message_id,
            sequence=sequence,
            token_count=token_count,
        )

        raise

    except ChatServiceError as exc:
        if not terminal_received:
            _log_exception(
                "Chat service error during stream",
                chat_step="chat-service-error",
                request_id=context.request_id,
                client_request_id=(context.client_request_id),
                stream_id=str(context.stream_id),
                conversation_id=(resolved_conversation_id),
                message_id=resolved_message_id,
                sequence=sequence,
                error_code=exc.code,
                error_type=type(exc).__name__,
                error_message=exc.message,
            )

            yield create_error_event(
                context=context,
                sequence=sequence,
                code=exc.code,
                message=exc.message,
                details=dict(exc.details),
                retryable=False,
                conversation_id=(resolved_conversation_id),
                message_id=resolved_message_id,
            )

            terminal_received = True
            sequence += 1

    except ModelError as exc:
        if not terminal_received:
            error_code = getattr(
                exc,
                "code",
                "MODEL_ERROR",
            )

            error_details = getattr(
                exc,
                "details",
                {},
            )

            _log_exception(
                "Model error during chat stream",
                chat_step="model-error",
                request_id=context.request_id,
                client_request_id=(context.client_request_id),
                stream_id=str(context.stream_id),
                conversation_id=(resolved_conversation_id),
                message_id=resolved_message_id,
                sequence=sequence,
                error_code=str(error_code),
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

            yield create_error_event(
                context=context,
                sequence=sequence,
                code=str(error_code),
                message=("Das angeforderte Modell konnte die Antwort nicht erzeugen."),
                details={
                    "error_type": type(exc).__name__,
                    "service_details": _to_json_value(
                        error_details,
                    ),
                },
                retryable=False,
                conversation_id=(resolved_conversation_id),
                message_id=resolved_message_id,
            )

            terminal_received = True
            sequence += 1

    except Exception as exc:
        if not terminal_received:
            _log_exception(
                "Unhandled error during chat stream",
                chat_step="stream-unhandled-error",
                request_id=context.request_id,
                client_request_id=(context.client_request_id),
                stream_id=str(context.stream_id),
                conversation_id=(resolved_conversation_id),
                message_id=resolved_message_id,
                sequence=sequence,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

            yield create_error_event(
                context=context,
                sequence=sequence,
                code="CHAT_STREAM_FAILED",
                message=("Die Chat-Antwort konnte nicht vollständig erzeugt werden."),
                details={
                    "error_type": type(exc).__name__,
                },
                retryable=False,
                conversation_id=(resolved_conversation_id),
                message_id=resolved_message_id,
            )

            terminal_received = True
            sequence += 1

    finally:
        _log_info(
            "Chat stream generation finished",
            chat_step="stream-generation-finished",
            request_id=context.request_id,
            client_request_id=(context.client_request_id),
            stream_id=str(context.stream_id),
            conversation_id=(resolved_conversation_id),
            message_id=resolved_message_id,
            sequence=sequence,
            token_count=token_count,
            terminal_received=terminal_received,
            model_id=resolved_model_id,
        )


# ============================================================
# Endpunkt
# ============================================================


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Chat-Antwort streamen",
    description=(
        "Erzeugt eine Chat-Antwort als versionierten Server-Sent-Events-Datenstrom."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": ("SSE-Datenstrom wurde gestartet."),
            "content": {
                "text/event-stream": {
                    "schema": {
                        "type": "string",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": ("Der Benutzer ist nicht berechtigt."),
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": ("Die Chat-Anfrage ist ungültig."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": ("Der ChatService ist nicht verfügbar."),
        },
    },
)
async def stream_chat(
    request: Request,
    payload: ChatRequest,
) -> StreamingResponse:
    service = require_chat_service(
        request,
    )

    context = create_stream_context(
        request=request,
        payload=payload,
    )

    # Muss vor dem Erzeugen der StreamingResponse stattfinden.
    await authorize_chat_request(
        request=request,
        payload=payload,
        context=context,
    )

    _log_info(
        "Chat stream request accepted",
        chat_step="stream-request-accepted",
        request_id=context.request_id,
        client_request_id=context.client_request_id,
        stream_id=str(context.stream_id),
        requested_conversation_id=(payload.conversation_id),
        requested_model_id=payload.model_id,
        requested_tool_count=len(payload.tool_ids),
        metadata_key_count=len(payload.metadata),
        message_length=len(payload.message),
        request_schema_version=(payload.schema_version),
        stream_schema_version=(CHAT_STREAM_SCHEMA_VERSION),
    )

    return StreamingResponse(
        generate_chat_events(
            request=request,
            payload=payload,
            context=context,
            service=service,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": ("no-cache, no-store, must-revalidate"),
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            SERVER_REQUEST_ID_HEADER: (context.request_id),
            "X-Chat-Stream-ID": str(
                context.stream_id,
            ),
            "X-Chat-Schema-Version": (CHAT_STREAM_SCHEMA_VERSION),
        },
    )


# ============================================================
# Strukturierte Logging-Hilfsfunktionen
# ============================================================


def _log_context(
    **values: object,
) -> dict[str, object]:
    return {
        "source": SOURCE_FILE,
        "area": LOG_AREA,
        **values,
    }


def _log_debug(
    message: str,
    **context: object,
) -> None:
    logger.debug(
        message,
        extra=_log_context(
            **context,
        ),
    )


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


def _log_error(
    message: str,
    **context: object,
) -> None:
    logger.error(
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
