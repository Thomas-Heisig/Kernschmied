from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models.chat import Chat, Message
from app.storage.repositories.base import Repository


class ChatRepository(Repository[Chat]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get(self, chat_id: str) -> Chat | None:
        return await self.session.get(Chat, chat_id)

    async def get_by_node_id(self, node_id: str) -> Chat | None:
        return await self.session.scalar(select(Chat).where(Chat.node_id == node_id))

    async def add_chat(self, chat: Chat) -> Chat:
        self.session.add(chat)
        await self.session.flush()
        await self.session.refresh(chat)
        return chat

    async def add_message(self, message: Message) -> Message:
        # Ensure a stable sequence_number within the same conversation.
        if getattr(message, "sequence_number", None) is None or message.sequence_number == 0:
            # compute max sequence_number for conversation
            result = await self.session.execute(
                select(func.max(Message.sequence_number)).where(Message.conversation_id == message.conversation_id)
            )
            max_seq = result.scalar() or -1
            message.sequence_number = int(max_seq) + 1

        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def list_messages(self, conversation_id: str, limit: int | None = None, offset: int | None = None) -> Sequence[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.sequence_number, Message.created_at)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.scalars(stmt)
        return result.all()

    async def get_message(self, message_id: str) -> Message | None:
        return await self.session.get(Message, message_id)

    async def mark_message_complete(self, message_id: str, *, completed_at: datetime | None = None) -> None:
        msg = await self.session.get(Message, message_id)
        if msg is None:
            return
        msg.status = "complete"
        msg.completed_at = completed_at or utc_now()
        self.session.add(msg)
        await self.session.flush()

    async def mark_message_failed(self, message_id: str, *, metadata: dict | None = None) -> None:
        msg = await self.session.get(Message, message_id)
        if msg is None:
            return
        msg.status = "failed"
        if metadata:
            md = dict(getattr(msg, "ui_context", {}) or {})
            md.update(metadata)
            msg.ui_context = md
        self.session.add(msg)
        await self.session.flush()
