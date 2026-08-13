import sqlite3, json
db=r'F:/Kernschmied/backend/data/chat.db'
conn=sqlite3.connect(db)
cur=conn.cursor()
print('--- registry where name="calendar" ---')
for row in cur.execute("SELECT id,name,status,widget_metadata,metadata,type FROM widget_registry WHERE name='calendar'"):
    print(row[0],row[1],row[2])
    try:
        print('widget_metadata=', json.loads(row[3]) if row[3] else row[3])
    except Exception:
        print('widget_metadata raw=', row[3])
    try:
        print('metadata=', json.loads(row[4]) if row[4] else row[4])
    except Exception:
        print('metadata raw=', row[4])
    print('type=',row[5])

print('\n--- assignments for bootstrap-admin ---')
for row in cur.execute("SELECT id,node_id,widget_id,name,enabled,inherit,position,configuration FROM widget_assignments WHERE node_id='bootstrap-admin'"):
    print(row)

print('\n--- assignments for project-root ---')
for row in cur.execute("SELECT id,node_id,widget_id,name,enabled,inherit,position,configuration FROM widget_assignments WHERE node_id='project-root'"):
    print(row)

conn.close()
