import sqlite3
c=sqlite3.connect('data/kernschmied.db')
for r in c.execute('PRAGMA table_info(hierarchy_nodes)'):
    print(r)
c.close()
