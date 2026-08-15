from __future__ import annotations

from collections.abc import Iterable
from typing import Literal, cast, Any

from app.hierarchy.models import HierarchyActor
from app.hierarchy.permissions import READ_ACTION, HierarchyPermissionService
from app.hierarchy.repository import HierarchyRepository
from app.prompts.errors import UnsupportedPromptModeError
from app.prompts.models import PROMPT_SCHEMA_VERSION, PromptFragment, ResolvedPrompt
import logging
import hashlib
from app.core.settings import settings

logger = logging.getLogger(__name__)

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
        fragments: list[PromptFragment] = []

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

            # Primary source: explicit `system_prompt` column
            content = getattr(node, "system_prompt", None)

            # Fallback for legacy or UI-stored prompts: some clients store
            # the prompt inside the node metadata under the key 'prompt'. Use
            # it when `system_prompt` is missing or empty.
            if content is None or (isinstance(content, str) and not str(content).strip()):
                try:
                    meta = getattr(node, "node_metadata", None) or getattr(node, "metadata", None)
                    if isinstance(meta, dict):
                        # narrow to a dict[str, Any] for the type-checker
                        meta_dict = cast(dict[str, Any], meta)
                        maybe = meta_dict.get("prompt")
                        if isinstance(maybe, str) and maybe.strip():
                            content = maybe
                except Exception:
                    # ignore metadata access errors and continue
                    pass

            if content is None:
                continue

            text = str(content).strip()
            if not text:
                continue

            node_id_str = str(getattr(node, "id", ""))
            fragments.append(
                PromptFragment(
                    source_type=str(getattr(node, "type", "node")),
                    source_id=node_id_str,
                    source_name=getattr(node, "name", None),
                    mode=cast(
                        Literal["append", "prepend", "replace", "disabled"], mode
                    ),
                    priority=int(getattr(node, "prompt_priority", 0)),
                    prompt=text,
                    enabled=True,
                    hierarchy_depth=idx,
                )
            )
            last_node_id = node_id_str

        # deterministic ordering:
        # primary: hierarchy depth (settings=-1, root=0, ...)
        # secondary: prompt_priority ascending
        # tertiary: source_id as tie-breaker
        fragments.sort(
            key=lambda f: (
                int(getattr(f, "hierarchy_depth", 0)),
                int(getattr(f, "priority", 0)),
                str(getattr(f, "source_id", "")),
            )
        )

        # apply replace semantics: when encountering a 'replace' fragment,
        # discard previously accumulated fragments
        applied: list[PromptFragment] = []
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
            raise ValueError(
                "HierarchyActor must be provided to PromptResolver.resolve"
            )

        # require read permission for the target node when permission service provided
        if self._permissions is not None:
            node = await repository.get_node(node_id)
            if node is None:
                raise LookupError(
                    f"Der Hierarchieknoten '{node_id}' wurde nicht gefunden."
                )
            self._permissions.require(actor, READ_ACTION, node)

        chain = await repository.get_ancestor_chain(node_id)

        # Ensure we have a concrete list so it can be inspected for logging
        chain_list = list(chain)

        # perform resolution from the collected chain
        resolved = self.resolve_from_chain(
            chain=chain_list, settings_system_prompt=settings_system_prompt
        )

        # Emit concise, non-sensitive diagnostic about prompt resolution.
        # Ensure diagnostic variables are defined for static analysis.
        system_prompt_sha256 = None
        try:
            chain_ids = [str(getattr(n, "id", None)) for n in chain]
            fragment_sources = [f.source_id for f in resolved.fragments]
            effective_len = len(resolved.system_prompt or "")
            # Count hierarchy fragments (exclude settings fragment)
            hierarchy_prompt_count = sum(1 for f in resolved.fragments if getattr(f, "source_type", "") != "settings")
            global_present = any(getattr(f, "source_type", "") == "settings" for f in resolved.fragments)
            global_prompt_length = 0
            if global_present:
                for f in resolved.fragments:
                    if getattr(f, "source_type", "") == "settings":
                        global_prompt_length = len(getattr(f, "prompt", "") or "")
                        break

            # Compute non-sensitive SHA-256 of the effective system prompt
            try:
                prompt_bytes = (resolved.system_prompt or "").encode("utf-8")
                system_prompt_sha256 = (
                    hashlib.sha256(prompt_bytes).hexdigest()
                    if prompt_bytes
                    else None
                )
            except Exception:
                system_prompt_sha256 = None

            logger.info(
                "prompt_resolution_completed",
                extra={
                    "prompt_resolution": True,
                    "target_node_id": node_id,
                    "chain_node_ids": chain_ids,
                    "source_node_ids": fragment_sources,
                    "global_prompt_present": bool(global_present),
                    "global_prompt_length": global_prompt_length,
                    "hierarchy_prompt_count": hierarchy_prompt_count,
                    "effective_prompt_length": effective_len,
                    "system_prompt_sha256": system_prompt_sha256,
                },
            )
        except Exception:
            logger.debug("prompt_resolution: logging failed", exc_info=True)

        # Development-mode: emit a human-readable prompt chain and effective preview
        try:
            is_dev = str(getattr(settings, "app_environment", "")).lower() == "development"

            if is_dev:
                # Log the PROMPT_CHAIN with per-node diagnostics
                try:
                    logger.info("PROMPT_CHAIN target_node_id=%s", node_id)
                    idx = 0
                    for n in chain_list:
                        idx += 1
                        nid = getattr(n, "id", None)
                        ntype = getattr(n, "type", None)
                        nname = getattr(n, "name", None)
                        local = getattr(n, "system_prompt", None)
                        present = bool(local and str(local).strip())
                        length = len(str(local)) if present else 0
                        sha = None
                        try:
                            if present:
                                sha = hashlib.sha256(str(local).encode("utf-8")).hexdigest()
                        except Exception:
                            sha = None

                        logger.info(
                            "CHAIN_ENTRY %s id=%s type=%s name=%s local_prompt_present=%s local_prompt_length=%s sha256=%s",
                            idx,
                            nid,
                            ntype,
                            nname,
                            present,
                            length,
                            sha,
                        )
                except Exception:
                    pass

                # EFFECTIVE_PROMPT: preview and stats
                try:
                    eff_preview = (resolved.system_prompt[:200]) if resolved.system_prompt else ""
                    logger.info(
                        "EFFECTIVE_PROMPT source_count=%s length=%s sha256=%s preview=%s",
                        len(resolved.fragments),
                        len(resolved.system_prompt or ""),
                        system_prompt_sha256,
                        eff_preview,
                    )
                except Exception:
                    pass
        except Exception:
            pass

        return resolved
