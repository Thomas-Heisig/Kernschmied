from __future__ import annotations

# Ensure all ORM model modules are imported so their Table objects
# are registered on Base.metadata before calling create_all().
import importlib
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.settings import settings
from app.database.base import Base

# Use importlib.import_module to perform a runtime-only import. This
# preserves the side-effect (module-level Table registrations) while
# avoiding Pylance reporting an unused import.
importlib.import_module("app.database.models")
# Also import storage models so their Table objects are registered too.
importlib.import_module("app.storage.models")
import logging
from pathlib import Path

from app.core.settings import DatabaseMigrationMode
from app.storage.models.base import Base as StorageBase

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Verwaltet Engine und Session-Factory für die Anwendung.

    Die Engine wird erst durch initialize() erstellt. Dadurch bleibt der
    Import dieser Datei frei von Datenbank-Nebenwirkungen.
    """

    def __init__(self, database_url: str | None) -> None:
        if database_url is None:
            raise ValueError("database_url must not be None")
        self._database_url = database_url
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("Die Datenbank wurde noch nicht initialisiert.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("Die Datenbank wurde noch nicht initialisiert.")
        return self._session_factory

    async def initialize(
        self,
        *,
        create_schema: bool = True,
        echo: bool = False,
    ) -> async_sessionmaker[AsyncSession]:
        if self._engine is not None:
            return self.session_factory

        # Log the configured and effective database URLs and ensure parent
        # directory exists for SQLite. This helps diagnosing mismatches
        # between Alembic and the application at startup.
        from contextlib import suppress

        with suppress(Exception):
            logger.info(
                "Configured DATABASE_URL: %s", getattr(settings, "database_url", None)
            )
            logger.info("Effective database URL: %s", self._database_url)

        if self._database_url.startswith("sqlite"):
            # Extract file path for sqlite( + aiosqlite ) scheme
            # Expected form: sqlite+aiosqlite:///absolute/path/to/db
            parts = self._database_url.split(":///", 1)
            if len(parts) == 2:
                db_path = Path(parts[1])
                parent = db_path.parent
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                    logger.info(
                        "Ensured SQLite parent directory exists: %s", str(parent)
                    )
                except Exception as e:
                    logger.exception(
                        "Failed to ensure SQLite parent directory %s: %s",
                        str(parent),
                        e,
                    )

            # If configured, attempt to run Alembic migrations before initializing the
            # SQLAlchemy engine. This upgrades the schema to the latest revision and
            # avoids OperationalError for missing columns during runtime.
            try:
                if settings.database_migration_mode == DatabaseMigrationMode.UPGRADE:
                    try:
                        from alembic import command
                        from alembic.config import Config
                        from alembic.script import ScriptDirectory

                        backend_dir = Path(__file__).resolve().parents[2]
                        alembic_ini = backend_dir / "alembic.ini"

                        if alembic_ini.exists():
                            alembic_cfg = Config(str(alembic_ini))
                            # Ensure script_location and DB URL are explicit and absolute
                            alembic_cfg.set_main_option(
                                "script_location",
                                str(backend_dir / "migrations"),
                            )
                            alembic_cfg.set_main_option(
                                "sqlalchemy.url",
                                str(settings.effective_database_url),
                            )

                            # Log available Alembic heads for diagnostics
                            try:
                                script = ScriptDirectory.from_config(alembic_cfg)
                                heads = script.get_heads()
                                logger.info("Alembic available heads: %s", heads)
                            except Exception:
                                logger.debug(
                                    "Could not enumerate Alembic heads", exc_info=True
                                )

                            logger.info(
                                "Running Alembic upgrade head using %s",
                                str(alembic_ini),
                            )
                            # If Alembic fails here we must NOT continue with create_all()
                            # because that can hide migration problems and lead to FK errors.
                            # Upgrade only the single head. The migration graph has
                            # been validated to be linear; accepting multiple heads
                            # on startup would hide merge issues. Use `head` so
                            # unexpected multiple heads fail loudly.
                            command.upgrade(alembic_cfg, "head")
                        else:
                            logger.info(
                                "Alembic config not found at %s, skipping migrations",
                                str(alembic_ini),
                            )
                    except Exception:
                        # Structured logging and re-raise to abort startup instead of
                        # silently continuing and letting SQLAlchemy create missing tables.
                        logger.exception(
                            "Failed to run Alembic migrations; aborting startup."
                        )
                        raise
            except Exception:
                # Defensive: any errors while checking settings should not block initialization
                logger.exception("Error while checking database migration mode")

        # Use NullPool for SQLite to avoid holding file handles open between
        # tests; helps on Windows where tempfile cleanup can fail with
        # PermissionError if the DB file is still open.
        engine_kwargs: dict[str, object] = dict(echo=echo, pool_pre_ping=True)
        if self._database_url.startswith("sqlite"):
            engine_kwargs["poolclass"] = NullPool

        self._engine = create_async_engine(
            self._database_url,
            **engine_kwargs,
        )

        # Ensure SQLite foreign keys are enabled for every new DBAPI connection.
        # Use event.listen on the underlying sync engine so both sync and async
        # connections created by SQLAlchemy will have the PRAGMA applied.
        try:
            if self._database_url.startswith("sqlite"):
                from sqlalchemy import event

                def _enable_sqlite_fk(
                    dbapi_connection: Any, connection_record: Any
                ) -> None:
                    from contextlib import suppress

                    with suppress(Exception):
                        dbapi_connection.execute("PRAGMA foreign_keys = ON")

                event.listen(self._engine.sync_engine, "connect", _enable_sqlite_fk)
        except Exception:
            logger.exception("Failed to attach SQLite PRAGMA foreign_keys handler")

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        if create_schema:
            async with self._engine.begin() as connection:
                # Create tables for both ORM bases used in the project.
                await connection.run_sync(Base.metadata.create_all)
                from contextlib import suppress

                with suppress(Exception):
                    await connection.run_sync(StorageBase.metadata.create_all)

        return self._session_factory

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()

        self._engine = None
        self._session_factory = None

    def _dispose_sync(self) -> None:
        """Synchronous disposal fallback for use during interpreter shutdown
        or when async loop isn't available (helps tests on Windows free
        temporary SQLite files)."""
        try:
            if self._engine is not None:
                with suppress(Exception):
                    # Close the underlying sync engine to release file handles.
                    self._engine.sync_engine.dispose()
        finally:
            self._engine = None
            self._session_factory = None

    def dispose_sync(self) -> None:
        """Public wrapper for synchronous disposal used by external shutdown hooks.

        This forwards to the internal `_dispose_sync` implementation while
        providing a public, non-protected attribute that can be safely
        referenced by external registrars (e.g. `atexit.register`).
        """
        self._dispose_sync()

    def __del__(self) -> None:
        # Best-effort synchronous cleanup when object is garbage-collected.
        with suppress(Exception):
            self._dispose_sync()


# Ensure runtime directories exist before constructing the database URL/manager.
# This guarantees the configured `data_directory` (and parent directories)
# are created so SQLite can open or create the file without an OSError.
settings.ensure_runtime_directories()

# Use the effective_database_url which falls back to a resolved SQLite path
# when `DATABASE_URL` is not explicitly configured.
_database_manager = DatabaseManager(settings.effective_database_url)

# Ensure we attempt synchronous cleanup at process exit to release any
# lingering SQLite file handles (helps Windows tempfile cleanup).
from contextlib import suppress

with suppress(Exception):
    import atexit

    # Register the public synchronous disposal wrapper to avoid referencing
    # a protected member from outside the class (Pylance warns about this).
    atexit.register(_database_manager.dispose_sync)


def get_database_manager() -> DatabaseManager:
    return _database_manager


async def init_database(
    *,
    create_schema: bool = True,
    echo: bool = False,
) -> async_sessionmaker[AsyncSession]:
    """
    Kompatible Initialisierungsfunktion für bestehende Aufrufer.
    """

    return await _database_manager.initialize(
        create_schema=create_schema,
        echo=echo,
    )


async def close_database() -> None:
    await _database_manager.dispose()


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return _database_manager.session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI-Dependency für eine transaktionale AsyncSession.
    """

    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
