from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from .contracts import (
    ConversationDto,
    MessageDto,
    NodeDto,
    ProjectionConfig,
    UserDto,
)
from .paths import node_folder_name, resolve_within_root, user_folder_name
from .projector import write_json, write_messages_jsonl


class WorkspaceProjectionService:
    def __init__(self, config: ProjectionConfig) -> None:
        self.config = config
        self.root = Path(self.config.root_path)

    def _user_root(self, user: UserDto) -> Path:
        return resolve_within_root(self.root, "users", user_folder_name(user.display_name, user.id))

    def _node_path(self, user: UserDto, *parts: str) -> Path:
        return self._user_root(user).joinpath(*parts)

    def project_user(self, user: UserDto) -> None:
        if not self.config.enabled:
            return

        root = self._user_root(user)
        root.mkdir(parents=True, exist_ok=True)

        user_json = {
            "id": user.id,
            "display_name": user.display_name,
            "metadata": dict(user.metadata or {}),
            "exported_at": datetime.utcnow().isoformat() + "Z",
        }

        write_json(root.joinpath("user.json"), user_json)

    def project_node(self, user: UserDto, node: NodeDto, parent_path_parts: List[str] | None = None) -> None:
        if not self.config.enabled:
            return

        # compute path
        parts = ["nodes"] + (parent_path_parts or []) + [node_folder_name(node.title, node.id)]
        node_root = self._node_path(user, *parts)
        node_root.mkdir(parents=True, exist_ok=True)

        node_json = {
            "id": node.id,
            "title": node.title,
            "type": node.type,
            "metadata": dict(node.metadata or {}),
            "exported_at": datetime.utcnow().isoformat() + "Z",
        }

        write_json(node_root.joinpath("node.json"), node_json)

    def project_conversation(self, user: UserDto, convo: ConversationDto, parent_path_parts: List[str] | None = None) -> None:
        if not self.config.enabled:
            return

        parts = ["nodes"] + (parent_path_parts or []) + [node_folder_name(None, convo.node_id or convo.id)]
        node_root = self._node_path(user, *parts)
        node_root.mkdir(parents=True, exist_ok=True)

        chat_json = {
            "schema_version": "1.0",
            "conversation_id": convo.id,
            "node_id": convo.node_id,
            "created_at": convo.created_at,
            "updated_at": convo.updated_at,
            "message_count": convo.message_count,
            "exported_at": datetime.utcnow().isoformat() + "Z",
        }

        write_json(node_root.joinpath("chat.json"), chat_json)

    def project_message_history(self, user: UserDto, convo: ConversationDto, messages: Iterable[MessageDto], parent_path_parts: List[str] | None = None) -> None:
        if not self.config.enabled:
            return

        parts = ["nodes"] + (parent_path_parts or []) + [node_folder_name(None, convo.node_id or convo.id)]
        node_root = self._node_path(user, *parts)
        node_root.mkdir(parents=True, exist_ok=True)

        # messages.jsonl: write entire file atomically from authoritative DB rows
        msgs = []
        count = 0
        for m in messages:
            msgs.append(
                {
                    "id": m.id,
                    "conversation_id": m.conversation_id,
                    "sequence_number": m.sequence_number,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at,
                    "request_id": m.request_id,
                    "status": m.status,
                }
            )
            count += 1

        write_messages_jsonl(node_root.joinpath("messages.jsonl"), msgs)


__all__ = ["WorkspaceProjectionService"]
