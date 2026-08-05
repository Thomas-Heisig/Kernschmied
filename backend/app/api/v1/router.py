# F:\Kernschmied\backend\app\api\v1\router.py

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    bootstrap,
    chat,
    configs,
    documentation,
    health,
    hierarchy,
    models,
    tools,
    ui,
)
from app.api.v1 import users
from app.api.v1 import auth
from app.api.v1 import debug_resolver
from app.api.v1 import calendar
from app.api.v1 import calendars
from app.api.v1.settings_catalog import router as settings_catalog_router
from app.api.v1 import chats

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

# Authentication endpoints (local identity provider)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)
