# F:\Kernschmied\backend\app\api\v1\router.py

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    bootstrap,
    calendar,
    calendars,
    chat,
    chats,
    configs,
    debug_resolver,
    documentation,
    files,
    system,
    audit,
    health,
    hierarchy,
    models,
    tools,
    ui,
    users,
    widgets,
)
from app.api.v1.settings_catalog import router as settings_catalog_router

API_VERSION = "v1"

api_router = APIRouter()

# ---------------------------------------------------------------------------
# System- und Betriebsendpunkte
# ---------------------------------------------------------------------------

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["System / Health"],
)

# Backwards-compatible system endpoints (frontend compatibility)
api_router.include_router(
    system.router,
    prefix="/system",
    tags=["System / Compatibility"],
)

api_router.include_router(settings_catalog_router)

api_router.include_router(
    bootstrap.router,
    prefix="/bootstrap",
    tags=["System / Bootstrap"],
)

# ---------------------------------------------------------------------------
# Schema-, Navigations- und Dokumentationsendpunkte
# ---------------------------------------------------------------------------

api_router.include_router(
    ui.router,
    prefix="/ui",
    tags=["UI / Schema"],
)

api_router.include_router(
    calendar.router,
    prefix="/calendar",
    tags=["Calendar"],
)

api_router.include_router(
    calendars.router,
    prefix="/calendars",
    tags=["Calendar / CRUD"],
)

# (calendar full-stub removed; using /calendars CRUD router)

api_router.include_router(
    hierarchy.router,
    prefix="/hierarchy",
    tags=["Hierarchy"],
)

api_router.include_router(
    documentation.router,
    prefix="/documentation",
    tags=["Documentation"],
)

# ---------------------------------------------------------------------------
# Dynamische Registries
# ---------------------------------------------------------------------------

api_router.include_router(
    models.router,
    prefix="/models",
    tags=["Registry / Models"],
)

api_router.include_router(
    tools.router,
    prefix="/tools",
    tags=["Registry / Tools"],
)

api_router.include_router(
    widgets.router,
    prefix="/widgets",
    tags=["Registry / Widgets"],
)

api_router.include_router(
    files.router,
    tags=["Files / Workspace"],
)

# Simple audit compatibility endpoint used by some widgets
api_router.include_router(
    audit.router,
    prefix="/audit",
    tags=["System / Audit"],
)

# ---------------------------------------------------------------------------
# Fachliche Laufzeitendpunkte
# ---------------------------------------------------------------------------

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"],
)

# Persistent chat storage endpoints
api_router.include_router(
    chats.router,
    prefix="/chats",
    tags=["Chat / Persistence"],
)

# ---------------------------------------------------------------------------
# Administrative Endpunkte
# ---------------------------------------------------------------------------

api_router.include_router(
    configs.router,
    prefix="/config",
    tags=["Administration / Configuration"],
)

api_router.include_router(
    debug_resolver.router,
    prefix="/debug",
    tags=["Debug / Development"],
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users / Administration"],
)

api_router.include_router(
    __import__("app.api.v1.roles", fromlist=["router"]).router,
    prefix="/roles",
    tags=["Roles / Administration"],
)

# Authentication endpoints (local identity provider)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)
