from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth import session_management_service as service
from app.auth.authentication_service import AuthenticationService


@pytest.mark.asyncio
async def test_list_sessions_normalizes_sqlite_datetimes_and_sorts_current_first(
    monkeypatch,
):
    now = datetime.now(UTC).replace(tzinfo=None)
    rows = [
        SimpleNamespace(
            id="newer-session",
            authentication_method="password",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            last_seen_at=now,
            revoked_at=None,
            ip_address="127.0.0.1",
            user_agent="Browser",
        ),
        SimpleNamespace(
            id="current-session",
            authentication_method="password",
            created_at=now - timedelta(hours=1),
            expires_at=now + timedelta(hours=1),
            last_seen_at=None,
            revoked_at=None,
            ip_address=None,
            user_agent=None,
        ),
    ]
    list_for_user = AsyncMock(return_value=rows)
    monkeypatch.setattr(service.AuthSessionRepository, "list_for_user", list_for_user)

    result = await service.list_sessions(
        AsyncMock(),
        "guest-user",
        "current-session",
    )

    assert [item.id for item in result] == ["current-session", "newer-session"]
    assert all(item.active for item in result)
    assert all(item.created_at.tzinfo is UTC for item in result)
    assert all(item.expires_at.tzinfo is UTC for item in result)
    list_for_user.assert_awaited_once_with("guest-user")


@pytest.mark.asyncio
async def test_resolve_session_exposes_the_actual_session_identity():
    auth_service = AuthenticationService(session=AsyncMock())
    user = SimpleNamespace(id="guest-user")
    auth_service.session_repo.get_by_token_hash = AsyncMock(
        return_value=SimpleNamespace(
            id="current-session",
            user_id="guest-user",
            revoked_at=None,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            authentication_method="password",
        )
    )
    auth_service.user_repo.get_by_id = AsyncMock(return_value=user)

    resolved = await auth_service.resolve_session("opaque-token")

    assert resolved is user
    assert auth_service.resolved_session_id == "current-session"
    assert auth_service.resolved_authentication_method == "password"