from __future__ import annotations

import pytest

from typing import Optional, cast

from app.prompts.resolver import PromptResolver
from app.prompts.errors import UnsupportedPromptModeError
# PromptFragment not required in these tests
from app.hierarchy.models import HierarchyActor
from app.hierarchy.permissions import HierarchyPermissionService
from app.hierarchy.repository import HierarchyRepository


class FakeNode:
    def __init__(
        self,
        id: str,
        type: str,
        system_prompt: Optional[str] = None,
        prompt_enabled: bool = True,
        prompt_priority: int = 0,
        prompt_mode: str = "append",
    ) -> None:
        self.id: str = id
        self.type: str = type
        self.system_prompt: Optional[str] = system_prompt
        self.prompt_enabled: bool = prompt_enabled
        self.prompt_priority: int = prompt_priority
        self.prompt_mode: str = prompt_mode


def test_full_ancestor_chain_order():
    # settings -> system-root -> user -> workspace -> project -> chat
    chain = [
        FakeNode("system-root", "system", system_prompt="S0", prompt_priority=-1000),
        FakeNode("user-thomas", "user", system_prompt="U0", prompt_priority=-100),
        FakeNode("corp-acme", "workspace", system_prompt="W0", prompt_priority=0),
        FakeNode("project-x", "project", system_prompt="P0", prompt_priority=10),
        FakeNode("chat-1", "chat", system_prompt="C0", prompt_priority=20),
    ]

    resolver = PromptResolver()
    resolved = resolver.resolve_from_chain(chain=chain, settings_system_prompt="SETTINGS")

    # fragments should be present in deterministic order by priority
    ids: list[str] = [f.source_id for f in resolved.fragments]
    assert ids[0] == "chat.system_prompt"
    assert ids[-1] == "chat-1"
    assert "user-thomas" in ids
    assert "project-x" in ids


def test_disabled_fragments_ignored():
    chain = [
        FakeNode("system-root", "system", system_prompt="S0"),
        FakeNode("user-a", "user", system_prompt="U0", prompt_enabled=False),
        FakeNode("chat-1", "chat", system_prompt="C0"),
    ]

    resolver = PromptResolver()
    resolved = resolver.resolve_from_chain(chain=chain)

    ids: list[str] = [f.source_id for f in resolved.fragments]
    assert "user-a" not in ids
    assert "chat-1" in ids


def test_replace_discards_previous():
    chain = [
        FakeNode("system-root", "system", system_prompt="S0", prompt_priority=-100),
        FakeNode("user-a", "user", system_prompt="U0", prompt_mode="replace", prompt_priority=0),
        FakeNode("chat-1", "chat", system_prompt="C0", prompt_priority=10),
    ]

    resolver = PromptResolver()
    resolved = resolver.resolve_from_chain(chain=chain)

    ids: list[str] = [f.source_id for f in resolved.fragments]
    # after replace only user-a and following fragments remain
    assert ids[0] == "user-a"
    assert "system-root" not in ids


def test_priorities_are_deterministic():
    chain = [
        FakeNode("a", "type", system_prompt="A", prompt_priority=5),
        FakeNode("b", "type", system_prompt="B", prompt_priority=1),
        FakeNode("c", "type", system_prompt="C", prompt_priority=3),
    ]

    resolver = PromptResolver()
    resolved = resolver.resolve_from_chain(chain=chain)

    keys = [(f.hierarchy_depth, f.priority) for f in resolved.fragments]
    assert keys == sorted(keys)


def test_unknown_mode_rejected():
    chain = [FakeNode("n", "type", system_prompt="X", prompt_mode="unknown")]
    resolver = PromptResolver()
    with pytest.raises(UnsupportedPromptModeError):
        resolver.resolve_from_chain(chain=chain)


@pytest.mark.asyncio
async def test_resolve_requires_read_permission():
    # fake repository that returns a simple chain and a node
    class Repo:
        async def get_node(self, node_id: str) -> FakeNode:
            return FakeNode(node_id, "chat", system_prompt="C")

        async def get_ancestor_chain(self, node_id: str) -> list[FakeNode]:
            return [
                FakeNode("system-root", "system", system_prompt="S"),
                FakeNode(node_id, "chat", system_prompt="C"),
            ]

    repo = Repo()
    actor = HierarchyActor(user_id="someone", roles=frozenset(), permissions=frozenset())
    permission_service = HierarchyPermissionService()
    resolver = PromptResolver(permission_service=permission_service)

    with pytest.raises(PermissionError):
        await resolver.resolve("chat-1", repository=cast(HierarchyRepository, repo), actor=actor)