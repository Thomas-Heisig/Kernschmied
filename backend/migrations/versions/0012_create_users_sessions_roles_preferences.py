"""create users, sessions, roles and preferences

Revision ID: 0012_create_users_sessions_roles_preferences
Revises: 0011_create_system_root_and_reparent_nodes
Create Date: 2026-08-03 12:45:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0012_create_users_sessions_roles_preferences"
down_revision = "0011_create_system_root_and_reparent_nodes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _conn = op.get_bind()

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("password_hash", sa.String(length=512), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column(
            "is_system_admin", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "failed_login_attempts", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column(
            "schema_version", sa.String(length=16), nullable=False, server_default="1.0"
        ),
    )

    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Roles and permissions
    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "schema_version", sa.String(length=16), nullable=False, server_default="1.0"
        ),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("permission", sa.String(length=200), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "schema_version", sa.String(length=16), nullable=False, server_default="1.0"
        ),
    )

    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            sa.String(length=36),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_roles"),
    )

    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            sa.String(length=36),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            sa.String(length=36),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permissions"),
    )

    # Auth sessions
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_token_hash", sa.String(length=512), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("csrf_token_hash", sa.String(length=512), nullable=True),
        sa.Column(
            "schema_version", sa.String(length=16), nullable=False, server_default="1.0"
        ),
    )

    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index(
        "ix_auth_sessions_session_token_hash",
        "auth_sessions",
        ["session_token_hash"],
        unique=False,
    )

    # User preferences
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(length=16), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("theme", sa.String(length=50), nullable=True),
        sa.Column("accent_color", sa.String(length=32), nullable=True),
        sa.Column(
            "compact_mode", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("default_model_id", sa.String(length=255), nullable=True),
        sa.Column("default_workspace_id", sa.String(length=36), nullable=True),
        sa.Column(
            "preferences_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("json('{}')"),
        ),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "schema_version", sa.String(length=16), nullable=False, server_default="1.0"
        ),
    )

    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])


def downgrade() -> None:
    conn = op.get_bind()
    dialect = getattr(conn, "dialect", None)
    _dialect_name = getattr(dialect, "name", "") if dialect is not None else ""

    # Helper to drop an index if it exists; some backends (SQLite) may
    # behave differently, so wrap in try/except to keep downgrade idempotent.
    def _safe_drop_index(name: str, table_name: str | None = None) -> None:
        try:
            if table_name:
                op.drop_index(name, table_name=table_name)
            else:
                op.drop_index(name)
        except Exception:
            # best-effort: ignore missing index or backend-specific errors
            pass

    # Drop association tables first to avoid FK constraint problems.
    # 1) role_permissions
    try:
        op.drop_table("role_permissions")
    except Exception:
        pass

    # 2) user_roles
    try:
        op.drop_table("user_roles")
    except Exception:
        pass

    # 3) user_preferences (drop indices first)
    _safe_drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    try:
        op.drop_table("user_preferences")
    except Exception:
        pass

    # 4) auth_sessions (drop indices first)
    _safe_drop_index("ix_auth_sessions_session_token_hash", table_name="auth_sessions")
    _safe_drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    try:
        op.drop_table("auth_sessions")
    except Exception:
        pass

    # 5) permissions
    try:
        op.drop_table("permissions")
    except Exception:
        pass

    # 6) roles
    try:
        op.drop_table("roles")
    except Exception:
        pass

    # 7) users (drop indices first)
    _safe_drop_index("ix_users_username", table_name="users")
    _safe_drop_index("ix_users_email", table_name="users")
    try:
        op.drop_table("users")
    except Exception:
        pass

    # End of downgrade. This operation is best-effort and written to be
    # repeatable in development and test environments. It intentionally
    # does not touch any other tables.
