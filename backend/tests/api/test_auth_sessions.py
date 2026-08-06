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


def test_sessions_requires_auth(client: TestClient):
    r = client.get("/api/v1/auth/sessions")
    assert r.status_code == 401


# further session tests to implement
