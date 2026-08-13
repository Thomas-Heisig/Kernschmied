import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB = Path(__file__).resolve().parents[2] / 'backend' / 'data' / 'chat.db'
SRC = Path(__file__).resolve().parents[2] / 'backend' / 'data' / 'kernschmied.db'
print('chat db:', DB)
print('src db:', SRC)

conn = sqlite3.connect(str(DB))
cur = conn.cursor()

# find suspect rows
q = "SELECT id,name,type,created_at,updated_at,metadata,required_permissions,status,version,interaction_mode FROM widget_registry WHERE created_at = '[]' OR updated_at = '[]' OR created_at LIKE '[%' OR updated_at LIKE '[%' OR created_at IN ('', 'None', 'null') OR updated_at IN ('', 'None', 'null')"
cur.execute(q)
suspects = cur.fetchall()
print('suspect count:', len(suspects))
for s in suspects:
    print('FOUND:', s)

if not suspects:
    print('No suspects found, exiting')
    conn.close()
    raise SystemExit(0)

# attach source DB if exists
attached = False
if SRC.exists():
    try:
        cur.execute(f"ATTACH DATABASE '{SRC}' AS src")
        attached = True
        print('Attached src DB')
    except Exception as e:
        print('Failed to attach src DB:', e)

now_iso = datetime.now(timezone.utc).isoformat()
print('fallback timestamp:', now_iso)

changed = []
try:
    for row in suspects:
        wid, name, typ, created_at, updated_at, metadata, req_perms, status, version, interaction_mode = row
        print('\nRepairing id=', wid, 'name=', name)
        # try to get source authoritative row by name
        src_row = None
        if attached:
            try:
                cur.execute("SELECT id,name,type,metadata,default_config,created_at,updated_at,required_permissions,status,version,interaction_mode FROM src.widget_registry WHERE name = ? LIMIT 1", (name,))
                src_row = cur.fetchone()
            except Exception as e:
                print('src lookup error', e)
        if src_row:
            print('Found source row for', name, '-> applying authoritative fields')
            # map columns from src_row
            (s_id,s_name,s_type,s_metadata,s_default_config,s_created_at,s_updated_at,s_required_permissions,s_status,s_version,s_interaction_mode) = src_row
            # update target with explicit columns
            cur.execute(
                "UPDATE widget_registry SET type=?, metadata=?, default_config=?, created_at=?, updated_at=?, required_permissions=?, status=?, version=?, interaction_mode=? WHERE id=?",
                (s_type, s_metadata, s_default_config, s_created_at, s_updated_at, s_required_permissions, s_status, s_version, s_interaction_mode, wid)
            )
            changed.append((wid, name, 'from_src'))
        else:
            # No source; only fix created_at/updated_at and required_permissions
            new_created = created_at
            new_updated = updated_at
            if not created_at or str(created_at).startswith('[') or str(created_at) in ('[]','None','null'):
                new_created = now_iso
            if not updated_at or str(updated_at).startswith('[') or str(updated_at) in ('[]','None','null'):
                new_updated = now_iso
            # fix required_permissions if it's an integer
            new_req = req_perms
            if isinstance(req_perms, int) or (isinstance(req_perms, str) and req_perms.isdigit()):
                new_req = '[]'
            cur.execute(
                "UPDATE widget_registry SET created_at=?, updated_at=?, required_permissions=? WHERE id=?",
                (new_created, new_updated, new_req, wid)
            )
            changed.append((wid, name, 'patched_timestamps'))
    conn.commit()
    print('\nCommitted changes:', changed)
finally:
    if attached:
        try:
            cur.execute('DETACH DATABASE src')
        except Exception:
            pass
    conn.close()

print('Repair script complete')
