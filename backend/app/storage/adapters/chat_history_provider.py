from __future__ import annotations

from typing import Sequence

from app.contracts.model_backend import ChatMessage, MessageRole
from app.services.chat_service import ChatHistoryProvider, ChatServiceContext
from app.storage.repositories.chat import ChatRepository as StorageChatRepository
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class ChatHistoryProviderAdapter:
    """Adapter implementing ChatHistoryProvider by loading messages
    from the storage `ChatRepository` and converting them to
    `ChatMessage` instances used for model prompts.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_history(
        self,
        *,
        conversation_id: str,
        context: ChatServiceContext,
    ) -> Sequence[ChatMessage]:
        async with self._session_factory() as session:
            repo = StorageChatRepository(session)
            msgs = await repo.list_messages(conversation_id)

            result: list[ChatMessage] = []

            for m in msgs:
                # map role string to MessageRole
                try:
                    role = MessageRole(m.role)
                except Exception:
                    # unknown roles default to user
                    role = MessageRole.USER

                # ensure metadata is a plain dict and include message id and sequence for deterministic behavior
                md = dict(getattr(m, "ui_context", {}) or {})
                md.setdefault("message_id", getattr(m, "id", None))
                md.setdefault("sequence_number", getattr(m, "sequence_number", None))
                md.setdefault("message_type", getattr(m, "message_type", None))

                cm = ChatMessage.create(
                    role=role,
                    content=(m.content or ""),
                    name=m.user_id,
                    metadata=md,
                )

                result.append(cm)

            return result


__all__ = ["ChatHistoryProviderAdapter"]
