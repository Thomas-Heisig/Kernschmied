from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import JsonValue
from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


JsonObject = dict[str, JsonValue]
def empty_json_object() -> JsonObject:
    """Typed factory for empty JSON objects to satisfy static checkers."""

    return {}


def empty_json_array() -> list[JsonObject]:
    """Typed factory for empty JSON arrays."""

    return []


class WidgetRegistryEntry(Base):
    __tablename__ = "widget_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    # Technical identifier / name of the widget
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Optional widget kind/category
    type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    widget_metadata: Mapped[JsonObject] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=empty_json_object,
    )

    default_config: Mapped[JsonObject] = mapped_column(
        JSON,
        nullable=False,
        default=empty_json_object,
    )

    # Optional list of required permissions (strings) for this widget to be visible
    required_permissions: Mapped[list[str]] = mapped_column(
        "required_permissions", JSON, nullable=False, default=empty_json_array
    )

    # Status, e.g. 'draft', 'active', 'deprecated'
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    # Semantic version or string identifier of the widget schema
    version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Interaction mode hint for frontend
    interaction_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)

    

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


# Note: Do not expose `metadata` as an attribute on the ORM class. Use
# `widget_metadata` for the ORM mapping and perform translation between
# `widget_metadata` and the external `metadata` field in the API/DTO layer.
