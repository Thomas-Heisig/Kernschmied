from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.api.v1.hierarchy import build_actor_from_request
from app.core.settings import AppEnvironment, settings
from app.hierarchy.permissions import HierarchyPermissionService
from app.hierarchy.repository import HierarchyRepository
from app.prompts.errors import (
    PromptHierarchyNodeNotFoundError,
)
from app.prompts.models import ResolvedContext
from app.prompts.resolver import PromptResolver

router = APIRouter()


@router.get("/resolved-context", response_model=ResolvedContext)
async def resolved_context(
    request: Request,
    hierarchy_node_id: str | None = Query(None, description="Zu resolvierender Knoten"),
) -> ResolvedContext:
    actor = build_actor_from_request(request)

    # Only allow in development or to admins
    if not (actor.is_admin or settings.app_environment == AppEnvironment.DEVELOPMENT):
        raise PermissionError(
            "Nur Administratoren oder Entwicklungsumgebung dürfen Debug-Informationen anfordern."
        )

    session_factory = getattr(request.app.state, "session_factory", None)
    config_service = getattr(request.app.state, "config_service", None)

    settings_prompt = None
    config_revision = None
    if config_service is not None:
        from contextlib import suppress

        with suppress(Exception):
            settings_prompt = config_service.get_required("chat", "system_prompt")
            config_revision = getattr(config_service, "revision", None)

    # If a hierarchy_node_id is provided, resolve against DB
    if hierarchy_node_id is not None:
        if session_factory is None:
            raise RuntimeError("Persistenz nicht verfügbar")

        async with session_factory() as session:
            repo = HierarchyRepository(session)
            permission_service = HierarchyPermissionService()
            resolver = PromptResolver(permission_service=permission_service)
            try:
                resolved = await resolver.resolve(
                    hierarchy_node_id,
                    repository=repo,
                    actor=actor,
                    settings_system_prompt=settings_prompt,
                )
            except PromptHierarchyNodeNotFoundError:
                raise RuntimeError("Hierarchieknoten nicht gefunden")

            # attach config revision when available
            if config_revision is not None:
                from contextlib import suppress

                with suppress(Exception):
                    resolved.config_revision = config_revision

            return ResolvedContext(
                hierarchy_node_id=hierarchy_node_id, resolved_prompt=resolved
            )

    # No hierarchy node: resolve only settings prompt
    resolver = PromptResolver()
    resolved = resolver.resolve_from_chain(
        chain=(), settings_system_prompt=settings_prompt
    )
    if config_revision is not None:
        from contextlib import suppress

        with suppress(Exception):
            resolved.config_revision = config_revision

    return ResolvedContext(hierarchy_node_id=None, resolved_prompt=resolved)
