from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models.base import utc_now
from app.storage.models.chat import Message
from app.storage.repositories.chat import ChatRepository


class MemoryService:
    """Kleine Service-Schicht zur Kapselung der Chat-Historie-Operationen.

    Der Service verwendet keine HTTP-spezifische Logik und erwartet, dass
    Autorisierung auf der Aufruferseite stattfindet.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ChatRepository(session)

    async def append_user_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        user_id: str | None,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message | None:
        await self._repo.add_message(
            Message(
                id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content=content,
                ui_context=metadata or {},
            )
        )

        return await self._repo.get_message(message_id)

    async def append_assistant_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        user_id: str | None,
        model_id: str,
        content: str,
        finish_reason: str | None = None,
        usage: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message | None:
        await self._repo.add_message(
            Message(
                id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=content,
                ui_context=metadata or {},
            )
        )

        return await self._repo.get_message(message_id)

    async def list_messages(
        self, conversation_id: str, limit: int | None = None, after: int | None = None
    ) -> Sequence[Message]:
        return await self._repo.list_messages(
            conversation_id, limit=limit, after_sequence=after
        )

    async def mark_message_complete(self, message_id: str) -> None:
        await self._repo.mark_message_complete(message_id, completed_at=utc_now())

    async def mark_message_failed(
        self, message_id: str, metadata: dict[str, Any] | None = None
    ) -> None:
        await self._repo.mark_message_failed(message_id, metadata=metadata)
