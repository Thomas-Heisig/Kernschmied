# F:\Kernschmied\backend\app\storage\models\chat.py

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import JsonValue
from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.models.base import Base, utc_now

# Keine eigene rekursive JsonValue-Definition – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


def _create_empty_json_object() -> JsonObject:
    """Erzeugt für jeden Datensatz ein eigenes leeres JSON-Objekt."""

    return {}


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "hierarchy_nodes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    config: Mapped[JsonObject] = mapped_column(
        JSON,
        nullable=False,
        default=_create_empty_json_object,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # Server-side message sequence counter used for atomic reservation
    next_message_sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    # Backwards-compatibility: some databases use legacy column name `chat_id`.
    conversation_id: Mapped[str] = mapped_column(
        # canonical column name
        "conversation_id",
        String(36),
        ForeignKey(
            "chats.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )

    parent_message_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="text",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Backwards-compatibility: map `ui_context` to legacy `metadata_json` column.
    ui_context: Mapped[JsonObject] = mapped_column(
        # canonical column name
        "ui_context",
        JSON,
        nullable=False,
        default=_create_empty_json_object,
    )

    # Backwards-compatibility: map `sequence_number` to legacy `position` column.
    sequence_number: Mapped[int] = mapped_column(
        # canonical column name
        "sequence_number",
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    request_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    schema_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0",
    )

    __table_args__ = (
        Index(
            "ix_messages_conversation_sequence",
            "conversation_id",
            "sequence_number",
        ),
        UniqueConstraint(
            "conversation_id",
            "sequence_number",
            name="uq_messages_conversation_sequence",
        ),
    )
