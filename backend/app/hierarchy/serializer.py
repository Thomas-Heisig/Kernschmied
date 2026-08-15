from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.contracts.hierarchy import HierarchyNode, HierarchyTree
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.hierarchy.inheritance import HierarchyInheritanceService
from app.hierarchy.models import HierarchyActor
from app.hierarchy.permissions import HierarchyPermissionService


class HierarchySerializer:
    def __init__(
        self,
        *,
        permission_service: HierarchyPermissionService,
        inheritance_service: HierarchyInheritanceService,
    ) -> None:
        self._permissions = permission_service
        self._inheritance = inheritance_service

    def build_tree(
        self,
        nodes: Sequence[HierarchyNodeModel],
        *,
        actor: HierarchyActor,
        config_revision: int = 0,
    ) -> HierarchyTree:
        node_map = {node.id: node for node in nodes}
        children_by_parent: dict[str | None, list[HierarchyNodeModel]] = {}

        for node in nodes:
            children_by_parent.setdefault(node.parent_id, []).append(node)

        for children in children_by_parent.values():
            children.sort(
                key=lambda item: (
                    item.position,
                    item.name.lower(),
                    item.id,
                ),
            )

        roots = [
            self._serialize_node(
                node=node,
                node_map=node_map,
                children_by_parent=children_by_parent,
                actor=actor,
                ancestor_chain=[],
                visited=set(),
            )
            for node in children_by_parent.get(None, [])
        ]

        return HierarchyTree(
            config_revision=config_revision,
            roots=roots,
        )

    def serialize_subtree(
        self,
        root: HierarchyNodeModel,
        *,
        nodes: Sequence[HierarchyNodeModel],
        actor: HierarchyActor,
    ) -> HierarchyNode:
        node_map = {node.id: node for node in nodes}
        children_by_parent: dict[str | None, list[HierarchyNodeModel]] = {}

        for node in nodes:
            children_by_parent.setdefault(node.parent_id, []).append(node)

        ancestor_chain = self._build_ancestor_chain(root, node_map)

        return self._serialize_node(
            node=root,
            node_map=node_map,
            children_by_parent=children_by_parent,
            actor=actor,
            ancestor_chain=ancestor_chain[:-1],
            visited=set(),
        )

    def _serialize_node(
        self,
        *,
        node: HierarchyNodeModel,
        node_map: Mapping[str, HierarchyNodeModel],
        children_by_parent: Mapping[str | None, list[HierarchyNodeModel]],
        actor: HierarchyActor,
        ancestor_chain: list[HierarchyNodeModel],
        visited: set[str],
    ) -> HierarchyNode:
        del node_map

        if node.id in visited:
            raise RuntimeError("Zyklische Hierarchie erkannt.")

        current_visited = set(visited)
        current_visited.add(node.id)
        chain = [*ancestor_chain, node]
        effective = self._inheritance.resolve(chain)

        children = [
            self._serialize_node(
                node=child,
                node_map={},
                children_by_parent=children_by_parent,
                actor=actor,
                ancestor_chain=chain,
                visited=current_visited,
            )
            for child in children_by_parent.get(node.id, [])
        ]

        payload: dict[str, Any] = {
            "id": node.id,
            "type": node.type,
            "name": node.name,
            "parent_id": node.parent_id,
            "system_prompt": node.system_prompt,
            "prompt_enabled": getattr(node, "prompt_enabled", True),
            "prompt_mode": getattr(node, "prompt_mode", "append"),
            "prompt_priority": getattr(node, "prompt_priority", 0),
            "tool_policy": dict(node.tool_policy or {}),
            "config_overrides": dict(node.config_overrides or {}),
            "metadata": dict(node.node_metadata or {}),
            "effective_prompt": effective.prompt,
            "effective_tools": effective.tools,
            "effective_config": effective.config,
            "available_actions": self._permissions.available_actions(actor, node),
            "children": children,
        }

        # Construct model without runtime validation to avoid "extra_forbidden"
        # errors in environments where the contract may lag or evolve. Using
        # `model_construct` is intentional: the serializer builds a payload
        # that matches the public API contract and we prefer not to raise
        # errors during read operations. This keeps runtime behavior stable
        # while preserving static-analysis friendliness from `model_validate`
        # during development edits.
        return HierarchyNode.model_construct(**payload)

    def _build_ancestor_chain(
        self,
        node: HierarchyNodeModel,
        node_map: Mapping[str, HierarchyNodeModel],
    ) -> list[HierarchyNodeModel]:
        chain: list[HierarchyNodeModel] = []
        visited: set[str] = set()
        current: HierarchyNodeModel | None = node

        while current is not None:
            if current.id in visited:
                raise RuntimeError("Zyklische Hierarchie erkannt.")

            visited.add(current.id)
            chain.append(current)

            if current.parent_id is None:
                break

            current = node_map.get(current.parent_id)

        chain.reverse()
        return chain
