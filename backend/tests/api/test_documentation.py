from app.api.v1 import documentation
from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_app():
    app = FastAPI()
    app.include_router(documentation.router, prefix="/documentation")
    return app


def test_list_documentation_index():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/documentation")
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data
    assert isinstance(data["sections"], list)
    # must not be empty for a consolidated repo
    assert len(data["sections"]) > 0


def test_get_home_page():
    app = create_app()
    client = TestClient(app)
    index = client.get("/documentation").json()
    default_page = index.get("default_page_id")
    assert default_page is not None
    resp = client.get(f"/documentation/pages/{default_page}")
    assert resp.status_code == 200
    page = resp.json()
    assert "content" in page
    assert page["content"].strip() != ""
