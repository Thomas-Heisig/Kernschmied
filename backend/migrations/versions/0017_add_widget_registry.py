"""add widget registry and widget_assignments field

Revision ID: 0017_add_widget_registry
Revises: 0016_add_role_flags
Create Date: 2026-08-09 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0017_add_widget_registry"
down_revision = "0016_add_role_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create widget_registry table if it does not exist
    if "widget_registry" not in inspector.get_table_names():
        op.create_table(
            "widget_registry",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("type", sa.String(length=100), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("default_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    # Add widget_assignments column to hierarchy_nodes
    if "hierarchy_nodes" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("hierarchy_nodes")}
        if "widget_assignments" not in cols:
            with op.batch_alter_table("hierarchy_nodes") as batch_op:
                batch_op.add_column(
                    sa.Column("widget_assignments", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
                )

    # Remove server defaults where applicable to keep schema clean
    if "hierarchy_nodes" in inspector.get_table_names():
        with op.batch_alter_table("hierarchy_nodes") as batch_op:
            try:
                batch_op.alter_column("widget_assignments", server_default=None)
            except Exception:
                pass


def downgrade() -> None:
    # Downgrade intentionally disabled to avoid accidental data loss
    pass
