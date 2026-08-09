import os
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.core.settings import reload_settings, settings
from app.storage import database as _database_module
from app.storage.database import init_database
from app.core.dev_seed import seed_development_hierarchy
from app.database.models.user import UserModel
from app.hierarchy.repository import HierarchyRepository
from app.auth.registration_service import RegistrationService, RegistrationError


@pytest.fixture()
async def session_factory(tmp_path: Path) -> async_sessionmaker[AsyncSession]:
    # Use a fresh sqlite file for isolation
    db_file = tmp_path / "kernschmied_test_users.db"
    os.environ["DATABASE_MIGRATION_MODE"] = "disabled"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    new_settings = reload_settings()
    _database_module.settings = new_settings
    # Replace module-level manager so init_database uses the new URL
    _database_module._database_manager = _database_module.DatabaseManager(
        new_settings.effective_database_url
    )

    sf = await init_database(create_schema=True, echo=False)
    return sf


@pytest.mark.asyncio
async def test_development_seed_creates_admin_and_user_node(session_factory):
    # Run seed
    await seed_development_hierarchy(session_factory)

    async with session_factory() as session:
        q = select(UserModel).where(UserModel.id == settings.development_admin_user_id)
        res = await session.execute(q)
        admin = res.scalar_one_or_none()
        assert admin is not None
        assert admin.username == settings.development_admin_username
        assert admin.display_name == settings.development_admin_display_name
        assert getattr(admin, "password_hash", None) is not None

        # Check hierarchy node exists for admin
        repo = HierarchyRepository(session)
        node = await repo.get_node(f"user-{admin.id}")
        assert node is not None
        assert node.node_metadata.get("entity_type") == "user"


@pytest.mark.asyncio
async def test_development_seed_is_idempotent(session_factory):
    # Run seed twice; expect no duplicates and no errors
    await seed_development_hierarchy(session_factory)
    await seed_development_hierarchy(session_factory)

    async with session_factory() as session:
        q = select(UserModel).where(UserModel.id == settings.development_admin_user_id)
        res = await session.execute(q)
        rows = res.scalars().all()
        assert len(rows) == 1

        repo = HierarchyRepository(session)
        node = await repo.get_node(f"user-{settings.development_admin_user_id}")
        assert node is not None


@pytest.mark.asyncio
async def test_registration_creates_user_and_hierarchy_node(session_factory):
    # Ensure system roots (users-root) exist
    await seed_development_hierarchy(session_factory)

    async with session_factory() as session:
        service = RegistrationService(session)
        user, _ = await service.register_user(
            username="tx-test-user",
            display_name="Tx Test User",
            email=None,
            password="verysecurepassword",
        )

        # After flush, the user id should exist and hierarchy node created
        repo = HierarchyRepository(session)
        node = await repo.get_node(f"user-{user.id}")
        assert node is not None
        assert node.node_metadata.get("entity_id") == user.id


@pytest.mark.asyncio
async def test_registration_rolls_back_on_hierarchy_failure(session_factory, monkeypatch):
    # ensure roots exist so failure is due to our monkeypatch, not missing parent
    await seed_development_hierarchy(session_factory)

    # Monkeypatch HierarchyRepository.create_node to raise, causing registration to fail
    async def _fail_create_node(self, *args, **kwargs):
        raise Exception("simulated failure")

    monkeypatch.setattr(HierarchyRepository, "create_node", _fail_create_node)

    async with session_factory() as session:
        service = RegistrationService(session)
        with pytest.raises(RegistrationError):
            await service.register_user(
                username="rollback-user",
                display_name="Rollback User",
                email=None,
                password="verysecurepassword",
            )

    # In a new session the user should not be present (no partial commit)
    async with session_factory() as session:
        q = select(UserModel).where(UserModel.username == "rollback-user")
        res = await session.execute(q)
        assert res.scalar_one_or_none() is None
