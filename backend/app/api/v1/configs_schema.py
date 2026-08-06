from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator

# API request/response models for the configs endpoints


class ConfigUpdateRequest(BaseModel):
    """
    Änderung eines einzelnen Konfigurationswertes.

    `expected_revision` schützt vor dem unbeabsichtigten Überschreiben
    einer zwischenzeitlich geänderten Konfiguration.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    value: JsonValue

    expected_revision: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Vom Client zuletzt gelesene Konfigurationsrevision. "
            "Bei Abweichung wird die Änderung abgelehnt."
        ),
    )

    reason: str | None = Field(
        default=None,
        max_length=500,
        description=("Optionale Begründung für das Audit-Log."),
    )

    @field_validator(
        "reason",
    )
    @classmethod
    def normalize_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None


class ConfigUpdateResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    status: Literal["updated"] = "updated"

    group: str
    key: str

    revision: int = Field(
        ge=0,
    )

    request_id: str | None = None


class ConfigErrorDetails(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )

    group: str | None = None
    key: str | None = None

    expected_revision: int | None = None
    current_revision: int | None = None


class ConfigChangeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group: str
    key: str
    value: JsonValue


class BulkConfigUpdateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    values: Mapping[str, Mapping[str, JsonValue]] = Field(
        default_factory=dict,
        description="Gruppierte Konfigurationswerte als Objekt { group: { key: value } }",
    )

    changes: list[ConfigChangeItem] = Field(  # type: ignore[reportUnknownVariableType]
        default_factory=list,
        description="Alternative sequentielle Änderungsbeschreibung [{group,key,value}, ...]",
    )

    expected_revision: int | None = Field(
        default=None,
        ge=0,
        description=("Erwartete Revision zur Vermeidung von Race-Conditions."),
    )
