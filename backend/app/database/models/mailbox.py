from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import JsonValue
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.storage.models.base import utc_now


class UserMailboxModel(Base):
    __tablename__ = "user_mailboxes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    internal_address: Mapped[str] = mapped_column(String(320), nullable=False)
    external_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    email_delivery_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    email_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_settings: Mapped[dict[str, JsonValue]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_mailboxes_user"),
        UniqueConstraint("internal_address", name="uq_user_mailboxes_internal_address"),
    )


class MailboxMessageModel(Base):
    __tablename__ = "mailbox_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    mailbox_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_mailboxes.id", ondelete="CASCADE"), nullable=False
    )
    sender_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    related_mention_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user_mentions.id", ondelete="CASCADE"), nullable=True
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="notification"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unread")
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="internal")
    delivery_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="delivered"
    )
    email_to: Mapped[str | None] = mapped_column(String(320), nullable=True)
    email_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_metadata: Mapped[dict[str, JsonValue]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "related_mention_id", name="uq_mailbox_messages_related_mention"
        ),
        Index("ix_mailbox_messages_mailbox_status", "mailbox_id", "status"),
        Index("ix_mailbox_messages_created_at", "created_at"),
    )