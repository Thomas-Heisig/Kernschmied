from __future__ import annotations

from app.contracts.ui_schema import NodeTypeDefinition


def create_default_node_types() -> dict[str, NodeTypeDefinition]:
    """Erzeugt die einfachen MVP-Node-Typen ohne globale mutable Instanz."""

    return {
        "system": NodeTypeDefinition(
            label="System",
            icon="ServerCog",
            color="#64748b",
            allowed_child_types=("users-root", "workspaces-root", "chats-root"),
            allowed_actions=(),
            selectable=True,
            draggable=False,
            droppable=True,
            expandable=True,
        ),
        "user": NodeTypeDefinition(
            label="Benutzer",
            icon="UserCircle",
            color="#6366f1",
            allowed_child_types=("workspace",),
            allowed_actions=(
                "rename",
                "create_child",
                "edit_prompt",
            ),
        ),
        "workspace": NodeTypeDefinition(
            label="Bereich",
            icon="Building2",
            color="#f59e0b",
            allowed_child_types=("project", "chat"),
            allowed_actions=(
                "rename",
                "delete",
                "create_child",
                "edit_prompt",
            ),
        ),
        "project": NodeTypeDefinition(
            label="Projekt",
            icon="FolderKanban",
            color="#3b82f6",
            allowed_child_types=("chat",),
            allowed_actions=(
                "rename",
                "delete",
                "create_child",
                "edit_prompt",
                "toggle_tools",
            ),
        ),
        "chat": NodeTypeDefinition(
            label="Chat",
            icon="MessageSquare",
            color="#8b5cf6",
            allowed_child_types=("chat", "folder"),
            allowed_actions=(
                "rename",
                "delete",
                "export",
                "create_child",
                "move",
                "edit_prompt",
                "toggle_tools",
            ),
            selectable=True,
            draggable=True,
            droppable=True,
            expandable=True,
        ),
        "folder": NodeTypeDefinition(
            label="Ordner",
            icon="Folder",
            color="#94a3b8",
            allowed_child_types=("chat", "folder"),
            allowed_actions=(
                "rename",
                "delete",
                "create_child",
                "move",
            ),
            selectable=True,
            draggable=True,
            droppable=True,
            expandable=True,
        ),
        # Container-specific node definitions (ID-specific) to allow the
        # frontend to resolve node rendering behavior by node ID first.
        # These definitions ensure that `users-root`, `workspaces-root` and
        # `chats-root` expose the correct allowed child types and actions
        # instead of inheriting the generic `folder` behavior.
        "users-root": NodeTypeDefinition(
            label="Benutzer",
            icon="UserCircle",
            color="#6366f1",
            allowed_child_types=("user",),
            allowed_actions=(
                "create_child",
            ),
            selectable=True,
            draggable=False,
            droppable=True,
            expandable=True,
        ),
        "workspaces-root": NodeTypeDefinition(
            label="Arbeitsbereiche",
            icon="Building2",
            color="#f59e0b",
            allowed_child_types=("workspace",),
            allowed_actions=(
                "create_child",
            ),
            selectable=True,
            draggable=False,
            droppable=True,
            expandable=True,
        ),
        "chats-root": NodeTypeDefinition(
            label="Chats",
            icon="MessageSquare",
            color="#8b5cf6",
            allowed_child_types=("chat",),
            allowed_actions=(),
            selectable=True,
            draggable=False,
            droppable=True,
            expandable=True,
        ),
    }
