from __future__ import annotations

from dataclasses import dataclass, field

from app.contracts.ui_schema import (
    UIActionDefinition,
    UIComponentDefinition,
)


class UIRegistryError(ValueError):
    """Basisklasse für Fehler der festen UI-Registry."""


class DuplicateUITypeError(UIRegistryError):
    """Ein Komponenten- oder Aktionstyp wurde doppelt registriert."""


class UnknownUITypeError(UIRegistryError):
    """Ein unbekannter Komponenten- oder Aktionstyp wurde angefordert."""


def _create_component_registry(
) -> dict[str, UIComponentDefinition]:
    return {}


def _create_action_registry(
) -> dict[str, UIActionDefinition]:
    return {}


@dataclass(slots=True)
class UIRegistry:
    """
    Feste serverseitige Freigabeliste für bekannte UI-Komponenten und Aktionen.

    Es werden ausschließlich deklarative Definitionen gespeichert.
    Dynamischer Frontend-Code wird nicht geladen.
    """

    _components: dict[
        str,
        UIComponentDefinition,
    ] = field(
        default_factory=_create_component_registry,
        repr=False,
    )

    _actions: dict[
        str,
        UIActionDefinition,
    ] = field(
        default_factory=_create_action_registry,
        repr=False,
    )

    def register_component(
        self,
        component_type: str,
        definition: UIComponentDefinition,
    ) -> None:
        normalized = self._normalize(
            component_type,
        )

        if normalized in self._components:
            raise DuplicateUITypeError(
                f"Die UI-Komponente '{normalized}' "
                "ist bereits registriert.",
            )

        self._components[
            normalized
        ] = definition

    def register_action(
        self,
        action_type: str,
        definition: UIActionDefinition,
    ) -> None:
        normalized = self._normalize(
            action_type,
        )

        if normalized in self._actions:
            raise DuplicateUITypeError(
                f"Die UI-Aktion '{normalized}' "
                "ist bereits registriert.",
            )

        self._actions[
            normalized
        ] = definition

    def require_component(
        self,
        component_type: str,
    ) -> str:
        normalized = self._normalize(
            component_type,
        )

        if normalized not in self._components:
            raise UnknownUITypeError(
                f"Die UI-Komponente '{normalized}' "
                "ist nicht freigegeben.",
            )

        return normalized

    def require_action(
        self,
        action_type: str,
    ) -> str:
        normalized = self._normalize(
            action_type,
        )

        if normalized not in self._actions:
            raise UnknownUITypeError(
                f"Die UI-Aktion '{normalized}' "
                "ist nicht freigegeben.",
            )

        return normalized

    def get_component(
        self,
        component_type: str,
    ) -> UIComponentDefinition:
        normalized = self.require_component(
            component_type,
        )

        return self._components[
            normalized
        ]

    def get_action(
        self,
        action_type: str,
    ) -> UIActionDefinition:
        normalized = self.require_action(
            action_type,
        )

        return self._actions[
            normalized
        ]

    def get_component_definitions(
        self,
    ) -> dict[str, UIComponentDefinition]:
        """Liefert eine Kopie aller Komponentendefinitionen."""

        return dict(
            self._components,
        )

    def get_action_definitions(
        self,
    ) -> dict[str, UIActionDefinition]:
        """Liefert eine Kopie aller Aktionsdefinitionen."""

        return dict(
            self._actions,
        )

    def list_components(
        self,
    ) -> list[str]:
        return sorted(
            self._components,
        )

    def list_actions(
        self,
    ) -> list[str]:
        return sorted(
            self._actions,
        )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        normalized = value.strip().lower()

        if not normalized:
            raise UIRegistryError(
                "Ein UI-Typ darf nicht leer sein.",
            )

        return normalized


def _create_component_definition(component_type: str) -> UIComponentDefinition:
    return UIComponentDefinition.model_validate({
        "id": component_type,          # <-- ID = component_type
        "component_type": component_type,
        # Weitere Felder nach Bedarf
    })
    

def _create_action_definition(action_type: str) -> UIActionDefinition:
    return UIActionDefinition.model_validate({
        "id": action_type,             # <-- ID = action_type
        "action_type": action_type,
        "label": action_type.replace("_", " ").title(),
    })

def create_default_ui_registry() -> UIRegistry:
    """Erstellt die feste Standard-Registry der Anwendung."""

    registry = UIRegistry()

    component_types: tuple[str, ...] = (
        "text",
        "textarea",
        "select",
        "checkbox",
        "toggle",
        "tree",
        "chat_view",
        "message_list",
        "chat_input",
        "table",
        "form",
        "card",
        "button_group",
        "icon",
        "prompt_editor",
        "model_selector",
        "file_upload",
    )

    action_types: tuple[str, ...] = (
        "create_child",
        "rename",
        "delete",
        "move",
        "open_form",
        "navigate",
        "download",
        "export",
        "edit_prompt",
        "toggle_tools",
        "invoke_operation",
    )

    for component_type in component_types:
        registry.register_component(
            component_type,
            _create_component_definition(
                component_type,
            ),
        )

    for action_type in action_types:
        registry.register_action(
            action_type,
            _create_action_definition(
                action_type,
            ),
        )

    return registry