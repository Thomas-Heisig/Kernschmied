import asyncio
import sys
from pathlib import Path

# Ensure backend package is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))

from app.storage.database import init_database, get_session
from app.widgets.service import WidgetResolverService

async def main():
    await init_database(create_schema=False, echo=False)
    async for session in get_session():
        resolver = WidgetResolverService(session)
        items = await resolver.resolve_effective_widgets('system-root', None)
        print('resolved items:', items)
        break

if __name__ == '__main__':
    asyncio.run(main())
