"""add is_system_user to users

Revision ID: 0015_add_is_system_user
Revises: 0014_add_unique_user_preferences_user_id
Create Date: 2026-08-08 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0015_add_is_system_user"
down_revision = "0014_add_unique_user_preferences_user_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "users" in inspector.get_table_names():
        # Add column if missing
        cols = [c.get("name") for c in inspector.get_columns("users")]
        if "is_system_user" not in cols:
            op.add_column(
                "users",
                sa.Column("is_system_user", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            )


def downgrade() -> None:
    try:
        op.drop_column("users", "is_system_user")
    except Exception:
        pass
