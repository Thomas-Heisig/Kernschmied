from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.storage.models.chat import Chat as ChatModel, Message as MessageModel
from app.storage.models.hierarchy import HierarchyNode
from app.storage.repositories.chat import ChatRepository as StorageChatRepository
from app.storage.repositories.hierarchy import HierarchyRepository as StorageHierarchyRepository


class ChatRepositoryAdapter:
    """Adapter implementing the ChatService.ChatRepository protocol
    by delegating to the storage repositories.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str | None,
        tenant_id: str | None,
        model_id: str,
        metadata: Mapping[str, Any],
    ) -> None:
        async with self._session_factory() as session:
            chat_repo = StorageChatRepository(session)
            hierarchy_repo = StorageHierarchyRepository(session)

            # try to obtain a hierarchy node id from metadata
            node_id = None

            try:
                node_id = metadata.get("hierarchy_node_id")
            except Exception:
                node_id = None

            if not node_id:
                # create a dedicated hierarchy node for this chat
                node = HierarchyNode(
                    node_type="chat",
                    name=f"Conversation {conversation_id}",
                    config=dict(metadata or {}),
                )

                await hierarchy_repo.add(node)
                node_id = node.id

            chat = ChatModel(
                id=conversation_id,
                node_id=node_id,
                title=f"Conversation {conversation_id}",
                config=(dict(metadata or {})),
            )

            await chat_repo.add_chat(chat)
            await session.commit()

    async def append_user_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        parent_message_id: str | None,
        content: str,
        metadata: Mapping[str, Any],
    ) -> None:
        async with self._session_factory() as session:
            chat_repo = StorageChatRepository(session)

            # compute next position
            messages = await chat_repo.list_messages(conversation_id)
            position = (messages[-1].position + 1) if messages else 0

            message = MessageModel(
                id=message_id,
                chat_id=conversation_id,
                role="user",
                content=content,
                metadata_json=(dict(metadata or {})),
                position=position,
            )

            await chat_repo.add_message(message)
            await session.commit()

    async def append_assistant_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        parent_message_id: str | None,
        model_id: str,
        content: str,
        finish_reason: str | None,
        usage: Mapping[str, Any] | None,
        metadata: Mapping[str, Any],
    ) -> None:
        async with self._session_factory() as session:
            chat_repo = StorageChatRepository(session)

            messages = await chat_repo.list_messages(conversation_id)
            position = (messages[-1].position + 1) if messages else 0

            # include finish_reason and usage into metadata for traceability
            md = dict(metadata or {})
            if finish_reason is not None:
                md.setdefault("finish_reason", finish_reason)
            if usage is not None:
                md.setdefault("usage", dict(usage))

            message = MessageModel(
                id=message_id,
                chat_id=conversation_id,
                role="assistant",
                content=content,
                metadata_json=md,
                position=position,
            )

            await chat_repo.add_message(message)
            await session.commit()

    async def mark_assistant_message_failed(
        self,
        *,
        conversation_id: str,
        message_id: str,
        error_code: str,
        error_message: str,
        metadata: Mapping[str, Any],
    ) -> None:
        async with self._session_factory() as session:
            # mark the message metadata with failure info
            msg = await session.get(MessageModel, message_id)
            if msg is None:
                return

            md = dict(getattr(msg, "metadata_json", {}) or {})
            md.setdefault("error", {})
            md["error"].update({"code": error_code, "message": error_message})
            md.update(dict(metadata or {}))

            msg.metadata_json = md
            session.add(msg)
            await session.commit()
