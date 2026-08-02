# F:\Kernschmied\backend\app\database\models\hierarchy_node.py

from __future__ import annotations

from datetime import UTC, datetime
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

from app.database.base import Base

# Keine eigene rekursive JsonValue-Definition – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


def utc_now() -> datetime:
    """
    Liefert den aktuellen UTC-Zeitpunkt als timezone-aware datetime.
    """

    return datetime.now(
        UTC,
    )


def new_uuid() -> str:
    """
    Erzeugt eine neue UUID als String.
    """

    return str(
        uuid4(),
    )


def empty_tool_policy() -> dict[str, bool]:
    """
    Typisierte Factory für die Tool-Richtlinie.
    """

    return {}


def empty_json_object() -> JsonObject:
    """
    Typisierte Factory für JSON-Objekte.

    Eine eigene Factory verhindert, dass Pylance bei
    `default=dict` den Typ `dict[Unknown, Unknown]` ableitet.
    """

    return {}


class HierarchyNodeModel(Base):
    """
    Persistentes Modell eines generischen Hierarchieknotens.

    Das Modell enthält ausschließlich generische Knoteneigenschaften.
    Fachlich fest verdrahtete Knotentypen werden bewusst vermieden.
    """

    __tablename__ = "hierarchy_nodes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_uuid,
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

    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tool_policy: Mapped[dict[str, bool]] = mapped_column(
        JSON,
        nullable=False,
        default=empty_tool_policy,
    )

    config_overrides: Mapped[JsonObject] = mapped_column(
        JSON,
        nullable=False,
        default=empty_json_object,
    )

    node_metadata: Mapped[JsonObject] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=empty_json_object,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True,
        ),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True,
        ),
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

    # Backwards-compatibility aliases for legacy storage model field names.
    # Older code (and tests) construct instances using names like
    # `node_type`, `prompt`, and `config`. Provide property aliases so the
    # declarative constructor accepts these keywords without creating a
    # duplicate ORM mapping.

    @property
    def node_type(self) -> str:
        return self.type

    @node_type.setter
    def node_type(self, value: str) -> None:
        self.type = value

    @property
    def prompt(self) -> str | None:
        return self.system_prompt

    @prompt.setter
    def prompt(self, value: str | None) -> None:
        self.system_prompt = value

    @property
    def config(self) -> JsonObject:
        return self.config_overrides

    @config.setter
    def config(self, value: JsonObject) -> None:
        self.config_overrides = value
    
