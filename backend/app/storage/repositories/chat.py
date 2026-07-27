from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models.chat import Chat, Message
from app.storage.repositories.base import Repository


class ChatRepository(Repository[Chat]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get(self, chat_id: str) -> Chat | None:
        return await self.session.get(Chat, chat_id)

    async def get_by_node_id(self, node_id: str) -> Chat | None:
        return await self.session.scalar(
            select(Chat).where(Chat.node_id == node_id)
        )

    async def add_chat(self, chat: Chat) -> Chat:
        self.session.add(chat)
        await self.session.flush()
        await self.session.refresh(chat)
        return chat

    async def add_message(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def list_messages(self, chat_id: str) -> Sequence[Message]:
        result = await self.session.scalars(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.position, Message.created_at)
        )
        return result.all()
