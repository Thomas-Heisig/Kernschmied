from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.api.v1 import auth, users
from app.auth.password_service import PasswordPolicyError
from app.contracts.users import UserCreateRequest
from fastapi import HTTPException, Response


class RejectingRegistrationService:
    async def register_user(self, **_kwargs: object) -> None:
        raise PasswordPolicyError(
            "PASSWORD_TOO_SHORT",
            "Das Passwort ist zu kurz (min. 12 Zeichen).",
        )


@pytest.mark.asyncio
async def test_self_registration_returns_policy_error_instead_of_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()
    monkeypatch.setattr(
        auth,
        "settings",
        SimpleNamespace(
            app_environment="development",
            development_self_registration_enabled=True,
        ),
    )
    monkeypatch.setattr(
        auth,
        "RegistrationService",
        lambda session: RejectingRegistrationService(),
    )

    with pytest.raises(HTTPException) as raised:
        await auth.register(
            request=SimpleNamespace(state=SimpleNamespace(request_id="request-1")),
            response=Response(),
            payload=auth.RegisterRequest(
                username="new-user",
                display_name="New User",
                password="short",
                password_confirmation="short",
            ),
            session=session,
        )

    assert raised.value.status_code == 422
    assert raised.value.detail == {
        "code": "PASSWORD_TOO_SHORT",
        "message": "Das Passwort ist zu kurz (min. 12 Zeichen).",
    }
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_user_creation_returns_policy_error_instead_of_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()
    monkeypatch.setattr(
        users,
        "RegistrationService",
        lambda session: RejectingRegistrationService(),
    )

    with pytest.raises(HTTPException) as raised:
        await users.create_user(
            request=SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace())),
            payload=UserCreateRequest(
                username="new-admin",
                display_name="New Admin",
                password="short",
                access_level="admin",
            ),
            session=session,
            _user=SimpleNamespace(id="admin-id"),
        )

    assert raised.value.status_code == 422
    assert raised.value.detail == {
        "code": "PASSWORD_TOO_SHORT",
        "message": "Das Passwort ist zu kurz (min. 12 Zeichen).",
    }
    session.rollback.assert_awaited_once()