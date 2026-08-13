import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
from app.storage.database import init_database, get_session
from sqlalchemy import select, func
from app.storage.models import WidgetRegistry

async def main():
    await init_database(create_schema=False, echo=False)
    async for session in get_session():
        stmt = select(WidgetRegistry).order_by(WidgetRegistry.id)
        res = await session.execute(stmt)
        rows = res.scalars().all()
        print(f'total registry rows: {len(rows)}')
        for r in rows:
            md = getattr(r,'widget_metadata', None) or {}
            comp = md.get('component_type') if isinstance(md, dict) else None
            print(r.id, r.name, getattr(r,'type',None), 'status=', r.status, 'component_type=', comp)

        # find duplicates by name
        stmt2 = select(WidgetRegistry.name, func.count(WidgetRegistry.id)).group_by(WidgetRegistry.name).having(func.count(WidgetRegistry.id) > 1)
        res2 = await session.execute(stmt2)
        dups = res2.fetchall()
        if dups:
            print('\nDuplicate names:')
            for name,count in dups:
                print(name, count)
        else:
            print('\nNo duplicate names')
        break

if __name__ == '__main__':
    asyncio.run(main())
