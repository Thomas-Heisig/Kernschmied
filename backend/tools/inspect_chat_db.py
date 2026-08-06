import sqlite3
from pathlib import Path

db = Path("data/chat.db")
if not db.exists():
    print("DB not found:", db)
    raise SystemExit(2)

con = sqlite3.connect(str(db))
cur = con.cursor()


def show_table_info(name: str) -> None:
    print(f"--- table info: {name} ---")
    try:
        cur.execute(f"PRAGMA table_info('{name}')")
        for r in cur.fetchall():
            print(r)
    except Exception as e:
        print("error table_info", e)


def show_foreign_keys(name: str) -> None:
    print(f"--- foreign keys for: {name} ---")
    try:
        cur.execute(f"PRAGMA foreign_key_list('{name}')")
        for r in cur.fetchall():
            print(r)
    except Exception as e:
        print("error foreign_key_list", e)


def show_rows(name: str, limit: int = 10) -> None:
    print(f"--- first rows: {name} (limit={limit}) ---")
    try:
        cur.execute(f"SELECT * FROM {name} LIMIT {limit}")
        for r in cur.fetchall():
            print(r)
    except Exception as e:
        print("error select", e)


print("PRAGMA foreign_keys =", cur.execute("PRAGMA foreign_keys").fetchone())
show_table_info("chats")
show_foreign_keys("chats")
show_table_info("hierarchy_nodes")
show_rows("hierarchy_nodes", limit=20)
show_rows("chats", limit=20)

con.close()
