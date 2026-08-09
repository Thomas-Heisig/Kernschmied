from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import String, Text
from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_uuid() -> str:
    return str(uuid4())


class RoleModel(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Role flags: whether the role is a system-managed role and whether it
    # may be assigned through the administrative UI/API.
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assignable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    schema_version: Mapped[str] = mapped_column(
        String(16), nullable=False, default="1.0"
    )


class PermissionModel(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    permission: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(
        String(16), nullable=False, default="1.0"
    )


class UserRoleModel(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, primary_key=True)
    role_id: Mapped[str] = mapped_column(String(36), nullable=False, primary_key=True)


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[str] = mapped_column(String(36), nullable=False, primary_key=True)
    permission_id: Mapped[str] = mapped_column(
        String(36), nullable=False, primary_key=True
    )
