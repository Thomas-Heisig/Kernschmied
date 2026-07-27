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

    return HierarchyService(
        repository=repository,
        permission_service=permission_service,
        serializer=serializer,
    )


__all__ = [
    "HierarchyActor",
    "HierarchyService",
    "create_hierarchy_service",
]
