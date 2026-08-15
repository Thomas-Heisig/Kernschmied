"""add parent message relation

Revision ID: 0023_add_message_parent
Revises: 0022_create_user_mailboxes
Create Date: 2026-08-15 21:30:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "0023_add_message_parent"
down_revision = "0022_create_user_mailboxes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("messages")}
    if "parent_message_id" in columns:
        return

    with op.batch_alter_table("messages") as batch_op:
        batch_op.add_column(sa.Column("parent_message_id", sa.String(36), nullable=True))
        batch_op.create_foreign_key(
            "fk_messages_parent_message_id",
            "messages",
            ["parent_message_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_messages_parent_message_id",
            ["parent_message_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("messages")}
    if "parent_message_id" not in columns:
        return

    with op.batch_alter_table("messages") as batch_op:
        batch_op.drop_index("ix_messages_parent_message_id")
        batch_op.drop_constraint("fk_messages_parent_message_id", type_="foreignkey")
        batch_op.drop_column("parent_message_id")
