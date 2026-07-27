from __future__ import annotations

from dataclasses import dataclass

from app.contracts.ui_schema import UISchema
from app.ui.repository import UISchemaRepository
from app.ui.serializer import UISchemaSerializer


@dataclass(frozen=True, slots=True)
class UISchemaResult:
    schema: UISchema
    config_revision: int


class UISchemaService:
    """Orchestriert Repository, Validierung und Schema-Erzeugung."""

    def __init__(
        self,
        *,
        repository: UISchemaRepository,
        serializer: UISchemaSerializer,
    ) -> None:
        self._repository = repository
        self._serializer = serializer

    async def get_schema(self) -> UISchema:
        node_types = await self._repository.get_node_types()
        return self._serializer.build_schema(node_types)

    async def get_schema_result(self) -> UISchemaResult:
        node_types = await self._repository.get_node_types()
        revision = await self._repository.get_config_revision()

        return UISchemaResult(
            schema=self._serializer.build_schema(node_types),
            config_revision=revision,
        )
