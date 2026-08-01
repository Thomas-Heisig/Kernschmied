from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import (
    SchemaError,
)
from jsonschema.exceptions import (
    ValidationError as JsonSchemaValidationError,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class JsonSchemaValidatorProtocol(Protocol):
    def validate(
        self,
        instance: object,
    ) -> None: ...


class ConfigScope(StrEnum):
    """
    Unterstützte fachliche Konfigurations-Ebenen.

    Die Enum-Reihenfolge definiert ausdrücklich keine Priorität.
    Die Prioritätsreihenfolge wird zentral im ConfigResolver festgelegt.
    """

    SYSTEM = "system"
    NODE = "node"
    PROJECT = "project"
    CHAT = "chat"
    USER = "user"
    REQUEST = "request"


class ConfigMergeStrategy(StrEnum):
    """
    Unterstützte Strategien zur Zusammenführung mehrerer Scope-Werte.
    """

    REPLACE = "replace"
    EXTEND = "extend"
    DEEP_MERGE = "deep_merge"


class ConfigValueType(StrEnum):
    """
    Grobe fachliche Typisierung für generische Administrationsoberflächen.

    Das JSON-Schema bleibt die maßgebliche Validierungsquelle.
    """

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"


class ConfigUIComponent(StrEnum):
    """
    Bekannte generische UI-Komponenten.

    Das Frontend darf ausschließlich Komponenten aus seiner festen
    Komponenten-Registry rendern. Unbekannte Werte werden sichtbar als
    nicht unterstützt dargestellt und niemals dynamisch importiert.
    """

    TEXT = "text"
    TEXTAREA = "textarea"
    PASSWORD = "password"
    NUMBER = "number"
    CHECKBOX = "checkbox"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    TAGS = "tags"
    JSON = "json"
    URL = "url"
    MODEL_SELECT = "model_select"
    TOOL_SELECT = "tool_select"
    NODE_SELECT = "node_select"
    HIDDEN = "hidden"


class ConfigVisibility(StrEnum):
    """
    Sichtbarkeit einer Definition in administrativen Oberflächen.
    """

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"
    INTERNAL = "internal"


class ConfigValueSource(StrEnum):
    """
    Optionale Quelle dynamischer Auswahlwerte.

    Das Frontend kennt nur diese festen Quellentypen. Die tatsächlichen
    Daten werden über definierte API-Endpunkte geladen.
    """

    STATIC = "static"
    MODELS = "models"
    TOOLS = "tools"
    HIERARCHY_NODES = "hierarchy_nodes"
    USERS = "users"
    API = "api"


class ConfigOption(BaseModel):
    """
    Statische Auswahloption für Select-Komponenten.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    value: str | int | float | bool
    label: str = Field(min_length=1, max_length=255)
    description: str | None = Field(
        default=None,
        max_length=1000,
    )
    disabled: bool = False


class ConfigDynamicOptions(BaseModel):
    """
    Definition einer dynamischen Optionsquelle.

    `endpoint` darf nur auf bekannte, kontrollierte interne API-Endpunkte
    zeigen. Beliebige externe URLs sind nicht vorgesehen.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    source: ConfigValueSource

    endpoint: str | None = Field(
        default=None,
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

    filters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_endpoint(self) -> ConfigDynamicOptions:
        if self.source == ConfigValueSource.API:
            if not self.endpoint:
                raise ValueError(
                    "Für eine API-Optionsquelle ist ein Endpoint erforderlich.",
                )

            if not self.endpoint.startswith("/api/"):
                raise ValueError(
                    "Dynamische Config-Endpunkte müssen mit '/api/' beginnen.",
                )

        return self


class ConfigUIMetadata(BaseModel):
    """
    Präsentationsmetadaten für ein generisches Admin-Frontend.

    Diese Daten steuern ausschließlich Darstellung und Eingabehilfen.
    Sie ersetzen niemals serverseitige Validierung oder Autorisierung.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    component: ConfigUIComponent | None = None

    category: str | None = Field(
        default=None,
        max_length=100,
    )

    section: str | None = Field(
        default=None,
        max_length=100,
    )

    order: int = Field(
        default=0,
        ge=-100_000,
        le=100_000,
    )

    placeholder: str | None = Field(
        default=None,
        max_length=500,
    )

    help_text: str | None = Field(
        default=None,
        max_length=2000,
    )

    unit: str | None = Field(
        default=None,
        max_length=50,
    )

    advanced: bool = False
    hidden: bool = False
    readonly: bool = False

    options: tuple[ConfigOption, ...] = ()

    dynamic_options: ConfigDynamicOptions | None = None

    @model_validator(mode="after")
    def validate_option_source(self) -> ConfigUIMetadata:
        if self.options and self.dynamic_options is not None:
            raise ValueError(
                "Statische und dynamische Optionen dürfen nicht gleichzeitig "
                "definiert werden.",
            )

        return self


class ConfigPermissions(BaseModel):
    """
    Berechtigungen für Lesen und Ändern einer Konfiguration.

    Die API muss diese Berechtigungen serverseitig prüfen.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    read: str = Field(
        default="config:read",
        min_length=1,
        max_length=255,
    )

    write: str = Field(
        default="config:write",
        min_length=1,
        max_length=255,
    )

    reveal_secret: str = Field(
        default="config:secret:read",
        min_length=1,
        max_length=255,
    )


class ConfigDefinition(BaseModel):
    """
    Vollständiger, versionierter Vertrag einer Fachkonfiguration.

    Die Definition beschreibt:

    - Identität und Version
    - erlaubte Geltungsbereiche
    - Validierung
    - Merge-Verhalten
    - Laufzeitverhalten
    - Berechtigungen
    - generische UI-Darstellung
    - Sicherheits- und Audit-Eigenschaften
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=False,
    )

    group: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )

    key: str = Field(
        min_length=1,
        max_length=150,
        pattern=r"^[a-z][a-z0-9_]*$",
    )

    schema_version: str = Field(
        default="1.0",
        min_length=1,
        max_length=50,
    )

    display_name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        default="",
        max_length=4000,
    )

    value_schema: dict[str, Any]

    default_value: Any

    allowed_scopes: frozenset[ConfigScope] = Field(
        min_length=1,
    )

    merge_strategy: ConfigMergeStrategy = ConfigMergeStrategy.REPLACE

    value_type: ConfigValueType | None = None

    is_secret: bool = False
    requires_restart: bool = False
    runtime_editable: bool = True

    request_override_allowed: bool = False

    nullable: bool = False

    visibility: ConfigVisibility = ConfigVisibility.ADMIN

    permissions: ConfigPermissions = Field(
        default_factory=ConfigPermissions,
    )

    ui: ConfigUIMetadata = Field(
        default_factory=ConfigUIMetadata,
    )

    tags: frozenset[str] = Field(default_factory=frozenset)

    deprecated: bool = False

    deprecation_message: str | None = Field(
        default=None,
        max_length=2000,
    )

    replaced_by: str | None = Field(
        default=None,
        max_length=255,
        pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$",
    )

    audit_enabled: bool = True

    @property
    def full_key(self) -> str:
        return f"{self.group}.{self.key}"

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(
        cls,
        value: Any,
    ) -> frozenset[str]:
        if value is None:
            return frozenset()

        if isinstance(value, str):
            raw_values = [value]
        else:
            raw_values = value

        tags: set[str] = set()

        for item in raw_values:
            tag = str(item).strip().lower()

            if tag:
                tags.add(tag)

        return frozenset(tags)

    @model_validator(mode="after")
    def validate_definition(self) -> ConfigDefinition:
        self._validate_json_schema()
        self._validate_default_value()
        self._validate_merge_strategy()
        self._validate_scope_rules()
        self._validate_runtime_rules()
        self._validate_secret_rules()
        self._validate_deprecation_rules()

        return self

    def _validate_json_schema(self) -> None:
        try:
            Draft202012Validator.check_schema(
                self.value_schema,
            )
        except SchemaError as exc:
            raise ValueError(
                f"Ungültiges JSON-Schema für '{self.full_key}': {exc.message}",
            ) from exc

    def _validate_default_value(self) -> None:
        raw_validator: object = Draft202012Validator(
            self.value_schema,
        )

        validator = cast(
            JsonSchemaValidatorProtocol,
            raw_validator,
        )

        try:
            validator.validate(
                self.default_value,
            )

        except JsonSchemaValidationError as exc:
            path = ".".join(str(part) for part in exc.absolute_path)

            location = path or "<root>"

            raise ValueError(
                f"Der Standardwert für '{self.full_key}' ist ungültig "
                f"an '{location}': {exc.message}",
            ) from exc

    def _validate_merge_strategy(self) -> None:
        schema_type = self.value_schema.get("type")

        if self.merge_strategy == ConfigMergeStrategy.EXTEND:
            valid_array_schema = schema_type == "array" or (
                isinstance(schema_type, list) and "array" in schema_type
            )

            if not valid_array_schema:
                raise ValueError(
                    f"Die Merge-Strategie 'extend' ist für "
                    f"'{self.full_key}' nur bei Arrays erlaubt.",
                )

        if self.merge_strategy == ConfigMergeStrategy.DEEP_MERGE:
            valid_object_schema = schema_type == "object" or (
                isinstance(schema_type, list) and "object" in schema_type
            )

            if not valid_object_schema:
                raise ValueError(
                    f"Die Merge-Strategie 'deep_merge' ist für "
                    f"'{self.full_key}' nur bei Objekten erlaubt.",
                )

    def _validate_scope_rules(self) -> None:
        if ConfigScope.REQUEST in self.allowed_scopes:
            if not self.request_override_allowed:
                raise ValueError(
                    f"'{self.full_key}' erlaubt den REQUEST-Scope, "
                    "aber request_override_allowed ist nicht aktiviert.",
                )

        if self.request_override_allowed:
            if ConfigScope.REQUEST not in self.allowed_scopes:
                raise ValueError(
                    f"'{self.full_key}' erlaubt Request-Overrides, "
                    "aber der REQUEST-Scope fehlt.",
                )

        if self.is_secret and ConfigScope.REQUEST in self.allowed_scopes:
            raise ValueError(
                f"Secret-Konfigurationen dürfen nicht im REQUEST-Scope "
                f"überschrieben werden: '{self.full_key}'.",
            )

    def _validate_runtime_rules(self) -> None:
        if self.requires_restart and self.runtime_editable:
            raise ValueError(
                f"'{self.full_key}' kann nicht gleichzeitig "
                "requires_restart=True und runtime_editable=True sein.",
            )

        if self.request_override_allowed and not self.runtime_editable:
            raise ValueError(
                f"Request-Overrides sind für die nicht laufzeitänderbare "
                f"Konfiguration '{self.full_key}' nicht erlaubt.",
            )

    def _validate_secret_rules(self) -> None:
        if not self.is_secret:
            return

        if self.ui.component not in {
            None,
            ConfigUIComponent.PASSWORD,
            ConfigUIComponent.HIDDEN,
        }:
            raise ValueError(
                f"Secret-Konfiguration '{self.full_key}' muss die "
                "UI-Komponente 'password' oder 'hidden' verwenden.",
            )

    def _validate_deprecation_rules(self) -> None:
        if self.deprecated and not self.deprecation_message:
            raise ValueError(
                f"Für die veraltete Konfiguration '{self.full_key}' "
                "ist eine deprecation_message erforderlich.",
            )

        if not self.deprecated and self.replaced_by is not None:
            raise ValueError(
                f"'{self.full_key}' besitzt replaced_by, ist aber nicht "
                "als deprecated markiert.",
            )


def config_definition(
    *,
    group: str,
    key: str,
    display_name: str,
    value_schema: dict[str, Any],
    default_value: Any,
    allowed_scopes: set[ConfigScope] | frozenset[ConfigScope],
    description: str = "",
    schema_version: str = "1.0",
    merge_strategy: ConfigMergeStrategy = ConfigMergeStrategy.REPLACE,
    value_type: ConfigValueType | None = None,
    is_secret: bool = False,
    requires_restart: bool = False,
    runtime_editable: bool = True,
    request_override_allowed: bool = False,
    nullable: bool = False,
    visibility: ConfigVisibility = ConfigVisibility.ADMIN,
    permissions: ConfigPermissions | None = None,
    ui: ConfigUIMetadata | None = None,
    tags: set[str] | frozenset[str] | None = None,
    audit_enabled: bool = True,
) -> ConfigDefinition:
    """
    Kleine Factory zur lesbaren Definition umfangreicher Konfigurationen.
    """

    return ConfigDefinition(
        group=group,
        key=key,
        schema_version=schema_version,
        display_name=display_name,
        description=description,
        value_schema=value_schema,
        default_value=default_value,
        allowed_scopes=frozenset(allowed_scopes),
        merge_strategy=merge_strategy,
        value_type=value_type,
        is_secret=is_secret,
        requires_restart=requires_restart,
        runtime_editable=runtime_editable,
        request_override_allowed=request_override_allowed,
        nullable=nullable,
        visibility=visibility,
        permissions=permissions or ConfigPermissions(),
        ui=ui or ConfigUIMetadata(),
        tags=frozenset(tags or set()),
        audit_enabled=audit_enabled,
    )


CONFIG_DEFINITIONS: tuple[ConfigDefinition, ...] = (
    # ============================================================
    # Allgemein
    # ============================================================
    config_definition(
        group="general",
        key="instance_name",
        display_name="Instanzname",
        description=("Anzeigename dieser Kernschmied-Installation."),
        value_schema={
            "type": "string",
            "minLength": 1,
            "maxLength": 120,
        },
        default_value="Kernschmied",
        allowed_scopes={
            ConfigScope.SYSTEM,
        },
        value_type=ConfigValueType.STRING,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.TEXT,
            category="Allgemein",
            section="Instanz",
            order=10,
            placeholder="Kernschmied",
        ),
        tags={
            "general",
            "instance",
        },
    ),
    config_definition(
        group="general",
        key="default_language",
        display_name="Standardsprache",
        description=("Standardsprache der Anwendung und generierter Inhalte."),
        value_schema={
            "type": "string",
            "enum": [
                "de",
                "en",
            ],
        },
        default_value="de",
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.SELECT,
            category="Allgemein",
            section="Sprache",
            order=20,
            options=(
                ConfigOption(
                    value="de",
                    label="Deutsch",
                ),
                ConfigOption(
                    value="en",
                    label="Englisch",
                ),
            ),
        ),
        tags={
            "general",
            "language",
        },
    ),
    
        # ============================================================
    # Identität und Verhalten
    # ============================================================
    config_definition(
        group="identity",
        key="name",
        display_name="Name",
        description="Anzeigename der KI-Arbeitskraft.",
        value_schema={
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
        },
        default_value="Kernschmied",
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.TEXT,
            category="Identität und Verhalten",
            section="Identität",
            order=10,
            placeholder="Kernschmied",
        ),
        tags={
            "identity",
            "name",
        },
    ),
    config_definition(
        group="identity",
        key="role_description",
        display_name="Rollenbeschreibung",
        description=(
            "Beschreibt die grundsätzliche Rolle von Kernschmied "
            "innerhalb der Organisation."
        ),
        value_schema={
            "type": "string",
            "minLength": 1,
            "maxLength": 2000,
        },
        default_value=(
            "Kernschmied ist eine allgemeine KI-Arbeitskraft und ein "
            "digitaler Mitarbeiter. Er erkennt Aufgaben, plant geeignete "
            "Arbeitsschritte, verwendet freigegebene Werkzeuge und erzeugt "
            "strukturierte, veränderbare Arbeitsergebnisse."
        ),
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.TEXTAREA,
            category="Identität und Verhalten",
            section="Identität",
            order=20,
        ),
        tags={
            "identity",
            "role",
        },
    ),
    config_definition(
        group="identity",
        key="mission",
        display_name="Grundauftrag",
        description=(
            "Übergeordneter Auftrag, an dem sich Kernschmied "
            "bei allen Aufgaben orientiert."
        ),
        value_schema={
            "type": "string",
            "minLength": 1,
            "maxLength": 10000,
        },
        default_value=(
            "Bearbeite freigegebene Aufgaben sorgfältig, nachvollziehbar "
            "und möglichst selbstständig. Erkenne das Ziel einer Anfrage, "
            "bestimme die erforderlichen Informationen, plane geeignete "
            "Arbeitsschritte und nutze freigegebene Modelle, Werkzeuge und "
            "Wissensquellen. Erzeuge Ergebnisse strukturiert, versionierbar "
            "und veränderbar. Beachte stets Berechtigungen, "
            "Bestätigungspflichten, Sicherheitsgrenzen und versionierte "
            "Systemverträge."
        ),
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.TEXTAREA,
            category="Identität und Verhalten",
            section="Identität",
            order=30,
            help_text=(
                "Der Grundauftrag beeinflusst das allgemeine Verhalten "
                "von Kernschmied und sollte nur bewusst geändert werden."
            ),
        ),
        tags={
            "identity",
            "mission",
            "behavior",
        },
    ),
    config_definition(
        group="identity",
        key="organization_description",
        display_name="Organisationsbeschreibung",
        description=(
            "Beschreibung des Unternehmens oder der Organisation, "
            "für die Kernschmied arbeitet."
        ),
        value_schema={
            "type": "string",
            "minLength": 0,
            "maxLength": 5000,
        },
        default_value=(
            "Heisig Naturstein ist ein Steinmetz- und "
            "Steinbildhauer-Meisterbetrieb. Das Unternehmen bearbeitet "
            "unter anderem Naturstein, Treppenanlagen, Bodenbeläge, "
            "Denkmalpflege, Restaurierung, Grabmale sowie kaufmännische "
            "und organisatorische Aufgaben."
        ),
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.TEXTAREA,
            category="Identität und Verhalten",
            section="Identität",
            order=40,
        ),
        tags={
            "identity",
            "organization",
        },
    ),
    config_definition(
        group="identity",
        key="default_language",
        display_name="Standardsprache",
        description=(
            "Bevorzugte Sprache für Antworten und erzeugte "
            "Arbeitsergebnisse."
        ),
        value_schema={
            "type": "string",
            "enum": [
                "de",
                "en",
            ],
        },
        default_value="de",
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.SELECT,
            category="Identität und Verhalten",
            section="Identität",
            order=50,
            options=(
                ConfigOption(
                    value="de",
                    label="Deutsch",
                ),
                ConfigOption(
                    value="en",
                    label="Englisch",
                ),
            ),
        ),
        tags={
            "identity",
            "language",
        },
    ),
    config_definition(
        group="identity",
        key="timezone",
        display_name="Zeitzone",
        description=(
            "IANA-Zeitzone für Termine, Fristen und "
            "zeitabhängige Aufgaben."
        ),
        value_schema={
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
        },
        default_value="Europe/Berlin",
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.TEXT,
            category="Identität und Verhalten",
            section="Identität",
            order=60,
            placeholder="Europe/Berlin",
            help_text=(
                "Die Zeitzone muss als gültiger IANA-Bezeichner "
                "angegeben werden."
            ),
        ),
        tags={
            "identity",
            "timezone",
        },
    ),
    config_definition(
        group="identity",
        key="behavior_principles",
        display_name="Allgemeine Verhaltensgrundsätze",
        description=(
            "Grundlegende Regeln für sorgfältiges, nachvollziehbares "
            "und sicheres Arbeiten."
        ),
        value_schema={
            "type": "string",
            "minLength": 1,
            "maxLength": 10000,
        },
        default_value=(
            "Arbeite sorgfältig, transparent, nachvollziehbar und "
            "lösungsorientiert. Prüfe Informationen und Ergebnisse auf "
            "Plausibilität, Vollständigkeit und Konsistenz. Kennzeichne "
            "Unsicherheiten und erfinde keine Tatsachen. Nutze nur "
            "freigegebene Modelle, Werkzeuge und Datenquellen. Führe "
            "wirkungsstarke, externe, schreibende oder löschende Aktionen "
            "nur innerhalb der geltenden Berechtigungen und "
            "Bestätigungspflichten aus. Verändere keine unveränderlichen "
            "Sicherheitsgrenzen, Berechtigungen oder produktiven Verträge "
            "eigenständig."
        ),
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.TEXTAREA,
            category="Identität und Verhalten",
            section="Identität",
            order=70,
            help_text=(
                "Diese Regeln ergänzen die festen Sicherheitsgrenzen, "
                "können diese aber niemals abschwächen."
            ),
        ),
        tags={
            "identity",
            "behavior",
            "governance",
        },
    ),

    # ============================================================
    # Uploads
    # ============================================================
    config_definition(
        group="uploads",
        key="max_size_mb",
        display_name="Maximale Uploadgröße",
        description=("Maximale Größe einer einzelnen hochgeladenen Datei."),
        value_schema={
            "type": "integer",
            "minimum": 1,
            "maximum": 500,
        },
        default_value=10,
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.INTEGER,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.NUMBER,
            category="Uploads",
            section="Grenzwerte",
            order=10,
            unit="MB",
            help_text=(
                "Die technische Servergrenze darf hierdurch nicht überschritten werden."
            ),
        ),
        tags={
            "uploads",
            "limits",
        },
    ),
    config_definition(
        group="uploads",
        key="allowed_types",
        display_name="Erlaubte Dateitypen",
        description=("Liste der erlaubten MIME-Typen für Datei-Uploads."),
        value_schema={
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 255,
            },
            "uniqueItems": True,
            "minItems": 1,
            "maxItems": 100,
        },
        default_value=[
            "image/jpeg",
            "image/png",
            "application/pdf",
            "text/plain",
        ],
        allowed_scopes={
            ConfigScope.SYSTEM,
        },
        merge_strategy=ConfigMergeStrategy.REPLACE,
        value_type=ConfigValueType.ARRAY,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.TAGS,
            category="Uploads",
            section="Dateitypen",
            order=20,
            placeholder="application/pdf",
        ),
        tags={
            "uploads",
            "mime",
            "security",
        },
    ),
    # ============================================================
    # Modelle
    # ============================================================
    config_definition(
        group="models",
        key="default_model",
        display_name="Standardmodell",
        description=(
            "Standardmäßig ausgewähltes Modell, sofern kein höher "
            "priorisierter Scope ein anderes Modell festlegt."
        ),
        value_schema={
            "type": "string",
            "minLength": 1,
            "maxLength": 255,
        },
        default_value="ollama-qwen2.5-coder-7b",
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.NODE,
            ConfigScope.PROJECT,
            ConfigScope.CHAT,
            ConfigScope.USER,
            ConfigScope.REQUEST,
        },
        request_override_allowed=True,
        value_type=ConfigValueType.STRING,
        permissions=ConfigPermissions(
            read="models:read",
            write="models:configure",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.MODEL_SELECT,
            category="Modelle",
            section="Standardauswahl",
            order=10,
            dynamic_options=ConfigDynamicOptions(
                source=ConfigValueSource.MODELS,
                endpoint="/api/v1/models",
                value_field="id",
                label_field="name",
                description_field="description",
                filters={
                    "include_disabled": False,
                },
            ),
        ),
        tags={
            "models",
            "defaults",
        },
    ),
    config_definition(
        group="models",
        key="temperature",
        display_name="Temperatur",
        description=("Steuert die Zufälligkeit der Modellausgabe."),
        value_schema={
            "type": "number",
            "minimum": 0,
            "maximum": 2,
        },
        default_value=0.2,
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.NODE,
            ConfigScope.PROJECT,
            ConfigScope.CHAT,
            ConfigScope.USER,
            ConfigScope.REQUEST,
        },
        request_override_allowed=True,
        value_type=ConfigValueType.NUMBER,
        permissions=ConfigPermissions(
            read="models:read",
            write="models:configure",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.NUMBER,
            category="Modelle",
            section="Generierung",
            order=20,
            help_text=(
                "Niedrige Werte liefern stabilere, hohe Werte kreativere Antworten."
            ),
        ),
        tags={
            "models",
            "generation",
        },
    ),
    config_definition(
        group="models",
        key="max_output_tokens",
        display_name="Maximale Ausgabetokens",
        description=("Maximale Anzahl erzeugter Tokens pro Modellantwort."),
        value_schema={
            "type": "integer",
            "minimum": 1,
            "maximum": 131072,
        },
        default_value=4096,
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.NODE,
            ConfigScope.PROJECT,
            ConfigScope.CHAT,
            ConfigScope.USER,
            ConfigScope.REQUEST,
        },
        request_override_allowed=True,
        value_type=ConfigValueType.INTEGER,
        permissions=ConfigPermissions(
            read="models:read",
            write="models:configure",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.NUMBER,
            category="Modelle",
            section="Generierung",
            order=30,
            unit="Tokens",
        ),
        tags={
            "models",
            "limits",
        },
    ),
    config_definition(
        group="models",
        key="ollama_host",
        display_name="Ollama-Endpunkt",
        description=("Lokale Basis-URL der Ollama-Installation."),
        value_schema={
            "type": "string",
            "format": "uri",
            "minLength": 1,
            "maxLength": 500,
        },
        default_value="http://127.0.0.1:11434",
        allowed_scopes={
            ConfigScope.SYSTEM,
        },
        value_type=ConfigValueType.STRING,
        requires_restart=True,
        runtime_editable=False,
        permissions=ConfigPermissions(
            read="models:read",
            write="models:admin",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.URL,
            category="Modelle",
            section="Provider",
            order=100,
            advanced=True,
            placeholder="http://127.0.0.1:11434",
        ),
        tags={
            "models",
            "ollama",
            "infrastructure",
        },
    ),
    # ============================================================
    # Tools
    # ============================================================
    config_definition(
        group="tools",
        key="enabled",
        display_name="Tools aktivieren",
        description=("Erlaubt grundsätzlich die Nutzung freigegebener Tools."),
        value_schema={
            "type": "boolean",
        },
        default_value=True,
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.NODE,
            ConfigScope.PROJECT,
            ConfigScope.CHAT,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.BOOLEAN,
        permissions=ConfigPermissions(
            read="tools:read",
            write="tools:configure",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Tools",
            section="Allgemein",
            order=10,
        ),
        tags={
            "tools",
            "feature",
        },
    ),
    config_definition(
        group="tools",
        key="allowed_tool_ids",
        display_name="Freigegebene Tools",
        description=(
            "Liste der für den jeweiligen Scope fachlich freigegebenen Tool-IDs."
        ),
        value_schema={
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 255,
            },
            "uniqueItems": True,
            "maxItems": 500,
        },
        default_value=[],
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.NODE,
            ConfigScope.PROJECT,
            ConfigScope.CHAT,
            ConfigScope.USER,
        },
        merge_strategy=ConfigMergeStrategy.REPLACE,
        value_type=ConfigValueType.ARRAY,
        permissions=ConfigPermissions(
            read="tools:read",
            write="tools:configure",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.TOOL_SELECT,
            category="Tools",
            section="Freigaben",
            order=20,
            dynamic_options=ConfigDynamicOptions(
                source=ConfigValueSource.TOOLS,
                endpoint="/api/v1/tools",
                value_field="id",
                label_field="name",
                description_field="description",
                filters={
                    "include_disabled": False,
                    "include_unavailable": False,
                },
            ),
        ),
        tags={
            "tools",
            "allowlist",
            "security",
        },
    ),
    config_definition(
        group="tools",
        key="confirmation_required",
        display_name="Tool-Bestätigung erforderlich",
        description=(
            "Verlangt eine Benutzerbestätigung vor potenziell "
            "verändernden Tool-Aufrufen."
        ),
        value_schema={
            "type": "boolean",
        },
        default_value=True,
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.NODE,
            ConfigScope.PROJECT,
        },
        value_type=ConfigValueType.BOOLEAN,
        permissions=ConfigPermissions(
            read="tools:read",
            write="tools:admin",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Tools",
            section="Sicherheit",
            order=30,
        ),
        tags={
            "tools",
            "confirmation",
            "security",
        },
    ),
    # ============================================================
    # Chat
    # ============================================================
    config_definition(
        group="chat",
        key="streaming_enabled",
        display_name="Streaming aktivieren",
        description=("Aktiviert SSE-Streaming für Chat-Antworten."),
        value_schema={
            "type": "boolean",
        },
        default_value=True,
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.BOOLEAN,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Chat",
            section="Ausgabe",
            order=10,
        ),
        tags={
            "chat",
            "streaming",
        },
    ),
    config_definition(
        group="chat",
        key="max_history_messages",
        display_name="Maximale Verlaufsnachrichten",
        description=(
            "Maximale Zahl älterer Nachrichten, die bei einer "
            "Modellanfrage berücksichtigt werden."
        ),
        value_schema={
            "type": "integer",
            "minimum": 0,
            "maximum": 1000,
        },
        default_value=50,
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.NODE,
            ConfigScope.PROJECT,
            ConfigScope.CHAT,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.INTEGER,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.NUMBER,
            category="Chat",
            section="Kontext",
            order=20,
            unit="Nachrichten",
        ),
        tags={
            "chat",
            "history",
            "limits",
        },
    ),
    # ============================================================
    # Prompt-Vererbung
    # ============================================================
    config_definition(
        group="prompts",
        key="level_order",
        display_name="Prompt-Ebenen",
        description=(
            "Reihenfolge der fachlichen Prompt-Vererbung von niedriger "
            "zu hoher Priorität."
        ),
        value_schema={
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "system",
                    "node",
                    "project",
                    "chat",
                    "user",
                    "request",
                ],
            },
            "minItems": 1,
            "uniqueItems": True,
        },
        default_value=[
            "system",
            "node",
            "project",
            "chat",
            "user",
            "request",
        ],
        allowed_scopes={
            ConfigScope.SYSTEM,
        },
        value_type=ConfigValueType.ARRAY,
        permissions=ConfigPermissions(
            read="prompts:read",
            write="prompts:admin",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.MULTI_SELECT,
            category="Prompts",
            section="Vererbung",
            order=10,
            advanced=True,
            options=(
                ConfigOption(
                    value="system",
                    label="System",
                ),
                ConfigOption(
                    value="node",
                    label="Hierarchieknoten",
                ),
                ConfigOption(
                    value="project",
                    label="Projekt",
                ),
                ConfigOption(
                    value="chat",
                    label="Chat",
                ),
                ConfigOption(
                    value="user",
                    label="Benutzer",
                ),
                ConfigOption(
                    value="request",
                    label="Anfrage",
                ),
            ),
        ),
        tags={
            "prompts",
            "inheritance",
        },
    ),
    # ============================================================
    # UI
    # ============================================================
    config_definition(
        group="ui",
        key="theme",
        display_name="Darstellung",
        description=("Bevorzugte Darstellung des Frontends."),
        value_schema={
            "type": "string",
            "enum": [
                "system",
                "light",
                "dark",
            ],
        },
        default_value="system",
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.SELECT,
            category="Oberfläche",
            section="Darstellung",
            order=10,
            options=(
                ConfigOption(
                    value="system",
                    label="Systemeinstellung",
                ),
                ConfigOption(
                    value="light",
                    label="Hell",
                ),
                ConfigOption(
                    value="dark",
                    label="Dunkel",
                ),
            ),
        ),
        tags={
            "ui",
            "theme",
        },
    ),
    config_definition(
        group="ui",
        key="schema_extensions",
        display_name="UI-Schema-Erweiterungen",
        description=(
            "Validierte zusätzliche UI-Schema-Eigenschaften für bekannte "
            "generische Komponenten."
        ),
        value_schema={
            "type": "object",
            "additionalProperties": True,
        },
        default_value={},
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.NODE,
            ConfigScope.PROJECT,
            ConfigScope.USER,
        },
        merge_strategy=ConfigMergeStrategy.DEEP_MERGE,
        value_type=ConfigValueType.OBJECT,
        permissions=ConfigPermissions(
            read="ui:read",
            write="ui:configure",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.JSON,
            category="Oberfläche",
            section="Schema",
            order=100,
            advanced=True,
        ),
        tags={
            "ui",
            "schema",
            "advanced",
        },
    ),
    # ============================================================
    # Sicherheit
    # ============================================================
    config_definition(
        group="security",
        key="auth_mode",
        display_name="Authentifizierungsmodus",
        description=(
            "Aktiver Authentifizierungsmodus. Das Betriebsprofil kann "
            "strengere Sicherheitsuntergrenzen erzwingen."
        ),
        value_schema={
            "type": "string",
            "enum": [
                "none",
                "api_key",
                "session",
                "oidc",
                "reverse_proxy",
            ],
        },
        default_value="none",
        allowed_scopes={
            ConfigScope.SYSTEM,
        },
        value_type=ConfigValueType.STRING,
        requires_restart=True,
        runtime_editable=False,
        permissions=ConfigPermissions(
            read="security:read",
            write="security:admin",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.SELECT,
            category="Sicherheit",
            section="Authentifizierung",
            order=10,
            advanced=True,
            options=(
                ConfigOption(
                    value="none",
                    label="Keine Authentifizierung",
                    description=("Nur für lokale Entwicklung zulässig."),
                ),
                ConfigOption(
                    value="api_key",
                    label="API-Key",
                ),
                ConfigOption(
                    value="session",
                    label="Session",
                ),
                ConfigOption(
                    value="oidc",
                    label="OpenID Connect",
                ),
                ConfigOption(
                    value="reverse_proxy",
                    label="Vertrauenswürdiger Reverse Proxy",
                ),
            ),
        ),
        tags={
            "security",
            "authentication",
        },
    ),
    config_definition(
        group="security",
        key="session_timeout_minutes",
        display_name="Session-Zeitlimit",
        description=("Maximale Dauer einer inaktiven Sitzung."),
        value_schema={
            "type": "integer",
            "minimum": 5,
            "maximum": 10080,
        },
        default_value=480,
        allowed_scopes={
            ConfigScope.SYSTEM,
        },
        value_type=ConfigValueType.INTEGER,
        permissions=ConfigPermissions(
            read="security:read",
            write="security:admin",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.NUMBER,
            category="Sicherheit",
            section="Session",
            order=20,
            unit="Minuten",
            advanced=True,
        ),
        tags={
            "security",
            "session",
        },
    ),
    config_definition(
        group="security",
        key="rate_limit_per_minute",
        display_name="Anfragen pro Minute",
        description=(
            "Fachliche Rate-Limit-Vorgabe. Das Betriebsprofil kann eine "
            "strengere Untergrenze erzwingen."
        ),
        value_schema={
            "type": "integer",
            "minimum": 1,
            "maximum": 100000,
        },
        default_value=120,
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.INTEGER,
        permissions=ConfigPermissions(
            read="security:read",
            write="security:admin",
        ),
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.NUMBER,
            category="Sicherheit",
            section="Rate Limiting",
            order=30,
            unit="Anfragen/min",
            advanced=True,
        ),
        tags={
            "security",
            "rate_limit",
        },
    ),
)


CONFIG_DEFINITION_MAP: dict[
    tuple[str, str],
    ConfigDefinition,
] = {
    (
        definition.group,
        definition.key,
    ): definition
    for definition in CONFIG_DEFINITIONS
}


CONFIG_DEFINITION_KEY_MAP: dict[
    str,
    ConfigDefinition,
] = {definition.full_key: definition for definition in CONFIG_DEFINITIONS}


def get_config_definition(
    group: str,
    key: str,
) -> ConfigDefinition:
    """
    Liefert eine Konfigurationsdefinition anhand von Gruppe und Schlüssel.
    """

    normalized_group = group.strip()
    normalized_key = key.strip()

    try:
        return CONFIG_DEFINITION_MAP[
            (
                normalized_group,
                normalized_key,
            )
        ]
    except KeyError as exc:
        raise KeyError(
            f"Unbekannte Konfiguration '{normalized_group}.{normalized_key}'.",
        ) from exc


def get_config_definition_by_full_key(
    full_key: str,
) -> ConfigDefinition:
    """
    Liefert eine Definition anhand des vollständigen Schlüssels.
    """

    normalized_key = full_key.strip()

    try:
        return CONFIG_DEFINITION_KEY_MAP[normalized_key]
    except KeyError as exc:
        raise KeyError(
            f"Unbekannte Konfiguration '{normalized_key}'.",
        ) from exc


def list_config_definitions(
    *,
    group: str | None = None,
    scope: ConfigScope | None = None,
    include_internal: bool = False,
    include_deprecated: bool = False,
) -> tuple[ConfigDefinition, ...]:
    """
    Filtert Definitionsdaten für API, Admin-Oberfläche oder Services.
    """

    result: list[ConfigDefinition] = []

    for definition in CONFIG_DEFINITIONS:
        if group is not None and definition.group != group:
            continue

        if scope is not None and scope not in definition.allowed_scopes:
            continue

        if not include_internal and definition.visibility == ConfigVisibility.INTERNAL:
            continue

        if not include_deprecated and definition.deprecated:
            continue

        result.append(definition)

    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.ui.category or "",
                item.ui.section or "",
                item.ui.order,
                item.group,
                item.key,
            ),
        ),
    )


def validate_definition_registry() -> None:
    """
    Prüft globale Konsistenz der Registry beim Import.

    Verhindert doppelte Schlüssel und ungültige replaced_by-Verweise.
    """

    seen_keys: set[str] = set()

    for definition in CONFIG_DEFINITIONS:
        if definition.full_key in seen_keys:
            raise RuntimeError(
                f"Doppelte Konfigurationsdefinition: '{definition.full_key}'.",
            )

        seen_keys.add(
            definition.full_key,
        )

    for definition in CONFIG_DEFINITIONS:
        if (
            definition.replaced_by is not None
            and definition.replaced_by not in seen_keys
        ):
            raise RuntimeError(
                f"Die Konfiguration '{definition.full_key}' verweist "
                f"auf den unbekannten Ersatz "
                f"'{definition.replaced_by}'.",
            )


validate_definition_registry()
