from pathlib import Path
import sqlite3

kern = Path(__file__).resolve().parents[2] / "backend" / "data" / "kernschmied.db"
chat = Path(__file__).resolve().parents[2] / "backend" / "data" / "chat.db"
print('kern db:', kern)
print('chat db:', chat)

if not kern.exists():
    print('kern db not found')
    raise SystemExit(1)
if not chat.exists():
    print('chat db not found')
    raise SystemExit(1)

conn = sqlite3.connect(str(chat))
cur = conn.cursor()
try:
    cur.execute(f"ATTACH DATABASE '{kern}' AS src")
    for table in ('widget_registry','widget_assignments'):
        try:
            cur.execute(f"INSERT OR IGNORE INTO {table} SELECT * FROM src.{table}")
            print(f"Inserted/ignored into {table}, rowcount={cur.rowcount}")
        except Exception as e:
            print('Failed to copy', table, e)
    conn.commit()
finally:
    try:
        cur.execute('DETACH DATABASE src')
    except Exception:
        pass
    conn.close()
print('done')
