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
from app.hierarchy.quotas import HierarchyQuotaService
from app.hierarchy.repository import HierarchyRepository
from app.hierarchy.serializer import HierarchySerializer
from app.hierarchy.visibility import HierarchyVisibilityService
from app.ui.node_type_provider import NodeTypeProvider


class HierarchyChildTypeNotAllowedError(ValueError):
    code = "HIERARCHY_CHILD_TYPE_NOT_ALLOWED"


class HierarchyNodeTypeChangeInvalidError(ValueError):
    code = "HIERARCHY_NODE_TYPE_CHANGE_INVALID"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details: dict[str, Any] = details or {}


class HierarchyService:
    def __init__(
        self,
        *,
        repository: HierarchyRepository,
        permission_service: HierarchyPermissionService,
        serializer: HierarchySerializer,
        node_type_provider: NodeTypeProvider | None = None,
        visibility_service: HierarchyVisibilityService | None = None,
        quota_service: HierarchyQuotaService | None = None,
    ) -> None:
        self._repository = repository
        self._permissions = permission_service
        self._serializer = serializer
        # NodeTypeProvider supplies the active registry. If none is provided,
        # create a provider that uses the UISchemaService (which may fall back
        # to in-memory defaults). This keeps create_default_node_types() as a
        # development fallback only.
        self._node_type_provider = node_type_provider or NodeTypeProvider()
        self._visibility = visibility_service or HierarchyVisibilityService()
        self._quotas = quota_service or HierarchyQuotaService(repository)

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
        tree = self._serializer.build_tree(
            nodes,
            actor=actor,
            config_revision=config_revision,
        )
        tree = self._visibility.project_tree(tree, actor=actor)

        # if a specific root is requested, serialize only that subtree
        if root_id is not None:
            await self._require_node(root_id)
            subtree = self._visibility.find_node(tree.roots, root_id)
            if subtree is None:
                raise PermissionError(
                    "Der angeforderte Hierarchieknoten ist für diesen Benutzer nicht sichtbar."
                )

            # Post-process available actions using node type definitions
            node_map = {n.id: n for n in nodes}
            node_types = await self._node_type_provider.list_node_types()

            def _apply(node: HierarchyNode):
                # derive candidate actions from node-type defaults and serializer-provided actions
                type_def = None
                if node.type:
                    type_def = node_types.get((node.type or "").strip().lower())

                type_actions = set(type_def.allowed_actions if type_def is not None else ())
                candidate = set(node.available_actions or []) | type_actions

                # honor node-level metadata restrictions if present
                model = node_map.get(node.id)
                if model is not None and isinstance(getattr(model, "node_metadata", None), dict):
                    md = model.node_metadata or {}
                    allowed_list = md.get("allowed_actions")
                    if isinstance(allowed_list, list):
                        candidate = set(str(v) for v in allowed_list if isinstance(v, str))
                    disallowed_list = md.get("disallowed_actions")
                    if isinstance(disallowed_list, list):
                        candidate -= set(str(v) for v in disallowed_list if isinstance(v, str))

                # filter by permission
                filtered = [a for a in sorted(candidate) if self._permissions.can(actor, a, model)]
                node.available_actions = filtered

                children = node.children or []
                for c in children:
                    _apply(c)

            _apply(subtree)
            return subtree

        # otherwise build full tree
        del max_depth
        # Post-process available actions for all nodes in the tree using node type definitions
        node_map = {n.id: n for n in nodes}
        node_types = await self._node_type_provider.list_node_types()

        def _apply_all(node: HierarchyNode):
            type_def = None
            if node.type:
                type_def = node_types.get((node.type or "").strip().lower())

            type_actions = set(type_def.allowed_actions if type_def is not None else ())
            candidate = set(node.available_actions or []) | type_actions

            model = node_map.get(node.id)
            if model is not None and isinstance(getattr(model, "node_metadata", None), dict):
                md = model.node_metadata or {}
                allowed_list = md.get("allowed_actions")
                if isinstance(allowed_list, list):
                    candidate = set(str(v) for v in allowed_list if isinstance(v, str))
                disallowed_list = md.get("disallowed_actions")
                if isinstance(disallowed_list, list):
                    candidate -= set(str(v) for v in disallowed_list if isinstance(v, str))

            filtered = [a for a in sorted(candidate) if self._permissions.can(actor, a, model)]
            node.available_actions = filtered

            children = node.children or []
            for c in children:
                _apply_all(c)

        roots = tree.roots or []
        for r in roots:
            _apply_all(r)

        return tree

    async def get_node(
        self,
        node_id: str,
        *,
        actor: HierarchyActor,
    ) -> HierarchyNode:
        node = await self._require_node(node_id)
        self._permissions.require(actor, READ_ACTION, node)
        nodes = await self._repository.list_nodes()
        tree = self._serializer.build_tree(
            nodes,
            actor=actor,
        )
        projected_tree = self._visibility.project_tree(tree, actor=actor)
        subtree = self._visibility.find_node(projected_tree.roots, node_id)
        if subtree is None:
            raise PermissionError(
                "Der angeforderte Hierarchieknoten ist für diesen Benutzer nicht sichtbar."
            )

        # Post-process actions for this subtree
        node_map = {n.id: n for n in nodes}
        node_types = await self._node_type_provider.list_node_types()

        def _apply(node: HierarchyNode):
            type_def = None
            if node.type:
                type_def = node_types.get((node.type or "").strip().lower())

            type_actions = set(type_def.allowed_actions if type_def is not None else ())
            candidate = set(node.available_actions or []) | type_actions

            model = node_map.get(node.id)
            if model is not None and isinstance(getattr(model, "node_metadata", None), dict):
                md = model.node_metadata or {}
                allowed_list = md.get("allowed_actions")
                if isinstance(allowed_list, list):
                    candidate = set(str(v) for v in allowed_list if isinstance(v, str))
                disallowed_list = md.get("disallowed_actions")
                if isinstance(disallowed_list, list):
                    candidate -= set(str(v) for v in disallowed_list if isinstance(v, str))

            filtered = [a for a in sorted(candidate) if self._permissions.can(actor, a, model)]
            node.available_actions = filtered

            children = node.children or []
            for c in children:
                _apply(c)

        _apply(subtree)
        return subtree

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
            if data.parent_id == "system-root" and not actor.is_admin:
                raise PermissionError(
                    "Anlegen von Knoten unter 'system-root' ist nicht erlaubt."
                )
            parent = await self._require_visible_node(data.parent_id, actor=actor)

            # Validate allowed child types via the injected NodeTypeProvider
            node_types = await self._node_type_provider.list_node_types()
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
                    f"Der Knotentyp '{parent_type}' erlaubt keine Kinder vom Typ '{data.type}'."
                )
        self._permissions.require(actor, CREATE_CHILD_ACTION, parent)
        data = await self._quotas.prepare_create(data, actor=actor, parent=parent)

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
        node = await self._require_visible_node(node_id, actor=actor)
        changes = data.model_dump(exclude_unset=True)

        if "name" in changes:
            self._permissions.require(actor, RENAME_ACTION, node)
        if "system_prompt" in changes:
            self._permissions.require(actor, EDIT_PROMPT_ACTION, node)
        if any(key in changes for key in ("prompt_enabled", "prompt_mode", "prompt_priority")):
            # Changing prompt flags/mode/priority is considered a prompt edit
            self._permissions.require(actor, EDIT_PROMPT_ACTION, node)
        if any(
            key in changes for key in ("tool_policy", "config_overrides", "metadata")
        ):
            self._permissions.require(actor, EDIT_CONFIG_ACTION, node)

        # If the node type is being changed, perform provider-driven validation
        if "type" in changes:
            new_type = (changes.get("type") or "").strip().lower()
            if not new_type:
                raise ValueError("Ungültiger Knotentyp")

            # ensure new type exists in registry
            node_types = await self._node_type_provider.list_node_types()
            if new_type not in node_types:
                raise ValueError(f"Unbekannter Knotentyp '{new_type}'")

            # Check parent compatibility
            parent = None
            if node.parent_id is not None:
                parent = await self._repository.get_node(node.parent_id)
                if parent is not None:
                    parent_type = (parent.type or "").strip().lower()
                    allowed = ()
                    if parent_type in node_types:
                        allowed = tuple(
                            t.strip().lower()
                            for t in node_types[parent_type].allowed_child_types
                        )
                    if allowed and new_type not in allowed:
                        raise HierarchyNodeTypeChangeInvalidError(
                            f"Parent vom Typ '{parent_type}' erlaubt keine Kinder vom Typ '{new_type}'.",
                            details={
                                "node_id": node.id,
                                "new_type": new_type,
                                "reason": "parent_not_allow",
                            },
                        )

            # Check existing children compatibility with the new type
            children = await self._repository.list_children(node.id)
            new_type_def = node_types.get(new_type)
            invalid_children: list[dict[str, Any]] = []
            if new_type_def is not None:
                allowed_child_types = tuple(
                    t.strip().lower() for t in new_type_def.allowed_child_types
                )
                for c in children:
                    child_type = (c.type or "").strip().lower()
                    if allowed_child_types and child_type not in allowed_child_types:
                        invalid_children.append({"id": c.id, "type": c.type})

            if invalid_children:
                raise HierarchyNodeTypeChangeInvalidError(
                    "Existing children are incompatible with the new type.",
                    details={
                        "node_id": node.id,
                        "new_type": new_type,
                        "invalid_children": invalid_children,
                    },
                )

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
        node = await self._require_visible_node(node_id, actor=actor)
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
            new_parent = await self._require_visible_node(new_parent_id, actor=actor)
            # Validate allowed child types for move target using provider
            node_types = await self._node_type_provider.list_node_types()
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
                    f"Der Knotentyp '{parent_type}' erlaubt keine Kinder vom Typ '{node_type}'."
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
            node = await self._require_visible_node(node_id, actor=actor)
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
                new_parent = await self._require_visible_node(new_parent_id, actor=actor)
                # Validate allowed child types for reorder targets via provider
                node_types = await self._node_type_provider.list_node_types()
                parent_type = getattr(new_parent, "type", "")
                normalized_parent_type = (parent_type or "").strip().lower()
                allowed = ()
                if normalized_parent_type in node_types:
                    allowed = tuple(
                        t.strip().lower()
                        for t in node_types[normalized_parent_type].allowed_child_types
                    )

                node = await self._require_visible_node(node_id, actor=actor)
                node_type = getattr(node, "type", "")
                normalized_node_type = (node_type or "").strip().lower()
                if allowed and normalized_node_type not in allowed:
                    raise HierarchyChildTypeNotAllowedError(
                        f"Der Knotentyp '{parent_type}' erlaubt keine Kinder vom Typ '{node_type}'."
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
        node = await self._require_visible_node(node_id, actor=actor)
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

    async def _require_visible_node(
        self,
        node_id: str,
        *,
        actor: HierarchyActor,
    ) -> HierarchyNodeModel:
        node = await self._require_node(node_id)
        if actor.is_admin:
            return node

        nodes = await self._repository.list_nodes()
        tree = self._serializer.build_tree(nodes, actor=actor)
        projected_tree = self._visibility.project_tree(tree, actor=actor)
        if not self._visibility.contains_node(projected_tree, node_id):
            raise PermissionError(
                "Der Hierarchieknoten ist für diesen Benutzer nicht zugänglich."
            )
        return node
