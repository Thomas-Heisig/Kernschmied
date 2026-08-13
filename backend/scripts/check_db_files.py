import sqlite3
from pathlib import Path

files = [
    Path('data/chat.db'),
    Path('data/kernschmied.db'),
]

for f in files:
    if not f.exists():
        print(f, 'MISSING')
        continue
    try:
        conn = sqlite3.connect(f)
        cur = conn.cursor()
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='widget_assignments'")
        if cur.fetchone():
            cur.execute('SELECT count(*) FROM widget_assignments')
            cnt = cur.fetchone()[0]
        else:
            cnt = 0
        print(f, 'widget_assignments_count=', cnt)
        # registry count
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='widget_registry'")
        if cur.fetchone():
            cur.execute('SELECT count(*) FROM widget_registry')
            rcnt = cur.fetchone()[0]
        else:
            rcnt = 0
        print(f, 'widget_registry_count=', rcnt)
        conn.close()
    except Exception as e:
        print('ERR', f, e)
