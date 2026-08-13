import sqlite3
from pathlib import Path
import uuid

DB = Path(__file__).resolve().parents[2] / 'backend' / 'data' / 'chat.db'
conn = sqlite3.connect(str(DB))
cur = conn.cursor()
# check existing
cur.execute("SELECT COUNT(*) FROM widget_assignments WHERE node_id = ? AND (widget_id = ? OR name = ?)", ("system-root","calendar","calendar"))
if cur.fetchone()[0] > 0:
    print('calendar assignment already exists for system-root')
else:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    new_id = str(uuid.uuid4())
    cur.execute("INSERT INTO widget_assignments (id,node_id,widget_id,name,enabled,inherit,position,configuration,required_permissions,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (new_id, 'system-root', 'calendar', 'calendar', 1, 0, 5, '{"view":"month"}', '[]', now, now))
    conn.commit()
    print('inserted calendar assignment id=', new_id)
conn.close()
