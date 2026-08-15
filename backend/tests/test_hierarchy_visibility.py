from __future__ import annotations

import pytest

from app.contracts.hierarchy import HierarchyNode, HierarchyTree
from app.hierarchy.models import HierarchyActor
from app.hierarchy.visibility import HierarchyVisibilityService


def node(
    node_id: str,
    node_type: str,
    *,
    parent_id: str | None = None,
    metadata: dict[str, object] | None = None,
    children: list[HierarchyNode] | None = None,
) -> HierarchyNode:
    return HierarchyNode(
        id=node_id,
        type=node_type,
        name=node_id,
        parent_id=parent_id,
        tool_policy={},
        config_overrides={},
        metadata=metadata or {},
        effective_tools={},
        effective_config={},
        available_actions=[],
        children=children or [],
    )


def hierarchy() -> HierarchyTree:
    own_chat = node("own-chat", "chat", parent_id="user-alice")
    own_user = node(
        "user-alice",
        "user",
        parent_id="users-root",
        metadata={"entity_type": "user", "entity_id": "alice"},
        children=[own_chat],
    )
    other_user = node(
        "user-bob",
        "user",
        parent_id="users-root",
        metadata={"entity_type": "user", "entity_id": "bob"},
        children=[node("bob-private", "workspace", parent_id="user-bob")],
    )
    users_root = node(
        "users-root",
        "folder",
        parent_id="system-root",
        children=[own_user, other_user],
    )
    workspaces_root = node(
        "workspaces-root",
        "folder",
        parent_id="system-root",
        children=[
            node("public", "workspace", metadata={"visibility": "public"}),
            node("internal", "workspace", metadata={"visibility": "internal"}),
            node("assigned", "workspace", metadata={"visibility": "assigned", "assigned_user_ids": ["alice"]}),
            node("private", "workspace", metadata={"visibility": "private"}),
        ],
    )
    return HierarchyTree(
        roots=[node("system-root", "system", children=[users_root, workspaces_root])]
    )


def test_admin_receives_the_canonical_tree_unchanged() -> None:
    tree = hierarchy()
    projected = HierarchyVisibilityService().project_tree(
        tree,
        actor=HierarchyActor(user_id="admin", roles=frozenset({"admin"})),
    )

    assert projected is tree
    assert projected.roots[0].id == "system-root"


def test_guest_receives_own_root_public_and_assigned_workspaces() -> None:
    projected = HierarchyVisibilityService().project_tree(
        hierarchy(),
        actor=HierarchyActor(
            user_id="alice",
            roles=frozenset({"guest"}),
            permissions=frozenset({"hierarchy.read"}),
        ),
    )

    assert [root.id for root in projected.roots] == ["user-alice"]
    visible_ids = {child.id for child in projected.roots[0].children}
    assert visible_ids == {"own-chat", "public", "assigned"}
    assert "user-bob" not in visible_ids
    assert "internal" not in visible_ids
    assert "private" not in visible_ids
    assert "system-root" not in visible_ids


def test_internal_user_also_receives_internal_workspaces() -> None:
    projected = HierarchyVisibilityService().project_tree(
        hierarchy(),
        actor=HierarchyActor(
            user_id="alice",
            roles=frozenset({"user"}),
            permissions=frozenset({"hierarchy.read"}),
        ),
    )

    visible_ids = {child.id for child in projected.roots[0].children}
    assert visible_ids == {"own-chat", "public", "internal", "assigned"}


def test_user_without_hierarchy_node_is_rejected() -> None:
    with pytest.raises(PermissionError, match="kein Hierarchieknoten"):
        HierarchyVisibilityService().project_tree(
            hierarchy(),
            actor=HierarchyActor(user_id="missing", permissions=frozenset({"hierarchy.read"})),
        )