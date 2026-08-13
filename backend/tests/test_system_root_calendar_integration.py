import asyncio
import os
import json
import pytest

from types import SimpleNamespace

from app.widgets.service import WidgetResolverService
from app.storage.database import init_database, get_session_factory


@pytest.mark.asyncio
async def test_system_root_effective_widgets_contains_calendar_component_type():
    """Integration-style check against the runtime SQLite DB where available.

    This test initializes the application's database layer (without creating
    schema changes) and asks the WidgetResolverService to compute the
    effective widgets for `system-root`. It asserts that a calendar entry
    is present and that `component_type` == "calendar_widget".
    """
    # Prevent automatic Alembic migrations during the test run
    os.environ.setdefault("DATABASE_MIGRATION_MODE", "disabled")

    # Initialize DB manager without creating schema
    await init_database(create_schema=False)
    sf = get_session_factory()

    # Use an admin actor to avoid permission filtering
    actor = SimpleNamespace(permissions=["admin"], roles=["admin"], is_system_admin=True)

    async with sf() as session:
        svc = WidgetResolverService(session)
        items = await svc.resolve_effective_widgets("system-root", actor)

        # Find calendar entry
        cal = None
        for it in items:
            if str(it.get("id") or it.get("name")) == "calendar":
                cal = it
                break

        assert cal is not None, "calendar widget not found in system-root effective items"
        assert cal.get("component_type") == "calendar_widget", f"unexpected component_type: {cal.get('component_type')}"
