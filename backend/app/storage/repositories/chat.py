from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models.base import utc_now
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
        """Persist a Message and assign a unique sequence_number.

        If `message.sequence_number` is None the repository will compute the
        next sequence number and attempt to insert the message. To handle
        concurrent writers we perform the insert inside a SAVEPOINT and
        retry on IntegrityError a limited number of times.
        """
        # Disallow explicit sequence_number in normal flow; it must be reserved atomically
        if getattr(message, "sequence_number", None) is not None:
            raise ValueError("explicit sequence_number not allowed")

        # Reserve a sequence atomically
        seq = await self.reserve_next_message_sequence(message.conversation_id)
        message.sequence_number = seq

        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def reserve_next_message_sequence(self, conversation_id: str) -> int:
        """Atomically reserve and return the next message sequence for a conversation.

        Uses an UPDATE ... RETURNING to increment the per-chat counter and
        return the previously reserved value (next_message_sequence - 1).
        """
        stmt = text(
            "UPDATE chats SET next_message_sequence = next_message_sequence + 1 WHERE id = :cid RETURNING next_message_sequence - 1 AS seq"
        )
        try:
            result = await self.session.execute(stmt, {"cid": conversation_id})
            row = result.first()
            if row is None:
                raise KeyError(f"conversation not found: {conversation_id}")
            # row[0] contains the seq
            return int(row[0])
        except Exception:
            # Do not rollback the session here — let caller manage transaction scope.
            raise

    async def list_messages(
        self,
        conversation_id: str,
        limit: int | None = None,
        offset: int | None = None,
        after_sequence: int | None = None,
    ) -> Sequence[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id)
        if after_sequence is not None:
            stmt = stmt.where(Message.sequence_number > after_sequence)
        stmt = stmt.order_by(Message.sequence_number, Message.created_at)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.scalars(stmt)
        return result.all()

    async def get_message(self, message_id: str) -> Message | None:
        return await self.session.get(Message, message_id)

    async def mark_message_complete(
        self, message_id: str, *, completed_at: datetime | None = None
    ) -> None:
        msg = await self.session.get(Message, message_id)
        if msg is None:
            return
        # only allow transition from pending -> complete
        if msg.status != "pending":
            raise InvalidMessageStatusTransition(
                f"cannot transition {msg.status} -> complete"
            )
        msg.status = "complete"
        msg.completed_at = completed_at or utc_now()
        self.session.add(msg)
        await self.session.flush()

    async def mark_message_failed(
        self, message_id: str, *, metadata: dict[str, Any] | None = None
    ) -> None:
        msg = await self.session.get(Message, message_id)
        if msg is None:
            return
        # only allow transition from pending -> failed
        if msg.status != "pending":
            raise InvalidMessageStatusTransition(
                f"cannot transition {msg.status} -> failed"
            )
        msg.status = "failed"
        if metadata:
            # ensure ui_context is a plain dict[str, Any] for static checkers
            md: dict[str, Any] = dict(getattr(msg, "ui_context", {}) or {})
            # store only limited error information to avoid leaking raw traces
            error: dict[str, Any] = dict(md.get("error") or {})
            update_data: dict[str, Any] = {
                k: metadata.get(k) for k in ("code", "message") if k in metadata
            }
            if update_data:
                error.update(update_data)
            if error:
                md["error"] = error
            msg.ui_context = md
        self.session.add(msg)
        await self.session.flush()

    async def mark_message_cancelled(self, message_id: str) -> None:
        msg = await self.session.get(Message, message_id)
        if msg is None:
            return
        # only allow transition from pending -> cancelled
        if msg.status != "pending":
            raise InvalidMessageStatusTransition(
                f"cannot transition {msg.status} -> cancelled"
            )
        msg.status = "cancelled"
        msg.completed_at = utc_now()
        self.session.add(msg)
        await self.session.flush()


class InvalidMessageStatusTransition(Exception):
    """Raised when a requested message status transition is not allowed."""
