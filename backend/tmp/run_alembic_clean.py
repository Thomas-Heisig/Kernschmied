import os
from alembic.config import Config
from alembic import command
os.environ['DATABASE_URL']='sqlite+aiosqlite:///F:/Kernschmied/backend/data/chat.clean-fresh-test.db'
print('Set DATABASE_URL=', os.environ['DATABASE_URL'])
cfg=Config('alembic.ini')
try:
    command.upgrade(cfg,'head')
    print('alembic upgrade head OK')
except Exception as e:
    import traceback
    traceback.print_exc()
