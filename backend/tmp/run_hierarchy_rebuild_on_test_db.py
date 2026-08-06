import sqlite3
from pathlib import Path

p = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "kernschmied.hierarchy-migration-test.db"
)
print("test db:", p)
if not p.exists():
    print("ERROR: test DB not found")
    raise SystemExit(2)

conn = sqlite3.connect(str(p))
cur = conn.cursor()

try:
    inspector_cols = [r for r in cur.execute("PRAGMA table_info('hierarchy_nodes')")]
    print("existing hierarchy_nodes columns:", [c[1] for c in inspector_cols])

    # Run rebuild similar to migration 0009_consolidate_hierarchy_node_schema
    print("Running safe rebuild...")
    sql = """
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS hierarchy_nodes_new (
    id TEXT PRIMARY KEY,
    parent_id TEXT,
    type TEXT NOT NULL,
    name TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    system_prompt TEXT,
    tool_policy JSON NOT NULL DEFAULT (json('{}')),
    config_overrides JSON NOT NULL DEFAULT (json('{}')),
    metadata JSON NOT NULL DEFAULT (json('{}')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
INSERT INTO hierarchy_nodes_new (id, parent_id, type, name, position, system_prompt, tool_policy, config_overrides, metadata, is_active, created_at, updated_at)
SELECT
    id,
    parent_id,
    COALESCE(
        (CASE WHEN (SELECT COUNT(1) FROM pragma_table_info('hierarchy_nodes') WHERE name='type')>0 THEN type END),
        (CASE WHEN (SELECT COUNT(1) FROM pragma_table_info('hierarchy_nodes') WHERE name='node_type')>0 THEN node_type END),
        'unknown'
    ) AS type,
    COALESCE(name, '') AS name,
    COALESCE(position, 0) AS position,
    COALESCE(
        (CASE WHEN (SELECT COUNT(1) FROM pragma_table_info('hierarchy_nodes') WHERE name='system_prompt')>0 THEN system_prompt END),
        (CASE WHEN (SELECT COUNT(1) FROM pragma_table_info('hierarchy_nodes') WHERE name='prompt')>0 THEN prompt END),
        NULL
    ) AS system_prompt,
    COALESCE(
        (CASE WHEN (SELECT COUNT(1) FROM pragma_table_info('hierarchy_nodes') WHERE name='tool_policy')>0 THEN tool_policy END),
        json('{}')
    ) AS tool_policy,
    COALESCE(
        (CASE WHEN (SELECT COUNT(1) FROM pragma_table_info('hierarchy_nodes') WHERE name='config_overrides')>0 THEN config_overrides END),
        (CASE WHEN (SELECT COUNT(1) FROM pragma_table_info('hierarchy_nodes') WHERE name='config')>0 THEN config END),
        json('{}')
    ) AS config_overrides,
    COALESCE(
        (CASE WHEN (SELECT COUNT(1) FROM pragma_table_info('hierarchy_nodes') WHERE name='metadata')>0 THEN metadata END),
        json('{}')
    ) AS metadata,
    COALESCE(is_active, 1) AS is_active,
    COALESCE(created_at, CURRENT_TIMESTAMP) AS created_at,
    COALESCE(updated_at, CURRENT_TIMESTAMP) AS updated_at
FROM hierarchy_nodes;
DROP TABLE hierarchy_nodes;
ALTER TABLE hierarchy_nodes_new RENAME TO hierarchy_nodes;
CREATE INDEX IF NOT EXISTS ix_hierarchy_nodes_parent_position ON hierarchy_nodes(parent_id, position);
COMMIT;
PRAGMA foreign_keys=ON;
"""
    try:
        cur.executescript(sql)
        conn.commit()
        print("Rebuild completed")
    except Exception as e:
        print("Rebuild failed:", e)
        conn.rollback()
        raise

    print("\nPost-migration checks:")
    for row in cur.execute("PRAGMA table_info('hierarchy_nodes')"):
        print(row)
    print("\nPRAGMA integrity_check:")
    for row in cur.execute("PRAGMA integrity_check"):
        print(row)
    print("\nPRAGMA foreign_key_check:")
    for row in cur.execute("PRAGMA foreign_key_check"):
        print(row)
    print("\nSample rows:")
    for row in cur.execute(
        "SELECT id, parent_id, type, name, position FROM hierarchy_nodes ORDER BY position, id LIMIT 50"
    ):
        print(row)
finally:
    conn.close()
