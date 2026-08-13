from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.v1 import health as health_mod

router = APIRouter()


@router.get(
    "/status",
    response_model=health_mod.HealthResponse,
    response_model_exclude_none=True,
    summary="System status (compat)",
)
async def system_status(request: Request, response: Response):
    """Compatibility endpoint that exposes the same payload as /health.

    This allows older frontend widgets to query /api/v1/system/status.
    """
    return await health_mod.health(request, response)
