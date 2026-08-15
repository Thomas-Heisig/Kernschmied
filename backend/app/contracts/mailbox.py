from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class MailboxRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    user_id: str
    internal_address: str
    external_email: str | None
    email_delivery_enabled: bool
    email_provider: str | None
    email_ready: bool


class MailboxMessageRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    mailbox_id: str
    sender_user_id: str | None
    sender_name: str | None
    related_mention_id: str | None
    hierarchy_node_id: str | None
    subject: str
    body: str
    message_type: str
    status: Literal["unread", "read", "archived"]
    channel: Literal["internal", "email"]
    delivery_status: str
    email_to: str | None
    created_at: datetime
    read_at: datetime | None
    archived_at: datetime | None


class UpdateMailboxMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["read", "archived"]