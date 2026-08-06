"""consolidate hierarchy_nodes schema

Revision ID: 0009_consolidate_hierarchy_node_schema
Revises: 0008_remove_sequence_server_default
Create Date: 2026-08-02 13:30:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0009_consolidate_hierarchy_node_schema"
down_revision = "0008_remove_sequence_server_default"
branch_labels = None
depends_on = None


def _sqlite_rebuild_table(conn: sa.engine.Connection) -> None:
    """Rebuild hierarchy_nodes table for SQLite, mapping legacy columns to canonical schema."""
    inspector = sa.inspect(conn)
    existing_cols = {c["name"] for c in inspector.get_columns("hierarchy_nodes")}

    # Create new table with canonical schema
    conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS hierarchy_nodes_new (
                id VARCHAR(36) PRIMARY KEY,
                parent_id VARCHAR(36) NULL,
                type VARCHAR(100) NOT NULL,
                name VARCHAR(255) NULL,
                position INTEGER NOT NULL DEFAULT 0,
                system_prompt TEXT NULL,
                tool_policy JSON NOT NULL DEFAULT (json('{}')),
                config_overrides JSON NOT NULL DEFAULT (json('{}')),
                metadata JSON NOT NULL DEFAULT (json('{}')),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                FOREIGN KEY(parent_id) REFERENCES hierarchy_nodes(id)
            );
            """))

    # Determine which legacy columns exist
    has_node_type = "node_type" in existing_cols
    has_type = "type" in existing_cols
    has_prompt = "prompt" in existing_cols
    has_system_prompt = "system_prompt" in existing_cols
    has_config = "config" in existing_cols
    has_config_overrides = "config_overrides" in existing_cols
    has_tool_policy = "tool_policy" in existing_cols
    has_metadata = "metadata" in existing_cols
    has_is_active = "is_active" in existing_cols
    has_position = "position" in existing_cols
    has_parent_id = "parent_id" in existing_cols
    has_created_at = "created_at" in existing_cols
    has_updated_at = "updated_at" in existing_cols
    has_name = "name" in existing_cols

    # Build SELECT list with COALESCE for each target column
    select_parts: list[str] = []

    # id
    select_parts.append("id")
    # parent_id
    select_parts.append("parent_id" if has_parent_id else "NULL AS parent_id")
    # type
    if has_node_type and has_type:
        select_parts.append("COALESCE(node_type, type, 'unknown') AS type")
    elif has_node_type:
        select_parts.append("COALESCE(node_type, 'unknown') AS type")
    elif has_type:
        select_parts.append("COALESCE(type, 'unknown') AS type")
    else:
        select_parts.append("'unknown' AS type")
    # name
    select_parts.append("name" if has_name else "NULL AS name")
    # position
    if has_position:
        select_parts.append("COALESCE(position, 0) AS position")
    else:
        select_parts.append("0 AS position")
    # system_prompt
    if has_prompt and has_system_prompt:
        select_parts.append("COALESCE(prompt, system_prompt) AS system_prompt")
    elif has_prompt:
        select_parts.append("prompt AS system_prompt")
    elif has_system_prompt:
        select_parts.append("system_prompt")
    else:
        select_parts.append("NULL AS system_prompt")
    # tool_policy
    if has_tool_policy:
        select_parts.append("COALESCE(tool_policy, json('{}')) AS tool_policy")
    else:
        select_parts.append("json('{}') AS tool_policy")
    # config_overrides
    if has_config and has_config_overrides:
        select_parts.append(
            "COALESCE(config, config_overrides, json('{}')) AS config_overrides"
        )
    elif has_config:
        select_parts.append("COALESCE(config, json('{}')) AS config_overrides")
    elif has_config_overrides:
        select_parts.append(
            "COALESCE(config_overrides, json('{}')) AS config_overrides"
        )
    else:
        select_parts.append("json('{}') AS config_overrides")
    # metadata
    if has_metadata:
        select_parts.append("COALESCE(metadata, json('{}')) AS metadata")
    else:
        select_parts.append("json('{}') AS metadata")
    # is_active
    if has_is_active:
        select_parts.append("COALESCE(is_active, 1) AS is_active")
    else:
        select_parts.append("1 AS is_active")
    # created_at
    select_parts.append(
        "created_at" if has_created_at else "CURRENT_TIMESTAMP AS created_at"
    )
    # updated_at
    select_parts.append(
        "updated_at" if has_updated_at else "CURRENT_TIMESTAMP AS updated_at"
    )

    # Build the INSERT statement
    columns = [
        "id",
        "parent_id",
        "type",
        "name",
        "position",
        "system_prompt",
        "tool_policy",
        "config_overrides",
        "metadata",
        "is_active",
        "created_at",
        "updated_at",
    ]
    column_list = ", ".join(columns)
    select_clause = ", ".join(select_parts)

    insert_sql = f"""
        INSERT INTO hierarchy_nodes_new ({column_list})
        SELECT {select_clause}
        FROM hierarchy_nodes;
    """
    conn.execute(sa.text(insert_sql))

    # Drop old and rename new
    conn.execute(sa.text("DROP TABLE hierarchy_nodes;"))
    conn.execute(sa.text("ALTER TABLE hierarchy_nodes_new RENAME TO hierarchy_nodes;"))

    # Recreate index
    try:
        conn.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS ix_hierarchy_nodes_parent_position ON hierarchy_nodes(parent_id, position);"
            )
        )
    except Exception:
        pass


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = inspector.get_table_names()

    if "hierarchy_nodes" not in existing:
        return

    # SQLite: full rebuild to canonical schema
    if conn.dialect.name == "sqlite":
        conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
        try:
            _sqlite_rebuild_table(conn)
            conn.execute(sa.text("PRAGMA foreign_keys=ON"))

            # Check for orphaned chats referencing missing nodes
            try:
                result = conn.execute(
                    sa.text(
                        "SELECT c.id, c.node_id FROM chats c LEFT JOIN hierarchy_nodes h ON h.id = c.node_id WHERE h.id IS NULL;"
                    )
                )
                orphans = list(result)
                if orphans:
                    print(
                        "WARNING: orphaned chat.node_id entries after migration:",
                        orphans,
                    )
            except Exception:
                pass

            # Verify foreign key integrity
            try:
                fk_result = conn.execute(sa.text("PRAGMA foreign_key_check;"))
                fk_issues = list(fk_result)
                if fk_issues:
                    raise RuntimeError(
                        f"Foreign key check failed after migration: {fk_issues}"
                    )
            except Exception:
                # If FK check fails, abort to avoid inconsistent state
                raise
        finally:
            try:
                conn.execute(sa.text("PRAGMA foreign_keys=ON"))
            except Exception:
                pass

    else:
        # Non‑SQLite: add missing columns and migrate data
        with op.batch_alter_table("hierarchy_nodes") as batch_op:
            cols = {c["name"] for c in inspector.get_columns("hierarchy_nodes")}
            if "type" not in cols:
                batch_op.add_column(
                    sa.Column(
                        "type",
                        sa.String(length=100),
                        nullable=False,
                        server_default="unknown",
                    )
                )
            if "system_prompt" not in cols:
                batch_op.add_column(
                    sa.Column("system_prompt", sa.Text(), nullable=True)
                )
            if "tool_policy" not in cols:
                batch_op.add_column(
                    sa.Column(
                        "tool_policy",
                        sa.JSON(),
                        nullable=False,
                        server_default=sa.text("'{}'"),
                    )
                )
            if "config_overrides" not in cols:
                batch_op.add_column(
                    sa.Column(
                        "config_overrides",
                        sa.JSON(),
                        nullable=False,
                        server_default=sa.text("'{}'"),
                    )
                )
            if "metadata" not in cols:
                batch_op.add_column(
                    sa.Column(
                        "metadata",
                        sa.JSON(),
                        nullable=False,
                        server_default=sa.text("'{}'"),
                    )
                )

        # Map legacy data
        try:
            conn.execute(
                sa.text("UPDATE hierarchy_nodes SET type = COALESCE(node_type, type);")
            )
            conn.execute(
                sa.text(
                    "UPDATE hierarchy_nodes SET system_prompt = COALESCE(prompt, system_prompt);"
                )
            )
            conn.execute(
                sa.text(
                    "UPDATE hierarchy_nodes SET config_overrides = COALESCE(config, config_overrides);"
                )
            )
        except Exception:
            pass


def downgrade() -> None:
    # Downgrade is intentionally a no-op to avoid data loss.
    pass
