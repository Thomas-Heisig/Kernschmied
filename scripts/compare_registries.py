import sqlite3, json

def inspect(db_path):
    print('\nDB:', db_path)
    try:
        conn=sqlite3.connect(db_path)
        cur=conn.cursor()
        for row in cur.execute("SELECT id,name,type,metadata,status FROM widget_registry WHERE name LIKE '%calendar%' ORDER BY id"):
            print(row[0], row[1], row[2], row[4])
            try:
                print(' metadata:', json.loads(row[3]))
            except Exception:
                print(' metadata raw:', row[3])
        conn.close()
    except Exception as e:
        print('FAILED to open', db_path, e)

inspect(r'F:/Kernschmied/backend/data/chat.db')
inspect(r'F:/Kernschmied/backend/data/kernschmied.db')

print('\n--- assignments in kernschmied.db for bootstrap-admin and project-root')
try:
    conn=__import__('sqlite3').connect(r'F:/Kernschmied/backend/data/kernschmied.db')
    cur=conn.cursor()
    for row in cur.execute("SELECT id,node_id,widget_id,name,enabled,inherit,position,configuration FROM widget_assignments WHERE node_id IN ('bootstrap-admin','project-root') ORDER BY node_id,position"):
        print(row)
    conn.close()
except Exception as e:
    print('failed to read assignments from kernschmied.db', e)
