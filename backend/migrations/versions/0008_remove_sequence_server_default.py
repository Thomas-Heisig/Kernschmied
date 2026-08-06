"""remove server_default for messages.sequence_number on SQLite

Revision ID: 0008_remove_sequence_server_default
Revises: 0007_consolidate_message_schema
Create Date: 2026-08-02 12:55:00.000000
"""

from typing import Any, cast

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_remove_sequence_server_default"
down_revision = "0007_consolidate_message_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Only perform the table-copy maneuver on SQLite; other DBs can ALTER
    if conn.dialect.name == "sqlite":
        # create new table without server_default for sequence_number
        raw_conn = cast(Any, conn.engine.raw_connection())
        try:
            sql = """
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS messages_new (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    user_id TEXT,
    role TEXT NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    ui_context JSON NOT NULL,
    sequence_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    request_id TEXT,
    created_at DATETIME NOT NULL,
    completed_at DATETIME,
    schema_version TEXT NOT NULL
);
INSERT INTO messages_new (id, conversation_id, user_id, role, message_type, content, ui_context, sequence_number, status, request_id, created_at, completed_at, schema_version)
SELECT id, conversation_id, user_id, role, message_type, content, ui_context, sequence_number, status, request_id, created_at, completed_at, schema_version FROM messages;
DROP TABLE messages;
ALTER TABLE messages_new RENAME TO messages;
CREATE UNIQUE INDEX IF NOT EXISTS uq_messages_conversation_sequence ON messages(conversation_id, sequence_number);
CREATE INDEX IF NOT EXISTS ix_messages_conversation_sequence ON messages(conversation_id, sequence_number);
COMMIT;
PRAGMA foreign_keys=ON;
"""
            raw_conn.executescript(sql)
            raw_conn.commit()
        finally:
            try:
                raw_conn.close()
            except Exception:
                pass
    else:
        # For other dialects attempt a safe ALTER (best-effort)
        try:
            op.alter_column(
                "messages", "sequence_number", server_default=cast(Any, None)
            )
        except Exception:
            pass


def downgrade() -> None:
    # Downgrade is intentionally a no-op in order to avoid reintroducing server defaults.
    pass
