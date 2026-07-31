from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.contracts.ui_schema import (
    NodeTypeDefinition,
    UIActionDefinition,
    UIComponentDefinition,
    UISchema,
)
from app.ui.registry import UIRegistry


class UISchemaSerializer:
    """
    Validiert konfigurierbare Node-Typen gegen die feste UI-Registry.
    """

    def __init__(
        self,
        registry: UIRegistry,
    ) -> None:
        self._registry = registry

    def build_schema(
        self,
        node_types: Mapping[
            str,
            NodeTypeDefinition,
        ],
    ) -> UISchema:
        validated_node_types: dict[
            str,
            NodeTypeDefinition,
        ] = {}

        for (
            node_type,
            definition,
        ) in node_types.items():
            normalized_node_type = node_type.strip().lower()

            if not normalized_node_type:
                raise ValueError(
                    "Ein Node-Typ darf nicht leer sein.",
                )

            if normalized_node_type in validated_node_types:
                raise ValueError(
                    f"Der Node-Typ '{normalized_node_type}' ist doppelt definiert.",
                )

            normalized_actions = self._validate_actions(
                definition.allowed_actions,
            )

            # Die Aktionen werden validiert. Das ursprüngliche
            # Definition-Objekt bleibt unverändert, sofern die
            # Vertragsklasse keine model_copy-Operation benötigt.
            del normalized_actions

            validated_node_types[normalized_node_type] = definition

        known_node_types = set(
            validated_node_types,
        )

        for (
            node_type,
            definition,
        ) in validated_node_types.items():
            normalized_child_types = {
                child_type.strip().lower()
                for child_type in definition.allowed_child_types
                if child_type.strip()
            }

            unknown_children = normalized_child_types - known_node_types

            if unknown_children:
                raise ValueError(
                    f"Der Node-Typ '{node_type}' "
                    "referenziert unbekannte Kindtypen: "
                    f"{sorted(unknown_children)}",
                )

        components: dict[
            str,
            UIComponentDefinition,
        ] = self._registry.get_component_definitions()

        actions: dict[
            str,
            UIActionDefinition,
        ] = self._registry.get_action_definitions()

        return UISchema(
            components=components,
            actions=actions,
            node_types=validated_node_types,
        )

    def _validate_actions(
        self,
        action_types: Sequence[str],
    ) -> list[str]:
        """
        Validiert und normalisiert alle Aktionen eines Node-Typs.
        """

        validated_actions: list[str] = []

        for action_type in action_types:
            validated_actions.append(
                self._registry.require_action(
                    action_type,
                ),
            )

        return validated_actions
