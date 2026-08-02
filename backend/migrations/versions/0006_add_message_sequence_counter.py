"""add chats.next_message_sequence column and initialize

Revision ID: 0006_add_message_sequence_counter
Revises: 0005_ensure_hierarchy_and_chat_schema
Create Date: 2026-08-02 12:46:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_add_message_sequence_counter'
down_revision = '0005_ensure_hierarchy_and_chat_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = inspector.get_table_names()

    if 'chats' in existing:
        cols = [c['name'] for c in inspector.get_columns('chats')]
        if 'next_message_sequence' not in cols:
            # Add column with a short-lived server_default to allow population,
            # then initialize values from messages.
            op.add_column('chats', sa.Column('next_message_sequence', sa.Integer(), nullable=False, server_default='0'))
            try:
                # Populate next_message_sequence from messages: max(sequence_number)+1 per chat
                conn.execute(
                    sa.text(
                        """
                        UPDATE chats
                        SET next_message_sequence = (
                            SELECT COALESCE(MAX(sequence_number), -1) + 1 FROM messages WHERE messages.conversation_id = chats.id
                        )
                        WHERE EXISTS (SELECT 1 FROM messages WHERE messages.conversation_id = chats.id)
                        """
                    )
                )
            except Exception:
                pass
            # Note: removing server_default on SQLite requires table-copy; leave as-is for now.


def downgrade() -> None:
    # Conservative downgrade: do not remove the column to avoid accidental data loss.
    pass
