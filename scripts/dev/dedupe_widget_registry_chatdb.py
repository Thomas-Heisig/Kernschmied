import asyncio
import sys
from pathlib import Path
import shutil
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
from app.storage.database import init_database, get_session
from sqlalchemy import select, func, update
from app.storage.models import WidgetRegistry

BACKUP_DIR = Path(__file__).resolve().parents[2] / 'backend' / 'data'
DB_FILE = BACKUP_DIR / 'chat.db'

async def main():
    # backup
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    bak = BACKUP_DIR / f'chat.db.pre_dedupe.{ts}.bak'
    print('Backing up', DB_FILE, '->', bak)
    shutil.copy(DB_FILE, bak)

    await init_database(create_schema=False, echo=False)
    async for session in get_session():
        # find duplicate names
        stmt = select(WidgetRegistry.name, func.count(WidgetRegistry.id)).group_by(WidgetRegistry.name).having(func.count(WidgetRegistry.id) > 1)
        res = await session.execute(stmt)
        dups = [r[0] for r in res.fetchall()]
        if not dups:
            print('No duplicates found')
            break
        print('Duplicate names:', dups)
        for name in dups:
            stmt2 = select(WidgetRegistry).where(WidgetRegistry.name == name).order_by(WidgetRegistry.updated_at.desc())
            res2 = await session.execute(stmt2)
            rows = res2.scalars().all()
            # choose canonical: prefer one with widget_metadata.component_type
            canonical = None
            for r in rows:
                md = getattr(r, 'widget_metadata', None) or {}
                comp = md.get('component_type') if isinstance(md, dict) else None
                if comp:
                    canonical = r
                    break
            if canonical is None:
                # fallback to latest updated_at
                canonical = rows[0]
            print('Canonical for', name, 'is', canonical.id)
            # deprecate others by renaming and setting status
            for r in rows:
                if r.id == canonical.id:
                    continue
                new_name = f"{r.name}__dup__{r.id[:8]}"
                print('Deprecating', r.id, 'old_name=', r.name, '-> new_name=', new_name)
                upd = update(WidgetRegistry).where(WidgetRegistry.id == r.id).values(name=new_name, status='deprecated')
                await session.execute(upd)
        await session.commit()
        print('Dedupe commit done')
        break

if __name__ == '__main__':
    asyncio.run(main())
