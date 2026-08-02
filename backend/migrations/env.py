from __future__ import annotations

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ensure backend directory is on path so we can import the `app` package
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.settings import settings
from app.database.base import Base as DatabaseBase

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        # ignore logging config errors in test/dev environments
        pass

# Set sqlalchemy.url from application settings when available
database_url = os.environ.get("DATABASE_URL") or str(settings.effective_database_url)
# Alembic runs synchronously; convert async sqlite URL to sync sqlite URL for local migrations
if database_url.startswith("sqlite+aiosqlite://"):
    # expected form: sqlite+aiosqlite:///absolute/path
    parts = database_url.split("://", 1)
    if len(parts) == 2:
        # keep triple-slash path
        _, rest = parts
        sync_url = f"sqlite://{rest}"
    else:
        sync_url = database_url.replace("sqlite+aiosqlite", "sqlite")
    config.set_main_option("sqlalchemy.url", sync_url)
else:
    config.set_main_option("sqlalchemy.url", database_url)

# Provide target metadata for 'autogenerate' support
target_metadata = DatabaseBase.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # `config.get_section` may return None; default to empty dict for typing
    cfg_section = config.get_section(config.config_ini_section) or {}

    connectable = engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
