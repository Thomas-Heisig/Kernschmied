from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

AccessLevel = Literal["guest", "internal", "admin"]


class BaseContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserCreateRequest(BaseContract):
    username: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    email: EmailStr | None = None

    # Password handling
    password: str | None = None
    generate_password: bool = False
    require_password_change: bool = Field(default=True)

    # Roles to assign (names)
    roles: list[str] | None = None
    access_level: AccessLevel = "guest"

    is_active: bool = True

    preferences: dict[str, object] | None = None

    # Optional default workspace creation
    create_default_workspace: bool = False
    default_workspace_name: str | None = None


class UserUpdateRequest(BaseContract):
    display_name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    access_level: AccessLevel | None = None


class UserRead(BaseContract):
    id: str
    username: str
    display_name: str
    email: EmailStr | None = None
    is_active: bool
    is_system: bool | None = False
    access_level: AccessLevel = "guest"
    created_at: str
    updated_at: str


class UserPreferencesResponse(BaseContract):
    schema_version: Literal["1.0"] = "1.0"

    language: str
    timezone: str
    theme: Literal["system", "light", "dark"]
    density: Literal["comfortable", "compact"]
    default_view: str | None
    notifications_enabled: bool
    delivery_receipts_enabled: bool
    notification_sound_enabled: bool
    ai_response_on_mentions: bool
    updated_at: datetime | None


class UpdateUserPreferencesRequest(BaseContract):
    language: str | None = None
    timezone: str | None = None
    theme: Literal["system", "light", "dark"] | None = None
    density: Literal["comfortable", "compact"] | None = None
    default_view: str | None = None
    notifications_enabled: bool | None = None
    delivery_receipts_enabled: bool | None = None
    notification_sound_enabled: bool | None = None
    ai_response_on_mentions: bool | None = None


class GeneratedCredentials(BaseContract):
    temporary_password: str


class UserCreateResponse(BaseContract):
    schema_version: Literal["1.0"] = "1.0"
    user: UserRead
    generated_credentials: GeneratedCredentials | None = None
