from __future__ import annotations

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Literal


class BaseContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserCreateRequest(BaseContract):
    username: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    email: EmailStr | None = None
    must_change_password: bool | None = False


class UserUpdateRequest(BaseContract):
    display_name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None


class UserRead(BaseContract):
    id: str
    username: str
    display_name: str
    email: EmailStr | None = None
    is_active: bool
    is_system: bool | None = False
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
    updated_at: datetime | None


class UpdateUserPreferencesRequest(BaseContract):
    language: str | None = None
    timezone: str | None = None
    theme: Literal["system", "light", "dark"] | None = None
    density: Literal["comfortable", "compact"] | None = None
    default_view: str | None = None
    notifications_enabled: bool | None = None
