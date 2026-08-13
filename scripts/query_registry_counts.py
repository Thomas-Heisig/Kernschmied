import sqlite3

db = r'F:/Kernschmied/backend/data/chat.db'
conn = sqlite3.connect(db)
cur = conn.cursor()
core = ['calendar','system_health','audit_log','registry_editor','files','chat']
for name in core:
    cur.execute('SELECT id,name,status FROM widget_registry WHERE name LIKE ?', (name+'%',))
    rows = cur.fetchall()
    print(name, len(rows))
    for r in rows:
        print('  ', r)
conn.close()
