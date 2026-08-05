from __future__ import annotations

from typing import Iterable, List, Literal, cast

from app.prompts.models import PromptFragment, ResolvedPrompt, PROMPT_SCHEMA_VERSION
from app.prompts.errors import UnsupportedPromptModeError
from app.hierarchy.models import HierarchyActor
from app.hierarchy.repository import HierarchyRepository
from app.hierarchy.permissions import HierarchyPermissionService, READ_ACTION


PROMPT_SEPARATOR = "\n\n"


class PromptResolver:
    VALID_MODES = {"append", "prepend", "replace", "disabled"}

    def __init__(self, *, permission_service: HierarchyPermissionService | None = None):
        self._permissions = permission_service

    def resolve_from_chain(
        self,
        *,
        chain: Iterable[object],
        settings_system_prompt: str | None = None,
    ) -> ResolvedPrompt:
        """Resolve prompt fragments from an ancestor chain.

        `chain` is an iterable of node-like objects with attributes:
        - id
        - type
        - prompt_enabled (bool)
        - prompt_priority (int)
        - prompt_mode (str)
        - system_prompt (str|None)

        Returns a ResolvedPrompt with a single composed `content` and
        the list of contributing fragments in deterministic order.
        """
        fragments: List[PromptFragment] = []

        # Settings-level system prompt comes first with very low priority
        if settings_system_prompt and settings_system_prompt.strip():
            fragments.append(
                PromptFragment(
                    source_type="settings",
                    source_id="chat.system_prompt",
                    source_name="Globaler Systemprompt",
                    mode="append",
                    priority=-10000,
                    prompt=settings_system_prompt.strip(),
                    enabled=True,
                    hierarchy_depth=-1,
                )
            )

        # collect fragments from chain (chain is expected root->...->node)
        idx = 0
        last_node_id: str | None = None
        for node in chain:
            idx += 1
            # guard required attributes
            mode = getattr(node, "prompt_mode", "append")
            if mode not in self.VALID_MODES:
                raise UnsupportedPromptModeError(
                    f"Unbekannter prompt_mode '{mode}' auf Knoten {getattr(node,'id',None)}"
                )

            # explicit 'disabled' mode takes precedence and skips the fragment
            if mode == "disabled":
                continue

            enabled = getattr(node, "prompt_enabled", True)
            if not enabled:
                continue

            content = getattr(node, "system_prompt", None)
            if content is None:
                continue

            text = str(content).strip()
            if not text:
                continue

            fragments.append(
                PromptFragment(
                    source_type=str(getattr(node, "type", "node")),
                    source_id=str(getattr(node, "id")),
                    source_name=getattr(node, "name", None),
                    mode=cast(Literal["append", "prepend", "replace", "disabled"], mode),
                    priority=int(getattr(node, "prompt_priority", 0)),
                    prompt=text,
                    enabled=True,
                    hierarchy_depth=idx,
                )
            )
            last_node_id = str(getattr(node, "id"))

        # deterministic ordering:
        # primary: hierarchy depth (settings=-1, root=0, ...)
        # secondary: prompt_priority ascending
        # tertiary: source_id as tie-breaker
        fragments.sort(key=lambda f: (int(getattr(f, "hierarchy_depth", 0)), int(getattr(f, "priority", 0)), str(getattr(f, "source_id", ""))))

        # apply replace semantics: when encountering a 'replace' fragment,
        # discard previously accumulated fragments
        applied: List[PromptFragment] = []
        for frag in fragments:
            if frag.mode == "replace":
                applied = [frag]
            elif frag.mode == "prepend":
                # prepend fragment content before previously applied fragments
                applied = [frag] + applied
            else:
                applied.append(frag)

        # compose final content as concatenation of fragment prompts
        parts = [f.prompt for f in applied if f.prompt]
        final = PROMPT_SEPARATOR.join(parts) if parts else None

        # Build ResolvedPrompt
        resolved = ResolvedPrompt(
            schema_version=PROMPT_SCHEMA_VERSION,
            hierarchy_node_id=last_node_id or None,
            config_revision=None,
            hierarchy_revision=None,
            fragments=tuple(applied),
            system_prompt=final or "",
        )

        return resolved

    async def resolve(
        self,
        node_id: str,
        *,
        repository: HierarchyRepository,
        actor: HierarchyActor | None = None,
        settings_system_prompt: str | None = None,
    ) -> ResolvedPrompt:
        if actor is None:
            raise ValueError("HierarchyActor must be provided to PromptResolver.resolve")

        # require read permission for the target node when permission service provided
        if self._permissions is not None:
            node = await repository.get_node(node_id)
            if node is None:
                raise LookupError(f"Der Hierarchieknoten '{node_id}' wurde nicht gefunden.")
            self._permissions.require(actor, READ_ACTION, node)

        chain = await repository.get_ancestor_chain(node_id)
        return self.resolve_from_chain(chain=chain, settings_system_prompt=settings_system_prompt)
