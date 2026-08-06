from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.chat_service import (
    ChatHierarchyNodeNotFoundError,
    ChatHierarchyNodeRequiredError,
)
from app.storage.models.chat import Chat as ChatModel
from app.storage.models.chat import Message as MessageModel
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
        metadata: Mapping[str, Any] | None = None,
        hierarchy_node_id: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            chat_repo = StorageChatRepository(session)
            hierarchy_repo = StorageHierarchyRepository(session)
            # Require an explicit hierarchy_node_id parameter (no metadata fallback).
            node_id = hierarchy_node_id

            if not node_id:
                # Do not auto-create hierarchy nodes. A visible chat requires
                # an explicit `hierarchy_node_id`. Fail early with a stable
                # error so the API layer can return 422.
                raise ChatHierarchyNodeRequiredError(
                    "Für einen sichtbaren Chat ist ein Hierarchieknoten erforderlich."
                )

            # validate that the provided hierarchy node exists
            existing = await hierarchy_repo.get(node_id)
            if existing is None:
                raise ChatHierarchyNodeNotFoundError(
                    f"Der Hierarchieknoten '{node_id}' wurde nicht gefunden.",
                )

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
