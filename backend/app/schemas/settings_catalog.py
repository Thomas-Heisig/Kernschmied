from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class SettingsAvailability(StrEnum):
    AVAILABLE = "available"
    PREPARED = "prepared"
    PLANNED = "planned"


class SettingsSource(StrEnum):
    CONFIG = "config"
    RESOURCE = "resource"
    RUNTIME = "runtime"
    LOCAL_PREFERENCE = "local_preference"


class SettingsControl(StrEnum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTISELECT = "multiselect"
    READONLY = "readonly"
    LINK = "link"


class SettingsOption(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str
    label: str


class SettingsFieldDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title: str
    description: str | None = None
    source: SettingsSource
    availability: SettingsAvailability = SettingsAvailability.PREPARED
    control: SettingsControl = SettingsControl.READONLY
    config_group: str | None = None
    config_key: str | None = None
    endpoint: str | None = None
    editable: bool = False
    sensitive: bool = False
    requires_confirmation: bool = False
    restart_required: bool = False
    options: tuple[SettingsOption, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    order: int = 0
    tags: tuple[str, ...] = ()


class SettingsSectionDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title: str
    description: str | None = None
    order: int = 0
    availability: SettingsAvailability = SettingsAvailability.PREPARED
    fields: tuple[SettingsFieldDescriptor, ...] = ()


class SettingsGroupDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title: str
    description: str
    icon: str
    order: int
    availability: SettingsAvailability = SettingsAvailability.PREPARED
    sections: tuple[SettingsSectionDescriptor, ...] = ()


class SettingsCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    groups: tuple[SettingsGroupDescriptor, ...]
    request_id: str | None = None
