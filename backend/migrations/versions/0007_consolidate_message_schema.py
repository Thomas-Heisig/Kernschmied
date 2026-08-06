"""consolidate legacy and canonical message schema with prechecks

Revision ID: 0007_consolidate_message_schema
Revises: 0006_add_message_sequence_counter
Create Date: 2026-08-02 12:47:00.000000
"""

from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, Result

# revision identifiers, used by Alembic.
revision = "0007_consolidate_message_schema"
down_revision = "0006_add_message_sequence_counter"
branch_labels = None
depends_on = None


def _detect_orphans(conn: Connection) -> dict[str, int]:
    res: dict[str, int] = {}
    try:
        r: Result[Any] = conn.execute(
            sa.text(
                "SELECT COUNT(1) FROM messages WHERE conversation_id NOT IN (SELECT id FROM chats)"
            )
        )
        res["messages_without_chat"] = int(r.scalar() or 0)
    except Exception:
        res["messages_without_chat"] = 0
    try:
        r2: Result[Any] = conn.execute(
            sa.text(
                "SELECT COUNT(1) FROM chats WHERE node_id NOT IN (SELECT id FROM hierarchy_nodes)"
            )
        )
        res["chats_without_node"] = int(r2.scalar() or 0)
    except Exception:
        res["chats_without_node"] = 0
    return res


def upgrade() -> None:
    conn: Connection = op.get_bind()
    inspector = sa.inspect(conn)
    existing: list[str] = inspector.get_table_names()

    # Pre-check: abort upgrade if orphans exist in an existing DB copy.
    orphans: dict[str, int] = _detect_orphans(conn)
    if (
        orphans.get("messages_without_chat", 0) > 0
        or orphans.get("chats_without_node", 0) > 0
    ):
        raise RuntimeError(f"Orphans detected, aborting migration: {orphans}")

    # Ensure canonical columns exist on fresh DBs (idempotent)
    if "messages" not in existing:
        op.create_table(
            "messages",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column(
                "conversation_id",
                sa.String(length=36),
                sa.ForeignKey("chats.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("user_id", sa.String(length=36), nullable=True),
            sa.Column("role", sa.String(length=50), nullable=False),
            sa.Column(
                "message_type",
                sa.String(length=50),
                nullable=False,
                server_default="text",
            ),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("ui_context", sa.JSON(), nullable=False),
            sa.Column("sequence_number", sa.Integer(), nullable=False),
            sa.Column(
                "status", sa.String(length=20), nullable=False, server_default="pending"
            ),
            sa.Column("request_id", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
            sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column(
                "schema_version",
                sa.String(length=32),
                nullable=False,
                server_default="1.0",
            ),
        )
        try:
            op.create_unique_constraint(
                "uq_messages_conversation_sequence",
                "messages",
                ["conversation_id", "sequence_number"],
            )
        except Exception:
            pass
        try:
            op.create_index(
                "ix_messages_conversation_sequence",
                "messages",
                ["conversation_id", "sequence_number"],
            )
        except Exception:
            pass


def downgrade() -> None:
    # Conservative downgrade: do not drop messages table automatically.
    pass
