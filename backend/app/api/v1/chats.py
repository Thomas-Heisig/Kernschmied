from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_session
from app.storage.repositories import ChatRepository

router = APIRouter()


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    role: str
    content: str
    metadata: dict
    position: int
    created_at: datetime


@router.get("/{conversation_id}/messages", response_model=List[ChatMessageResponse])
async def list_chat_messages(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
) -> List[ChatMessageResponse]:
    """Listet persistente Chat-Nachrichten zu einer Unterhaltung auf.

    Diese minimale Implementierung gibt alle Nachrichten in aufsteigender
    Reihenfolge zurück. Paging kann später ergänzt werden.
    """

    repo = ChatRepository(session)

    try:
        messages = await repo.list_messages(conversation_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    result: List[ChatMessageResponse] = []

    for m in messages:
        result.append(
            ChatMessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                metadata=getattr(m, "metadata_json", {}),
                position=m.position,
                created_at=m.created_at,
            )
        )

    return result
