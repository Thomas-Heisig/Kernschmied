from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MentionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    username: str
    display_name: str
    online: bool = False
    is_administrator: bool = False


class UserMentionRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    message_id: str
    conversation_id: str
    hierarchy_node_id: str
    sender_user_id: str
    sender_name: str
    target_user_id: str
    mention_text: str
    status: Literal["unread", "read", "answered", "closed"]
    created_at: datetime
    read_at: datetime | None = None
    answered_at: datetime | None = None
    closed_at: datetime | None = None


class UpdateMentionStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["read", "answered", "closed"]


class MentionReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, max_length=36)
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)