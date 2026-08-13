import sqlite3, json, os

db='data/chat.db'
out='widget_registry_dump.txt'
if not os.path.exists(db):
    with open(out, 'w', encoding='utf-8') as f:
        f.write('DB not found: ' + db + '\n')
else:
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    try:
        cur.execute('SELECT id,name,type,widget_metadata,status FROM widget_registry ORDER BY id')
    except Exception as e:
        with open(out, 'w', encoding='utf-8') as f:
            f.write('Query failed: ' + str(e) + '\n')
    else:
        rows=cur.fetchall()
        with open(out, 'w', encoding='utf-8') as f:
            f.write('rows_count=' + str(len(rows)) + '\n')
            for r in rows:
                id,name,type_,md,status=r
                try:
                    md2=json.loads(md) if md else md
                except Exception:
                    md2=md
                f.write(repr(id) + '\t' + repr(name) + '\t' + repr(type_) + '\t' + repr(md2) + '\t' + repr(status) + '\n')
    conn.close()
print('dump written to', out)
