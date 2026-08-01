from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
)


class ConfigOptionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str | int | float | bool
    label: str
    description: str | None = None
    disabled: bool = False


class ConfigDynamicOptionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    endpoint: str | None = None

    value_field: str = "id"
    label_field: str = "name"
    description_field: str | None = "description"

    filters: dict[str, JsonValue] = Field(
        default_factory=dict,
    )

    depends_on: str | None = None
    dependency_parameter: str | None = None


class ConfigUIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component: str | None = None

    category: str | None = None
    section: str | None = None
    order: int = 0

    placeholder: str | None = None
    help_text: str | None = None
    unit: str | None = None

    advanced: bool = False
    hidden: bool = False
    readonly: bool = False

    options: list[ConfigOptionResponse] = Field(
        default_factory=lambda: list[ConfigOptionResponse](),
    )

    dynamic_options: ConfigDynamicOptionsResponse | None = None


class ConfigEntryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group: str
    key: str
    full_key: str

    display_name: str
    description: str

    value: JsonValue
    default_value: JsonValue

    schema_version: str
    value_type: str | None = None

    value_schema: dict[str, JsonValue] = Field(
        default_factory=dict,
    )

    editable: bool
    sensitive: bool
    secret_configured: bool = False

    requires_restart: bool
    runtime_editable: bool
    nullable: bool

    visibility: str

    allowed_scopes: list[str] = Field(
        default_factory=lambda: list[str](),
    )

    current_scope: str

    class ConfigPermissionsResponse(BaseModel):
        model_config = ConfigDict(extra="forbid")

        read: str
        write: str
        reveal_secret: str | None = None

    permissions: ConfigPermissionsResponse | None = None

    ui: ConfigUIResponse

    deprecated: bool = False
    deprecation_message: str | None = None
    replaced_by: str | None = None


class ConfigGroupResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    description: str | None = None
    order: int = 0

    entries: list[ConfigEntryResponse] = Field(
        default_factory=lambda: list[ConfigEntryResponse](),
    )


class ConfigListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["2.0"] = "2.0"
    revision: int = Field(ge=0)

    groups: list[ConfigGroupResponse] = Field(
        default_factory=lambda: list[ConfigGroupResponse](),
    )

    request_id: str | None = None
