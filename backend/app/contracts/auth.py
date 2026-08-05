from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class TenantSummary(BaseModel):
    id: str
    display_name: str


class CurrentUserResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"

    id: str
    username: str
    display_name: str
    email: EmailStr | None = None
    authenticated: bool
    development_session: bool
    password_login_available: bool

    tenant: TenantSummary | None = None

    created_at: datetime | None = None
    last_login_at: datetime | None = None



class UserSessionResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"

    id: str
    authentication_method: str
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime | None = None
    revoked_at: datetime | None = None

    current: bool
    active: bool

    ip_address: str | None = None
    user_agent: str | None = None

