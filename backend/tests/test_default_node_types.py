from app.ui.node_types import create_default_node_types


def test_system_root_is_exposed_as_protected_ui_node_type() -> None:
    system = create_default_node_types()["system"]

    assert system.label == "System"
    assert system.allowed_child_types == ("users-root", "workspaces-root", "chats-root")
    assert system.allowed_actions == ()
    assert system.selectable is True
    assert system.draggable is False
    assert system.droppable is True
    assert system.expandable is True