from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel

PROMPT_SCHEMA_VERSION: Final[Literal["1.0"]] = "1.0"


class PromptFragment(BaseModel):
    source_type: str
    source_id: str
    source_name: str | None = None
    prompt: str
    enabled: bool = True
    priority: int = 0
    mode: Literal["append", "prepend", "replace", "disabled"] = "append"
    hierarchy_depth: int = 0

    pass


class ResolvedPrompt(BaseModel):
    schema_version: Literal["1.0"] = PROMPT_SCHEMA_VERSION
    hierarchy_node_id: str | None
    config_revision: int | None = None
    hierarchy_revision: int | None = None
    fragments: tuple[PromptFragment, ...] = ()
    system_prompt: str = ""


class ResolvedContext(BaseModel):
    schema_version: Literal["1.0"] = PROMPT_SCHEMA_VERSION
    hierarchy_node_id: str | None
    resolved_prompt: ResolvedPrompt
