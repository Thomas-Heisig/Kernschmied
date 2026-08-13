from __future__ import annotations

from typing import Mapping

from app.contracts.ui_schema import NodeTypeDefinition
from app.services.ui_schema_service import create_ui_schema_service
from app.ui.service import UISchemaService


class NodeTypeProvider:
    """Provides node type definitions from the active UI schema/source.

    This adapter reads from the existing UISchemaService and exposes a
    minimal async interface used by business services.
    """

    def __init__(self, service: UISchemaService | None = None) -> None:
        # lazily construct a UISchemaService using the existing compatibility
        # factory when none is provided. The factory itself respects configured
        # repositories and falls back to development defaults.
        self._service = service or create_ui_schema_service()

    async def list_node_types(self) -> Mapping[str, NodeTypeDefinition]:
        schema = await self._service.get_schema()
        # return the mapping of node_types as provided by the UISchema
        return schema.node_types

    async def get_node_type(self, type_id: str) -> NodeTypeDefinition | None:
        types = await self.list_node_types()
        return types.get((type_id or "").strip().lower())
