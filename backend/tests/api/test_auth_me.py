from datetime import UTC, datetime
from types import SimpleNamespace

from app.api.v1.router import api_router
from app.auth.models import UserContext
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


def test_current_user_uses_canonical_profile_and_context_access():
    app = FastAPI()

    @app.middleware("http")
    async def provide_authenticated_user(request: Request, call_next):
        request.state.user = UserContext(
            id="guest-user",
            name="UI Bereich Check",
            authenticated=True,
            active=True,
            roles=("guest",),
            permissions=("widgets.read",),
        )
        request.state.user_model = SimpleNamespace(
            id="guest-user",
            username="ui-area-check",
            display_name="UI Bereich Check",
            email=None,
            password_hash="hashed-password",
            created_at=datetime(2026, 8, 15, tzinfo=UTC),
            last_login_at=None,
        )
        return await call_next(request)

    app.include_router(api_router, prefix="/api/v1")

    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": "guest-user",
        "username": "ui-area-check",
        "display_name": "UI Bereich Check",
        "email": None,
        "authenticated": True,
        "development_session": False,
        "password_login_available": True,
        "roles": ["guest"],
        "permissions": ["widgets.read"],
        "tenant": None,
        "created_at": "2026-08-15T00:00:00Z",
        "last_login_at": None,
        "schema_version": "1.0",
    }