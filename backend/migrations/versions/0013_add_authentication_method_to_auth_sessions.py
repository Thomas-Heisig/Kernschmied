"""Add authentication_method to auth_sessions

Revision ID: 0013_add_authentication_method_to_auth_sessions
Revises: 0012_create_users_sessions_roles_preferences
Create Date: 2026-08-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0013_add_authentication_method_to_auth_sessions'
down_revision = '0012_create_users_sessions_roles_preferences'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite needs special handling for adding columns in some cases.
    op.add_column('auth_sessions', sa.Column('authentication_method', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('auth_sessions', 'authentication_method')
