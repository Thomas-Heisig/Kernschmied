import sys
from pathlib import Path
import asyncio
from types import SimpleNamespace
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Ensure backend package is importable when tests run from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.storage.models.base import Base as StorageBase
from app.storage.models.calendar import Calendar
from app.storage.models.event import Event
from app.api.v1.calendars import (
    create_calendar,
    list_calendars,
    create_event,
    list_events,
)


def test_calendar_and_event_crud():
    async def _run():
        # Setup in-memory SQLite and create schema
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(StorageBase.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:  # type: AsyncSession
            # Dummy request with user in state
            user = SimpleNamespace(id="test-user", roles=(), permissions=())
            state = SimpleNamespace(user=user)
            request = SimpleNamespace(state=state)

            # Create calendar
            payload = SimpleNamespace(name="My Cal", color="#ff0000", description="desc")
            cal = await create_calendar(request, payload, session=session)
            assert cal.owner_id == "test-user"
            assert cal.name == "My Cal"

            # List calendars
            items = await list_calendars(request, session=session)
            assert any(i.id == cal.id for i in items)

            # Create event
            now = datetime.utcnow()
            ev_payload = SimpleNamespace(title="Meeting", description="", start=now, end=now + timedelta(hours=1), all_day=False)
            ev = await create_event(cal.id, ev_payload, request, session=session)
            assert ev.calendar_id == cal.id
            assert ev.title == "Meeting"

            # List events
            evs = await list_events(cal.id, request, session=session)
            assert any(e.id == ev.id for e in evs)

        await engine.dispose()

    asyncio.run(_run())
