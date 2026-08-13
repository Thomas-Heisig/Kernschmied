from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import JsonValue
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


JsonObject = dict[str, JsonValue]


def empty_json_object() -> JsonObject:
    return {}


class WidgetAssignmentModel(Base):
    __tablename__ = "widget_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    node_id: Mapped[str] = mapped_column(String(36), ForeignKey("hierarchy_nodes.id", ondelete="CASCADE"), nullable=False, index=True)

    widget_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("widget_registry.id", ondelete="SET NULL"), nullable=True, index=True)

    # Friendly name or stable identifier of the widget instance
    name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    inherit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)

    size: Mapped[str | None] = mapped_column(String(50), nullable=True)

    configuration: Mapped[JsonObject] = mapped_column(JSON, nullable=False, default=empty_json_object)

    required_permissions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    visible: Mapped[JsonObject] = mapped_column(JSON, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


__all__ = ["WidgetAssignmentModel"]
