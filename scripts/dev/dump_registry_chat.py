import sqlite3
from pathlib import Path
p = Path('backend/data/chat.db')
print('db', p.resolve())
conn = sqlite3.connect(str(p))
cur = conn.cursor()
for row in cur.execute('select id,name,type,metadata,required_permissions,status from widget_registry'):
    print(row)
conn.close()
