import asyncio
import json
import sys
from pathlib import Path
import logging

# Ensure the backend package root is on sys.path when executed as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
# Force the database URL to the kernschmied DB for this debug run
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///F:/Kernschmied/backend/data/kernschmied.db')
os.environ.setdefault('DATABASE_MIGRATION_MODE', 'disabled')

from app.storage.database import init_database, get_session_factory
from app.widgets.service import WidgetResolverService
from types import SimpleNamespace
import sqlite3


def load_chain_from_sqlite(db_path: str, node_id: str) -> list:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    chain = []
    cur.execute('SELECT id, parent_id, type FROM hierarchy_nodes WHERE id = ?', (node_id,))
    row = cur.fetchone()
    while row:
        nid, parent_id, ntype = row[0], row[1], row[2]
        # Older DBs may not have `is_system`; infer by node type or id
        is_system = True if (ntype == 'system_root' or nid == 'system-root') else False
        node = SimpleNamespace(id=nid, parent_id=parent_id, type=ntype, is_system=is_system, widget_assignments=None)
        chain.append(node)
        if not parent_id:
            break
        cur.execute('SELECT id, parent_id, type FROM hierarchy_nodes WHERE id = ?', (parent_id,))
        row = cur.fetchone()
    conn.close()
    return list(reversed(chain))

# Configure logging to see resolver instrumentation
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [%(name)s] %(message)s')


async def main():
    # Initialize database connections but don't create schema
    await init_database(create_schema=False)
    sf = get_session_factory()
    async with sf() as session:
        svc = WidgetResolverService(session)
        # Build chain from sqlite directly to avoid ORM schema mismatches
        db_path = 'data/kernschmied.db'
        chain = load_chain_from_sqlite(db_path, 'bootstrap-admin')
        # Monkeypatch the service loader to return our chain
        async def _fake_load_chain(node_id: str):
            return chain
        svc._load_chain = _fake_load_chain
        print("CHAIN:")
        for n in chain:
            print(f" - id={getattr(n,'id',None)} type={getattr(n,'type',None)} is_system={getattr(n,'is_system',None)}")
        # Use an admin actor so system nodes in the chain do not short-circuit
        actor = type("Actor", (), {"permissions": ["admin"], "roles": ["admin"]})()
        res = await svc.resolve_effective_widgets("bootstrap-admin", actor=actor)
        print("RESULT:")
        print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
