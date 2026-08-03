from __future__ import annotations

from typing import Optional, List
from app.prompts.models import ResolvedPrompt

from app.prompts.resolver import PromptResolver
# PromptFragment not required in these tests


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
        self.id = id
        self.type = type
        self.system_prompt = system_prompt
        self.prompt_enabled = prompt_enabled
        self.prompt_priority = prompt_priority
        self.prompt_mode = prompt_mode


def _ids(resolved: ResolvedPrompt) -> List[str]:
    return [f.source_id for f in resolved.fragments]


def test_append_prepend_replace_sequences():
    # append
    chain = [
        FakeNode("a", "n", system_prompt="A", prompt_priority=0),
        FakeNode("b", "n", system_prompt="B", prompt_priority=0),
    ]
    r = PromptResolver()
    resolved = r.resolve_from_chain(chain=chain)
    assert _ids(resolved) == ["a", "b"]

    # prepend
    chain = [
        FakeNode("a", "n", system_prompt="A", prompt_priority=0),
        FakeNode("b", "n", system_prompt="B", prompt_mode="prepend", prompt_priority=0),
    ]
    resolved = r.resolve_from_chain(chain=chain)
    assert _ids(resolved) == ["b", "a"]

    # replace
    chain = [
        FakeNode("a", "n", system_prompt="A", prompt_priority=0),
        FakeNode("b", "n", system_prompt="B", prompt_mode="replace", prompt_priority=0),
        FakeNode("c", "n", system_prompt="C", prompt_priority=1),
    ]
    resolved = r.resolve_from_chain(chain=chain)
    # after replace only b and c (which follows) should remain
    assert _ids(resolved)[0] == "b"


def test_mode_transitions():
    r = PromptResolver()

    # append -> replace
    chain = [
        FakeNode("s", "n", system_prompt="S"),
        FakeNode("p", "n", system_prompt="P", prompt_mode="replace"),
        FakeNode("c", "n", system_prompt="C"),
    ]
    resolved = r.resolve_from_chain(chain=chain)
    assert _ids(resolved)[0] == "p"

    # replace -> append
    chain = [
        FakeNode("s", "n", system_prompt="S"),
        FakeNode("r", "n", system_prompt="R", prompt_mode="replace"),
        FakeNode("a", "n", system_prompt="A", prompt_priority=1),
    ]
    resolved = r.resolve_from_chain(chain=chain)
    assert _ids(resolved)[0] == "r"

    # append -> prepend
    chain = [
        FakeNode("a", "n", system_prompt="A"),
        FakeNode("b", "n", system_prompt="B", prompt_mode="prepend"),
    ]
    resolved = r.resolve_from_chain(chain=chain)
    assert _ids(resolved) == ["b", "a"]


def test_ignores_disabled_and_empty_and_whitespace():
    r = PromptResolver()
    chain = [
        FakeNode("a", "n", system_prompt="A"),
        FakeNode("b", "n", system_prompt="   ", prompt_priority=0),
        FakeNode("c", "n", system_prompt=None),
        FakeNode("d", "n", system_prompt="D", prompt_enabled=False),
    ]
    resolved = r.resolve_from_chain(chain=chain)
    assert _ids(resolved) == ["a"]


def test_unknown_mode_raises():
    r = PromptResolver()
    chain = [FakeNode("x", "n", system_prompt="X", prompt_mode="unknown")]
    try:
        r.resolve_from_chain(chain=chain)
        raised = False
    except Exception:
        raised = True

    assert raised
