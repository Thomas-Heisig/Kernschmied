import pytest
from app.api.v1.router import api_router
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


# further preference tests to implement
