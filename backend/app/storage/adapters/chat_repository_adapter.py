from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.storage.models.chat import Chat as ChatModel
from app.storage.models.chat import Message as MessageModel
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.services.chat_service import ChatHierarchyNodeNotFoundError
from app.storage.repositories.chat import ChatRepository as StorageChatRepository
from app.storage.repositories.hierarchy import (
    HierarchyRepository as StorageHierarchyRepository,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


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

            if node_id:
                # validate that the provided hierarchy node exists
                existing = await hierarchy_repo.get(node_id)
                if existing is None:
                    raise ChatHierarchyNodeNotFoundError(
                        f"Der Hierarchieknoten '{node_id}' wurde nicht gefunden.",
                    )
            if not node_id:
                # create a dedicated hierarchy node for this chat
                node = HierarchyNodeModel(
                    type="chat",
                    name=f"Conversation {conversation_id}",
                    system_prompt=None,
                    tool_policy={},
                    config_overrides=dict(metadata or {}),
                    node_metadata={},
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
        user_id: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            chat_repo = StorageChatRepository(session)

            # Let the repository assign the sequence_number atomically.
            message = MessageModel(
                id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content=content,
                ui_context=(dict(metadata or {})),
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
        user_id: str | None = None,
        content: str,
        finish_reason: str | None,
        usage: Mapping[str, Any] | None,
        metadata: Mapping[str, Any],
    ) -> None:
        async with self._session_factory() as session:
            chat_repo = StorageChatRepository(session)

            # include finish_reason and usage into metadata for traceability
            md = dict(metadata or {})
            if finish_reason is not None:
                md.setdefault("finish_reason", finish_reason)
            if usage is not None:
                md.setdefault("usage", dict(usage))
            message = MessageModel(
                id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=content,
                ui_context=md,
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

            md: dict[str, Any] = dict(getattr(msg, "ui_context", {}) or {})
            # store only limited error information to avoid dumping full traces
            error: dict[str, Any] = md.get("error", {}) or {}
            error.update({"code": error_code, "message": error_message})
            md["error"] = error
            # preserve provided metadata keys that are not sensitive
            for k, v in dict(metadata or {}).items():
                if k not in ("traceback", "exception"):
                    md.setdefault(k, v)

            msg.ui_context = md
            session.add(msg)
            await session.commit()
