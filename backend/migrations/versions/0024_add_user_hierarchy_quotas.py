"""add per-user hierarchy quotas

Revision ID: 0024_add_user_hierarchy_quotas
Revises: 0023_add_message_parent
Create Date: 2026-08-15 23:50:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "0024_add_user_hierarchy_quotas"
down_revision = "0023_add_message_parent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("workspace_quota", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("project_quota", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("chat_quota", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("chat_quota")
        batch_op.drop_column("project_quota")
        batch_op.drop_column("workspace_quota")
