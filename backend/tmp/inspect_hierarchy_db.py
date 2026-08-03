import sqlite3
import sys
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'data' / 'kernschmied.db'
print('db path:', p)
if not p.exists():
    print('ERROR: database file not found at', p)
    sys.exit(2)
conn = sqlite3.connect(str(p))
cur = conn.cursor()

try:
    print('\nPRAGMA table_info(hierarchy_nodes);')
    for row in cur.execute("PRAGMA table_info('hierarchy_nodes')"):
        print(row)

    print('\nPRAGMA index_list(hierarchy_nodes);')
    for row in cur.execute("PRAGMA index_list('hierarchy_nodes')"):
        print(row)

    print('\nPRAGMA foreign_key_list(hierarchy_nodes);')
    for row in cur.execute("PRAGMA foreign_key_list('hierarchy_nodes')"):
        print(row)

    print('\nSELECT COUNT(*) FROM hierarchy_nodes;')
    for row in cur.execute("SELECT COUNT(*) FROM hierarchy_nodes"):
        print(row)

    print('\nSELECT id, parent_id, * FROM hierarchy_nodes ORDER BY position, id LIMIT 20;')
    try:
        for row in cur.execute("SELECT id, parent_id, type, name, position FROM hierarchy_nodes ORDER BY position, id LIMIT 50"):
            print(row)
    except sqlite3.OperationalError:
        # try legacy column names
        try:
            for row in cur.execute("SELECT id, parent_id, node_type, name, position FROM hierarchy_nodes ORDER BY position, id LIMIT 50"):
                print(row)
        except Exception as e:
            print('Failed to select sample rows:', e)

finally:
    conn.close()
