import sys
from pathlib import Path
import asyncio
from types import SimpleNamespace
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Ensure backend package is importable when tests run from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.storage.models.base import Base as StorageBase
from app.api.v1.calendar import select_date
from app.storage.models.calendar_selection import CalendarSelection


def test_calendar_selection_user_binding():
    async def _run():
        # Setup in-memory SQLite and create schema
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(StorageBase.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:  # type: AsyncSession
            # Dummy request with user in state
            user = SimpleNamespace(id="user-123")
            state = SimpleNamespace(user=user)
            request = SimpleNamespace(state=state)

            payload = SimpleNamespace(selected=datetime.utcnow(), note="a test note")

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
