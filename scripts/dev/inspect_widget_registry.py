import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB = Path(__file__).resolve().parents[2] / 'backend' / 'data' / 'chat.db'
print('using db:', DB)
conn = sqlite3.connect(str(DB))
cur = conn.cursor()

print('\nPRAGMA table_info(widget_registry):')
for row in cur.execute("PRAGMA table_info(widget_registry);"):
    print(row)

print('\nAll widget_registry rows (id,name,type,created_at,updated_at,metadata,required_permissions,status,interaction_mode):')
try:
    for r in cur.execute('SELECT id,name,type,created_at,updated_at,metadata,required_permissions,status,interaction_mode FROM widget_registry'):
        print(r)
except Exception as e:
    print('Error selecting rows:', e)

print('\nSuspect rows (created_at or updated_at contains [] or starts with [):')
q = "SELECT id,name,type,created_at,updated_at,metadata,required_permissions,status,interaction_mode FROM widget_registry WHERE created_at = '[]' OR updated_at = '[]' OR created_at LIKE '[%' OR updated_at LIKE '[%' OR created_at IN ('', 'None', 'null') OR updated_at IN ('', 'None', 'null')"
for r in cur.execute(q):
    print(r)

# also check for other obvious anomalies where metadata looks like a date
print('\nRows where metadata looks like an ISO date (heuristic):')
for r in cur.execute("SELECT id,name,metadata,created_at,updated_at FROM widget_registry"):
    meta = r[2]
    if isinstance(meta, str) and len(meta) > 0 and meta[0].isdigit():
        # naive iso-like
        print('maybe-shifted:', r)

# summarize counts
print('\nCounts:')
for t in ('widget_registry',):
    try:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(t, cur.fetchone()[0])
    except Exception as e:
        print('count error', t, e)

conn.close()
