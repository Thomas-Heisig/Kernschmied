from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Protocol

from app.contracts.ui_schema import NodeTypeDefinition
from app.ui.node_types import create_default_node_types


class UISchemaRepository(Protocol):
    """Abstraktion für fachlich konfigurierbare UI-Schema-Daten."""

    async def get_node_types(self) -> Mapping[str, NodeTypeDefinition]: ...

    async def get_config_revision(self) -> int: ...


class InMemoryUISchemaRepository:
    """
    Einfache MVP-Implementierung.

    Später kann diese Klasse durch ein SQLAlchemy-Repository ersetzt werden,
    ohne Serializer oder Service zu ändern.
    """

    def __init__(
        self,
        *,
        node_types: Mapping[str, NodeTypeDefinition] | None = None,
        config_revision: int = 0,
    ) -> None:
        self._node_types = dict(
            node_types or create_default_node_types(),
        )
        self._config_revision = config_revision

    async def get_node_types(self) -> Mapping[str, NodeTypeDefinition]:
        return deepcopy(self._node_types)

    async def get_config_revision(self) -> int:
        return self._config_revision

    async def replace_node_types(
        self,
        node_types: Mapping[str, NodeTypeDefinition],
    ) -> int:
        self._node_types = deepcopy(dict(node_types))
        self._config_revision += 1
        return self._config_revision
