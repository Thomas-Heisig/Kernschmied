from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.contracts.hierarchy import HierarchyNodeCreate
from app.hierarchy.models import HierarchyActor
from app.hierarchy.permissions import (
    CREATE_CHILD_ACTION,
    DELETE_ACTION,
    EDIT_CONFIG_ACTION,
    EDIT_PROMPT_ACTION,
    EXPORT_ACTION,
    MOVE_ACTION,
    RENAME_ACTION,
    TOGGLE_TOOLS_ACTION,
    HierarchyPermissionService,
)
from app.hierarchy.quotas import (
    HierarchyQuotaExceededError,
    HierarchyQuotaService,
)


def model(
    node_id: str,
    node_type: str,
    *,
    parent_id: str | None,
    owner_user_id: str | None = None,
):
    return SimpleNamespace(
        id=node_id,
        type=node_type,
        parent_id=parent_id,
        node_metadata=(
            {"owner_user_id": owner_user_id} if owner_user_id is not None else {}
        ),
    )


def payload(node_type: str, parent_id: str) -> HierarchyNodeCreate:
    return HierarchyNodeCreate(
        type=node_type,
        name=f"New {node_type}",
        parent_id=parent_id,
        tool_policy={},
        config_overrides={},
        metadata={"visibility": "public", "owner_user_id": "forged"},
    )


class ConfigStub:
    def __init__(self, values: dict[tuple[str, str], int]) -> None:
        self.values = values

    def get(self, group: str, key: str, default=None):
        return self.values.get((group, key), default)


@pytest.mark.asyncio
async def test_guest_create_is_owned_private_and_limited_to_one_workspace():
    actor = HierarchyActor(user_id="alice", roles=frozenset({"guest"}))
    user_root = model("user-alice", "user", parent_id="users-root")
    repository = SimpleNamespace(list_nodes=AsyncMock(return_value=[user_root]))
    quota_service = HierarchyQuotaService(repository)

    prepared = await quota_service.prepare_create(
        payload("workspace", user_root.id),
        actor=actor,
        parent=user_root,
    )

    assert prepared.metadata == {
        "visibility": "private",
        "owner_user_id": "alice",
    }

    workspace = model(
        "workspace-alice",
        "workspace",
        parent_id=user_root.id,
        owner_user_id="alice",
    )
    repository.list_nodes.return_value = [user_root, workspace]

    with pytest.raises(HierarchyQuotaExceededError, match="1/1"):
        await quota_service.prepare_create(
            payload("workspace", user_root.id),
            actor=actor,
            parent=user_root,
        )


@pytest.mark.asyncio
async def test_guest_cannot_create_below_an_assigned_foreign_workspace():
    actor = HierarchyActor(user_id="alice", roles=frozenset({"guest"}))
    user_root = model("user-alice", "user", parent_id="users-root")
    foreign = model("foreign", "workspace", parent_id="workspaces-root")
    repository = SimpleNamespace(
        list_nodes=AsyncMock(return_value=[user_root, foreign])
    )

    with pytest.raises(PermissionError, match="eigenen Bereich"):
        await HierarchyQuotaService(repository).prepare_create(
            payload("project", foreign.id),
            actor=actor,
            parent=foreign,
        )


def test_guest_receives_prompt_permission_only_for_own_user_node():
    actor = HierarchyActor(user_id="alice", roles=frozenset({"guest"}))
    permissions = HierarchyPermissionService()
    own_root = model("user-alice", "user", parent_id="users-root")
    own_workspace = model(
        "own-workspace",
        "workspace",
        parent_id=own_root.id,
        owner_user_id="alice",
    )
    foreign_workspace = model("foreign", "workspace", parent_id="workspaces-root")
    foreign_user = model("user-bob", "user", parent_id="users-root")

    assert permissions.can(actor, CREATE_CHILD_ACTION, own_root)
    assert permissions.can(actor, EDIT_PROMPT_ACTION, own_root)
    assert permissions.can(actor, CREATE_CHILD_ACTION, own_workspace)
    assert not permissions.can(actor, CREATE_CHILD_ACTION, foreign_workspace)
    assert not permissions.can(actor, EDIT_PROMPT_ACTION, foreign_user)


def test_owner_receives_edit_actions_for_own_chat_and_not_foreign_chat():
    actor = HierarchyActor(user_id="alice", roles=frozenset({"guest"}))
    permissions = HierarchyPermissionService()
    own_chat = model(
        "own-chat",
        "chat",
        parent_id="own-project",
        owner_user_id="alice",
    )
    foreign_chat = model(
        "foreign-chat",
        "chat",
        parent_id="foreign-project",
        owner_user_id="bob",
    )

    expected_actions = {
        CREATE_CHILD_ACTION,
        RENAME_ACTION,
        DELETE_ACTION,
        MOVE_ACTION,
        EDIT_PROMPT_ACTION,
        EDIT_CONFIG_ACTION,
        TOGGLE_TOOLS_ACTION,
        EXPORT_ACTION,
    }
    assert expected_actions.issubset(
        set(permissions.available_actions(actor, own_chat))
    )
    assert expected_actions.isdisjoint(
        permissions.available_actions(actor, foreign_chat)
    )


@pytest.mark.asyncio
async def test_admin_configured_guest_limit_is_enforced():
    actor = HierarchyActor(user_id="alice", roles=frozenset({"guest"}))
    user_root = model("user-alice", "user", parent_id="users-root")
    repository = SimpleNamespace(list_nodes=AsyncMock(return_value=[user_root]))
    config = ConfigStub({("security", "guest_workspace_limit"): 0})

    with pytest.raises(HierarchyQuotaExceededError) as exc_info:
        await HierarchyQuotaService(repository, config).prepare_create(
            payload("workspace", user_root.id),
            actor=actor,
            parent=user_root,
        )

    assert exc_info.value.details == {
        "node_type": "workspace",
        "limit": 0,
        "used": 0,
    }


@pytest.mark.asyncio
async def test_internal_defaults_are_higher_and_admin_is_unlimited():
    user_root = model("user-alice", "user", parent_id="users-root")
    repository = SimpleNamespace(list_nodes=AsyncMock(return_value=[user_root]))
    quota_service = HierarchyQuotaService(repository)

    internal_status = await quota_service.status(
        HierarchyActor(user_id="alice", roles=frozenset({"internal"}))
    )
    admin_status = await quota_service.status(
        HierarchyActor(user_id="admin", roles=frozenset({"admin"}))
    )

    assert internal_status["limits"] == {
        "workspace": 5,
        "project": 10,
        "chat": 25,
    }
    assert admin_status["limits"] is None