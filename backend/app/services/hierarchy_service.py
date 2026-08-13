"""
Kompatibilitätsschicht für den bisherigen Importpfad.

Neue Module sollten HierarchyService bevorzugt direkt aus
app.hierarchy.service importieren.
"""

from __future__ import annotations

from app.hierarchy.inheritance import HierarchyInheritanceService
from app.hierarchy.models import HierarchyActor
from app.hierarchy.permissions import HierarchyPermissionService
from app.hierarchy.repository import HierarchyRepository
from app.hierarchy.serializer import HierarchySerializer
from app.hierarchy.service import HierarchyService
from app.ui.node_type_provider import NodeTypeProvider
from app.services.ui_schema_service import create_ui_schema_service


def create_hierarchy_service(
    repository: HierarchyRepository,
) -> HierarchyService:
    """
    Erstellt einen vollständig verdrahteten HierarchyService.

    Diese Factory bleibt ausschließlich zur Kompatibilität mit dem
    bisherigen Importpfad bestehen.
    """

    permission_service = HierarchyPermissionService()
    inheritance_service = HierarchyInheritanceService()

    serializer = HierarchySerializer(
        permission_service=permission_service,
        inheritance_service=inheritance_service,
    )

    # Construct a NodeTypeProvider backed by the active UI schema service.
    ui_schema_service = create_ui_schema_service()
    node_type_provider = NodeTypeProvider(service=ui_schema_service)

    return HierarchyService(
        repository=repository,
        permission_service=permission_service,
        serializer=serializer,
        node_type_provider=node_type_provider,
    )


__all__ = [
    "HierarchyActor",
    "HierarchyService",
    "create_hierarchy_service",
]
