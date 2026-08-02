from __future__ import annotations

from app.database.base import Base
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.storage.models.chat import Chat, Message


def test_chat_and_hierarchy_share_metadata() -> None:
    # All models must use the same MetaData instance
    assert Chat.metadata is HierarchyNodeModel.metadata
    assert Message.metadata is HierarchyNodeModel.metadata


def test_required_tables_are_registered() -> None:
    tables = Base.metadata.tables

    assert "hierarchy_nodes" in tables
    assert "chats" in tables
    assert "messages" in tables


def test_chat_node_foreign_key_resolves() -> None:
    node_id_column = Chat.__table__.c.node_id
    foreign_keys = list(node_id_column.foreign_keys)

    assert len(foreign_keys) == 1
    assert foreign_keys[0].column.table.name == "hierarchy_nodes"
    assert foreign_keys[0].column.name == "id"
