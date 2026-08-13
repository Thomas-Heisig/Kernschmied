import sqlite3, json, sys

DB=r'F:/Kernschmied/backend/data/chat.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()

print('PRAGMA table_info(widget_registry):')
for row in cur.execute("PRAGMA table_info(widget_registry)"):
    print(row)

print('\nPRAGMA table_info(widget_assignments):')
for row in cur.execute("PRAGMA table_info(widget_assignments)"):
    print(row)

print('\n--- sample widget_registry rows with name LIKE "%calendar%" ---')
for row in cur.execute("SELECT * FROM widget_registry WHERE name LIKE '%calendar%' LIMIT 10"):
    print(row)

print('\n--- all widget_registry rows (first 20) ---')
for i,row in enumerate(cur.execute("SELECT * FROM widget_registry LIMIT 20")):
    print(i, row)

print('\n--- assignments for bootstrap-admin ---')
for row in cur.execute("SELECT * FROM widget_assignments WHERE node_id='bootstrap-admin'"):
    print(row)

print('\n--- assignments for project-root ---')
for row in cur.execute("SELECT * FROM widget_assignments WHERE node_id='project-root'"):
    print(row)

conn.close()
