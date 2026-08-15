from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class SystemServiceStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["up", "down", "unknown"]


class SystemRegistryCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    models: int = Field(ge=0)
    tools: int = Field(ge=0)


class SystemOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    api_version: Literal["v1"] = "v1"
    status: Literal["ok"] = "ok"
    environment: str
    config_revision: int = Field(ge=0)
    security_profile: dict[str, JsonValue]
    services: dict[str, SystemServiceStatus]
    registries: SystemRegistryCounts
    request_id: str | None = None