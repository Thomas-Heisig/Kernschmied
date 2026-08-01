import sqlite3
from pathlib import Path

DBS = [Path('backend/data/chat.db'), Path('backend/data/kernschmied.db')]

for db in DBS:
    if not db.exists():
        print(db, 'missing')
        continue
    print('\nRebuilding table in', db)
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA foreign_keys=OFF")
        cur.execute('BEGIN TRANSACTION')
        # Create new table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS hierarchy_nodes_new (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            system_prompt TEXT,
            tool_policy TEXT NOT NULL DEFAULT '{}',
            config_overrides TEXT NOT NULL DEFAULT '{}',
            metadata TEXT NOT NULL DEFAULT '{}',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        # Copy data mapping legacy columns
        cur.execute('''
        INSERT INTO hierarchy_nodes_new (id, parent_id, type, name, position, system_prompt, tool_policy, config_overrides, metadata, is_active, created_at, updated_at)
        SELECT
            id,
            parent_id,
            CASE WHEN type IS NOT NULL AND type != '' THEN type WHEN node_type IS NOT NULL AND node_type != '' THEN node_type ELSE 'unknown' END as type,
            name,
            COALESCE(position, 0) as position,
            COALESCE(system_prompt, prompt) as system_prompt,
            COALESCE(tool_policy, '{}') as tool_policy,
            COALESCE(config_overrides, config, '{}') as config_overrides,
            COALESCE(metadata, '{}') as metadata,
            COALESCE(is_active, 1) as is_active,
            COALESCE(created_at, '1970-01-01') as created_at,
            COALESCE(updated_at, COALESCE(created_at, '1970-01-01')) as updated_at
        FROM hierarchy_nodes
        ''')
        # Drop old table and rename
        cur.execute('DROP TABLE hierarchy_nodes')
        cur.execute('ALTER TABLE hierarchy_nodes_new RENAME TO hierarchy_nodes')
        # Recreate index
        cur.execute("CREATE INDEX IF NOT EXISTS ix_hierarchy_nodes_parent_position ON hierarchy_nodes(parent_id, position)")
        conn.commit()
        print('Rebuilt table successfully')
    except Exception as e:
        conn.rollback()
        print('error during rebuild', e)
    finally:
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
        conn.close()
