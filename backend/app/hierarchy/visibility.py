from __future__ import annotations

from collections.abc import Iterable

from app.contracts.hierarchy import HierarchyNode, HierarchyTree
from app.hierarchy.models import HierarchyActor


PUBLIC_VISIBILITIES = frozenset({"public"})
INTERNAL_VISIBILITIES = frozenset({"internal", "intern"})
INTERNAL_ROLES = frozenset({"user", "internal", "intern"})
RESTRICTED_VISIBILITIES = frozenset({"private", "restricted", "assigned"})
USER_NODE_TYPES = frozenset({"user", "benutzer"})


class HierarchyVisibilityService:
    """Projects the canonical hierarchy into the caller's readable view."""

    def project_tree(
        self,
        tree: HierarchyTree,
        *,
        actor: HierarchyActor,
    ) -> HierarchyTree:
        if actor.is_admin:
            return tree

        if not actor.user_id:
            raise PermissionError("Für die Hierarchie ist eine Anmeldung erforderlich.")

        own_node = self._find_user_node(tree.roots, actor.user_id)
        if own_node is None:
            raise PermissionError(
                "Für den angemeldeten Benutzer wurde kein Hierarchieknoten gefunden."
            )

        own_copy = own_node.model_copy(deep=True)
        own_copy.parent_id = None
        own_ids = self._collect_ids(own_node)
        can_read_internal = bool(
            {role.strip().casefold() for role in actor.roles} & INTERNAL_ROLES
        )

        shared_roots: list[HierarchyNode] = []
        for root in tree.roots:
            shared_roots.extend(
                self._collect_shared_roots(
                    root,
                    actor_user_id=actor.user_id,
                    excluded_ids=own_ids,
                    inherited_access=False,
                    can_read_internal=can_read_internal,
                )
            )

        known_ids = {node.id for node in own_copy.children}
        for shared_root in shared_roots:
            if shared_root.id in known_ids:
                continue
            shared_root.parent_id = own_copy.id
            own_copy.children.append(shared_root)
            known_ids.add(shared_root.id)

        return tree.model_copy(update={"roots": [own_copy]})

    def contains_node(self, tree: HierarchyTree, node_id: str) -> bool:
        return self.find_node(tree.roots, node_id) is not None

    def find_node(
        self,
        roots: Iterable[HierarchyNode],
        node_id: str,
    ) -> HierarchyNode | None:
        for root in roots:
            if root.id == node_id:
                return root
            found = self.find_node(root.children, node_id)
            if found is not None:
                return found
        return None

    def _find_user_node(
        self,
        roots: Iterable[HierarchyNode],
        user_id: str,
    ) -> HierarchyNode | None:
        for node in roots:
            metadata = node.metadata or {}
            entity_id = metadata.get("entity_id")
            if (
                node.type.strip().casefold() in USER_NODE_TYPES
                and metadata.get("entity_type") == "user"
                and str(entity_id) == user_id
            ):
                return node
            found = self._find_user_node(node.children, user_id)
            if found is not None:
                return found
        return None

    def _collect_shared_roots(
        self,
        node: HierarchyNode,
        *,
        actor_user_id: str,
        excluded_ids: set[str],
        inherited_access: bool,
        can_read_internal: bool,
    ) -> list[HierarchyNode]:
        if node.id in excluded_ids:
            return []

        node_type = node.type.strip().casefold()
        if node_type in USER_NODE_TYPES:
            return self._collect_from_children(
                node.children,
                actor_user_id=actor_user_id,
                excluded_ids=excluded_ids,
                inherited_access=False,
                can_read_internal=can_read_internal,
            )

        metadata = node.metadata or {}
        visibility = str(metadata.get("visibility") or "").strip().casefold()
        explicitly_assigned = self._is_assigned(metadata, actor_user_id)
        explicitly_shared = visibility in PUBLIC_VISIBILITIES or (
            can_read_internal and visibility in INTERNAL_VISIBILITIES
        )
        explicitly_restricted = visibility in RESTRICTED_VISIBILITIES
        readable = explicitly_assigned or explicitly_shared or (
            inherited_access and not explicitly_restricted
        )

        if not readable:
            return self._collect_from_children(
                node.children,
                actor_user_id=actor_user_id,
                excluded_ids=excluded_ids,
                inherited_access=False,
                can_read_internal=can_read_internal,
            )

        projected = node.model_copy(deep=True)
        projected.children = self._collect_from_children(
            node.children,
            actor_user_id=actor_user_id,
            excluded_ids=excluded_ids,
            inherited_access=True,
            can_read_internal=can_read_internal,
        )
        for child in projected.children:
            child.parent_id = projected.id
        return [projected]

    def _collect_from_children(
        self,
        children: Iterable[HierarchyNode],
        *,
        actor_user_id: str,
        excluded_ids: set[str],
        inherited_access: bool,
        can_read_internal: bool,
    ) -> list[HierarchyNode]:
        result: list[HierarchyNode] = []
        for child in children:
            result.extend(
                self._collect_shared_roots(
                    child,
                    actor_user_id=actor_user_id,
                    excluded_ids=excluded_ids,
                    inherited_access=inherited_access,
                    can_read_internal=can_read_internal,
                )
            )
        return result

    @staticmethod
    def _is_assigned(metadata: dict[str, object], user_id: str) -> bool:
        if str(metadata.get("owner_user_id") or "") == user_id:
            return True

        for key in ("assigned_user_ids", "member_user_ids", "user_ids"):
            value = metadata.get(key)
            if isinstance(value, list) and user_id in {str(item) for item in value}:
                return True
        return False

    def _collect_ids(self, node: HierarchyNode) -> set[str]:
        result = {node.id}
        for child in node.children:
            result.update(self._collect_ids(child))
        return result