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
    op.create_table(
        'chats',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('node_id', sa.String(length=36), sa.ForeignKey('hierarchy_nodes.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    try:
        op.create_index('ix_chats_node_id', 'chats', ['node_id'])
    except Exception:
        pass

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
