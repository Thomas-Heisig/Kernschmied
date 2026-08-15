"""Cleanup duplicate WidgetRegistry entries by deprecating safe duplicates.

Run from the workspace root with the backend virtualenv active:

    backend\.venv\Scripts\python.exe scripts/cleanup_widget_registry.py
"""
import asyncio
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.settings import settings
from app.storage.models import WidgetRegistry

logger = logging.getLogger("cleanup_widget_registry")
logging.basicConfig(level=logging.INFO)


async def main() -> None:
    url = settings.effective_database_url
    engine = create_async_engine(url, echo=False)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as session:
        # Find all distinct names and their rows
        stmt = select(WidgetRegistry.name).distinct()
        res = await session.execute(stmt)
        names = [r[0] for r in res.fetchall()]

        for name in names:
            q = select(WidgetRegistry).where(WidgetRegistry.name == name)
            r = await session.execute(q)
            rows = r.scalars().all()
            if len(rows) <= 1:
                continue

            # prefer canonical row where id == name
            canonical = None
            for row in rows:
                if getattr(row, "id", None) == name:
                    canonical = row
                    break
            if canonical is None:
                canonical = rows[0]

            # compute canonical metadata
            can_md = getattr(canonical, "widget_metadata", {}) or {}
            if isinstance(can_md, str):
                try:
                    can_md = json.loads(can_md)
                except Exception:
                    can_md = {}

            canonical_id = getattr(canonical, "id", None)
            changed = False
            for dup in rows:
                if getattr(dup, "id", None) == canonical_id:
                    continue
                try:
                    dup_md = getattr(dup, "widget_metadata", {}) or {}
                    if isinstance(dup_md, str):
                        try:
                            dup_md = json.loads(dup_md)
                        except Exception:
                            dup_md = {}

                    dup_supported = set(dup_md.get("supported_node_types") or [])
                    can_supported = set(can_md.get("supported_node_types") or [])
                    if dup_supported and not dup_supported.issubset(can_supported):
                        logger.info(
                            "Skipping deprecation of duplicate %s: exposes additional supported_node_types %s",
                            getattr(dup, "id", None),
                            dup_supported - can_supported,
                        )
                        continue

                    # Mark duplicate as deprecated
                    if getattr(dup, "status", None) != "deprecated":
                        logger.info("Deprecating duplicate registry row %s (name=%s)", getattr(dup, "id", None), name)
                        dup.status = "deprecated"
                        session.add(dup)
                        changed = True
                except Exception:
                    logger.exception("Failed to evaluate duplicate row %s", getattr(dup, "id", None))

            if changed:
                await session.flush()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
