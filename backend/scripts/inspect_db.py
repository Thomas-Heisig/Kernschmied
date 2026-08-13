import sqlite3
c=sqlite3.connect('data/kernschmied.db')
cur=c.cursor()
print('Tables:')
for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(row[0])

print('\nSample widget_registry columns:')
try:
    for row in cur.execute('PRAGMA table_info(widget_registry)'):
        print(row)
except Exception as e:
    print('error:', e)

print('\nCount widget_registry rows:')
try:
    print(cur.execute('SELECT COUNT(*) FROM widget_registry').fetchone())
except Exception as e:
    print('error:', e)

c.close()
