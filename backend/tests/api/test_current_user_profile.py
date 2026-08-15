import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.v1 import users as users_api
from app.api.v1.router import api_router
from app.auth.dependencies import get_current_user
from app.auth.models import UserContext
from app.storage.database import get_session
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    with TestClient(app) as c:
        yield c


def test_get_own_profile_requires_auth(client: TestClient):
    r = client.get("/api/v1/users/me")
    assert r.status_code == 401


def test_guest_can_update_own_profile(monkeypatch):
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

    updated_profile = SimpleNamespace(
        id="guest-user",
        username="guest",
        display_name="Updated Guest",
        email=None,
        password_hash="hash",
        created_at=datetime.now(timezone.utc),
        last_login_at=None,
    )
    update_profile = AsyncMock(return_value=updated_profile)
    monkeypatch.setattr(users_api, "update_current_profile", update_profile)
    app.dependency_overrides[get_current_user] = get_guest_user
    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as test_client:
        response = test_client.patch(
            "/api/v1/users/me",
            json={"display_name": "Updated Guest"},
        )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated Guest"
    update_profile.assert_awaited_once_with(
        session,
        "guest-user",
        display_name="Updated Guest",
        email=None,
    )
    session.commit.assert_awaited_once()
