import sqlite3
p='data/kernschmied.hierarchy-migration-test.db'
conn=sqlite3.connect(p)
cur=conn.cursor()
try:
    try:
        cur.execute("SELECT version_num FROM alembic_version")
        v = cur.fetchone()
        print('alembic_version:', v)
    except Exception as e:
        print('no alembic_version table or error:', e)
    print('\nTables:')
    for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        print(r[0])
finally:
    conn.close()
