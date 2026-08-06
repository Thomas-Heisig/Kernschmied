import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parents[1] / "data" / "kernschmied.db"
print("DB:", db)
con = sqlite3.connect(str(db))
try:
    rows = list(con.execute("SELECT * FROM alembic_version"))
    if not rows:
        print("alembic_version table empty")
    else:
        for r in rows:
            print(r)
except Exception as e:
    print("Error reading alembic_version:", e)
con.close()
