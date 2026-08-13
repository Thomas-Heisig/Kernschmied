import sqlite3, json
DB=r'F:/Kernschmied/backend/data/chat.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()

print('=== widget_registry rows where name=="calendar" OR id=="calendar" ===')
for row in cur.execute("SELECT id,name,type,metadata,status,created_at,updated_at FROM widget_registry WHERE name='calendar' OR id='calendar'"):
    id,name,type_,metadata,status,created_at,updated_at = row
    print('registry id:', id)
    print(' name:', name)
    print(' type:', type_)
    print(' status:', status)
    try:
        print(' widget_metadata:', json.loads(metadata) if metadata else None)
    except Exception:
        print(' widget_metadata raw:', metadata)
    print(' created_at:', created_at)
    print(' updated_at:', updated_at)
    print(' component_type (from metadata):', (json.loads(metadata).get('component_type') if metadata else None))
    print('---')

print('\n=== assignments for node_id=system-root ===')
for row in cur.execute("SELECT id,node_id,widget_id,name,enabled,inherit,position,configuration,required_permissions FROM widget_assignments WHERE node_id='system-root'"):
    print('assignment id:', row[0])
    print(' node_id:', row[1])
    print(' widget_id:', row[2])
    print(' name:', row[3])
    print(' enabled:', bool(row[4]))
    print(' inherit:', bool(row[5]))
    print(' position:', row[6])
    print(' configuration:', row[7])
    print(' required_permissions:', row[8])
    print('---')

print('\n=== API /api/v1/widgets/ (via DB rows) ===')
for row in cur.execute("SELECT id,name,type,metadata,status FROM widget_registry ORDER BY name LIMIT 200"):
    print(row[0], row[1], row[2], row[4])

conn.close()
