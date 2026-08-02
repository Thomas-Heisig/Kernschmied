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
    PROVIDER_SELECT = "provider_select"
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
    PROVIDERS = "providers"
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

    depends_on: str | None = Field(
        default=None,
        max_length=255,
        pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$",
    )

    dependency_parameter: str | None = Field(
        default=None,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )

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

        if self.depends_on is None and self.dependency_parameter is not None:
            raise ValueError(
                "dependency_parameter benötigt depends_on.",
            )

        if self.depends_on is not None and self.dependency_parameter is None:
            raise ValueError(
                "depends_on benötigt dependency_parameter.",
            )

        # Note: preventing depends_on from referencing the same key
        # requires knowledge of the parent definition's full key and is
        # validated later when all definitions are available.

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
    # general.default_language removed — use identity.default_language instead
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
            "Bevorzugte Sprache für Antworten und erzeugte Arbeitsergebnisse."
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
        key="response_depth",
        display_name="Antworttiefe",
        description=(
            "Bestimmt den standardmäßigen Umfang und Detailgrad von Antworten."
        ),
        value_schema={
            "type": "string",
            "enum": [
                "compact",
                "balanced",
                "detailed",
                "comprehensive",
            ],
        },
        default_value="balanced",
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.SELECT,
            category="Identität und Verhalten",
            section="Kommunikation",
            order=60,
            options=(
                ConfigOption(value="compact", label="Kompakt"),
                ConfigOption(value="balanced", label="Ausgewogen"),
                ConfigOption(value="detailed", label="Detailliert"),
                ConfigOption(value="comprehensive", label="Umfassend"),
            ),
        ),
        tags={
            "identity",
            "communication",
            "verbosity",
        },
    ),
    config_definition(
        group="identity",
        key="timezone",
        display_name="Zeitzone",
        description=("IANA-Zeitzone für Termine, Fristen und zeitabhängige Aufgaben."),
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
                "Die Zeitzone muss als gültiger IANA-Bezeichner angegeben werden."
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
    # Additional identity configuration keys referenced by the settings catalog
    config_definition(
        group="identity",
        key="tone",
        display_name="Tonalität",
        description=(
            "Bevorzugter Kommunikationsstil von Kernschmied."
        ),
        value_schema={
            "type": "string",
            "enum": [
                "professional",
                "friendly",
                "direct",
                "formal",
                "adaptive",
            ],
        },
        default_value="professional",
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.SELECT,
            category="Identität und Verhalten",
            section="Kommunikation",
            order=55,
            options=(
                ConfigOption(value="professional", label="Professionell"),
                ConfigOption(value="friendly", label="Freundlich"),
                ConfigOption(value="direct", label="Direkt"),
                ConfigOption(value="formal", label="Formell"),
                ConfigOption(value="adaptive", label="Situativ anpassen"),
            ),
        ),
        tags={
            "identity",
            "communication",
            "tone",
        },
    ),
    config_definition(
        group="identity",
        key="ask_when_unclear",
        display_name="Bei Unklarheit nachfragen",
        description=(
            "Bei entscheidenden fehlenden Informationen gezielt Rückfragen stellen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Kommunikation",
            order=60,
        ),
        tags={"identity", "communication", "questions"},
    ),
    config_definition(
        group="identity",
        key="allow_reasonable_assumptions",
        display_name="Vertretbare Annahmen zulassen",
        description=(
            "Bei nicht kritischen Informationslücken klar gekennzeichnete, plausible Annahmen treffen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Kommunikation",
            order=70,
        ),
        tags={"identity", "communication", "assumptions"},
    ),
    config_definition(
        group="identity",
        key="mark_uncertainty",
        display_name="Unsicherheit kennzeichnen",
        description=(
            "Unsichere Annahmen, Schätzungen und nicht bestätigte Informationen sichtbar kennzeichnen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Kommunikation",
            order=80,
        ),
        tags={"identity", "communication", "uncertainty"},
    ),
    config_definition(
        group="identity",
        key="cite_sources",
        display_name="Quellen nennen",
        description=(
            "Verwendete interne oder externe Quellen in Ergebnissen sichtbar ausweisen."
        ),
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Kommunikation",
            order=90,
        ),
        tags={"identity", "communication", "sources"},
    ),
    config_definition(
        group="identity",
        key="show_alternatives",
        display_name="Alternativen darstellen",
        description=(
            "Bei mehreren sinnvollen Lösungswegen geeignete Alternativen und deren Unterschiede darstellen."
        ),
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Kommunikation",
            order=100,
        ),
        tags={"identity", "communication", "alternatives"},
    ),
    config_definition(
        group="identity",
        key="include_recommendations",
        display_name="Handlungsempfehlungen geben",
        description=(
            "Geeignete nächste Schritte und konkrete Handlungsempfehlungen ergänzen."
        ),
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Kommunikation",
            order=110,
        ),
        tags={"identity", "communication", "recommendations"},
    ),
    config_definition(
        group="identity",
        key="autonomy_level",
        display_name="Autonomiegrad",
        description=(
            "Allgemeiner Standard für selbstständige Planung und Ausführung."
        ),
        value_schema={
            "type": "string",
            "enum": ["advisory", "draft", "prepare", "execute_approved"],
        },
        default_value="advisory",
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.STRING,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.SELECT,
            category="Identität und Verhalten",
            section="Autonomie",
            order=10,
            options=(
                ConfigOption(value="advisory", label="Nur beraten"),
                ConfigOption(value="draft", label="Entwürfe erstellen"),
                ConfigOption(value="prepare", label="Änderungen vorbereiten"),
                ConfigOption(value="execute_approved", label="Freigegebene Aktionen ausführen"),
            ),
        ),
        tags={"identity", "autonomy"},
    ),
    config_definition(
        group="identity",
        key="prepare_actions_without_confirmation",
        display_name="Aktionen ohne Bestätigung vorbereiten",
        description=(
            "Kernschmied darf Entwürfe und Aktionsvorschläge ohne vorherige Bestätigung vorbereiten."
        ),
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Autonomie",
            order=20,
        ),
        tags={"identity", "autonomy", "draft"},
    ),
    config_definition(
        group="identity",
        key="confirm_high_impact_actions",
        display_name="Wirkungsstarke Aktionen bestätigen",
        description=(
            "Aktionen mit erheblichen externen, finanziellen oder dauerhaften Auswirkungen bestätigen lassen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Autonomie",
            order=30,
        ),
        tags={"identity", "autonomy", "confirmation", "high-impact"},
    ),
    config_definition(
        group="identity",
        key="stop_on_security_uncertainty",
        display_name="Bei Sicherheitsunsicherheit stoppen",
        description=(
            "Die Ausführung abbrechen, wenn Berechtigung, Datenzugriff oder Auswirkung nicht sicher bestimmt werden können."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Autonomie",
            order=40,
        ),
        tags={"identity", "autonomy", "security"},
    ),
    config_definition(
        group="identity",
        key="propose_follow_up_actions",
        display_name="Folgeaktionen vorschlagen",
        description=(
            "Nach Abschluss einer Aufgabe sinnvolle nächste Schritte vorschlagen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Autonomie",
            order=50,
        ),
        tags={"identity", "autonomy", "follow-up"},
    ),
    config_definition(
        group="identity",
        key="use_user_preferences",
        display_name="Benutzerpräferenzen berücksichtigen",
        description=(
            "Freigegebene, versionierte Benutzerpräferenzen bei Kommunikation und Ergebnissen berücksichtigen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Anpassung",
            order=10,
        ),
        tags={"identity", "adaptation", "user"},
    ),
    config_definition(
        group="identity",
        key="use_organization_context",
        display_name="Organisationskontext berücksichtigen",
        description=(
            "Freigegebenes Organisationswissen bei Planung und Ergebniserstellung berücksichtigen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Anpassung",
            order=20,
        ),
        tags={"identity", "adaptation", "organization"},
    ),
    config_definition(
        group="identity",
        key="use_project_context",
        display_name="Projektkontext berücksichtigen",
        description=(
            "Den aktiven Projekt- und Hierarchiekontext bei Aufgaben berücksichtigen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Anpassung",
            order=30,
        ),
        tags={"identity", "adaptation", "project"},
    ),
    config_definition(
        group="identity",
        key="adapt_communication_style",
        display_name="Kommunikationsstil anpassen",
        description=(
            "Den Stil innerhalb der freigegebenen Grenzen an Benutzer, Aufgabe und Kommunikationskanal anpassen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Anpassung",
            order=40,
        ),
        tags={"identity", "adaptation", "communication"},
    ),
    config_definition(
        group="identity",
        key="self_check_enabled",
        display_name="Selbstprüfung aktivieren",
        description=(
            "Ergebnisse vor Abschluss auf offensichtliche Fehler, Widersprüche und Regelverletzungen prüfen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Selbstprüfung",
            order=10,
        ),
        tags={"identity", "self-check"},
    ),
    config_definition(
        group="identity",
        key="check_goal_completion",
        display_name="Zielerreichung prüfen",
        description=(
            "Prüfen, ob die ursprüngliche Aufgabe vollständig und angemessen erfüllt wurde."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Selbstprüfung",
            order=20,
        ),
        tags={"identity", "self-check", "goal"},
    ),
    config_definition(
        group="identity",
        key="check_completeness",
        display_name="Vollständigkeit prüfen",
        description=(
            "Prüfen, ob erforderliche Bestandteile und Angaben im Ergebnis enthalten sind."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Selbstprüfung",
            order=30,
        ),
        tags={"identity", "self-check", "completeness"},
    ),
    config_definition(
        group="identity",
        key="check_consistency",
        display_name="Konsistenz prüfen",
        description=(
            "Zahlen, Aussagen, Einheiten und Bezüge auf innere Widersprüche prüfen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Selbstprüfung",
            order=40,
        ),
        tags={"identity", "self-check", "consistency"},
    ),
    config_definition(
        group="identity",
        key="check_plausibility",
        display_name="Plausibilität prüfen",
        description=(
            "Zahlen, Aussagen und Schlussfolgerungen auf offensichtliche Unplausibilitäten prüfen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Selbstprüfung",
            order=50,
        ),
        tags={"identity", "self-check", "plausibility"},
    ),
    config_definition(
        group="identity",
        key="detect_missing_information",
        display_name="Fehlende Informationen erkennen",
        description=(
            "Fehlende Angaben erkennen und als Rückfrage, Annahme oder offene Stelle sichtbar machen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Selbstprüfung",
            order=60,
        ),
        tags={"identity", "self-check", "missing-information"},
    ),
    config_definition(
        group="identity",
        key="allow_correction_attempt",
        display_name="Korrekturversuch erlauben",
        description=(
            "Bei erkannten Fehlern einen kontrollierten Korrekturversuch durchführen."
        ),
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Identität und Verhalten",
            section="Selbstprüfung",
            order=70,
        ),
        tags={"identity", "self-check", "correction"},
    ),
    config_definition(
        group="identity",
        key="max_correction_attempts",
        display_name="Maximale Korrekturversuche",
        description=(
            "Begrenzt automatische Korrekturversuche vor Abbruch oder Rückfrage."
        ),
        value_schema={"type": "integer", "minimum": 0, "maximum": 10},
        default_value=3,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.INTEGER,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.NUMBER,
            category="Identität und Verhalten",
            section="Selbstprüfung",
            order=80,
        ),
        tags={"identity", "self-check", "limits"},
    ),
    # ------------------------------------------------------------------
    # Auto-generated placeholder definitions for settings referenced
    # by the settings catalog but not yet modelled in CONFIG_DEFINITIONS.
    # These are conservative defaults and should be reviewed by a
    # maintainer to add precise schemas, defaults and UI metadata.
    # ------------------------------------------------------------------
    # Appearance
    config_definition(
        group="appearance",
        key="show_tool_activity",
        display_name="Tool-Aktivität anzeigen",
        description="Tool-Aufrufe und sichere Ergebniszusammenfassungen anzeigen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        ui=ConfigUIMetadata(component=ConfigUIComponent.CHECKBOX, category="Darstellung und Ausgabe", section="Oberfläche", order=30),
    ),
    config_definition(
        group="appearance",
        key="show_sources",
        display_name="Quellen anzeigen",
        description="Verwendete Quellen in Ergebnissen anzeigen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        ui=ConfigUIMetadata(component=ConfigUIComponent.CHECKBOX, category="Darstellung und Ausgabe", section="Oberfläche", order=40),
    ),
    config_definition(
        group="appearance",
        key="source_display_mode",
        display_name="Quellendarstellung",
        description="Legt fest, wann Quellen sichtbar dargestellt werden.",
        value_schema={"type": "string"},
        default_value="when_available",
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.STRING,
        ui=ConfigUIMetadata(component=ConfigUIComponent.SELECT, category="Darstellung und Ausgabe", section="Oberfläche", order=50),
    ),
    config_definition(
        group="appearance",
        key="show_draft_status",
        display_name="Entwurfsstatus anzeigen",
        description="Nicht freigegebene Ergebnisse sichtbar als Entwurf kennzeichnen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        ui=ConfigUIMetadata(component=ConfigUIComponent.CHECKBOX, category="Darstellung und Ausgabe", section="Ergebnisdarstellung", order=20),
    ),
    config_definition(
        group="appearance",
        key="show_revision_information",
        display_name="Revision anzeigen",
        description="Versions- und Revisionsinformationen bei gespeicherten Ergebnissen anzeigen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        ui=ConfigUIMetadata(component=ConfigUIComponent.CHECKBOX, category="Darstellung und Ausgabe", section="Ergebnisdarstellung", order=30),
    ),
    config_definition(
        group="appearance",
        key="automatic_result_view",
        display_name="Ansicht automatisch auswählen",
        description="Je nach Ergebnis eine bekannte generische Ansicht wie Text, Tabelle oder Baum auswählen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
        ui=ConfigUIMetadata(component=ConfigUIComponent.CHECKBOX, category="Darstellung und Ausgabe", section="Ergebnisdarstellung", order=10),
    ),

    # Artifacts / Data
    config_definition(
        group="artifacts",
        key="default_status",
        display_name="Standardstatus",
        description="Status neuer Arbeitsergebnisse.",
        value_schema={"type": "string"},
        default_value="draft",
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.STRING,
    ),
    config_definition(
        group="artifacts",
        key="automatic_versioning",
        display_name="Automatisch versionieren",
        description="Änderungen an gespeicherten Artifacts als neue Revision ablegen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="data",
        key="store_structured_content",
        display_name="Strukturierte Inhalte speichern",
        description="Neben gerenderten Dokumenten den strukturierten Inhalt versioniert speichern.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="data",
        key="store_rendered_outputs",
        display_name="Gerenderte Ausgaben speichern",
        description="Erzeugte PDF-, DOCX- oder andere Ausgaben als referenzierte Dateien speichern.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="data",
        key="record_provenance",
        display_name="Herkunft speichern",
        description="Benutzeranfrage, Prompts, Modelle, Tools, Quellen und Annahmen nachvollziehbar speichern.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="data",
        key="default_retention_days",
        display_name="Standard-Aufbewahrung",
        description="Standard-Aufbewahrungsdauer in Tagen.",
        value_schema={"type": "integer", "minimum": 1, "maximum": 36500},
        default_value=365,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="data",
        key="archive_before_delete",
        display_name="Vor Löschung archivieren",
        description="Daten vor einer zulässigen Löschung in einen Archivstatus überführen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),

    # Communication
    config_definition(
        group="communication",
        key="proactive_notifications",
        display_name="Proaktiv informieren",
        description="Bei wichtigen Ereignissen und relevanten Abweichungen aktiv informieren.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="communication",
        key="progress_updates",
        display_name="Fortschritt melden",
        description="Bei längeren Aufgaben sichere Zwischenstände anzeigen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="communication",
        key="completion_notifications",
        display_name="Abschluss melden",
        description="Nach Abschluss einer Aufgabe eine eindeutige Abschlussmeldung erzeugen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="communication",
        key="error_notifications",
        display_name="Fehler melden",
        description="Fehler, Abbrüche und blockierende Zustände sichtbar kommunizieren.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="communication",
        key="chat_streaming_enabled",
        display_name="Streaming aktivieren",
        description="Antworten als SSE-Stream übertragen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="communication",
        key="max_message_length",
        display_name="Maximale Nachrichtenlänge",
        description="Maximale Länge einer Chat-Nachricht.",
        value_schema={"type": "integer", "minimum": 1, "maximum": 1000000},
        default_value=10000,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),

    # Knowledge (many keys)
    config_definition(
        group="knowledge",
        key="automatic_context_selection",
        display_name="Automatische Kontextauswahl",
        description="Relevante freigegebene Quellen automatisch auswählen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="knowledge",
        key="context_strategy",
        display_name="Kontextstrategie",
        description="Steuert Breite und Vorsicht der Kontextzusammenstellung.",
        value_schema={"type": "string"},
        default_value="automatic",
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.STRING,
    ),
    config_definition(
        group="knowledge",
        key="max_context_sources",
        display_name="Maximale Quellenzahl",
        description="Maximale Zahl kombinierter Kontextquellen.",
        value_schema={"type": "integer", "minimum": 1, "maximum": 100},
        default_value=5,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="knowledge",
        key="max_context_tokens",
        display_name="Maximale Kontexttokens",
        description="Obergrenze des aus Wissensquellen erzeugten Kontexts.",
        value_schema={"type": "integer", "minimum": 1, "maximum": 1000000},
        default_value=20000,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="knowledge",
        key="relevance_threshold",
        display_name="Relevanzschwelle",
        description="Mindestwert für die Aufnahme einer Quelle.",
        value_schema={"type": "number", "minimum": 0, "maximum": 1},
        default_value=0.5,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.NUMBER,
    ),
    config_definition(
        group="knowledge",
        key="remove_duplicate_context",
        display_name="Duplikate entfernen",
        description="Inhaltlich gleiche oder nahezu gleiche Kontextbestandteile zusammenführen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),

    # Prompts
    config_definition(
        group="prompts",
        key="inheritance_enabled",
        display_name="Prompt-Vererbung",
        description="Prompt-Vererbung über Organisation, Arbeitsbereich, Projekt und Aufgabe aktivieren.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="prompts",
        key="conflict_strategy",
        display_name="Konfliktstrategie",
        description="Legt fest, wie widersprüchliche Prompt-Anweisungen behandelt werden.",
        value_schema={"type": "string"},
        default_value="more_specific",
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.STRING,
    ),
    config_definition(
        group="prompts",
        key="max_composed_length",
        display_name="Maximale Prompt-Länge",
        description="Obergrenze für den vollständig zusammengesetzten Prompt.",
        value_schema={"type": "integer", "minimum": 100, "maximum": 500000},
        default_value=20000,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="prompts",
        key="include_examples",
        display_name="Beispiele berücksichtigen",
        description="Freigegebene positive und negative Beispiele in Aufgabenprompts einbeziehen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="prompts",
        key="automatic_selection",
        display_name="Automatische Prompt-Auswahl",
        description="Passende freigegebene Aufgabenprompts anhand der erkannten Absicht auswählen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="prompts",
        key="require_active_revision",
        display_name="Nur aktive Revisionen verwenden",
        description="Entwürfe und archivierte Revisionen von der produktiven Verwendung ausschließen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),

    # Models: use conservative defaults
    # removed duplicate models.default_model_id; prefer `models.default_model`
    config_definition(
        group="models",
        key="fallback_model_id",
        display_name="Fallback-Modell",
        description="Ersatzmodell bei Nichtverfügbarkeit.",
        value_schema={"type": ["string", "null"]},
        default_value=None,
        allowed_scopes={ConfigScope.SYSTEM},
        nullable=True,
        value_type=ConfigValueType.STRING,
    ),
    config_definition(
        group="models",
        key="routing_mode",
        display_name="Routing-Modus",
        description="Strategie für die Auswahl eines geeigneten Modells.",
        value_schema={"type": "string"},
        default_value="manual",
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.STRING,
    ),
    config_definition(
        group="models",
        key="prefer_local_models",
        display_name="Lokale Modelle bevorzugen",
        description="Geeignete lokale Modelle vor externen Providern priorisieren.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="models",
        key="allow_paid_models",
        display_name="Kostenpflichtige Modelle erlauben",
        description="Freigegebene kostenpflichtige Provider bei Bedarf in das Routing einbeziehen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    # `models.temperature` rich definition exists later; earlier placeholder removed.
    config_definition(
        group="models",
        key="top_p",
        display_name="Top P",
        description="Nucleus-Sampling-Grenze.",
        value_schema={"type": "number", "minimum": 0, "maximum": 1},
        default_value=1.0,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.NUMBER,
    ),
    config_definition(
        group="models",
        key="top_k",
        display_name="Top K",
        description="Optionale Begrenzung der berücksichtigten Tokens.",
        value_schema={"type": "integer", "minimum": 0},
        default_value=0,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="models",
        key="repeat_penalty",
        display_name="Repeat Penalty",
        description="Standardwert zur Verringerung unnötiger Wiederholungen.",
        value_schema={"type": "number", "minimum": 0},
        default_value=1.0,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.NUMBER,
    ),
    config_definition(
        group="models",
        key="max_retries",
        display_name="Maximale Wiederholungen",
        description="Maximale Wiederholungen bei geeigneten vorübergehenden Providerfehlern.",
        value_schema={"type": "integer", "minimum": 0, "maximum": 100},
        default_value=3,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),

    # Remaining placeholders
    config_definition(
        group="data",
        key="default_export_format",
        display_name="Standard-Exportformat",
        description="Bevorzugtes Format für allgemeine Exporte.",
        value_schema={"type": "string"},
        default_value="pdf",
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.STRING,
    ),

    # Knowledge
    config_definition(
        group="knowledge",
        key="auto_persist_conversation_facts",
        display_name="Gesprächsinhalte automatisch übernehmen",
        description="Gesprächsinhalte automatisch in Kandidaten übernehmen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="knowledge",
        key="compress_context",
        display_name="Kontext komprimieren",
        description="Lange Kontextbestandteile kontrolliert zusammenfassen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="knowledge",
        key="conversation_memory_enabled",
        display_name="Gesprächsgedächtnis",
        description="Relevante Inhalte der aktuellen Unterhaltung als Kontext verwenden.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM, ConfigScope.USER},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="knowledge",
        key="mark_context_conflicts",
        display_name="Widersprüche markieren",
        description="Widersprüchliche Quellen sichtbar kennzeichnen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="knowledge",
        key="organization_memory_enabled",
        display_name="Organisationsgedächtnis",
        description="Freigegebenes Organisationswissen verwenden.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="knowledge",
        key="prefer_recent_sources",
        display_name="Aktuelle Quellen bevorzugen",
        description="Bei vergleichbarer Vertrauenswürdigkeit aktuellere Quellen bevorzugen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="knowledge",
        key="project_memory_enabled",
        display_name="Projektgedächtnis",
        description="Freigegebenes Wissen des aktiven Projekts verwenden.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),

    # Learning
    config_definition(
        group="learning",
        key="auto_apply_productive_changes",
        display_name="Produktive Änderungen automatisch anwenden",
        description="Produktive Änderungen automatisch anwenden (nicht empfohlen).",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="learning",
        key="minimum_confidence",
        display_name="Mindestvertrauen",
        description="Mindestvertrauen für einen Optimierungsvorschlag.",
        value_schema={"type": "number", "minimum": 0, "maximum": 1},
        default_value=0.8,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.NUMBER,
    ),
    config_definition(
        group="learning",
        key="minimum_observations",
        display_name="Mindestanzahl Beobachtungen",
        description="Mindestanzahl ähnlicher Beobachtungen vor Erzeugung eines Kandidaten.",
        value_schema={"type": "integer", "minimum": 1},
        default_value=3,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="learning",
        key="mode",
        display_name="Lernmodus",
        description="Legt fest, ob Erfahrungen nicht, passiv oder als Kandidaten erfasst werden.",
        value_schema={"type": "string"},
        default_value="off",
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.STRING,
    ),
    config_definition(
        group="learning",
        key="record_failed_tasks",
        display_name="Fehlgeschlagene Aufgaben erfassen",
        description="Fehler und Abbrüche für spätere Ursachenanalyse protokollieren.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="learning",
        key="record_successful_tasks",
        display_name="Erfolgreiche Aufgaben erfassen",
        description="Erfolgreiche Aufgaben für spätere Mustererkennung protokollieren.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="learning",
        key="record_user_corrections",
        display_name="Nutzerkorrekturen erfassen",
        description="Nachträgliche Korrekturen als Signal für Lernkandidaten erfassen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="learning",
        key="require_manual_approval",
        display_name="Manuelle Freigabe verlangen",
        description="Produktive Lern- und Optimierungsänderungen müssen manuell freigegeben werden.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),

    # Models extras
    config_definition(
        group="models",
        key="failover_enabled",
        display_name="Failover aktivieren",
        description="Bei geeigneten Fehlern ein freigegebenes Fallback-Modell verwenden.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="models",
        key="prefer_structured_output",
        display_name="Strukturierte Ausgabe bevorzugen",
        description="Bei geeigneten Aufgaben und Modellen strukturierte Ausgaben bevorzugen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="models",
        key="request_timeout_seconds",
        display_name="Request-Timeout",
        description="Standard-Timeout einer Modellanfrage in Sekunden.",
        value_schema={"type": "integer", "minimum": 1},
        default_value=30,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),

    # Planning
    config_definition(
        group="planning",
        key="ask_when_blocked",
        display_name="Bei Blockierung nachfragen",
        description="Bei fehlenden entscheidenden Informationen gezielt nachfragen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="planning",
        key="check_output_format",
        display_name="Format prüfen",
        description="Erwartete Struktur und Ausgabeform prüfen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="planning",
        key="check_rule_compliance",
        display_name="Regelkonformität prüfen",
        description="Ergebnis gegen freigegebene fachliche und technische Regeln prüfen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="planning",
        key="enabled",
        display_name="Planung aktivieren",
        description="Vor komplexen Aufgaben einen expliziten internen Arbeitsplan erzeugen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="planning",
        key="failure_strategy",
        display_name="Standard-Fehlerstrategie",
        description="Standardreaktion bei nicht sicher behebbaren Ausführungsfehlern.",
        value_schema={"type": "string"},
        default_value="stop",
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.STRING,
    ),
    config_definition(
        group="planning",
        key="mark_draft_results",
        display_name="Entwürfe kennzeichnen",
        description="Noch nicht freigegebene Ergebnisse deutlich als Entwurf markieren.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="planning",
        key="max_duration_seconds",
        display_name="Maximale Dauer",
        description="Maximale Laufzeit einer Aufgabe in Sekunden.",
        value_schema={"type": "integer", "minimum": 1},
        default_value=3600,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="planning",
        key="max_replans",
        display_name="Maximale Neuplanungen",
        description="Begrenzt automatische Anpassungen eines fehlgeschlagenen Plans.",
        value_schema={"type": "integer", "minimum": 0},
        default_value=3,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="planning",
        key="max_steps",
        display_name="Maximale Schritte",
        description="Obergrenze der Ausführungsschritte.",
        value_schema={"type": "integer", "minimum": 1},
        default_value=100,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="planning",
        key="parallel_execution_enabled",
        display_name="Parallelisierung zulassen",
        description="Unabhängige, sichere Arbeitsschritte parallel ausführen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="planning",
        key="quality_check_enabled",
        display_name="Qualitätsprüfung aktivieren",
        description="Ergebnisse vor Abschluss gegen verfügbare Qualitätsregeln prüfen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="planning",
        key="save_checkpoints",
        display_name="Zwischenstände speichern",
        description="Relevante Zwischenstände für Wiederaufnahme und Diagnose speichern.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="planning",
        key="show_progress",
        display_name="Zwischenstände anzeigen",
        description="Sichere Fortschrittszusammenfassungen im Frontend anzeigen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="planning",
        key="warn_before_risky_actions",
        display_name="Vor Risiken warnen",
        description="Erkannte relevante Risiken vor Ausführung sichtbar darstellen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),

    # Prompts fallback
    config_definition(
        group="prompts",
        key="fallback_enabled",
        display_name="Fallback-Prompt verwenden",
        description="Bei unbekannten Aufgaben einen freigegebenen allgemeinen Arbeits-Prompt verwenden.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),

    # Security
    config_definition(
        group="security",
        key="block_secret_output",
        display_name="Secret-Ausgabe blockieren",
        description="Verhindert die Ausgabe bekannter Secrets über normale Ergebnis- und Chatkanäle.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="security",
        key="data_exfiltration_detection",
        display_name="Datenexfiltration prüfen",
        description="Verdächtige Massenexporte und unerlaubte Datenübertragungen erkennen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="security",
        key="default_data_classification",
        display_name="Standard-Datenklassifizierung",
        description="Standardklassifizierung neuer Inhalte.",
        value_schema={"type": "string"},
        default_value="internal",
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.STRING,
    ),
    config_definition(
        group="security",
        key="mask_sensitive_logs",
        display_name="Sensible Logdaten maskieren",
        description="Bekannte sensible Werte in Protokollen maskieren.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="security",
        key="prompt_injection_detection",
        display_name="Prompt-Injection-Prüfung",
        description="Externe Inhalte auf manipulative Anweisungen prüfen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="security",
        key="tool_manipulation_detection",
        display_name="Tool-Manipulation prüfen",
        description="Tool-Eingaben und Tool-Ergebnisse auf Manipulationsversuche prüfen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),

    # Tools
    config_definition(
        group="tools",
        key="automatic_selection",
        display_name="Automatische Tool-Auswahl",
        description="Das Modell darf geeignete freigegebene Tools selbst auswählen.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="tools",
        key="confirm_delete_actions",
        display_name="Löschaktionen bestätigen",
        description="Löschende Aktionen erfordern immer eine Bestätigung.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="tools",
        key="confirm_external_communication",
        display_name="Externe Kommunikation bestätigen",
        description="Versand, Veröffentlichung und sonstige externe Kommunikation bestätigen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="tools",
        key="confirm_financial_actions",
        display_name="Finanzielle Aktionen bestätigen",
        description="Zahlungen, Buchungen und andere finanzielle Aktionen benötigen eine ausdrückliche Bestätigung.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="tools",
        key="confirm_write_actions",
        display_name="Schreibaktionen bestätigen",
        description="Schreibende Aktionen erfordern eine Benutzerbestätigung.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="tools",
        key="default_timeout_seconds",
        display_name="Standard-Timeout",
        description="Maximale Standardlaufzeit eines Tool-Aufrufs in Sekunden.",
        value_schema={"type": "integer", "minimum": 1},
        default_value=30,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="tools",
        key="max_output_bytes",
        display_name="Maximale Ausgabegröße",
        description="Maximale normalisierte Tool-Ausgabe in Bytes.",
        value_schema={"type": "integer", "minimum": 1},
        default_value=1048576,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="tools",
        key="max_parallel_calls",
        display_name="Maximale Parallelität",
        description="Maximale Zahl parallel laufender Tool-Aufrufe.",
        value_schema={"type": "integer", "minimum": 1},
        default_value=5,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="tools",
        key="max_retries",
        display_name="Maximale Wiederholungen",
        description="Maximale Wiederholungen bei geeigneten vorübergehenden Fehlern.",
        value_schema={"type": "integer", "minimum": 0},
        default_value=3,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="tools",
        key="max_rounds",
        display_name="Maximale Tool-Runden",
        description="Obergrenze der Tool-Runden je Aufgabe.",
        value_schema={"type": "integer", "minimum": 0},
        default_value=10,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="tools",
        key="max_selected_tools",
        display_name="Maximale Tool-Anzahl",
        description="Maximale Zahl gleichzeitig für eine Aufgabe ausgewählter Tools.",
        value_schema={"type": "integer", "minimum": 0},
        default_value=5,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.INTEGER,
    ),
    config_definition(
        group="tools",
        key="record_result_provenance",
        display_name="Herkunft dokumentieren",
        description="Verwendetes Tool, Version, Eingabe und Ergebnisreferenz nachvollziehbar speichern.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="tools",
        key="send_progress",
        display_name="Fortschritt anzeigen",
        description="Sichere Fortschrittsmeldungen bei längeren Tool-Ausführungen übertragen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="tools",
        key="store_intermediate_results",
        display_name="Zwischenergebnisse speichern",
        description="Relevante Zwischenergebnisse innerhalb des Auftragskontexts speichern.",
        value_schema={"type": "boolean"},
        default_value=False,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),
    config_definition(
        group="tools",
        key="validate_results",
        display_name="Ergebnisse validieren",
        description="Tool-Ergebnisse vor weiterer Verwendung gegen den bekannten Vertrag prüfen.",
        value_schema={"type": "boolean"},
        default_value=True,
        allowed_scopes={ConfigScope.SYSTEM},
        value_type=ConfigValueType.BOOLEAN,
    ),

    # Tools & Planning & Security & Learning & others are intentionally left with
    # conservative placeholders. Add more specific schemas as needed.
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
        key="default_provider",
        display_name="Standardprovider",
        description=(
            "Provider, dessen Modelle standardmäßig für neue Chats angeboten werden."
        ),
        value_schema={
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
        },
        default_value="ollama",
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
            component=ConfigUIComponent.PROVIDER_SELECT,
            category="Modelle",
            section="Standardauswahl",
            order=10,
            dynamic_options=ConfigDynamicOptions(
                source=ConfigValueSource.PROVIDERS,
                endpoint="/api/v1/models/providers",
                value_field="id",
                label_field="name",
                description_field="description",
            ),
        ),
        tags={
            "models",
            "providers",
            "defaults",
        },
    ),
    config_definition(
        group="models",
        key="default_model",
        display_name="Standardmodell",
        description=(
            "Standardmodell für neue Chats. "
            "Die Auswahl wird automatisch auf den aktuellen Provider gefiltert."
        ),
        value_schema={
            "type": [
                "string",
                "null",
            ],
            "minLength": 1,
            "maxLength": 255,
        },
        default_value="ollama-qwen2.5-coder-7b",
        nullable=True,
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
            order=20,
            dynamic_options=ConfigDynamicOptions(
                source=ConfigValueSource.MODELS,
                endpoint="/api/v1/models",
                value_field="id",
                label_field="name",
                description_field="description",
                filters={
                    "include_disabled": False,
                    "capability": "chat",
                },
                depends_on="models.default_provider",
                dependency_parameter="provider",
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
        key="autosave_enabled",
        display_name="Autosave",
        description=(
            "Änderungen automatisch speichern (Frontend-Autosave)."
        ),
        value_schema={
            "type": "boolean",
        },
        default_value=True,
        allowed_scopes={
            ConfigScope.SYSTEM,
            ConfigScope.USER,
        },
        value_type=ConfigValueType.BOOLEAN,
        runtime_editable=True,
        ui=ConfigUIMetadata(
            component=ConfigUIComponent.CHECKBOX,
            category="Oberfläche",
            section="Allgemein",
            order=20,
        ),
        tags={
            "ui",
            "autosave",
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
