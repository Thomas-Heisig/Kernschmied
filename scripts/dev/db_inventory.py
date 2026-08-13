import sqlite3
import json
from pathlib import Path
from datetime import datetime

backend = Path(__file__).resolve().parents[2] / 'backend' / 'data'
files = ['chat.db','kernschmied.db']
out = {}
for f in files:
    p = backend / f
    record = {'exists': p.exists()}
    if not p.exists():
        out[f]=record
        continue
    stat = p.stat()
    record['path']=str(p)
    record['size']=stat.st_size
    record['mtime']=datetime.fromtimestamp(stat.st_mtime).isoformat()
    # read alembic_version
    try:
        conn = sqlite3.connect(str(p))
        cur = conn.cursor()
        try:
            cur.execute("SELECT version_num FROM alembic_version LIMIT 1")
            row = cur.fetchone()
            record['alembic_version']=row[0] if row else None
        except Exception:
            record['alembic_version']=None
        tables = ['users','hierarchy_nodes','chats','messages','widget_registry','widget_assignments','files']
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                row = cur.fetchone()
                record['count_'+t]=row[0]
            except Exception:
                record['count_'+t]=None
        conn.close()
    except Exception as e:
        record['error']=str(e)
    out[f]=record
print(json.dumps(out,indent=2))
