"""create user mentions

Revision ID: 0021_create_user_mentions
Revises: 0020_create_widget_assignments
Create Date: 2026-08-15 18:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "0021_create_user_mentions"
down_revision = "0020_create_widget_assignments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "user_mentions" in inspector.get_table_names():
        return

    op.create_table(
        "user_mentions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "message_id",
            sa.String(length=36),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.String(length=36),
            sa.ForeignKey("chats.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mention_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="unread"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "message_id", "target_user_id", name="uq_user_mentions_message_target"
        ),
    )
    op.create_index(
        "ix_user_mentions_target_status",
        "user_mentions",
        ["target_user_id", "status"],
    )
    op.create_index(
        "ix_user_mentions_conversation", "user_mentions", ["conversation_id"]
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "user_mentions" in inspector.get_table_names():
        op.drop_table("user_mentions")