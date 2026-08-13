import pytest
from app.prompts.resolver import PromptResolver
from app.prompts.models import ResolvedPrompt


class FakeNode:
    def __init__(self, id, type, system_prompt=None, prompt_mode="append", prompt_priority=0, prompt_enabled=True):
        self.id = id
        self.type = type
        self.system_prompt = system_prompt
        self.prompt_mode = prompt_mode
        self.prompt_priority = prompt_priority
        self.prompt_enabled = prompt_enabled


def test_marker_ordering_from_chain():
    # build chain: root -> parent -> chat
    root = FakeNode("system-root", "system", system_prompt="ROOT_PROMPT\nGLOBAL_MARKER_2026")
    parent = FakeNode("parent-1", "project", system_prompt="PARENT_PROMPT\nPARENT_MARKER_2026")
    chat = FakeNode("chat-1", "chat", system_prompt="CHAT_PROMPT\nCHAT_MARKER_2026")

    resolver = PromptResolver()

    resolved = resolver.resolve_from_chain(chain=(root, parent, chat), settings_system_prompt="GLOBAL_MARKER_2026")

    assert isinstance(resolved, ResolvedPrompt)

    final = resolved.system_prompt

    assert final is not None
    assert "GLOBAL_MARKER_2026" in final
    assert "PARENT_MARKER_2026" in final
    assert "CHAT_MARKER_2026" in final

    # ensure order: global then parent then chat
    g_idx = final.index("GLOBAL_MARKER_2026")
    p_idx = final.index("PARENT_MARKER_2026")
    c_idx = final.index("CHAT_MARKER_2026")

    assert g_idx < p_idx < c_idx
