import asyncio

from app.storage.database import init_database, get_session
from app.widgets.service import WidgetResolverService

async def main():
    # Initialize DB layer (no schema creation)
    await init_database(create_schema=False, echo=False)
    async for session in get_session():
        resolver = WidgetResolverService(session)
        items = await resolver.resolve_effective_widgets('bootstrap-admin', None)
        print('resolved items:', items)
        break

if __name__ == '__main__':
    asyncio.run(main())
