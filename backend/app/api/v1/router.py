# F:\Kernschmied\backend\app\api\v1\router.py

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    bootstrap,
    chat,
    configs,
    health,
    hierarchy,
    models,
    tools,
    ui,
)


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

api_router.include_router(
    bootstrap.router,
    prefix="/bootstrap",
    tags=["System / Bootstrap"],
)


# ---------------------------------------------------------------------------
# Schema- und Navigationsendpunkte
# ---------------------------------------------------------------------------

api_router.include_router(
    ui.router,
    prefix="/ui",
    tags=["UI / Schema"],
)

api_router.include_router(
    hierarchy.router,
    prefix="/hierarchy",
    tags=["Hierarchy"],
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


# ---------------------------------------------------------------------------
# Administrative Endpunkte
# ---------------------------------------------------------------------------

api_router.include_router(
    configs.router,
    prefix="/config",
    tags=["Administration / Configuration"],
)