from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.models.base import Base, utc_now


class CalendarSelection(Base):
    __tablename__ = "calendar_selections"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )

    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    __table_args__ = (
        Index("ix_calendar_selected_at", "selected_at"),
    )
