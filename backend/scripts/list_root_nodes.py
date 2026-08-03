from __future__ import annotations
import asyncio
from sqlalchemy import select
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.storage.database import init_database
from app.core.settings import settings


def resolve_sqlite_path(database_url: str):
    if database_url.startswith("sqlite"):
        parts = database_url.split(":///", 1)
        if len(parts) == 2:
            return parts[1]
    return None

async def main():
    session_factory = await init_database(create_schema=False)
    async with session_factory() as session:
        q = select(HierarchyNodeModel).where(HierarchyNodeModel.parent_id.is_(None))
        rows = (await session.execute(q)).scalars().all()
        print(f"Found {len(rows)} root nodes:")
        for r in rows:
            print(f"- id={r.id} type={r.type} name={r.name}")

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
