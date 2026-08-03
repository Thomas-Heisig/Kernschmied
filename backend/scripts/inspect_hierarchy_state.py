"""Read-only inspection of the hierarchy DB state for diagnostics.

This script prints the effective database URL from settings and — if it's
an SQLite file — runs a set of read-only queries to report hierarchy and
chat state. It never writes or modifies the DB.

Run from repo backend folder:
  .\\.venv\\Scripts\\python.exe scripts\\inspect_hierarchy_state.py
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
# Path not required here; keep imports minimal

try:
    from app.core.settings import settings
except Exception as exc:  # pragma: no cover - best-effort diagnostics
    print("ERROR: could not import app.core.settings — is PYTHONPATH set to backend?", file=sys.stderr)
    raise


def parse_sqlite_path(db_url: str) -> str | None:
    # Support forms like sqlite:///C:/path/to/db.sqlite or sqlite+aiosqlite:///... or file:... ?mode=ro
    if not db_url:
        return None
    # If it's a plain file path
    if os.path.exists(db_url):
        return db_url

    # common SQLAlchemy URL prefix for sqlite file urls
    m = re.match(r"^(?:sqlite(?:\+[a-zA-Z0-9_]+)?):/{2,3}(.+)$", db_url)
    if m:
        path = m.group(1)
        # On Windows the path may start with a drive letter like C:/...\n        path = path.replace("%20", " ")
        return os.path.normpath(path)

    # file: URI possibly with query params
    m = re.match(r"^file:(.+)$", db_url)
    if m:
        path = m.group(1).split("?")[0]
        return os.path.normpath(path)

    return None


def run_queries(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    def q(sql: str):
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            print("\n--- QUERY:\n", sql)
            if cur.description:
                cols = [c[0] for c in cur.description]
                print(json.dumps([dict(zip(cols, r)) for r in rows], indent=2, default=str))
            else:
                print(json.dumps(rows, indent=2, default=str))
        except Exception as exc:  # pragma: no cover - best-effort
            print(f"Query failed: {exc}\nSQL: {sql}")

    # Alembic version
    try:
        q("SELECT version_num FROM alembic_version;")
    except Exception:
        print("alembic_version table not found or query failed")

    # Table info
    try:
        q("PRAGMA table_info('hierarchy_nodes');")
    except Exception:
        print("hierarchy_nodes table not found or PRAGMA failed")

    # hierarchy nodes
    q("""
    SELECT
        id,
        parent_id,
        type,
        name,
        position,
        is_system,
        is_active,
        is_movable,
        is_deletable,
        prompt_enabled,
        prompt_priority,
        prompt_mode
    FROM hierarchy_nodes
    ORDER BY
        CASE WHEN parent_id IS NULL THEN 0 ELSE 1 END,
        parent_id,
        position,
        name;
    """)

    # chats
    q("SELECT id, conversation_id, node_id, user_id, created_at FROM chats ORDER BY created_at;")

    # roots without parent
    q("SELECT id, type, name FROM hierarchy_nodes WHERE parent_id IS NULL;")

    # children with missing parent
    q("""
    SELECT child.id AS id, child.name AS name, child.parent_id AS parent_id
    FROM hierarchy_nodes AS child
    LEFT JOIN hierarchy_nodes AS parent
        ON parent.id = child.parent_id
    WHERE child.parent_id IS NOT NULL
      AND parent.id IS NULL;
    """)

    # chats by orphan node
    q("""
    SELECT chats.id AS id, chats.conversation_id AS conversation_id, chats.node_id AS node_id
    FROM chats
    LEFT JOIN hierarchy_nodes
        ON hierarchy_nodes.id = chats.node_id
    WHERE hierarchy_nodes.id IS NULL;
    """)

    # integrity checks
    try:
        q("PRAGMA integrity_check;")
    except Exception:
        print("PRAGMA integrity_check failed")
    try:
        q("PRAGMA foreign_key_check;")
    except Exception:
        print("PRAGMA foreign_key_check failed")


def main() -> int:
    print("effective_database_url:", settings.effective_database_url)
    sqlite_path = parse_sqlite_path(settings.effective_database_url)
    if not sqlite_path:
        print("Non-sqlite or could not parse sqlite path; exiting.")
        return 0

    print("resolved sqlite path:", sqlite_path)
    if not os.path.exists(sqlite_path):
        print("SQLite file does not exist:", sqlite_path)
        return 1

    print("SQLite file size:", os.path.getsize(sqlite_path))
    conn = sqlite3.connect(sqlite_path)
    try:
        run_queries(conn)
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
