from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from app.database.models.user_mention import UserMentionModel
from app.services.chat_service import (
    ChatHierarchyNodeNotFoundError,
    ChatHierarchyNodeRequiredError,
)
from app.services.mailbox_service import (
    deliver_mailbox_message_email,
    deliver_mention_to_mailbox,
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
            # Annotate the hierarchy node with the conversation mapping so
            # the canonical node -> conversation relationship is persisted.
            # Do not store absolute paths or sensitive data on the node.
            node = await hierarchy_repo.get(node_id)
            if node is not None:
                md = dict(getattr(node, "node_metadata", {}) or {})
                md.update({"entity_type": "conversation", "entity_id": chat.id})
                node.node_metadata = md
                session.add(node)
                await session.flush()

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
        hierarchy_node_id: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            chat_repo = StorageChatRepository(session)

            # If the client supplied a conversation_id that does not exist
            # (stale localStorage), attempt to create a conversation server-side
            # when a valid hierarchy_node_id is provided. This makes the
            # client resilient to DB resets.
            existing_chat = await chat_repo.get(conversation_id)
            if existing_chat is None:
                # If caller provided a hierarchy node id, validate it and
                # create the chat record using that node. Otherwise fail
                # early with the existing behavior.
                if hierarchy_node_id:
                    hierarchy_repo = StorageHierarchyRepository(session)
                    node = await hierarchy_repo.get(hierarchy_node_id)
                    if node is None:
                        raise ChatHierarchyNodeNotFoundError(
                            f"Der Hierarchieknoten '{hierarchy_node_id}' wurde nicht gefunden."
                        )

                    chat = ChatModel(
                        id=conversation_id,
                        node_id=hierarchy_node_id,
                        title=f"Conversation {conversation_id}",
                        config=(dict(metadata or {})),
                    )

                    await chat_repo.add_chat(chat)

                    # Ensure the hierarchy node is annotated with the
                    # conversation mapping so opening the node later can
                    # resolve the existing conversation id.
                    node = await hierarchy_repo.get(hierarchy_node_id)
                    if node is not None:
                        md = dict(getattr(node, "node_metadata", {}) or {})
                        md.update({"entity_type": "conversation", "entity_id": chat.id})
                        node.node_metadata = md
                        session.add(node)

                    await session.flush()
                else:
                    # No node provided — preserve previous behavior which will
                    # result in a KeyError deeper in the repository.
                    pass

            # Let the repository assign the sequence_number atomically.
            message = MessageModel(
                id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                parent_message_id=parent_message_id,
                role="user",
                content=content,
                ui_context=(dict(metadata or {})),
            )

            await chat_repo.add_message(message)
            await chat_repo.mark_message_complete(message.id)
            raw_mentions = metadata.get("mentions", [])
            mailbox_message_ids: list[str] = []
            if user_id and isinstance(raw_mentions, list):
                seen_targets: set[str] = set()
                for raw_mention in cast(list[object], raw_mentions):
                    if not isinstance(raw_mention, Mapping):
                        continue
                    mention_data = cast(Mapping[str, object], raw_mention)
                    target_user_id = str(mention_data.get("user_id", "")).strip()
                    if not target_user_id or target_user_id in seen_targets:
                        continue
                    seen_targets.add(target_user_id)
                    mention = UserMentionModel(
                        message_id=message_id,
                        conversation_id=conversation_id,
                        sender_user_id=user_id,
                        target_user_id=target_user_id,
                        mention_text=content,
                    )
                    session.add(mention)
                    await session.flush()
                    mailbox_message = await deliver_mention_to_mailbox(session, mention)
                    mailbox_message_ids.append(mailbox_message.id)
            await session.commit()
            try:
                for mailbox_message_id in mailbox_message_ids:
                    await deliver_mailbox_message_email(session, mailbox_message_id)
                if mailbox_message_ids:
                    await session.commit()
            except Exception:
                await session.rollback()
            # best-effort projection: project conversation messages
            # The safe integration point is to let API handlers trigger projection; repository must not rely on app state here.

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
                parent_message_id=parent_message_id,
                role="assistant",
                content=content,
                ui_context=md,
            )

            await chat_repo.add_message(message)
            await chat_repo.mark_message_complete(message.id)
            await session.commit()
            # best-effort: do not call projection here; projection should be triggered by API layer after commit

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
