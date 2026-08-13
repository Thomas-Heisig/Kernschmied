import asyncio
import sys
from pathlib import Path
# Ensure backend package is on sys.path when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
from app.storage.database import init_database, get_session
from sqlalchemy import select
from app.storage.models import WidgetRegistry

async def main():
    await init_database(create_schema=False, echo=False)
    async for session in get_session():
        stmt = select(WidgetRegistry)
        res = await session.execute(stmt)
        regs = res.scalars().all()
        print('widget registry count (orm):', len(regs))
        for r in regs:
            print('id=', r.id, 'name=', r.name, 'created_at=', getattr(r,'created_at',None))
        break

if __name__ == '__main__':
    asyncio.run(main())
