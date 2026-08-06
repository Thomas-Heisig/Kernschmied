from __future__ import annotations

from collections.abc import Mapping

from app.auth.principal_mapper import build_principal_from_user
from app.auth.models import UserContext
from app.api.v1.tools import read_mapping_value


class DummyUser:
    def __init__(self) -> None:
        self.id = "dev-admin"
        self.username = "dev-admin"
        self.display_name = "Dev Admin"
        self.email = "dev@example.local"
        self.is_active = True
        self.is_system_admin = True
        self.roles = ["admin"]
        self.permissions = ["config.read"]


def test_build_principal_from_user_returns_mapping_and_not_model() -> None:
    user = DummyUser()
    principal = build_principal_from_user(user, authentication_method="development")

    assert isinstance(principal, Mapping)
    assert principal.get("id") == "dev-admin"
    assert principal.get("authentication_method") == "development"


def test_usercontext_from_principal_admin_flag() -> None:
    user = DummyUser()
    principal = build_principal_from_user(user)
    ctx = UserContext.from_principal(principal)

    assert isinstance(ctx, UserContext)
    assert ctx.is_system_admin or "admin" in ctx.roles


def test_read_mapping_value_with_non_mapping() -> None:
    class Fake:
        permissions = ["x"]

    result = read_mapping_value(Fake(), "permissions", [])
    assert result == []


def test_read_mapping_value_with_mapping() -> None:
    src = {"permissions": ["config:read"]}
    result = read_mapping_value(src, "permissions", [])
    assert result == ["config:read"]
