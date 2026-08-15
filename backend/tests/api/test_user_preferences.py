from unittest.mock import AsyncMock

import pytest
from app.api.v1 import users as users_api
from app.api.v1.router import api_router
from app.auth.dependencies import get_current_user
from app.auth.models import UserContext
from app.contracts.users import UserPreferencesResponse
from app.storage.database import get_session
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    with TestClient(app) as c:
        yield c


def test_get_preferences_requires_auth(client: TestClient):
    r = client.get("/api/v1/users/me/preferences")
    assert r.status_code == 401


@pytest.fixture
def guest_client():
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    session = AsyncMock()

    async def get_guest_user() -> UserContext:
        return UserContext(
            id="guest-user",
            name="Guest User",
            authenticated=True,
            active=True,
            roles=("guest",),
            permissions=(),
        )

    async def get_test_session():
        yield session

    app.dependency_overrides[get_current_user] = get_guest_user
    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client, session


def _preferences(*, theme: str = "system") -> UserPreferencesResponse:
    return UserPreferencesResponse(
        language="de",
        timezone="Europe/Berlin",
        theme=theme,
        density="comfortable",
        default_view=None,
        notifications_enabled=True,
        delivery_receipts_enabled=True,
        notification_sound_enabled=False,
        ai_response_on_mentions=False,
        updated_at=None,
    )


def test_guest_can_read_own_preferences(guest_client, monkeypatch):
    test_client, session = guest_client
    get_preferences = AsyncMock(return_value=_preferences())
    monkeypatch.setattr(users_api, "get_preferences", get_preferences)

    response = test_client.get("/api/v1/users/me/preferences")

    assert response.status_code == 200
    get_preferences.assert_awaited_once_with(session, "guest-user")


def test_guest_can_update_own_preferences(guest_client, monkeypatch):
    test_client, session = guest_client
    update_preferences = AsyncMock(return_value=_preferences(theme="dark"))
    monkeypatch.setattr(users_api, "update_preferences", update_preferences)

    response = test_client.patch(
        "/api/v1/users/me/preferences",
        json={"theme": "dark"},
    )

    assert response.status_code == 200
    assert response.json()["theme"] == "dark"
    update_preferences.assert_awaited_once()
    assert update_preferences.await_args.args[1] == "guest-user"
    session.commit.assert_awaited_once()
