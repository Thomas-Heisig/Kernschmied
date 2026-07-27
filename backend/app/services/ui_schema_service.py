"""
Kompatibilitätsschicht für den bisherigen Importpfad.

Neue Module sollten UISchemaService bevorzugt aus app.ui.service importieren.
"""

from __future__ import annotations

from app.contracts.ui_schema import UISchema
from app.ui.node_types import create_default_node_types
from app.ui.registry import UIRegistry, create_default_ui_registry
from app.ui.repository import InMemoryUISchemaRepository, UISchemaRepository
from app.ui.serializer import UISchemaSerializer
from app.ui.service import UISchemaResult, UISchemaService


def create_ui_schema_service(
    repository: UISchemaRepository | None = None,
    registry: UIRegistry | None = None,
) -> UISchemaService:
    effective_registry = registry or create_default_ui_registry()
    effective_repository = repository or InMemoryUISchemaRepository(
        node_types=create_default_node_types(),
    )

    serializer = UISchemaSerializer(effective_registry)

    return UISchemaService(
        repository=effective_repository,
        serializer=serializer,
    )


def build_ui_schema() -> UISchema:
    """
    Synchrone Kompatibilitätsfunktion für bestehende MVP-Endpunkte.

    Sie nutzt dieselbe feste Registry und dieselben Node-Typ-Definitionen wie
    der neue Service, benötigt aber keinen Event-Loop.
    """

    registry = create_default_ui_registry()
    serializer = UISchemaSerializer(registry)

    return serializer.build_schema(
        create_default_node_types(),
    )


__all__ = [
    "UISchemaResult",
    "UISchemaService",
    "build_ui_schema",
    "create_ui_schema_service",
]
