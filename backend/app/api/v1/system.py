from __future__ import annotations

import inspect

from fastapi import APIRouter, Request, Response

from app.api.v1 import health as health_mod
from app.contracts.system import (
    SystemOverviewResponse,
    SystemRegistryCounts,
    SystemServiceStatus,
)

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


async def _registry_count(registry: object | None, *member_names: str) -> int:
    if registry is None:
        return 0

    for member_name in member_names:
        member = getattr(registry, member_name, None)
        if member is None:
            continue

        value = member() if callable(member) else member
        if inspect.isawaitable(value):
            value = await value

        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return max(value, 0)
        if isinstance(value, (list, tuple, set, frozenset, dict)):
            return len(value)

    return 0


@router.get(
    "/overview",
    response_model=SystemOverviewResponse,
    response_model_exclude_none=True,
    summary="System overview",
)
async def system_overview(
    request: Request,
    response: Response,
) -> SystemOverviewResponse:
    health = await health_mod.health(request, response)

    return SystemOverviewResponse(
        environment=health.environment,
        config_revision=health.config_revision,
        security_profile=health.security_profile,
        services={
            name: SystemServiceStatus(status=service.status)
            for name, service in health.services.items()
        },
        registries=SystemRegistryCounts(
            models=await _registry_count(
                getattr(request.app.state, "model_registry", None),
                "get_count",
                "count",
                "list_entries",
            ),
            tools=await _registry_count(
                getattr(request.app.state, "tool_registry", None),
                "count",
                "list_tools",
            ),
        ),
        request_id=health.request_id,
    )
