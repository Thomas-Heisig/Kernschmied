import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parents[1] / "data" / "kernschmied.db"
print('DB file:', db)
con = sqlite3.connect(str(db))
rows = list(con.execute('PRAGMA table_info(calendars)'))
if not rows:
    print('No calendars table or no columns returned')
else:
    for r in rows:
        print(r)
con.close()
