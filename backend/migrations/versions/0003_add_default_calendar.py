"""add is_default to calendars and unique per-owner constraint

Revision ID: 0003_add_default_calendar
Revises: 0002_create_calendars_events
Create Date: 2026-08-01 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_default_calendar'
down_revision = '0002_create_calendars_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # add column
    op.add_column('calendars', sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')))

    # try to create a unique partial index (owner_id where is_default true)
    # PostgreSQL supports partial indexes via postgresql_where; SQLite recent versions support sqlite_where.
    try:
        op.create_index(
            'uq_calendars_owner_default',
            'calendars',
            ['owner_id'],
            unique=True,
            postgresql_where=sa.text('is_default'),
            sqlite_where=sa.text('is_default'),
        )
    except Exception:
        # best-effort: some dialects may not accept the where clause; fall back to no index
        pass


def downgrade() -> None:
    try:
        op.drop_index('uq_calendars_owner_default', table_name='calendars')
    except Exception:
        pass

    op.drop_column('calendars', 'is_default')
