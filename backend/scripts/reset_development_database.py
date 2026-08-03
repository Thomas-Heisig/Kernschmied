"""Reset the development SQLite database safely.

This script is intentionally conservative:
- Only runs when APP_ENVIRONMENT is development
- Performs a backup before destructive operations
- Requires explicit --apply to make changes
- After recreate, runs only the minimal system seed

Usage:
  python scripts/reset_development_database.py [--apply]
"""
from __future__ import annotations

import argparse
import asyncio
import shutil
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.settings import settings
from app.storage.database import init_database
from app.core import dev_seed


def resolve_sqlite_path(database_url: str) -> Path | None:
    if database_url and database_url.startswith("sqlite"):
        parts = database_url.split(":///", 1)
        if len(parts) == 2:
            return Path(parts[1])
    return None


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reset development database (dry-run default)")
    parser.add_argument("--apply", action="store_true", help="Actually perform destructive changes")
    args = parser.parse_args(argv)

    if not settings.is_development:
        print("Refusing to run: APP_ENVIRONMENT is not development")
        return 2

    db_path = resolve_sqlite_path(settings.effective_database_url)
    if db_path is None:
        print("This script currently supports SQLite development DB only.")
        return 3

    will_recreate = True
    will_create_system_root = True
    will_create_bootstrap_admin = True
    will_create_demo = False

    print("MODE=" + ("APPLY" if args.apply else "DRY_RUN"))
    print(f"PROFILE={settings.app_environment}")
    print(f"DATABASE_PATH={db_path}")
    backup_path = db_path.with_name(f"{db_path.stem}.backup.before-reset.{datetime.now().strftime('%Y%m%d-%H%M%S')}{db_path.suffix}")
    print(f"BACKUP_PATH={backup_path}")
    print(f"WILL_RECREATE_DATABASE={will_recreate}")
    print(f"WILL_CREATE_SYSTEM_ROOT={will_create_system_root}")
    print(f"WILL_CREATE_BOOTSTRAP_ADMIN={will_create_bootstrap_admin}")
    print(f"WILL_CREATE_DEMO_DATA={will_create_demo}")

    if not args.apply:
        print("Dry-run complete. Rerun with --apply to perform actions.")
        return 0

    # Apply path
    # 1) Backup
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")
    except Exception as exc:
        print(f"Failed to create backup: {exc}")
        return 4

    # 2) Remove DB file
    try:
        db_path.unlink()
        print(f"Removed existing DB file: {db_path}")
    except FileNotFoundError:
        print("No existing DB file to remove; proceeding")
    except Exception as exc:
        print(f"Failed to remove DB file: {exc}")
        return 5

    # 3) Run Alembic upgrade head to (re)create schema
    try:
        backend_dir = Path(__file__).resolve().parents[1]
        alembic_ini = backend_dir / "alembic.ini"
        if not alembic_ini.exists():
            print(f"alembic.ini not found at {alembic_ini}; skipping migrations")
        else:
            cfg = Config(str(alembic_ini))
            cfg.set_main_option("script_location", str(backend_dir / "migrations"))
            cfg.set_main_option("sqlalchemy.url", str(settings.effective_database_url))
            print("Running Alembic upgrade head...")
            command.upgrade(cfg, "head")
            print("Alembic upgrade completed")
    except Exception as exc:
        print(f"Alembic failed: {exc}")
        return 6

    # 4) Run minimal system seed
    try:
        session_factory = await init_database(create_schema=False)
        await dev_seed.seed_development_hierarchy(session_factory)
        print("Minimal system seed applied")
    except Exception as exc:
        print(f"Failed to apply minimal system seed: {exc}")
        return 7

    print("Reset completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
