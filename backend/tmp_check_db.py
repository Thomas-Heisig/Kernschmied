from pathlib import Path
import sqlite3
p=Path('F:/Kernschmied/backend/data/chat.db')
print('DB exists:', p.exists())
conn=sqlite3.connect(str(p))
c=conn.cursor()
# counts
for t in ('hierarchy_nodes','chats','messages'):
    try:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        n=c.fetchone()[0]
    except Exception as e:
        n=f'ERROR: {e}'
    print(f"COUNT({t})={n}")
# list hierarchy nodes
try:
    c.execute('SELECT id,type,name,parent_id FROM hierarchy_nodes')
    rows=c.fetchall()
    print('NODES:')
    for r in rows:
        print(r)
except Exception as e:
    print('Nodes query error:', e)
# check forbidden names
forbidden=['Thomas Heisig','Heisig Naturstein','Angebote','Angebot Müller','Conversation conversation_','Public','Intern']
for s in forbidden:
    try:
        c.execute("SELECT COUNT(*) FROM hierarchy_nodes WHERE name LIKE ?",(f'%{s}%',))
        cnt=c.fetchone()[0]
    except Exception:
        cnt=0
    print(f"FOUND '{s}': {cnt}")
conn.close()
