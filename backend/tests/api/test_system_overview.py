from app.api.v1 import system
from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeConfigService:
    async def get_revision(self) -> int:
        return 7


class FakeModelRegistry:
    async def get_count(self) -> int:
        return 3


class FakeToolRegistry:
    count = 5


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def execute(self, statement):
        return object()


class FakeSessionFactory:
    def __call__(self):
        return FakeSession()


class BrokenSession(FakeSession):
    async def execute(self, statement):
        raise RuntimeError("database unavailable")


class BrokenSessionFactory:
    def __call__(self):
        return BrokenSession()


def test_system_overview_combines_health_and_registry_counts() -> None:
    app = FastAPI()
    app.state.config_service = FakeConfigService()
    app.state.model_registry = FakeModelRegistry()
    app.state.tool_registry = FakeToolRegistry()
    app.state.session_factory = FakeSessionFactory()
    app.include_router(system.router, prefix="/api/v1/system")

    response = TestClient(app).get("/api/v1/system/overview")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate"
    assert response.json() == {
        "schema_version": "1.0",
        "api_version": "v1",
        "status": "ok",
        "environment": "development",
        "config_revision": 7,
        "security_profile": response.json()["security_profile"],
        "services": {
            "config_service": {"status": "up"},
            "model_registry": {"status": "up"},
            "tool_registry": {"status": "up"},
            "database": {"status": "up"},
        },
        "registries": {"models": 3, "tools": 5},
    }


def test_system_overview_reports_database_down_when_probe_fails() -> None:
    app = FastAPI()
    app.state.session_factory = BrokenSessionFactory()
    app.include_router(system.router, prefix="/api/v1/system")

    response = TestClient(app).get("/api/v1/system/overview")

    assert response.status_code == 200
    assert response.json()["services"]["database"] == {"status": "down"}