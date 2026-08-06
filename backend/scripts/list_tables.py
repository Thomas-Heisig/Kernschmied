import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parents[1] / "data" / "kernschmied.db"
print("DB:", db)
con = sqlite3.connect(str(db))
rows = list(
    con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
)
if not rows:
    print("No tables found")
else:
    for r in rows:
        print(r[0])
con.close()
