"""create files table

Revision ID: 0018_create_files
Revises: 0017_add_widget_registry
Create Date: 2026-08-09 12:30:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0018_create_files"
down_revision = "0017_add_widget_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "files" not in inspector.get_table_names():
        op.create_table(
            "files",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("node_id", sa.String(length=36), nullable=True),
            sa.Column("owner_id", sa.String(length=36), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("mime_type", sa.String(length=255), nullable=True),
            sa.Column("size", sa.Integer(), nullable=True),
            sa.Column("storage_path", sa.String(length=1024), nullable=True),
            sa.Column("source", sa.String(length=32), nullable=False, server_default=sa.text("'upload'")),
            sa.Column("deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )


def downgrade() -> None:
    # Downgrade intentionally disabled to avoid accidental data loss
    pass
