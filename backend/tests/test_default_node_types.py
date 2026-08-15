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


def test_chat_node_type_exposes_prompt_and_tool_actions() -> None:
    chat = create_default_node_types()["chat"]

    assert "edit_prompt" in chat.allowed_actions
    assert "toggle_tools" in chat.allowed_actions


def test_user_node_type_exposes_prompt_action() -> None:
    user = create_default_node_types()["user"]

    assert "edit_prompt" in user.allowed_actions