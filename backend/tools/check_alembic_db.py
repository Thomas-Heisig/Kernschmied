import sqlite3
from pathlib import Path

candidates = [
    Path('data/kernschmied.db'),
    Path('data/chat.db'),
    Path('backend/data/chat.db'),
    Path('backend/data/kernschmied.db'),
]

def check_db(path: Path):
    if not path.exists():
        print(f'not found: {path}')
        return
    try:
        conn = sqlite3.connect(str(path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        if not cur.fetchone():
            print(f'no alembic_version table in {path}')
            conn.close()
            return
        cur.execute('SELECT * FROM alembic_version')
        rows = cur.fetchall()
        print(f'alembic_version rows in {path}:', rows)
        conn.close()
    except Exception as e:
        print('ERROR reading', path, e)

if __name__ == '__main__':
    for p in candidates:
        check_db(p)
