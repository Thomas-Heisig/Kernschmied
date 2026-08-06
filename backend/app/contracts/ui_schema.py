# F:\Kernschmied\backend\app\contracts\ui_schema.py

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Final, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

UI_SCHEMA_NAME: Final[Literal["app-ui"]] = "app-ui"
UI_SCHEMA_VERSION: Final[Literal["1.0"]] = "1.0"
MINIMUM_CLIENT_VERSION: Final[str] = "0.1.0"


IDENTIFIER_PATTERN = re.compile(
    r"^[a-z][a-z0-9_.-]*$",
)


class UISchemaContractError(ValueError):
    """
    Basisklasse für ungültige UI-Schema-Verträge.
    """


class UIComponentKind(str, Enum):
    """
    Bekannte generische Komponentenarten.

    Diese Werte beschreiben nur den Typ einer Komponente. Das Frontend
    entscheidet über eine feste Registry, welche konkrete React-Komponente
    dafür verwendet wird.
    """

    TREE = "tree"
    LIST = "list"
    TABLE = "table"
    FORM = "form"
    CHAT = "chat"
    PANEL = "panel"
    TABS = "tabs"
    TEXT = "text"
    MARKDOWN = "markdown"
    BADGE = "badge"
    BUTTON = "button"
    INPUT = "input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    NUMBER = "number"
    TEXTAREA = "textarea"
    JSON = "json"
    UNKNOWN = "unknown"


class UIActionKind(str, Enum):
    """
    Fest definierte Kategorien von UI-Aktionen.

    Das Frontend darf keine beliebigen Funktionen aus dem Schema ausführen.
    Jede Aktion wird über eine bekannte Action-Registry aufgelöst.
    """

    NAVIGATE = "navigate"
    OPEN_DIALOG = "open_dialog"
    CLOSE_DIALOG = "close_dialog"
    SUBMIT_FORM = "submit_form"
    RELOAD = "reload"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    SELECT = "select"
    TOGGLE = "toggle"
    COPY = "copy"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    UNKNOWN = "unknown"


class UIActionMethod(str, Enum):
    """
    Zulässige HTTP-Methoden für API-gebundene Aktionen.
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class UIActionConfirmationStyle(str, Enum):
    """
    Darstellung einer Aktionsbestätigung.
    """

    NONE = "none"
    SIMPLE = "simple"
    DANGER = "danger"
    TYPED = "typed"


class UIFormFieldType(str, Enum):
    """
    Bekannte generische Formularfelder.
    """

    TEXT = "text"
    TEXTAREA = "textarea"
    PASSWORD = "password"
    NUMBER = "number"
    INTEGER = "integer"
    CHECKBOX = "checkbox"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    TAGS = "tags"
    JSON = "json"
    DATE = "date"
    DATETIME = "datetime"
    URL = "url"
    EMAIL = "email"
    FILE = "file"
    MODEL_SELECT = "model_select"
    TOOL_SELECT = "tool_select"
    NODE_SELECT = "node_select"
    HIDDEN = "hidden"
    UNKNOWN = "unknown"


class UIVisibility(str, Enum):
    """
    Sichtbarkeit eines Schemaelements.
    """

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"
    INTERNAL = "internal"


class UIOption(BaseModel):
    """
    Statische Auswahloption.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    value: str | int | float | bool

    label: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    disabled: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class UIDynamicOptions(BaseModel):
    """
    Kontrollierte dynamische Optionsquelle.

    Es dürfen ausschließlich interne API-Endpunkte verwendet werden.
    Das Frontend interpretiert keine beliebigen externen URLs.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    endpoint: str = Field(
        min_length=1,
        max_length=500,
    )

    value_field: str = Field(
        default="id",
        min_length=1,
        max_length=100,
    )

    label_field: str = Field(
        default="name",
        min_length=1,
        max_length=100,
    )

    description_field: str | None = Field(
        default="description",
        max_length=100,
    )

    filters: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(
        cls,
        value: str,
    ) -> str:
        if not value.startswith("/api/"):
            raise ValueError(
                "Dynamische UI-Optionsquellen müssen mit '/api/' beginnen.",
            )

        return value


class UIComponentDefinition(BaseModel):
    """
    Beschreibung einer bekannten generischen UI-Komponente.

    `component_type` muss durch die feste Frontend-Registry unterstützt
    werden. Unbekannte Typen werden nicht dynamisch importiert.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    id: str = Field(
        min_length=1,
        max_length=150,
    )

    component_type: str = Field(
        min_length=1,
        max_length=150,
    )

    kind: UIComponentKind = UIComponentKind.UNKNOWN

    label: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    icon: str | None = Field(
        default=None,
        max_length=255,
    )

    order: int = Field(
        default=0,
        ge=-100_000,
        le=100_000,
    )

    visibility: UIVisibility = UIVisibility.AUTHENTICATED

    required_permissions: tuple[str, ...] = ()

    props: dict[str, Any] = Field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator(
        "id",
        "component_type",
    )
    @classmethod
    def validate_identifier(
        cls,
        value: str,
    ) -> str:
        if not IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError(
                f"Ungültiger UI-Bezeichner: '{value}'.",
            )

        return value


class UIActionConfirmation(BaseModel):
    """
    Optionale Bestätigungsdefinition einer UI-Aktion.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    style: UIActionConfirmationStyle = UIActionConfirmationStyle.SIMPLE

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    message: str = Field(
        min_length=1,
        max_length=2000,
    )

    confirm_label: str = Field(
        default="Bestätigen",
        min_length=1,
        max_length=100,
    )

    cancel_label: str = Field(
        default="Abbrechen",
        min_length=1,
        max_length=100,
    )

    typed_value: str | None = Field(
        default=None,
        max_length=255,
    )

    @model_validator(mode="after")
    def validate_typed_confirmation(
        self,
    ) -> UIActionConfirmation:
        if self.style == UIActionConfirmationStyle.TYPED and not self.typed_value:
            raise ValueError(
                "Eine typed-Bestätigung benötigt typed_value.",
            )

        return self


class UIActionDefinition(BaseModel):
    """
    Versionierte Beschreibung einer bekannten Frontend-Aktion.

    Die Definition ist keine ausführbare Logik. Das Frontend löst `id`
    ausschließlich über seine feste Action-Registry auf. Der Server
    autorisiert jede daraus entstehende Anfrage erneut.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    id: str = Field(
        min_length=1,
        max_length=150,
    )

    action_type: str = Field(
        min_length=1,
        max_length=150,
    )

    kind: UIActionKind = UIActionKind.UNKNOWN

    label: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    icon: str | None = Field(
        default=None,
        max_length=255,
    )

    method: UIActionMethod | None = None

    endpoint: str | None = Field(
        default=None,
        max_length=500,
    )

    required_permissions: tuple[str, ...] = ()

    confirmation: UIActionConfirmation | None = None

    payload_schema: dict[str, Any] | None = None

    result_schema: dict[str, Any] | None = None

    enabled: bool = True

    visibility: UIVisibility = UIVisibility.AUTHENTICATED

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator(
        "id",
        "action_type",
    )
    @classmethod
    def validate_identifier(
        cls,
        value: str,
    ) -> str:
        if not IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError(
                f"Ungültiger UI-Aktionsbezeichner: '{value}'.",
            )

        return value

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not value.startswith("/api/"):
            raise ValueError(
                "UI-Aktionsendpunkte müssen mit '/api/' beginnen.",
            )

        return value

    @model_validator(mode="after")
    def validate_endpoint_method_pair(
        self,
    ) -> UIActionDefinition:
        if self.endpoint is None and self.method is not None:
            raise ValueError(
                "Eine HTTP-Methode darf nur zusammen mit endpoint angegeben werden.",
            )

        if self.endpoint is not None and self.method is None:
            raise ValueError(
                "Ein API-Endpunkt benötigt eine HTTP-Methode.",
            )

        return self


class UIFormFieldDefinition(BaseModel):
    """
    Generisches Formularfeld.

    Das JSON-Schema des Formulars bleibt für die serverseitige
    Datenvalidierung maßgeblich. Diese Definition steuert Darstellung,
    Reihenfolge und Eingabehilfen.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    field_type: UIFormFieldType

    label: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    placeholder: str | None = Field(
        default=None,
        max_length=500,
    )

    help_text: str | None = Field(
        default=None,
        max_length=2000,
    )

    required: bool = False
    readonly: bool = False
    hidden: bool = False
    disabled: bool = False

    order: int = Field(
        default=0,
        ge=-100_000,
        le=100_000,
    )

    default_value: Any = None

    options: tuple[UIOption, ...] = ()

    dynamic_options: UIDynamicOptions | None = None

    validation_schema: dict[str, Any] | None = None

    visible_when: dict[str, Any] | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        if not IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError(
                f"Ungültiger Formularfeldname: '{value}'.",
            )

        return value

    @model_validator(mode="after")
    def validate_option_sources(
        self,
    ) -> UIFormFieldDefinition:
        if self.options and self.dynamic_options is not None:
            raise ValueError(
                "Ein Formularfeld darf nicht gleichzeitig statische "
                "und dynamische Optionen besitzen.",
            )

        return self


class UIFormDefinition(BaseModel):
    """
    Generische, schema-gesteuerte Formulardefinition.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    id: str = Field(
        min_length=1,
        max_length=150,
    )

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    schema_version: str = Field(
        default="1.0",
        min_length=1,
        max_length=50,
    )

    value_schema: dict[str, Any]

    fields: tuple[UIFormFieldDefinition, ...] = ()

    submit_action: str | None = Field(
        default=None,
        max_length=150,
    )

    cancel_action: str | None = Field(
        default=None,
        max_length=150,
    )

    required_permissions: tuple[str, ...] = ()

    visibility: UIVisibility = UIVisibility.AUTHENTICATED

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator(
        "id",
        "submit_action",
        "cancel_action",
    )
    @classmethod
    def validate_identifier(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError(
                f"Ungültiger Formularbezeichner: '{value}'.",
            )

        return value

    @model_validator(mode="after")
    def validate_unique_fields(
        self,
    ) -> UIFormDefinition:
        field_names = [field_definition.name for field_definition in self.fields]

        if len(field_names) != len(set(field_names)):
            raise ValueError(
                f"Formular '{self.id}' enthält doppelte Feldnamen.",
            )

        return self


class NodeTypeDefinition(BaseModel):
    """
    Beschreibung eines generischen Hierarchieknotentyps.

    Diese Definition enthält keine fachlich fest verdrahtete
    React-Komponente. Knoten werden durch den generischen rekursiven Baum
    dargestellt.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    label: str = Field(
        min_length=1,
        max_length=255,
    )

    plural_label: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    icon: str | None = Field(
        default=None,
        max_length=255,
    )

    color: str | None = Field(
        default=None,
        max_length=100,
    )

    allowed_child_types: tuple[str, ...] = ()

    allowed_actions: tuple[str, ...] = ()

    create_form: str | None = Field(
        default=None,
        max_length=150,
    )

    edit_form: str | None = Field(
        default=None,
        max_length=150,
    )

    selectable: bool = True
    draggable: bool = False
    droppable: bool = False
    expandable: bool = True

    visibility: UIVisibility = UIVisibility.AUTHENTICATED

    required_permissions: tuple[str, ...] = ()

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator(
        "create_form",
        "edit_form",
    )
    @classmethod
    def validate_optional_identifier(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError(
                f"Ungültiger Formularbezeichner: '{value}'.",
            )

        return value

    @field_validator(
        "allowed_child_types",
        "allowed_actions",
    )
    @classmethod
    def validate_identifier_collection(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        normalized: list[str] = []

        for value in values:
            if not IDENTIFIER_PATTERN.fullmatch(value):
                raise ValueError(
                    f"Ungültiger UI-Bezeichner: '{value}'.",
                )

            normalized.append(value)

        if len(normalized) != len(set(normalized)):
            raise ValueError(
                "Doppelte Bezeichner sind nicht erlaubt.",
            )

        return tuple(normalized)


class UISchemaFeatureFlags(BaseModel):
    """
    Optionale, bekannte Feature-Schalter.

    Unbekannte Features werden durch `extra='forbid'` abgelehnt.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    chat_streaming: bool = True
    hierarchy_drag_and_drop: bool = False
    dynamic_forms: bool = True
    tool_execution: bool = False
    model_selection: bool = True
    admin_configuration: bool = False


class UISchema(BaseModel):
    """
    Öffentlicher, versionierter Vertrag zwischen Backend und Frontend.

    Das Schema enthält ausschließlich deklarative Daten. Es darf keine
    ausführbaren Funktionen, Importpfade oder beliebigen JavaScript-Code
    enthalten.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    schema_name: Literal["app-ui"] = UI_SCHEMA_NAME

    schema_version: str = Field(
        default=UI_SCHEMA_VERSION,
        min_length=1,
        max_length=50,
    )

    minimum_client_version: str = Field(
        default=MINIMUM_CLIENT_VERSION,
        min_length=1,
        max_length=50,
    )

    revision: int = Field(
        default=0,
        ge=0,
    )

    components: dict[str, UIComponentDefinition] = Field(
        default_factory=dict,
    )

    actions: dict[str, UIActionDefinition] = Field(
        default_factory=dict,
    )

    node_types: dict[str, NodeTypeDefinition] = Field(
        default_factory=dict,
    )

    forms: dict[str, UIFormDefinition] = Field(
        default_factory=dict,
    )

    feature_flags: UISchemaFeatureFlags = Field(
        default_factory=UISchemaFeatureFlags,
    )

    root_component: str | None = Field(
        default=None,
        max_length=150,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator(
        "components",
        "actions",
        "node_types",
        "forms",
    )
    @classmethod
    def validate_registry_keys(
        cls,
        registry: dict[str, Any],
    ) -> dict[str, Any]:
        for key in registry:
            if not IDENTIFIER_PATTERN.fullmatch(key):
                raise ValueError(
                    f"Ungültiger Registry-Schlüssel: '{key}'.",
                )

        return registry

    @field_validator("root_component")
    @classmethod
    def validate_root_component_identifier(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError(
                f"Ungültige Root-Komponenten-ID: '{value}'.",
            )

        return value

    @model_validator(mode="after")
    def validate_schema_references(
        self,
    ) -> UISchema:
        self._validate_component_registry()
        self._validate_action_registry()
        self._validate_form_registry()
        self._validate_node_types()
        self._validate_root_component()

        return self

    def _validate_component_registry(
        self,
    ) -> None:
        for registry_key, definition in self.components.items():
            if registry_key != definition.id:
                raise ValueError(
                    "Der Komponenten-Registry-Schlüssel "
                    f"'{registry_key}' stimmt nicht mit der Komponenten-ID "
                    f"'{definition.id}' überein.",
                )

    def _validate_action_registry(
        self,
    ) -> None:
        for registry_key, definition in self.actions.items():
            if registry_key != definition.id:
                raise ValueError(
                    "Der Action-Registry-Schlüssel "
                    f"'{registry_key}' stimmt nicht mit der Action-ID "
                    f"'{definition.id}' überein.",
                )

    def _validate_form_registry(
        self,
    ) -> None:
        action_ids = set(self.actions)

        for registry_key, definition in self.forms.items():
            if registry_key != definition.id:
                raise ValueError(
                    "Der Formular-Registry-Schlüssel "
                    f"'{registry_key}' stimmt nicht mit der Formular-ID "
                    f"'{definition.id}' überein.",
                )

            if (
                definition.submit_action is not None
                and definition.submit_action not in action_ids
            ):
                raise ValueError(
                    f"Formular '{definition.id}' verweist auf die "
                    f"unbekannte Submit-Aktion "
                    f"'{definition.submit_action}'.",
                )

            if (
                definition.cancel_action is not None
                and definition.cancel_action not in action_ids
            ):
                raise ValueError(
                    f"Formular '{definition.id}' verweist auf die "
                    f"unbekannte Cancel-Aktion "
                    f"'{definition.cancel_action}'.",
                )

    def _validate_node_types(
        self,
    ) -> None:
        node_type_ids = set(self.node_types)
        action_ids = set(self.actions)
        form_ids = set(self.forms)

        for node_type_id, definition in self.node_types.items():
            unknown_children = (
                set(
                    definition.allowed_child_types,
                )
                - node_type_ids
            )

            if unknown_children:
                raise ValueError(
                    f"Knotentyp '{node_type_id}' verweist auf unbekannte "
                    "Kindtypen: "
                    f"{', '.join(sorted(unknown_children))}.",
                )

            unknown_actions = (
                set(
                    definition.allowed_actions,
                )
                - action_ids
            )

            if unknown_actions:
                raise ValueError(
                    f"Knotentyp '{node_type_id}' verweist auf unbekannte "
                    "Aktionen: "
                    f"{', '.join(sorted(unknown_actions))}.",
                )

            if (
                definition.create_form is not None
                and definition.create_form not in form_ids
            ):
                raise ValueError(
                    f"Knotentyp '{node_type_id}' verweist auf das "
                    f"unbekannte Erstellungsformular "
                    f"'{definition.create_form}'.",
                )

            if (
                definition.edit_form is not None
                and definition.edit_form not in form_ids
            ):
                raise ValueError(
                    f"Knotentyp '{node_type_id}' verweist auf das "
                    f"unbekannte Bearbeitungsformular "
                    f"'{definition.edit_form}'.",
                )

    def _validate_root_component(
        self,
    ) -> None:
        if self.root_component is None:
            return

        if self.root_component not in self.components:
            raise ValueError(
                f"Die Root-Komponente '{self.root_component}' ist nicht "
                "in der Komponenten-Registry vorhanden.",
            )

    def public_component_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(sorted(self.components))

    def public_action_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(sorted(self.actions))

    def public_form_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(sorted(self.forms))

    def public_node_type_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(sorted(self.node_types))
