from __future__ import annotations

from typing import Any

from app.contracts.hierarchy import (
    HierarchyNode,
    HierarchyNodeCreate,
    HierarchyNodeUpdate,
    HierarchyTree,
)
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.hierarchy.models import HierarchyActor
from app.hierarchy.permissions import (
    CREATE_CHILD_ACTION,
    DELETE_ACTION,
    EDIT_CONFIG_ACTION,
    EDIT_PROMPT_ACTION,
    MOVE_ACTION,
    READ_ACTION,
    RENAME_ACTION,
    HierarchyPermissionService,
)
from app.hierarchy.repository import HierarchyRepository
from app.hierarchy.serializer import HierarchySerializer


class HierarchyService:
    def __init__(
        self,
        *,
        repository: HierarchyRepository,
        permission_service: HierarchyPermissionService,
        serializer: HierarchySerializer,
    ) -> None:
        self._repository = repository
        self._permissions = permission_service
        self._serializer = serializer

    async def get_tree(
        self,
        *,
        actor: HierarchyActor,
        config_revision: int = 0,
    ) -> HierarchyTree:
        self._permissions.require(actor, READ_ACTION)
        nodes = await self._repository.list_nodes()
        return self._serializer.build_tree(
            nodes,
            actor=actor,
            config_revision=config_revision,
        )

    async def get_node(
        self,
        node_id: str,
        *,
        actor: HierarchyActor,
    ) -> HierarchyNode:
        node = await self._require_node(node_id)
        self._permissions.require(actor, READ_ACTION, node)
        nodes = await self._repository.list_nodes()
        return self._serializer.serialize_subtree(
            node,
            nodes=nodes,
            actor=actor,
        )

    async def create_node(
        self,
        data: HierarchyNodeCreate,
        *,
        actor: HierarchyActor,
    ) -> HierarchyNode:
        parent = None

        if data.parent_id is not None:
            parent = await self._require_node(data.parent_id)

        self._permissions.require(actor, CREATE_CHILD_ACTION, parent)

        try:
            node = await self._repository.create_node(data)
            await self._repository.commit()
        except Exception:
            await self._repository.rollback()
            raise

        return await self.get_node(node.id, actor=actor)

    async def update_node(
        self,
        node_id: str,
        data: HierarchyNodeUpdate,
        *,
        actor: HierarchyActor,
    ) -> HierarchyNode:
        node = await self._require_node(node_id)
        changes = data.model_dump(exclude_unset=True)

        if "name" in changes:
            self._permissions.require(actor, RENAME_ACTION, node)
        if "system_prompt" in changes:
            self._permissions.require(actor, EDIT_PROMPT_ACTION, node)
        if any(
            key in changes for key in ("tool_policy", "config_overrides", "metadata")
        ):
            self._permissions.require(actor, EDIT_CONFIG_ACTION, node)

        try:
            await self._repository.update_node(node, data)
            await self._repository.commit()
        except Exception:
            await self._repository.rollback()
            raise

        return await self.get_node(node.id, actor=actor)

    async def move_node(
        self,
        node_id: str,
        *,
        new_parent_id: str | None,
        actor: HierarchyActor,
    ) -> HierarchyNode:
        node = await self._require_node(node_id)
        self._permissions.require(actor, MOVE_ACTION, node)

        if new_parent_id == node.id:
            raise ValueError(
                "Ein Knoten kann nicht sein eigener Elternknoten sein.",
            )

        if new_parent_id is not None:
            new_parent = await self._require_node(new_parent_id)
            self._permissions.require(
                actor,
                CREATE_CHILD_ACTION,
                new_parent,
            )

            is_descendant = await self._repository.is_descendant(
                node_id=new_parent_id,
                possible_ancestor_id=node.id,
            )

            if is_descendant:
                raise ValueError(
                    "Ein Knoten kann nicht unter einen eigenen "
                    "Nachfahren verschoben werden.",
                )

        try:
            await self._repository.move_node(
                node,
                new_parent_id=new_parent_id,
            )
            await self._repository.commit()
        except Exception:
            await self._repository.rollback()
            raise

        return await self.get_node(node.id, actor=actor)

    async def delete_node(
        self,
        node_id: str,
        *,
        actor: HierarchyActor,
    ) -> None:
        node = await self._require_node(node_id)
        self._permissions.require(actor, DELETE_ACTION, node)

        try:
            await self._repository.delete_node(node.id)
            await self._repository.commit()
        except Exception:
            await self._repository.rollback()
            raise

    async def resolve_effective_values(
        self,
        node_id: str,
        *,
        actor: HierarchyActor,
    ) -> dict[str, Any]:
        node = await self.get_node(node_id, actor=actor)
        return {
            "prompt": node.effective_prompt,
            "tools": node.effective_tools,
            "config": node.effective_config,
        }

    async def _require_node(self, node_id: str) -> HierarchyNodeModel:
        node = await self._repository.get_node(node_id)

        if node is None:
            raise LookupError(
                f"Der Hierarchieknoten '{node_id}' wurde nicht gefunden.",
            )

        return node
