from __future__ import annotations

from app.contracts.ui_schema import NodeTypeDefinition


def create_default_node_types() -> dict[str, NodeTypeDefinition]:
    """Erzeugt die einfachen MVP-Node-Typen ohne globale mutable Instanz."""

    return {
        "user": NodeTypeDefinition(
            label="Benutzer",
            icon="UserCircle",
            color="#6366f1",
            allowed_child_types=("workspace",),
            allowed_actions=(
                "rename",
                "create_child",
            ),
        ),
        "workspace": NodeTypeDefinition(
            label="Bereich",
            icon="Building2",
            color="#f59e0b",
            allowed_child_types=("project",),
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
            allowed_child_types=(),
            allowed_actions=(
                "rename",
                "delete",
                "export",
            ),
        ),
    }
