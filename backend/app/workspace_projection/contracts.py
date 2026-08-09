from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass
class UserDto:
    id: str
    display_name: str | None
    metadata: Mapping[str, Any] | None = None


@dataclass
class NodeDto:
    id: str
    title: str | None
    type: str | None
    metadata: Mapping[str, Any] | None = None
    parent_id: str | None = None


@dataclass
class MessageDto:
    id: str
    conversation_id: str
    role: str
    content: str
    sequence_number: int | None
    created_at: str
    request_id: str | None = None
    status: str | None = None


@dataclass
class ConversationDto:
    id: str
    node_id: str | None
    created_at: str | None = None
    updated_at: str | None = None
    message_count: int | None = None


@dataclass
class ProjectionConfig:
    enabled: bool
    root_path: str


__all__ = [
    "UserDto",
    "NodeDto",
    "MessageDto",
    "ConversationDto",
    "ProjectionConfig",
]
