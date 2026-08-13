import sqlite3
from pathlib import Path
p=Path('backend/data/chat.db')
print('db', p.resolve())
conn=sqlite3.connect(str(p))
cur=conn.cursor()
for r in cur.execute('select id,node_id,widget_id,name,enabled,inherit,position,configuration,required_permissions from widget_assignments'):
    print(r)
conn.close()
