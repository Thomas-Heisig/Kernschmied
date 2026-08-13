import sqlite3
import json
import datetime
import uuid

DB = 'data/kernschmied.db'

def now():
    return datetime.datetime.utcnow().isoformat()

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ensure tables exist (safe no-op if created by alembic)
cur.execute("CREATE TABLE IF NOT EXISTS widget_registry (id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT, metadata JSON, default_config JSON, required_permissions JSON, status TEXT, version TEXT, interaction_mode TEXT, created_at TEXT, updated_at TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS widget_assignments (id TEXT PRIMARY KEY, node_id TEXT NOT NULL, widget_id TEXT, name TEXT, enabled INTEGER NOT NULL DEFAULT 1, inherit INTEGER NOT NULL DEFAULT 1, position INTEGER NOT NULL DEFAULT 1000, size TEXT, configuration JSON, required_permissions JSON, visible JSON, created_at TEXT, updated_at TEXT)")
conn.commit()

widget_pool = [
    ("system_health","system_health_widget",{"component_type":"system_health_widget","supported_node_types":["system"]}),
    ("audit_log","audit_log_widget",{"component_type":"audit_log_widget","supported_node_types":["system"]}),
    ("registry_editor","registry_editor_widget",{"component_type":"registry_editor_widget","supported_node_types":["system"]}),
    ("calendar","calendar_widget",{"component_type":"calendar_widget","supported_node_types":["user","workspace","project","chat","folder"]}),
    ("files","files_widget",{"component_type":"files_widget","supported_node_types":["workspace","project","chat","user","folder"]}),
    ("chat","chat_widget",{"component_type":"chat_widget","supported_node_types":["chat","user","workspace"]}),
]

for name, typ, meta in widget_pool:
    cur.execute("SELECT id FROM widget_registry WHERE name=?", (name,))
    if cur.fetchone() is None:
        wid = str(uuid.uuid4())
        cur.execute("INSERT INTO widget_registry (id,name,type,metadata,default_config,required_permissions,status,version,interaction_mode,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (wid,name,typ,json.dumps(meta),json.dumps({}),json.dumps([]),"active","1.0","panel",now(),now()))
        print('inserted widget', name)
conn.commit()

# ensure standard nodes exist
standard_nodes = [
    ("system-root", None, "system"),
    ("bootstrap-admin", "system-root", "user"),
    ("workspace-root", "system-root", "folder"),
    ("project-root", "system-root", "folder"),
    ("chat-root", "system-root", "folder"),
]

for nid, parent, ntype in standard_nodes:
    cur.execute("SELECT id FROM hierarchy_nodes WHERE id=?", (nid,))
    if cur.fetchone() is None:
        # detect available columns and compose an insert accordingly
        cols = [r[1] for r in cur.execute("PRAGMA table_info(hierarchy_nodes)")]
        insert_cols = ["id"]
        values = [nid]
        if "parent_id" in cols:
            insert_cols.append("parent_id"); values.append(parent)
        if "type" in cols:
            insert_cols.append("type"); values.append(ntype)
        if "name" in cols:
            insert_cols.append("name"); values.append(nid.replace('-', ' ').title())
        if "position" in cols:
            insert_cols.append("position"); values.append(0)
        if "system_prompt" in cols:
            insert_cols.append("system_prompt"); values.append(None)
        if "tool_policy" in cols:
            insert_cols.append("tool_policy"); values.append(json.dumps({}))
        if "config_overrides" in cols:
            insert_cols.append("config_overrides"); values.append(json.dumps({}))
        if "metadata" in cols:
            insert_cols.append("metadata"); values.append(json.dumps({}))
        if "widget_assignments" in cols:
            insert_cols.append("widget_assignments"); values.append(json.dumps([]))
        # flags that may not exist in older schema are skipped
        if "is_active" in cols:
            insert_cols.append("is_active"); values.append(1)
        if "created_at" in cols:
            insert_cols.append("created_at"); values.append(now())
        if "updated_at" in cols:
            insert_cols.append("updated_at"); values.append(now())

        placeholders = ",".join(["?"] * len(values))
        cur.execute(f"INSERT INTO hierarchy_nodes ({','.join(insert_cols)}) VALUES ({placeholders})", tuple(values))
        print('created node', nid)
conn.commit()

# desired assignments mapping
assignments = {
    "system-root": [
        {"name":"system_health","inherit":False,"position":10},
        {"name":"audit_log","inherit":False,"position":20},
        {"name":"registry_editor","inherit":False,"position":30},
    ],
    "bootstrap-admin": [
        {"name":"calendar","inherit":True,"position":10,"configuration":{"view":"month"}},
        {"name":"files","inherit":True,"position":20},
        {"name":"chat","inherit":True,"position":30},
    ],
    "workspace-root": [
        {"name":"files","inherit":False,"position":10},
    ],
    "project-root": [
        {"name":"calendar","inherit":True,"position":10,"configuration":{"view":"month"}},
        {"name":"files","inherit":False,"position":20},
    ],
    "chat-root": [
        {"name":"chat","inherit":False,"position":10},
        {"name":"files","inherit":False,"position":20},
    ],
}

for node_id, widgets in assignments.items():
    # ensure JSON widget_assignments on node (only when column present)
    cols = [r[1] for r in cur.execute("PRAGMA table_info(hierarchy_nodes)")]
    if node_id is None:
        continue
    if "widget_assignments" in cols:
        cur.execute("SELECT widget_assignments FROM hierarchy_nodes WHERE id=?", (node_id,))
        row = cur.fetchone()
        if row is None:
            print('node missing, skipping assignments for', node_id)
            continue
        existing = json.loads(row[0] or '[]') if row[0] else []
    else:
        # legacy DB without widget_assignments column
        cur.execute("SELECT id FROM hierarchy_nodes WHERE id=?", (node_id,))
        row = cur.fetchone()
        if row is None:
            print('node missing, skipping assignments for', node_id)
            continue
        existing = []
    existing_names = {str(a.get('id') or a.get('name')) for a in existing if isinstance(a, dict)}
    new = []
    for w in widgets:
        if w['name'] not in existing_names:
            new.append({
                'id': w['name'], 'name': w['name'], 'component_type': w.get('component_type', w['name'] + '_widget'),
                'position': w.get('position',100), 'configuration': w.get('configuration', {}), 'enabled': True, 'inherit': w.get('inherit', False)
            })
    if new:
        updated = existing + new
        if "widget_assignments" in cols:
            cur.execute("UPDATE hierarchy_nodes SET widget_assignments=? WHERE id=?", (json.dumps(updated), node_id))
            print('updated node assignments', node_id, [n['name'] for n in new])
    # ensure relational rows
    for w in widgets:
        cur.execute("SELECT id FROM widget_assignments WHERE node_id=? AND (widget_id=? OR name=?)", (node_id, w['name'], w['name']))
        if cur.fetchone() is None:
            aid = str(uuid.uuid4())
            cur.execute("INSERT INTO widget_assignments (id,node_id,widget_id,name,enabled,inherit,position,configuration,required_permissions,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (aid,node_id,w['name'],w['name'],1,1 if w.get('inherit', False) else 0,w.get('position',100),json.dumps(w.get('configuration', {})),json.dumps([]),now(),now()))
            print('inserted relational assignment', aid, 'for', node_id, w['name'])
conn.commit()
conn.close()
print('dev widget seeding complete')
