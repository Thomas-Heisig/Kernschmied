"""add hierarchy policy and prompt fields

Revision ID: 0010_add_hierarchy_policy_fields
Revises: 0009_consolidate_hierarchy_node_schema
Create Date: 2026-08-03 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0010_add_hierarchy_policy_fields"
down_revision = "0009_consolidate_hierarchy_node_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "hierarchy_nodes" not in inspector.get_table_names():
        return

    with op.batch_alter_table("hierarchy_nodes") as batch_op:
        cols = {c["name"] for c in inspector.get_columns("hierarchy_nodes")}

        if "is_system" not in cols:
            batch_op.add_column(
                sa.Column(
                    "is_system",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )

        if "is_movable" not in cols:
            batch_op.add_column(
                sa.Column(
                    "is_movable",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                )
            )

        if "is_deletable" not in cols:
            batch_op.add_column(
                sa.Column(
                    "is_deletable",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                )
            )

        if "prompt_enabled" not in cols:
            batch_op.add_column(
                sa.Column(
                    "prompt_enabled",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                )
            )

        if "prompt_priority" not in cols:
            batch_op.add_column(
                sa.Column(
                    "prompt_priority",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                )
            )

        if "prompt_mode" not in cols:
            batch_op.add_column(
                sa.Column(
                    "prompt_mode",
                    sa.String(length=20),
                    nullable=False,
                    server_default="append",
                )
            )

    # Remove server defaults now that columns exist to keep schema clean
    with op.batch_alter_table("hierarchy_nodes") as batch_op:
        try:
            batch_op.alter_column("is_system", server_default=None)
            batch_op.alter_column("is_movable", server_default=None)
            batch_op.alter_column("is_deletable", server_default=None)
            batch_op.alter_column("prompt_enabled", server_default=None)
            batch_op.alter_column("prompt_priority", server_default=None)
            batch_op.alter_column("prompt_mode", server_default=None)
        except Exception:
            # Some DB backends don't allow altering server_default easily; ignore.
            pass


def downgrade() -> None:
    # Downgrade is intentionally disabled to avoid data loss.
    pass
