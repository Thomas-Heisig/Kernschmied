"""add unique constraint/index to user_preferences.user_id

Revision ID: 0014_add_unique_user_preferences_user_id
Revises: 0013_add_authentication_method_to_auth_sessions
Create Date: 2026-08-06 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0014_add_unique_user_preferences_user_id"
down_revision = "0013_add_authentication_method_to_auth_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Detect any existing duplicate preferences rows for the same user.
    try:
        res = conn.execute(
            sa.text(
                "SELECT user_id, COUNT(*) as cnt FROM user_preferences GROUP BY user_id HAVING COUNT(*) > 1"
            )
        )
        duplicates = list(res.fetchall())
    except Exception:
        # If the table doesn't exist yet or query fails, re-raise to surface problem.
        raise

    if duplicates:
        # Fail the migration to avoid creating a unique index on inconsistent data.
        dup_ids = ", ".join(str(r[0]) for r in duplicates)
        raise RuntimeError(
            "Cannot create unique index ux_user_preferences_user_id: found duplicate user_preferences for user_id(s): "
            + dup_ids
        )

    # Safe to create a unique index enforcing one row per user
    op.create_index(
        "ux_user_preferences_user_id",
        "user_preferences",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    # Drop the unique index (best-effort)
    try:
        op.drop_index("ux_user_preferences_user_id", table_name="user_preferences")
    except Exception:
        pass
