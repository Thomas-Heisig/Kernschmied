import sqlite3
from pathlib import Path

db = Path('backend/backend/data/chat.db')
if not db.exists():
    print('DB not found:', db)
    raise SystemExit(2)

con = sqlite3.connect(str(db))
cur = con.cursor()
try:
    cur.execute("SELECT version_num FROM alembic_version")
    rows = cur.fetchall()
    print('alembic_version rows:', rows)
except sqlite3.OperationalError as e:
    print('OperationalError:', e)
finally:
    con.close()
