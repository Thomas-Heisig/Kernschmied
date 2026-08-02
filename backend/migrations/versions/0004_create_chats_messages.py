"""create chats and messages tables

Revision ID: 0004_create_chats_messages
Revises: 0003_add_default_calendar
Create Date: 2026-08-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_create_chats_messages'
down_revision = '0003_add_default_calendar'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make the migration idempotent: only create tables/indexes if they don't exist.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'chats' not in existing_tables:
        op.create_table(
            'chats',
            sa.Column('id', sa.String(length=36), primary_key=True),
            # Do not enforce a UNIQUE constraint on node_id here. Multiple chats
            # per hierarchy node are allowed and the UNIQUE constraint caused
            # conflicts when a single node was reused.
            sa.Column('node_id', sa.String(length=36), sa.ForeignKey('hierarchy_nodes.id', ondelete='CASCADE'), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('config', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        )
        try:
            op.create_index('ix_chats_node_id', 'chats', ['node_id'])
        except Exception:
            pass
    else:
        # If the table already exists, try to remove an existing UNIQUE constraint
        # on `node_id` to avoid future insert errors. Constraint names vary by
        # backend, so inspect unique constraints and drop any that include
        # the `node_id` column.
        try:
            for uq in inspector.get_unique_constraints('chats'):
                cols = uq.get('column_names') or uq.get('columns') or []
                if 'node_id' in cols:
                    try:
                        op.drop_constraint(uq['name'], 'chats', type_='unique')
                    except Exception:
                        pass
        except Exception:
            pass
        # Ensure the node_id index exists
        try:
            index_names = [idx['name'] for idx in inspector.get_indexes('chats')]
            if 'ix_chats_node_id' not in index_names:
                op.create_index('ix_chats_node_id', 'chats', ['node_id'])
        except Exception:
            pass

    if 'messages' not in existing_tables:
        op.create_table(
            'messages',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('chat_id', sa.String(length=36), sa.ForeignKey('chats.id', ondelete='CASCADE'), nullable=False),
            sa.Column('role', sa.String(length=50), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('metadata_json', sa.JSON(), nullable=False),
            sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        )
        try:
            op.create_index('ix_messages_chat_position', 'messages', ['chat_id', 'position'])
        except Exception:
            pass


def downgrade() -> None:
    try:
        op.drop_index('ix_messages_chat_position', table_name='messages')
    except Exception:
        pass
    op.drop_table('messages')

    try:
        op.drop_index('ix_chats_node_id', table_name='chats')
    except Exception:
        pass
    op.drop_table('chats')
