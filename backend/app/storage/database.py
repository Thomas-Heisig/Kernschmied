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
import app.database.models  # noqa: F401


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
                await connection.run_sync(Base.metadata.create_all)

        return self._session_factory

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()

        self._engine = None
        self._session_factory = None


_database_manager = DatabaseManager(settings.database_url)


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
