import sqlite3
p = r'F:/Kernschmied/backend/data/chat.e2e-persistence.db'
conn = sqlite3.connect(p)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
print('alembic_version_exists=', cur.fetchone())
try:
    cur.execute('select version_num from alembic_version')
    print('version_num=', cur.fetchone())
except Exception as e:
    print('select error', e)
conn.close()
