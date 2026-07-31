# F:\Kernschmied\backend\app\storage\models\hierarchy.py

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
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.models.base import Base, utc_now

# Keine eigene rekursive JsonValue-Definition – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


def _create_empty_config() -> JsonObject:
    """Erzeugt für jeden Datensatz ein eigenes leeres Konfigurationsobjekt."""

    return {}


class HierarchyNode(Base):
    __tablename__ = "hierarchy_nodes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "hierarchy_nodes.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    node_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    config: Mapped[JsonObject] = mapped_column(
        JSON,
        nullable=False,
        default=_create_empty_config,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    __table_args__ = (
        Index(
            "ix_hierarchy_nodes_parent_position",
            "parent_id",
            "position",
        ),
    )
