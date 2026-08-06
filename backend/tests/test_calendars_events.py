import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol, cast

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure backend package is importable when tests run from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.api.v1.calendars import (
    create_calendar,
    create_event,
    list_calendars,
    list_events,
)
from app.storage.models.base import Base as StorageBase


class UserProto(Protocol):
    id: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]


class CalendarOutProto(Protocol):
    id: str
    owner_id: str | None
    name: str
    color: str | None
    description: str | None


class EventOutProto(Protocol):
    id: str
    calendar_id: str
    title: str
    description: str | None


def test_calendar_and_event_crud() -> None:
    async def _run() -> None:
        # Setup in-memory SQLite and create schema
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(StorageBase.metadata.create_all)

        session_factory = async_sessionmaker[AsyncSession](
            engine, expire_on_commit=False
        )

        async with session_factory() as session:
            # Dummy request with user in state
            user = cast(
                UserProto, SimpleNamespace(id="test-user", roles=(), permissions=())
            )
            state = SimpleNamespace(user=user)
            request = SimpleNamespace(state=state)

            # Create calendar
            payload = SimpleNamespace(
                name="My Cal", color="#ff0000", description="desc"
            )
            cal = cast(CalendarOutProto, await create_calendar(request, payload, session=session))  # type: ignore[arg-type]
            assert cal.owner_id == "test-user"
            assert cal.name == "My Cal"

            # List calendars
            items = cast(list[CalendarOutProto], await list_calendars(request, session=session))  # type: ignore[arg-type]
            assert any(i.id == cal.id for i in items)

            # Create event
            now = datetime.now(UTC)
            ev_payload = SimpleNamespace(
                title="Meeting",
                description="",
                start=now,
                end=now + timedelta(hours=1),
                all_day=False,
            )
            ev = cast(EventOutProto, await create_event(cal.id, ev_payload, request, session=session))  # type: ignore[arg-type]
            assert ev.calendar_id == cal.id
            assert ev.title == "Meeting"

            # List events
            evs = cast(list[EventOutProto], await list_events(cal.id, request, session=session))  # type: ignore[arg-type]
            assert any(e.id == ev.id for e in evs)

        await engine.dispose()

    asyncio.run(_run())
