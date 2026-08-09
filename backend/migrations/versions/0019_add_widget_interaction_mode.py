"""add interaction_mode to widget_registry

Revision ID: 0019_add_widget_interaction_mode
Revises: 0018_seed_system_widgets
Create Date: 2026-08-09 12:55:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0019_add_widget_interaction_mode"
down_revision = "0018_seed_system_widgets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "widget_registry" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("widget_registry")}
        with op.batch_alter_table("widget_registry") as batch_op:
            if "interaction_mode" not in cols:
                batch_op.add_column(sa.Column("interaction_mode", sa.String(length=32), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "widget_registry" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("widget_registry")}
        with op.batch_alter_table("widget_registry") as batch_op:
            if "interaction_mode" in cols:
                batch_op.drop_column("interaction_mode")
