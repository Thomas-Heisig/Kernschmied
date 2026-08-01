from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import settings
from app.database.base import Base

# Ensure all ORM model modules are imported so their Table objects
# are registered on Base.metadata before calling create_all().
import importlib

# Use importlib.import_module to perform a runtime-only import. This
# preserves the side-effect (module-level Table registrations) while
# avoiding Pylance reporting an unused import.
importlib.import_module("app.database.models")
# Also import storage models so their Table objects are registered too.
importlib.import_module("app.storage.models")
from app.storage.models.base import Base as StorageBase
import logging
from pathlib import Path
from app.core.settings import DatabaseMigrationMode

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

        # Log the database URL and ensure parent directory exists for SQLite.
        try:
            logger.info("Initializing database with URL: %s", self._database_url)
        except Exception:
            pass

        if self._database_url.startswith("sqlite"):
            # Extract file path for sqlite( + aiosqlite ) scheme
            # Expected form: sqlite+aiosqlite:///absolute/path/to/db
            parts = self._database_url.split(":///", 1)
            if len(parts) == 2:
                db_path = Path(parts[1])
                parent = db_path.parent
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                    logger.info("Ensured SQLite parent directory exists: %s", str(parent))
                except Exception as e:
                    logger.exception("Failed to ensure SQLite parent directory %s: %s", str(parent), e)

            # If configured, attempt to run Alembic migrations before initializing the
            # SQLAlchemy engine. This upgrades the schema to the latest revision and
            # avoids OperationalError for missing columns during runtime.
            try:
                if settings.database_migration_mode == DatabaseMigrationMode.UPGRADE:
                    try:
                        from alembic.config import Config
                        from alembic import command

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
                            logger.info("Running Alembic upgrade head using %s", str(alembic_ini))
                            command.upgrade(alembic_cfg, "head")
                        else:
                            logger.info("Alembic config not found at %s, skipping migrations", str(alembic_ini))

                    except Exception:
                        logger.exception("Failed to run Alembic migrations; continuing and letting SQLAlchemy create missing tables.")
            except Exception:
                # Defensive: any errors while checking settings should not block initialization
                logger.exception("Error while checking database migration mode")

        self._engine = create_async_engine(
            self._database_url,
            echo=echo,
            pool_pre_ping=True,
        )

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
                try:
                    await connection.run_sync(StorageBase.metadata.create_all)
                except Exception:
                    # StorageBase may be empty in some contexts; ignore errors here
                    # and let later steps surface real issues.
                    pass

        return self._session_factory

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()

        self._engine = None
        self._session_factory = None


# Ensure runtime directories exist before constructing the database URL/manager.
# This guarantees the configured `data_directory` (and parent directories)
# are created so SQLite can open or create the file without an OSError.
settings.ensure_runtime_directories()

# Use the effective_database_url which falls back to a resolved SQLite path
# when `DATABASE_URL` is not explicitly configured.
_database_manager = DatabaseManager(settings.effective_database_url)


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
