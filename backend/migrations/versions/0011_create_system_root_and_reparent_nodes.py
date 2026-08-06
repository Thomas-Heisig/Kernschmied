"""create system-root and reparent existing root nodes

Revision ID: 0011_create_system_root_and_reparent_nodes
Revises: 0010_add_hierarchy_policy_fields
Create Date: 2026-08-03 12:30:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0011_create_system_root_and_reparent_nodes"
down_revision = "0010_add_hierarchy_policy_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) Insert system-root if missing
    conn.execute(sa.text("""
            INSERT INTO hierarchy_nodes (
                id,
                parent_id,
                type,
                name,
                position,
                system_prompt,
                tool_policy,
                config_overrides,
                metadata,
                is_active,
                is_system,
                is_movable,
                is_deletable,
                prompt_enabled,
                prompt_priority,
                prompt_mode,
                created_at,
                updated_at
            )
            SELECT
                'system-root',
                NULL,
                'system_root',
                'System',
                0,
                NULL,
                json('{}'),
                json('{}'),
                json('{}'),
                1,
                1,
                0,
                0,
                1,
                -1000,
                'append',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            WHERE NOT EXISTS (
                SELECT 1 FROM hierarchy_nodes WHERE id = 'system-root'
            );
            """))

    # 2) Repair protective flags on system-root if it already exists
    conn.execute(sa.text("""
            UPDATE hierarchy_nodes
            SET
                parent_id = NULL,
                type = 'system_root',
                is_system = 1,
                is_movable = 0,
                is_deletable = 0,
                prompt_enabled = 1,
                prompt_priority = -1000,
                prompt_mode = 'append'
            WHERE id = 'system-root';
            """))

    # 3) Reparent existing top-level nodes (except system-root) under system-root
    conn.execute(sa.text("""
            UPDATE hierarchy_nodes
            SET parent_id = 'system-root'
            WHERE parent_id IS NULL
              AND id <> 'system-root';
            """))

    # 4) Optional: ensure deterministic ordering for children of system-root
    # If desired, this could set positions based on previous rowid or created_at.


def downgrade() -> None:
    # Downgrade intentionally omitted to avoid accidental data loss.
    pass
