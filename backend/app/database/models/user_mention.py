from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.storage.models.base import utc_now


class UserMentionModel(Base):
    __tablename__ = "user_mentions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    sender_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mention_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unread"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "message_id", "target_user_id", name="uq_user_mentions_message_target"
        ),
        Index("ix_user_mentions_target_status", "target_user_id", "status"),
        Index("ix_user_mentions_conversation", "conversation_id"),
    )