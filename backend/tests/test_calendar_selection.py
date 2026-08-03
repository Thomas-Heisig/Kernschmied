import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

# Ensure backend package is importable when tests run from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.api.v1.calendar import select_date
from app.storage.models.base import Base as StorageBase
from app.storage.models.calendar_selection import CalendarSelection


def test_calendar_selection_user_binding() -> None:
    async def _run() -> None:
        # Setup in-memory SQLite and create schema
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(StorageBase.metadata.create_all)

        session_factory = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)

        async with session_factory() as session:
            # Dummy request with user in state
            user = SimpleNamespace(id="user-123")
            state = SimpleNamespace(user=user)
            request = cast(Request, SimpleNamespace(state=state))

            from app.api.v1.calendar import CalendarSelectionIn
            payload = CalendarSelectionIn(selected=datetime.now(UTC), note="a test note")

            res = await select_date(payload, request, session=session)

            assert res is not None

            # verify persisted user_id
            stmt = select(CalendarSelection).where(CalendarSelection.id == res.id)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            assert obj is not None
            assert obj.user_id == "user-123"

        await engine.dispose()

    asyncio.run(_run())