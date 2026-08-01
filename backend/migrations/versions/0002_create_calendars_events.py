"""create calendars and events tables

Revision ID: 0002_create_calendars_events
Revises: None
Create Date: 2026-08-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_create_calendars_events'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'calendars',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('owner_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    # index is created by SQLAlchemy metadata when using create_all; keep for Alembic completeness
    try:
        op.create_index('ix_calendars_owner_id', 'calendars', ['owner_id'])
    except Exception:
        pass

    op.create_table(
        'events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('calendar_id', sa.String(length=36), sa.ForeignKey('calendars.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('end', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('all_day', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    try:
        op.create_index('ix_events_calendar_start', 'events', ['calendar_id', 'start'])
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index('ix_events_calendar_start', table_name='events')
    op.drop_table('events')
    op.drop_index('ix_calendars_owner_id', table_name='calendars')
    op.drop_table('calendars')
