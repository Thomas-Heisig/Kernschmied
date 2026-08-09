"""add role flags

Revision ID: 0016_add_role_flags
Revises: 0015_add_is_system_user
Create Date: 2026-08-08 21:50:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0016_add_role_flags'
down_revision = '0015_add_is_system_user'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Add columns if not present
    with op.batch_alter_table('roles') as batch_op:
        try:
            batch_op.add_column(sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('assignable', sa.Boolean(), nullable=False, server_default=sa.text('1')))
        except Exception:
            pass

    # Set sensible defaults for existing known roles
    try:
        conn.execute(sa.text("UPDATE roles SET is_system=1 WHERE name IN ('admin', 'administrator')"))
    except Exception:
        pass


def downgrade() -> None:
    with op.batch_alter_table('roles') as batch_op:
        try:
            batch_op.drop_column('assignable')
        except Exception:
            pass
        try:
            batch_op.drop_column('is_system')
        except Exception:
            pass
