from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

JsonObject = dict[str, object]


class ChatUiContextV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = Field(default="1.0")
    selected_calendar_id: str | None = Field(default=None, max_length=36)
    current_month: str | None = Field(default=None, max_length=20)
    view_mode: Literal["day", "week", "month", "agenda"] | None = None


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    conversation_id: str
    hierarchy_node_id: str | None
    user_id: str | None
    parent_message_id: str | None
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    message_type: Literal["text", "tool_call", "tool_result", "reasoning", "summary"]
    ui_context: JsonObject | None
    sequence_number: int
    status: Literal["pending", "complete", "failed", "cancelled"]
    request_id: str | None
    created_at: datetime
    completed_at: datetime | None
    schema_version: str


class ChatHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = Field(default="1.0")
    conversation_id: str
    items: list[ChatMessageRead]
    has_more: bool = False
    next_cursor: int | None = None


class ChatMutationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = Field(default="1.0")
    conversation_id: str
    action: Literal["delete_message", "clear", "truncate_after"]
    affected_messages: int = Field(ge=0)
    retained_through_message_id: str | None = None
