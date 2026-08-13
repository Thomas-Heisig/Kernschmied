import sqlite3
from pathlib import Path

f = Path('data/kernschmied.db')
conn = sqlite3.connect(f)
cur = conn.cursor()
cur.execute("PRAGMA table_info('hierarchy_nodes')")
for r in cur.fetchall():
    print(r)
conn.close()
