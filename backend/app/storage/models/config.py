from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.models.base import Base, utc_now


class SystemConfig(Base):
    __tablename__ = "system_configs"
    __table_args__ = (
        UniqueConstraint(
            "config_group",
            "config_key",
            name="uq_system_configs_group_key",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    config_group: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    config_key: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )
    value: Mapped[object] = mapped_column(
        JSON,
        nullable=False,
    )
    schema_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    is_secret: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    requires_restart: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    runtime_editable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    updated_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ConfigState(Base):
    __tablename__ = "config_state"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        default=1,
    )
    revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
