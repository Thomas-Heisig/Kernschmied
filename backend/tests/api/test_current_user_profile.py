import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.api.v1.router import api_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    with TestClient(app) as c:
        yield c


def test_get_own_profile_requires_auth(client: TestClient):
    r = client.get('/api/v1/users/me')
    assert r.status_code == 401

# more tests to be implemented by developer
