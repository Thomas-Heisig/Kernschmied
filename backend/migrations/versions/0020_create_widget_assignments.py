"""create widget_assignments table

Revision ID: 0020_create_widget_assignments
Revises: 0019_add_widget_interaction_mode
Create Date: 2026-08-09 13:30:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0020_create_widget_assignments"
down_revision = "0019_add_widget_interaction_mode"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "widget_assignments" not in inspector.get_table_names():
        op.create_table(
            "widget_assignments",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("node_id", sa.String(length=36), sa.ForeignKey("hierarchy_nodes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("widget_id", sa.String(length=36), sa.ForeignKey("widget_registry.id", ondelete="SET NULL"), nullable=True),
            sa.Column("name", sa.String(length=100), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("inherit", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("1000")),
            sa.Column("size", sa.String(length=50), nullable=True),
            sa.Column("configuration", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column("required_permissions", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
            sa.Column("visible", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        with op.batch_alter_table("widget_assignments") as batch_op:
            batch_op.create_index(batch_op.f("ix_widget_assignments_node_id"), ["node_id"])
            batch_op.create_index(batch_op.f("ix_widget_assignments_widget_id"), ["widget_id"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "widget_assignments" in inspector.get_table_names():
        op.drop_table("widget_assignments")
