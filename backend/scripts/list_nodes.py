import sqlite3
c=sqlite3.connect('data/kernschmied.db')
cur=c.cursor()
for r in cur.execute('SELECT id, name, type FROM hierarchy_nodes LIMIT 50'):
    print(r)
c.close()
