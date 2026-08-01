import sqlite3
from pathlib import Path

DBS = [Path('backend/data/chat.db'), Path('backend/data/kernschmied.db')]

for db in DBS:
    if not db.exists():
        print(f"{db} does not exist, skipping")
        continue
    print(f"Processing {db}")
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info('hierarchy_nodes')")
        cols = [r[1] for r in cur.fetchall()]
        print('existing columns:', cols)
        # Add missing columns
        adds = []
        if 'system_prompt' not in cols:
            adds.append("ALTER TABLE hierarchy_nodes ADD COLUMN system_prompt TEXT DEFAULT NULL")
        if 'tool_policy' not in cols:
            adds.append("ALTER TABLE hierarchy_nodes ADD COLUMN tool_policy TEXT DEFAULT '{}'")
        if 'config_overrides' not in cols:
            adds.append("ALTER TABLE hierarchy_nodes ADD COLUMN config_overrides TEXT DEFAULT '{}'")
        if 'metadata' not in cols:
            adds.append("ALTER TABLE hierarchy_nodes ADD COLUMN metadata TEXT DEFAULT '{}'")
        for a in adds:
            print('Executing:', a)
            cur.execute(a)
        conn.commit()
        # Refresh cols
        cur.execute("PRAGMA table_info('hierarchy_nodes')")
        cols = [r[1] for r in cur.fetchall()]
        print('after add columns:', cols)
        # Copy legacy values
        # node_type -> type
        if 'node_type' in cols and 'type' in cols:
            print('Copying node_type -> type')
            cur.execute("UPDATE hierarchy_nodes SET type = node_type WHERE (type IS NULL OR type = '' OR type = 'unknown') AND node_type IS NOT NULL")
        # prompt -> system_prompt
        if 'prompt' in cols and 'system_prompt' in cols:
            print('Copying prompt -> system_prompt')
            cur.execute("UPDATE hierarchy_nodes SET system_prompt = prompt WHERE system_prompt IS NULL AND prompt IS NOT NULL")
        # config -> config_overrides
        if 'config' in cols and 'config_overrides' in cols:
            print('Copying config -> config_overrides')
            cur.execute("UPDATE hierarchy_nodes SET config_overrides = config WHERE config_overrides = '{}' OR config_overrides IS NULL")
        conn.commit()
        # Show sample row
        cur.execute("SELECT id, parent_id, type, node_type, name, prompt, system_prompt, config, config_overrides, metadata FROM hierarchy_nodes LIMIT 5")
        rows = cur.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print('error:', e)
    finally:
        cur.close()
        conn.close()
