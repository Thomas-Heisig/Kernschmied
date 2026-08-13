import sqlite3
from pathlib import Path

f = Path('data/kernschmied.db')
if not f.exists():
    print('missing', f)
else:
    conn = sqlite3.connect(f)
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, node_id, widget_id, name, enabled, inherit, position, configuration, required_permissions FROM widget_assignments WHERE node_id = ?', ('bootstrap-admin',))
        rows = cur.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print('err', e)
    conn.close()
