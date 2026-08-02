from __future__ import annotations

from datetime import UTC, datetime

# Re-export the canonical DeclarativeBase from app.database.base so all
# ORM models in `app.storage.models` share the same Base/MetaData as the
# rest of the application and Alembic migrations.
from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


__all__ = ["Base", "utc_now"]
