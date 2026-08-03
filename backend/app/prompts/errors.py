from __future__ import annotations


class UnsupportedPromptModeError(ValueError):
    """Raised when a prompt fragment uses an unknown prompt mode."""


class PromptHierarchyNodeNotFoundError(LookupError):
    code = "PROMPT_HIERARCHY_NODE_NOT_FOUND"


class BrokenPromptHierarchyError(LookupError):
    code = "PROMPT_HIERARCHY_BROKEN"


class PromptHierarchyCycleError(RuntimeError):
    code = "PROMPT_HIERARCHY_CYCLE"


class PromptHierarchyDepthError(RuntimeError):
    code = "PROMPT_HIERARCHY_DEPTH"


class InactivePromptHierarchyNodeError(RuntimeError):
    code = "PROMPT_HIERARCHY_INACTIVE"


class UnsupportedPromptModeError(ValueError):
    """Raised when a prompt fragment uses an unknown prompt mode."""

    pass
