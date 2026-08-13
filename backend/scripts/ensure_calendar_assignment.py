import sqlite3, json, uuid, datetime

DB='data/kernschmied.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()

# Ensure calendar widget in widget_registry
cur.execute("SELECT id FROM widget_registry WHERE name=?", ('calendar',))
row=cur.fetchone()
if row:
    wid=row[0]
    print('calendar exists', wid)
else:
    wid=str(uuid.uuid4())
    metadata={'component_type':'calendar_widget','supported_node_types':['user','workspace','project','chat','folder'],'icon':'calendar','description':'Calendar widget'}
    now=datetime.datetime.utcnow().isoformat()
    cur.execute("INSERT INTO widget_registry (id,name,type,metadata,default_config,required_permissions,status,version,interaction_mode,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (wid,'calendar','calendar_widget',json.dumps(metadata),json.dumps({}),json.dumps([]),'active','1.0','panel',now,now))
    conn.commit()
    print('inserted calendar', wid)

# find node id to assign to
cur.execute("SELECT id FROM hierarchy_nodes WHERE id IN ('bootstrap-admin','system-root') LIMIT 1")
row=cur.fetchone()
if row:
    node_id=row[0]
    print('assign to node', node_id)
else:
    print('no bootstrap-admin or system-root node found; listing first 5 nodes')
    cur.execute('SELECT id,name FROM hierarchy_nodes LIMIT 5')
    for r in cur.fetchall():
        print(r)
    node_id=None

if node_id:
    cur.execute('SELECT id FROM widget_assignments WHERE node_id=? AND widget_id=?', (node_id,wid))
    if cur.fetchone():
        print('assignment exists')
    else:
        aid=str(uuid.uuid4())
        now=datetime.datetime.utcnow().isoformat()
        cur.execute('INSERT INTO widget_assignments (id,node_id,widget_id,name,enabled,inherit,position,size,configuration,required_permissions,visible,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (aid,node_id,wid,'calendar',1,1,1000,None,json.dumps({}),json.dumps([]),None,now,now))
        conn.commit()
        print('inserted assignment', aid)

conn.close()
print('done')
