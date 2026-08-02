from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_session
from app.storage.models.calendar import Calendar
from app.storage.models.event import Event

router = APIRouter()


# -----------------------------
# Pydantic DTOs
# -----------------------------


class CalendarCreate(BaseModel):
    name: str
    color: str | None = None
    description: str | None = None
    is_default: bool | None = False


class CalendarOut(CalendarCreate):
    id: str
    owner_id: str | None = None
    created_at: datetime
    updated_at: datetime


class CalendarUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    description: str | None = None
    is_default: bool | None = None


class EventCreate(BaseModel):
    title: str
    description: str | None = None
    start: datetime
    end: datetime
    all_day: bool | None = False


class EventOut(EventCreate):
    id: str
    calendar_id: str
    created_at: datetime
    updated_at: datetime


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    all_day: bool | None = None


def _ensure_owner(request: Request = None, owner_id: str | None = None):  # type: ignore[assignment]
    if request is None:  # type: ignore[reportUnnecessaryComparison]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = getattr(request.state, "user", None)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if owner_id is None:
        # allow creation if owner not set
        return

    is_admin = "admin" in getattr(user, "roles", ()) or "*" in getattr(user, "permissions", ())
    if is_admin:
        return

    if str(user.id) != str(owner_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")


# -----------------------------
# Calendars CRUD
# -----------------------------


@router.get("/", response_model=list[CalendarOut])
async def list_calendars(request: Request, session: AsyncSession = Depends(get_session)):
    if request is None:  # type: ignore[reportUnnecessaryComparison]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    stmt = select(Calendar).where(Calendar.owner_id == user.id)
    result = await session.execute(stmt)
    items = result.scalars().all()

    return [
        CalendarOut(
            id=i.id,
            name=i.name,
            color=i.color,
            description=i.description,
            owner_id=i.owner_id,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in items
    ]


@router.post("/", response_model=CalendarOut, status_code=status.HTTP_201_CREATED)
async def create_calendar(request: Request, payload: CalendarCreate = Body(...), session: AsyncSession = Depends(get_session)):
    if request is None:  # type: ignore[reportUnnecessaryComparison]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # If payload asks to be default or user has no calendars yet, mark as default.
    # payload can be a pydantic model or a SimpleNamespace in tests, so access safely.
    wants_default = bool(getattr(payload, "is_default", False))
    # check if user already has any calendars
    stmt = select(Calendar).where(Calendar.owner_id == user.id)
    result = await session.execute(stmt)
    existing = result.scalars().all()

    is_default = wants_default or (len(existing) == 0)

    obj = Calendar(
        owner_id=user.id,
        name=payload.name,
        color=payload.color,
        description=payload.description,
        is_default=is_default,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    # if this calendar is default, unset is_default on other calendars for this user
    if is_default:
        try:
            await session.execute(
                select(Calendar).where(Calendar.owner_id == user.id, Calendar.id != obj.id)
            )
            await session.execute(
                # raw SQL update to unset other defaults
                sa.text("UPDATE calendars SET is_default = 0 WHERE owner_id = :owner AND id != :id"),
                {"owner": user.id, "id": obj.id},
            )
            await session.commit()
        except Exception:
            # Ignore; best-effort to maintain uniqueness at application layer
            pass

    return CalendarOut(
        id=obj.id,
        name=obj.name,
        color=obj.color,
        description=obj.description,
        owner_id=obj.owner_id,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


async def _get_calendar_or_404(calendar_id: str, session: AsyncSession) -> Calendar:
    stmt = select(Calendar).where(Calendar.id == calendar_id)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return obj


@router.get("/{calendar_id}", response_model=CalendarOut)
async def get_calendar(calendar_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    obj = await _get_calendar_or_404(calendar_id, session)
    _ensure_owner(request, obj.owner_id)

    return CalendarOut(
        id=obj.id,
        name=obj.name,
        color=obj.color,
        description=obj.description,
        owner_id=obj.owner_id,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.patch("/{calendar_id}", response_model=CalendarOut)
async def patch_calendar(calendar_id: str, payload: CalendarUpdate = Body(...), request: Request = None, session: AsyncSession = Depends(get_session)):  # type: ignore[assignment]
    obj = await _get_calendar_or_404(calendar_id, session)
    _ensure_owner(request, obj.owner_id)

    if payload.name is not None:
        obj.name = payload.name
    if payload.color is not None:
        obj.color = payload.color
    if payload.description is not None:
        obj.description = payload.description
    if getattr(payload, "is_default", None) is not None:
        # If setting this calendar to default, unset others for this owner first
        if payload.is_default:
            try:
                await session.execute(
                    sa.text("UPDATE calendars SET is_default = 0 WHERE owner_id = :owner AND id != :id"),
                    {"owner": obj.owner_id, "id": obj.id},
                )
            except Exception:
                pass
            obj.is_default = True
        else:
            obj.is_default = False

    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    return CalendarOut(
        id=obj.id,
        name=obj.name,
        color=obj.color,
        description=obj.description,
        owner_id=obj.owner_id,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.delete("/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar(calendar_id: str, request: Request = None, session: AsyncSession = Depends(get_session)):  # type: ignore[assignment]
    obj = await _get_calendar_or_404(calendar_id, session)
    _ensure_owner(request, obj.owner_id)

    await session.delete(obj)
    await session.commit()

    return None


# -----------------------------
# Events
# -----------------------------


@router.get("/{calendar_id}/events", response_model=list[EventOut])
async def list_events(
    calendar_id: str,
    request: Request = None,  # type: ignore[assignment]
    time_min: datetime | None = None,
    time_max: datetime | None = None,
    session: AsyncSession = Depends(get_session),
):
    cal = await _get_calendar_or_404(calendar_id, session)
    _ensure_owner(request, cal.owner_id)

    stmt = select(Event).where(Event.calendar_id == calendar_id)
    if time_min is not None and time_max is not None:
        # overlap: start < time_max and end > time_min
        stmt = stmt.where(Event.start < time_max, Event.end > time_min)

    result = await session.execute(stmt)
    items = result.scalars().all()

    return [
        EventOut(
            id=e.id,
            calendar_id=e.calendar_id,
            title=e.title,
            description=e.description,
            start=e.start,
            end=e.end,
            all_day=e.all_day,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in items
    ]


@router.post("/{calendar_id}/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(calendar_id: str, payload: EventCreate = Body(...), request: Request = None, session: AsyncSession = Depends(get_session)):  # type: ignore[assignment]
    cal = await _get_calendar_or_404(calendar_id, session)
    _ensure_owner(request, cal.owner_id)

    e = Event(
        calendar_id=calendar_id,
        title=payload.title,
        description=payload.description,
        start=payload.start,
        end=payload.end,
        all_day=payload.all_day or False,
    )

    session.add(e)
    await session.commit()
    await session.refresh(e)

    return EventOut(
        id=e.id,
        calendar_id=e.calendar_id,
        title=e.title,
        description=e.description,
        start=e.start,
        end=e.end,
        all_day=e.all_day,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


async def _get_event_or_404(event_id: str, session: AsyncSession) -> Event:
    stmt = select(Event).where(Event.id == event_id)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return obj


@router.get("/{calendar_id}/events/{event_id}", response_model=EventOut)
async def get_event(calendar_id: str, event_id: str, request: Request = None, session: AsyncSession = Depends(get_session)):  # type: ignore[assignment]
    cal = await _get_calendar_or_404(calendar_id, session)
    _ensure_owner(request, cal.owner_id)
    evt = await _get_event_or_404(event_id, session)

    if evt.calendar_id != calendar_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return EventOut(
        id=evt.id,
        calendar_id=evt.calendar_id,
        title=evt.title,
        description=evt.description,
        start=evt.start,
        end=evt.end,
        all_day=evt.all_day,
        created_at=evt.created_at,
        updated_at=evt.updated_at,
    )


@router.patch("/{calendar_id}/events/{event_id}", response_model=EventOut)
async def patch_event(calendar_id: str, event_id: str, payload: EventUpdate = Body(...), request: Request = None, session: AsyncSession = Depends(get_session)):  # type: ignore[assignment]
    cal = await _get_calendar_or_404(calendar_id, session)
    _ensure_owner(request, cal.owner_id)
    evt = await _get_event_or_404(event_id, session)

    if evt.calendar_id != calendar_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if payload.title is not None:
        evt.title = payload.title
    if payload.description is not None:
        evt.description = payload.description
    if payload.start is not None:
        evt.start = payload.start
    if payload.end is not None:
        evt.end = payload.end
    if payload.all_day is not None:
        evt.all_day = payload.all_day

    session.add(evt)
    await session.commit()
    await session.refresh(evt)

    return EventOut(
        id=evt.id,
        calendar_id=evt.calendar_id,
        title=evt.title,
        description=evt.description,
        start=evt.start,
        end=evt.end,
        all_day=evt.all_day,
        created_at=evt.created_at,
        updated_at=evt.updated_at,
    )


@router.delete("/{calendar_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(calendar_id: str, event_id: str, request: Request = None, session: AsyncSession = Depends(get_session)):  # type: ignore[assignment]
    cal = await _get_calendar_or_404(calendar_id, session)
    _ensure_owner(request, cal.owner_id)
    evt = await _get_event_or_404(event_id, session)

    if evt.calendar_id != calendar_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await session.delete(evt)
    await session.commit()

    return None
