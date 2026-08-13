import asyncio, sys
from pathlib import Path
import shutil
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
from app.storage.database import init_database, get_session
from sqlalchemy import select, update
from app.storage.models import WidgetRegistry

TARGETS = ['calendar','system_health','audit_log','registry_editor']
BACKUP_DIR = Path(__file__).resolve().parents[2] / 'backend' / 'data'
DB_FILE = BACKUP_DIR / 'chat.db'

async def main():
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    bak = BACKUP_DIR / f'chat.db.pre_add_system_root.{ts}.bak'
    print('Backing up', DB_FILE, '->', bak)
    shutil.copy(DB_FILE, bak)

    await init_database(create_schema=False, echo=False)
    async for s in get_session():
        for name in TARGETS:
            stmt = select(WidgetRegistry).where(WidgetRegistry.name == name)
            res = await s.execute(stmt)
            row = res.scalar_one_or_none()
            if not row:
                print('No registry row for', name)
                continue
            md = getattr(row, 'widget_metadata', None) or {}
            if not isinstance(md, dict):
                md = {}
            supported = md.get('supported_node_types') or []
            if 'system_root' not in supported:
                supported = list(supported) + ['system_root']
                md['supported_node_types'] = supported
                print('Updating', name, 'supported_node_types->', supported)
                upd = update(WidgetRegistry).where(WidgetRegistry.id == row.id).values(widget_metadata=md)
                await s.execute(upd)
            else:
                print(name, 'already supports system_root')
        await s.commit()
        break

if __name__=='__main__':
    asyncio.run(main())
