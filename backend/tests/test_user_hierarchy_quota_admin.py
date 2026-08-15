from collections.abc import AsyncIterator

import httpx
import pytest
from app.api.v1 import users as users_api
from app.auth.models import UserContext
from app.database.models.user import UserModel
from app.database.models.user_role import RoleModel, UserRoleModel
from app.hierarchy.models import HierarchyActor
from app.hierarchy.quotas import HierarchyQuotaService
from app.hierarchy.repository import HierarchyRepository
from app.storage.database import DatabaseManager, get_session
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.fixture
async def session_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    manager = DatabaseManager(
        f"sqlite+aiosqlite:///{(tmp_path / 'user-quotas.db').as_posix()}"
    )
    factory = await manager.initialize(create_schema=True)
    yield factory
    await manager.dispose()


@pytest.mark.asyncio
async def test_admin_updates_lists_and_enforces_user_quota_overrides(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        user = UserModel(
            username="quota-user",
            display_name="Quota User",
            email="quota@example.com",
        )
        role = RoleModel(name="guest", display_name="Gast")
        session.add_all([user, role])
        await session.flush()
        session.add(UserRoleModel(user_id=user.id, role_id=role.id))
        await session.commit()
        user_id = user.id

    admin = UserContext(
        id="admin-user",
        name="Administrator",
        authenticated=True,
        active=True,
        roles=("admin",),
        permissions=("users.read", "users.update"),
    )
    app = FastAPI()

    async def test_session():
        async with session_factory() as session:
            yield session

    async def test_admin() -> UserContext:
        return admin

    app.dependency_overrides[get_session] = test_session
    app.dependency_overrides[users_api.USERS_READ_DEP.dependency] = test_admin
    app.dependency_overrides[users_api.USERS_UPDATE_DEP.dependency] = test_admin
    app.include_router(users_api.router, prefix="/users")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.patch(
            f"/users/{user_id}",
            json={
                "workspace_quota": "unlimited",
                "project_quota": 7,
                "chat_quota": None,
            },
        )
        assert response.status_code == 200
        assert response.json()["workspace_quota"] == "unlimited"
        assert response.json()["project_quota"] == 7
        assert response.json()["chat_quota"] is None

        listed = await client.get("/users/")
        assert listed.status_code == 200
        listed_user = next(item for item in listed.json() if item["id"] == user_id)
        assert listed_user["workspace_quota"] == "unlimited"
        assert listed_user["project_quota"] == 7
        assert listed_user["chat_quota"] is None

    async with session_factory() as session:
        status = await HierarchyQuotaService(HierarchyRepository(session)).status(
            HierarchyActor(user_id=user_id, roles=frozenset({"guest"}))
        )

    assert status["limits"] == {"workspace": None, "project": 7, "chat": 5}
