import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
from app.storage.database import init_database, get_session
from sqlalchemy import select
from app.storage.models import WidgetRegistry

async def main():
    await init_database(create_schema=False, echo=False)
    async for session in get_session():
        stmt = select(WidgetRegistry).where(WidgetRegistry.name == 'calendar')
        res = await session.execute(stmt)
        rows = res.scalars().all()
        print('found', len(rows), 'registry rows with name=calendar')
        for r in rows:
            print('id=', r.id, 'name=', r.name, 'created_at=', r.created_at, 'widget_metadata=', getattr(r,'widget_metadata',None))
        break

if __name__ == '__main__':
    asyncio.run(main())
