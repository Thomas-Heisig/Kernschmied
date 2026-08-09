"""seed system widgets into registry and assign to system root

Revision ID: 0018_seed_system_widgets
Revises: 0017_add_widget_registry
Create Date: 2026-08-09 12:30:00.000000
"""

import json
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0018_seed_system_widgets"
down_revision = "0017_add_widget_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Ensure new columns exist when upgrading from older schema
    if "widget_registry" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("widget_registry")}
        with op.batch_alter_table("widget_registry") as batch_op:
            if "required_permissions" not in cols:
                batch_op.add_column(sa.Column("required_permissions", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
            if "status" not in cols:
                batch_op.add_column(sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")))
            if "version" not in cols:
                batch_op.add_column(sa.Column("version", sa.String(length=32), nullable=True))

    # Insert registry entries for system widgets
    widget_rows = [
        {
            "id": "w-system-health",
            "name": "system_health",
            "type": "system",
            "metadata": json.dumps({"icon": "server", "description": "System status"}),
            "default_config": json.dumps({}),
            "required_permissions": json.dumps(["admin"]),
            "status": "active",
            "version": "1.0",
        },
        {
            "id": "w-audit-log",
            "name": "audit_log",
            "type": "system",
            "metadata": json.dumps({"icon": "list", "description": "Recent audit log"}),
            "default_config": json.dumps({}),
            "required_permissions": json.dumps(["admin"]),
            "status": "active",
            "version": "1.0",
        },
        {
            "id": "w-registry-editor",
            "name": "registry_editor",
            "type": "system",
            "metadata": json.dumps({"icon": "edit", "description": "Registry management"}),
            "default_config": json.dumps({}),
            "required_permissions": json.dumps(["admin"]),
            "status": "active",
            "version": "1.0",
        },
    ]

    for r in widget_rows:
        try:
            conn.execute(
                sa.text(
                    "INSERT INTO widget_registry (id, name, type, metadata, default_config, required_permissions, status, version, created_at, updated_at) VALUES (:id, :name, :type, :metadata, :default_config, :required_permissions, :status, :version, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                r,
            )
        except Exception:
            # ignore insertion errors if already present
            pass

    # Assign these widgets to the stable system root node 'system-root' if present
    try:
        # Build JSON array of assignments
        assigns = json.dumps([
            {"name": "system_health", "icon": "server"},
            {"name": "audit_log", "icon": "list"},
            {"name": "registry_editor", "icon": "edit"},
        ])

        conn.execute(
            sa.text(
                "UPDATE hierarchy_nodes SET widget_assignments = :assigns WHERE id = :id"
            ),
            {"assigns": assigns, "id": "system-root"},
        )
    except Exception:
        pass


def downgrade() -> None:
    # Intentionally not reversible
    pass
