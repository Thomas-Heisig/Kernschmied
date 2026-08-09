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
from app.ui.node_types import create_default_node_types


class HierarchyChildTypeNotAllowedError(ValueError):
    code = "HIERARCHY_CHILD_TYPE_NOT_ALLOWED"


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
        actor: HierarchyActor | None = None,
        root_id: str | None = None,
        max_depth: int | None = None,
        config_revision: int = 0,
    ) -> HierarchyTree | HierarchyNode:
        # allow anonymous calls when actor is not provided
        if actor is None:
            actor = HierarchyActor()

        self._permissions.require(actor, READ_ACTION)

        nodes = await self._repository.list_nodes()

        # if a specific root is requested, serialize only that subtree
        if root_id is not None:
            root = await self._require_node(root_id)
            return self._serializer.serialize_subtree(
                root,
                nodes=nodes,
                actor=actor,
            )

        # otherwise build full tree
        del max_depth
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
        # Only the `system-root` may be created without a parent. All other
        # nodes must specify a parent_id. This enforces a single canonical root.
        if data.parent_id is None and data.node_id != "system-root":
            raise ValueError("Nur 'system-root' darf ohne Parent existieren.")

        parent = None
        if data.parent_id is not None:
            parent = await self._require_node(data.parent_id)

            # Validate allowed child types via the central node-type registry
            node_types = create_default_node_types()
            parent_type = getattr(parent, "type", "")
            normalized_parent_type = (parent_type or "").strip().lower()
            allowed = ()
            if normalized_parent_type in node_types:
                allowed = tuple(
                    t.strip().lower()
                    for t in node_types[normalized_parent_type].allowed_child_types
                )

            child_type = (data.type or "").strip().lower()
            if allowed and child_type not in allowed:
                raise HierarchyChildTypeNotAllowedError(
                    
                        f"Der Knotentyp '{parent_type}' erlaubt keine Kinder "
                        f"vom Typ '{data.type}'."
                    
                )
            # Disallow non-admins creating children directly under the system root.
            if parent.id == "system-root" and not getattr(actor, "is_admin", False):
                raise PermissionError(
                    "Anlegen von Knoten unter 'system-root' ist nicht erlaubt."
                )

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
        # Protect immovable/system nodes
        if getattr(node, "is_system", False) or not getattr(node, "is_movable", True):
            raise PermissionError(
                "Dieser Hierarchieknoten darf nicht verschoben werden."
            )

        self._permissions.require(actor, MOVE_ACTION, node)

        if new_parent_id == node.id:
            raise ValueError(
                "Ein Knoten kann nicht sein eigener Elternknoten sein.",
            )
        if new_parent_id is not None:
            new_parent = await self._require_node(new_parent_id)
            # Validate allowed child types for move target
            node_types = create_default_node_types()
            parent_type = getattr(new_parent, "type", "")
            normalized_parent_type = (parent_type or "").strip().lower()
            allowed = ()
            if normalized_parent_type in node_types:
                allowed = tuple(
                    t.strip().lower()
                    for t in node_types[normalized_parent_type].allowed_child_types
                )

            node_type = getattr(node, "type", "")
            normalized_node_type = (node_type or "").strip().lower()
            if allowed and normalized_node_type not in allowed:
                raise HierarchyChildTypeNotAllowedError(
                    
                        f"Der Knotentyp '{parent_type}' erlaubt keine Kinder "
                        f"vom Typ '{node_type}'."
                    
                )
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

    async def reorder_nodes(
        self,
        moves: list[tuple[str, str | None, int]],
        *,
        actor: HierarchyActor,
    ) -> None:
        """
        Atomar mehrere Neuanordnungen anwenden.

        `moves` ist eine Liste von Tupeln `(node_id, new_parent_id, new_position)`.
        """
        # Basic validation + permission checks
        # Load all nodes to move and verify existence
        for node_id, new_parent_id, _ in moves:
            node = await self._require_node(node_id)
            # Protect immovable/system nodes from being reordered
            if getattr(node, "is_system", False) or not getattr(
                node, "is_movable", True
            ):
                raise PermissionError("Dieser Knoten darf nicht verschoben werden.")
            # require permission to move
            self._permissions.require(actor, MOVE_ACTION, node)

            if new_parent_id == node.id:
                raise ValueError(
                    "Ein Knoten kann nicht sein eigener Elternknoten sein."
                )

            if new_parent_id is not None:
                new_parent = await self._require_node(new_parent_id)
                # Validate allowed child types for reorder targets
                node_types = create_default_node_types()
                parent_type = getattr(new_parent, "type", "")
                normalized_parent_type = (parent_type or "").strip().lower()
                allowed = ()
                if normalized_parent_type in node_types:
                    allowed = tuple(
                        t.strip().lower()
                        for t in node_types[normalized_parent_type].allowed_child_types
                    )

                node = await self._require_node(node_id)
                node_type = getattr(node, "type", "")
                normalized_node_type = (node_type or "").strip().lower()
                if allowed and normalized_node_type not in allowed:
                    raise HierarchyChildTypeNotAllowedError(
                        
                            f"Der Knotentyp '{parent_type}' erlaubt keine Kinder "
                            f"vom Typ '{node_type}'."
                        
                    )
                # require permission to create child under new parent
                self._permissions.require(actor, CREATE_CHILD_ACTION, new_parent)

                # prevent moving under descendant
                is_descendant = await self._repository.is_descendant(
                    node_id=new_parent_id, possible_ancestor_id=node.id
                )
                if is_descendant:
                    raise ValueError(
                        "Verschieben unter eigenen Nachfahren ist nicht erlaubt."
                    )

        try:
            await self._repository.reorder_nodes(moves)
            await self._repository.commit()
        except Exception:
            await self._repository.rollback()
            raise

    async def delete_node(
        self,
        node_id: str,
        *,
        actor: HierarchyActor,
    ) -> None:
        node = await self._require_node(node_id)
        # Protect system and non-deletable nodes
        if getattr(node, "is_system", False) or not getattr(node, "is_deletable", True):
            raise PermissionError("Dieser Hierarchieknoten darf nicht gelöscht werden.")

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
