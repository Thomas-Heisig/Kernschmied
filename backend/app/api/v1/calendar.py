from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_session
from app.storage.models.calendar_selection import CalendarSelection

router = APIRouter()


class CalendarSelectionIn(BaseModel):
    selected: datetime
    note: str | None = None


class CalendarSelectionOut(BaseModel):
    id: str
    selected: datetime
    note: str | None = None
    created_at: datetime


@router.post("/selection", response_model=CalendarSelectionOut, status_code=status.HTTP_201_CREATED)
async def select_date(payload: CalendarSelectionIn, session: AsyncSession = Depends(get_session)):
    """Persist a selected calendar date. Integration point for frontend calendar."""
    try:
        obj = CalendarSelection(
            selected_at=payload.selected,
            note=payload.note,
        )

        session.add(obj)
        await session.commit()
        await session.refresh(obj)

        return CalendarSelectionOut(
            id=obj.id,
            selected=obj.selected_at,
            note=obj.note,
            created_at=obj.created_at,
        )

    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail={"message": "Failed to persist calendar selection", "error": str(exc)})
