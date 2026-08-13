import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.storage.database import init_database, get_session_factory
from sqlalchemy import text

async def main():
    await init_database(create_schema=False)
    sf = get_session_factory()
    async with sf() as session:
        q = text('SELECT id,node_id,widget_id,name,enabled,inherit,position,configuration,required_permissions FROM widget_assignments WHERE node_id = :nid')
        res = await session.execute(q, {'nid':'bootstrap-admin'})
        rows = res.fetchall()
        print('RAW_ROWS:')
        for r in rows:
            print(r)

if __name__ == '__main__':
    asyncio.run(main())
