from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from app.database.models.hierarchy_node import HierarchyNodeModel
from app.hierarchy.models import EffectiveHierarchyValues


class HierarchyInheritanceService:
    def resolve(
        self,
        chain: Sequence[HierarchyNodeModel],
    ) -> EffectiveHierarchyValues:
        prompt_parts: list[str] = []
        tools: dict[str, bool] = {}
        config: dict[str, Any] = {}

        for node in chain:
            if node.system_prompt:
                normalized_prompt = node.system_prompt.strip()
                if normalized_prompt:
                    prompt_parts.append(normalized_prompt)

            tools.update(node.tool_policy or {})
            config = self._deep_merge(
                config,
                node.config_overrides or {},
            )

        return EffectiveHierarchyValues(
            prompt="\n\n".join(prompt_parts) if prompt_parts else None,
            tools=tools,
            config=config,
        )

    def _deep_merge(
        self,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        result = dict(base)

        for key, value in override.items():
            current_value = result.get(key)
            if isinstance(current_value, dict) and isinstance(value, dict):
                result[key] = self._deep_merge(
                    cast(dict[str, Any], current_value),
                    cast(dict[str, Any], value),
                )
            else:
                result[key] = value

        return result
