from __future__ import annotations

from app.database.models.hierarchy_node import HierarchyNodeModel
from app.hierarchy.models import HierarchyActor

READ_ACTION = "read"
RENAME_ACTION = "rename"
CREATE_CHILD_ACTION = "create_child"
DELETE_ACTION = "delete"
MOVE_ACTION = "move"
EDIT_PROMPT_ACTION = "edit_prompt"
EDIT_CONFIG_ACTION = "edit_config"
TOGGLE_TOOLS_ACTION = "toggle_tools"
EXPORT_ACTION = "export"


class HierarchyPermissionService:
    def can(
        self,
        actor: HierarchyActor,
        action: str,
        node: HierarchyNodeModel | None = None,
    ) -> bool:
        if actor.is_admin:
            return True
        if f"hierarchy.{action}" in actor.permissions:
            return True
        normalized_roles = {role.strip().casefold() for role in actor.roles}
        if action == READ_ACTION:
            return bool(
                normalized_roles.intersection(
                    {"guest", "user", "internal", "intern"}
                )
            )
        if (
            action in {CREATE_CHILD_ACTION, RENAME_ACTION, DELETE_ACTION}
            and actor.user_id is not None
            and normalized_roles.intersection({"guest", "user", "internal", "intern"})
            and node is not None
        ):
            if node.id == f"user-{actor.user_id}":
                return action == CREATE_CHILD_ACTION
            metadata = dict(node.node_metadata or {})
            return metadata.get("owner_user_id") == actor.user_id
        return False

    def require(
        self,
        actor: HierarchyActor,
        action: str,
        node: HierarchyNodeModel | None = None,
    ) -> None:
        if not self.can(actor, action, node):
            raise PermissionError(
                f"Die Aktion '{action}' ist nicht erlaubt.",
            )

    def available_actions(
        self,
        actor: HierarchyActor,
        node: HierarchyNodeModel,
    ) -> list[str]:
        possible_actions = [
            READ_ACTION,
            RENAME_ACTION,
            CREATE_CHILD_ACTION,
            DELETE_ACTION,
            MOVE_ACTION,
            EDIT_PROMPT_ACTION,
            EDIT_CONFIG_ACTION,
            TOGGLE_TOOLS_ACTION,
        ]

        if node.type == "chat":
            possible_actions.append(EXPORT_ACTION)

        return [action for action in possible_actions if self.can(actor, action, node)]
