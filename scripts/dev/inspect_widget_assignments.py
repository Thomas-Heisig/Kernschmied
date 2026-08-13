import sqlite3
from pathlib import Path
DB = Path(__file__).resolve().parents[2] / 'backend' / 'data' / 'chat.db'
print('db', DB)
conn = sqlite3.connect(str(DB))
cur = conn.cursor()
print('\nPRAGMA table_info(widget_assignments):')
for r in cur.execute('PRAGMA table_info(widget_assignments);'):
    print(r)
print('\nAll widget_assignments rows:')
for r in cur.execute('SELECT id,node_id,widget_id,name,enabled,inherit,position,configuration,required_permissions,created_at,updated_at FROM widget_assignments'):
    print(r)
conn.close()
