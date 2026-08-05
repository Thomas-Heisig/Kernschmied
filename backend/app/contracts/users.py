from __future__ import annotations

from pydantic import BaseModel, Field, EmailStr


class BaseContract(BaseModel):
    class Config:
        extra = "forbid"


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
