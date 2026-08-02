"""ensure hierarchy_nodes exists and chat indexes

Revision ID: 0005_ensure_hierarchy_and_chat_schema
Revises: 0004_create_chats_messages
Create Date: 2026-08-02 12:45:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_ensure_hierarchy_and_chat_schema'
down_revision = '0004_create_chats_messages'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = inspector.get_table_names()

    # ensure hierarchy_nodes table exists (idempotent)
    if 'hierarchy_nodes' not in existing:
        op.create_table(
            'hierarchy_nodes',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('parent_id', sa.String(length=36), nullable=True),
            sa.Column('node_type', sa.String(length=100), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=True),
            sa.Column('prompt', sa.Text(), nullable=True),
            sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('config', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        )
        try:
            op.create_index('ix_hierarchy_nodes_parent_position', 'hierarchy_nodes', ['parent_id', 'position'])
        except Exception:
            pass

    # ensure chats table has index on node_id (do not alter constraints here)
    if 'chats' in existing:
        try:
            index_names = [idx['name'] for idx in inspector.get_indexes('chats')]
            if 'ix_chats_node_id' not in index_names:
                op.create_index('ix_chats_node_id', 'chats', ['node_id'])
        except Exception:
            pass


def downgrade() -> None:
    # Do not drop hierarchy_nodes in downgrade to avoid data loss in conservative flows.
    # This downgrade keeps the operation lightweight and reversible in schema-only contexts.
    pass
