from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import Any, List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .service import WorkspaceProjectionService
from .contracts import UserDto, NodeDto, ConversationDto, MessageDto, ProjectionConfig
from app.storage.repositories.user import UserRepository
from app.storage.repositories.hierarchy import HierarchyRepository
from app.storage.repositories.chat import ChatRepository

logger = logging.getLogger(__name__)


class PostCommitProjectionService:
    def __init__(self, *, session_factory: async_sessionmaker[AsyncSession], config: ProjectionConfig) -> None:
        self._session_factory = session_factory
        self._config = config
        self._workspace = WorkspaceProjectionService(config)

    async def _run_in_thread(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    async def project_user(self, user_id: str) -> None:
        if not self._config.enabled:
            return

        async with self._session_factory() as session:
            ur = UserRepository(session)
            user = await ur.get_by_id(user_id)

            if user is None:
                logger.warning("PostCommit: user not found for projection", extra={"user_id": user_id})
                return

            dto = UserDto(id=user.id, display_name=getattr(user, "display_name", None), metadata=None)

        try:
            await self._run_in_thread(self._workspace.project_user, dto)
        except Exception:
            logger.exception("Workspace projection failed after user commit", extra={"user_id": user_id})

    async def _collect_node_path_parts(self, session: AsyncSession, node_id: str) -> tuple[str | None, List[str]]:
        """Return (user_id_or_none, parent_path_parts list from user down to parent)

        parent_path_parts are folder names (as node_folder_name) excluding the user root node.
        """
        hre = HierarchyRepository(session)

        parts: list[str] = []
        current_id = node_id
        user_id: str | None = None

        # Walk up until root or until we find a node with metadata.entity_type == 'user'
        while current_id is not None:
            node = await hre.get(current_id)
            if node is None:
                break

            md = dict(getattr(node, "node_metadata", {}) or {})
            if md.get("entity_type") == "user" and md.get("entity_id"):
                user_id = str(md.get("entity_id"))
                break

            # Prepend folder name for this node
            # Use serializer-like naming: title + __ + id
            title = getattr(node, "name", None)
            parts.append(f"{(title or 'node').strip()}__{node.id}")

            current_id = getattr(node, "parent_id", None)

        parts.reverse()
        return user_id, parts

    async def project_node(self, node_id: str) -> None:
        if not self._config.enabled:
            return

        async with self._session_factory() as session:
            hre = HierarchyRepository(session)
            node = await hre.get(node_id)
            if node is None:
                logger.warning("PostCommit: node not found for projection", extra={"node_id": node_id})
                return

            # find owning user and parent path parts
            user_id, parent_parts = await self._collect_node_path_parts(session, node.id)

            user_display = None
            if user_id is not None:
                ur = UserRepository(session)
                user = await ur.get_by_id(user_id)
                if user is not None:
                    user_display = getattr(user, "display_name", None)

            user_dto = UserDto(id=(user_id or "unknown"), display_name=user_display)
            node_dto = NodeDto(id=node.id, title=getattr(node, "name", None), type=getattr(node, "type", None), metadata=getattr(node, "node_metadata", None) or {}, parent_id=getattr(node, "parent_id", None))

        try:
            await self._run_in_thread(self._workspace.project_node, user_dto, node_dto, parent_parts)
        except Exception:
            logger.exception("Workspace projection failed after node commit", extra={"node_id": node_id})

    async def project_conversation(self, conversation_id: str) -> None:
        if not self._config.enabled:
            return

        async with self._session_factory() as session:
            cr = ChatRepository(session)
            chat = await cr.get(conversation_id)
            if chat is None:
                logger.warning("PostCommit: conversation not found for projection", extra={"conversation_id": conversation_id})
                return

            # find user and path parts via node
            hre = HierarchyRepository(session)
            node = await hre.get(getattr(chat, "node_id", None))

            user_id = None
            parent_parts = []
            if node is not None:
                uid, parts = await self._collect_node_path_parts(session, node.id)
                user_id = uid
                parent_parts = parts

            user_display = None
            if user_id is not None:
                ur = UserRepository(session)
                u = await ur.get_by_id(user_id)
                if u is not None:
                    user_display = getattr(u, "display_name", None)

            user_dto = UserDto(id=(user_id or "unknown"), display_name=user_display)
            convo_dto = ConversationDto(id=chat.id, node_id=getattr(chat, "node_id", None), created_at=(getattr(chat, "created_at", None).isoformat() if getattr(chat, "created_at", None) is not None else None), updated_at=(getattr(chat, "updated_at", None).isoformat() if getattr(chat, "updated_at", None) is not None else None), message_count=None)

            # load messages authoritative
            rows = await cr.list_messages(conversation_id)
            msgs: list[MessageDto] = []
            for m in rows:
                msgs.append(MessageDto(id=str(getattr(m, "id", "")), conversation_id=conversation_id, role=getattr(m, "role", ""), content=getattr(m, "content", "") or "", sequence_number=getattr(m, "sequence_number", None), created_at=(getattr(m, "created_at", None).isoformat() if getattr(m, "created_at", None) is not None else ""), request_id=getattr(m, "request_id", None), status=getattr(m, "status", None)))

        try:
            # call projection methods in thread to avoid blocking event loop
            await self._run_in_thread(self._workspace.project_conversation, user_dto, convo_dto, parent_parts)
            await self._run_in_thread(self._workspace.project_message_history, user_dto, convo_dto, msgs, parent_parts)
        except Exception:
            logger.exception("Workspace projection failed after conversation commit", extra={"conversation_id": conversation_id})

    async def project_conversation_by_node(self, node_id: str) -> None:
        """Resolve conversation by node metadata and project it."""
        async with self._session_factory() as session:
            hre = HierarchyRepository(session)
            node = await hre.get(node_id)
            if node is None:
                return
            md = dict(getattr(node, "node_metadata", {}) or {})
            if md.get("entity_type") != "conversation" or not md.get("entity_id"):
                return
            convo_id = str(md.get("entity_id"))

        await self.project_conversation(convo_id)

    async def rebuild_user(self, user_id: str) -> None:
        """Rebuild entire user projection by walking hierarchy and conversations."""
        if not self._config.enabled:
            return

        async with self._session_factory() as session:
            # find user node
            hre = HierarchyRepository(session)
            # list all nodes and find ones with metadata.entity_type == user and entity_id == user_id
            nodes = await hre.list_all()
            user_node = None
            for n in nodes:
                md = dict(getattr(n, "node_metadata", {}) or {})
                if md.get("entity_type") == "user" and str(md.get("entity_id")) == user_id:
                    user_node = n
                    break

            if user_node is None:
                logger.warning("PostCommit: rebuild_user user node not found", extra={"user_id": user_id})
                return

            # Project user
            ur = UserRepository(session)
            u = await ur.get_by_id(user_id)
            user_display = getattr(u, "display_name", None) if u is not None else None
            user_dto = UserDto(id=user_id, display_name=user_display)

            # find subtree nodes under this user
            # collect nodes whose ancestor chain includes user_node.id
            subtree = []
            for n in nodes:
                cur = n
                while cur is not None:
                    if cur.id == user_node.id:
                        subtree.append(n)
                        break
                    if getattr(cur, "parent_id", None) is None:
                        break
                    cur = await hre.get(getattr(cur, "parent_id", None))

        # Project user and nodes/messages in thread
        try:
            await self._run_in_thread(self._workspace.project_user, user_dto)
            # project nodes and conversations iteratively
            for n in subtree:
                parent_parts = []
                # build path parts by walking up to user_node
                cur = n
                parts = []
                while cur is not None and cur.id != user_node.id:
                    parts.append(f"{(getattr(cur, 'name', None) or 'node').strip()}__{cur.id}")
                    cur = await hre.get(getattr(cur, "parent_id", None))
                parts.reverse()
                node_dto = NodeDto(id=n.id, title=getattr(n, "name", None), type=getattr(n, "type", None), metadata=getattr(n, "node_metadata", None) or {}, parent_id=getattr(n, "parent_id", None))
                await self._run_in_thread(self._workspace.project_node, user_dto, node_dto, parts)
        except Exception:
            logger.exception("Workspace rebuild failed for user", extra={"user_id": user_id})


__all__ = ["PostCommitProjectionService"]
