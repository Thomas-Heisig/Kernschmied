from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class BaseContract(BaseModel):
    class Config:
        extra = "forbid"


class LoginRequest(BaseContract):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseContract):
    id: str
    username: str
    display_name: str
    email: str | None = None


class CurrentUserResponse(LoginResponse):
    is_active: bool


class LogoutResponse(BaseContract):
    success: bool


class ChangePasswordRequest(BaseContract):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=12)
