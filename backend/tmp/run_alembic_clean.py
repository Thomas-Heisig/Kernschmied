import os

from alembic import command
from alembic.config import Config

os.environ["DATABASE_URL"] = (
    "sqlite+aiosqlite:///F:/Kernschmied/backend/data/chat.clean-fresh-test.db"
)
print("Set DATABASE_URL=", os.environ["DATABASE_URL"])
cfg = Config("alembic.ini")
try:
    command.upgrade(cfg, "head")
    print("alembic upgrade head OK")
except Exception:
    import traceback

    traceback.print_exc()
