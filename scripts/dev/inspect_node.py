import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
from app.storage.database import init_database, get_session
from sqlalchemy import select
from app.storage.models import HierarchyNode

async def main():
    await init_database(create_schema=False, echo=False)
    async for s in get_session():
        stmt = select(HierarchyNode).where(HierarchyNode.id == 'system-root')
        res = await s.execute(stmt)
        n = res.scalar_one_or_none()
        if not n:
            print('system-root not found')
        else:
            print('system-root type=', getattr(n,'type',None), 'id=', n.id)
        break

if __name__=='__main__':
    asyncio.run(main())
