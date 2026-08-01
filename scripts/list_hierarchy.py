import sqlite3
from pathlib import Path

for db in [Path('backend/data/kernschmied.db'), Path('backend/data/chat.db')]:
    if not db.exists():
        print(db, 'missing')
        continue
    print('\nDB:', db)
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, parent_id, type, name, position FROM hierarchy_nodes ORDER BY parent_id, position LIMIT 50")
        for r in cur.fetchall():
            print(r)
    except Exception as e:
        print('error', e)
    finally:
        cur.close()
        conn.close()
