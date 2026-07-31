# F:\Kernschmied\backend\app\api\v1\health.py

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Mapping, Sequence
from typing import Literal, TypeAlias, cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from app.core.security_profile import get_security_profile

router = APIRouter()


API_VERSION = "v1"
HEALTH_SCHEMA_VERSION = "1.0"


# Eigene rekursive Definition ENTFERNEN – stattdessen Pydantic's JsonValue verwenden
JsonObject: TypeAlias = dict[str, JsonValue]


class ServiceStatus(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    status: Literal[
        "up",
        "down",
        "unknown",
    ]


class HealthResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: str = HEALTH_SCHEMA_VERSION
    api_version: str = API_VERSION

    status: Literal["ok"] = "ok"

    environment: str

    config_revision: int = Field(
        ge=0,
    )

    security_profile: JsonObject

    services: dict[str, ServiceStatus]

    request_id: str | None = None


def get_request_id(
    request: Request,
) -> str | None:
    raw_request_id: object = getattr(
        request.state,
        "request_id",
        None,
    )

    if raw_request_id is None:
        return None

    normalized = str(
        raw_request_id,
    ).strip()

    return normalized or None


def service_status(
    service: object | None,
) -> ServiceStatus:
    if service is None:
        return ServiceStatus(
            status="down",
        )

    return ServiceStatus(
        status="up",
    )


def normalize_non_negative_int(
    value: object,
    *,
    default: int = 0,
) -> int:
    if isinstance(value, bool):
        return int(
            value,
        )

    if isinstance(value, int):
        return max(
            value,
            0,
        )

    if isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            return default

        try:
            return max(
                int(normalized),
                0,
            )
        except ValueError:
            return default

    return default


async def resolve_maybe_awaitable(
    value: object,
) -> object:
    if inspect.isawaitable(
        value,
    ):
        return await cast(
            Awaitable[object],
            value,
        )

    return value


async def get_config_revision(
    config_service: object | None,
) -> int:
    if config_service is None:
        return 0

    revision_getter: object = getattr(
        config_service,
        "get_revision",
        None,
    )

    if callable(
        revision_getter,
    ):
        try:
            raw_revision = revision_getter()

            resolved_revision = await resolve_maybe_awaitable(
                raw_revision,
            )

            return normalize_non_negative_int(
                resolved_revision,
            )
        except (
            RuntimeError,
            TypeError,
            ValueError,
        ):
            return 0

    raw_revision: object = getattr(
        config_service,
        "revision",
        0,
    )

    try:
        resolved_revision = await resolve_maybe_awaitable(
            raw_revision,
        )
    except (
        RuntimeError,
        TypeError,
        ValueError,
    ):
        return 0

    return normalize_non_negative_int(
        resolved_revision,
    )


def normalize_json_value(
    value: object,
) -> JsonValue:
    if value is None:
        return None

    if isinstance(
        value,
        str | int | float | bool,
    ):
        return value

    if isinstance(
        value,
        Mapping,
    ):
        typed_mapping = cast(
            Mapping[object, object],
            value,
        )

        result: dict[str, JsonValue] = {}

        for raw_key, raw_value in typed_mapping.items():
            key = str(
                raw_key,
            )

            result[key] = normalize_json_value(
                raw_value,
            )

        return result

    if isinstance(
        value,
        Sequence,
    ):
        if isinstance(
            value,
            bytes | bytearray,
        ):
            return value.decode(
                encoding="utf-8",
                errors="replace",
            )

        typed_sequence = cast(
            Sequence[object],
            value,
        )

        return [
            normalize_json_value(
                item,
            )
            for item in typed_sequence
        ]

    if isinstance(
        value,
        set | frozenset,
    ):
        typed_set = cast(
            set[object] | frozenset[object],
            value,
        )

        return [
            normalize_json_value(
                item,
            )
            for item in typed_set
        ]

    value_attribute: object = getattr(
        value,
        "value",
        None,
    )

    if value_attribute is not None:
        return normalize_json_value(
            value_attribute,
        )

    return str(
        value,
    )


def get_security_profile_data() -> JsonObject:
    security_profile = get_security_profile()

    raw_profile: object = security_profile.model_dump(
        mode="json",
    )

    normalized_profile = normalize_json_value(
        raw_profile,
    )

    if isinstance(
        normalized_profile,
        dict,
    ):
        return normalized_profile

    return {
        "value": normalized_profile,
    }


def get_environment() -> str:
    """
    Liefert das feste Betriebsprofil.

    Das Betriebsprofil darf nicht aus der Fachkonfiguration oder der
    Datenbank gelesen werden, weil es eine Sicherheitsuntergrenze
    definiert.
    """

    security_profile = get_security_profile()

    raw_environment: object = getattr(
        security_profile,
        "environment",
        "development",
    )

    enum_value: object = getattr(
        raw_environment,
        "value",
        raw_environment,
    )

    normalized = (
        str(
            enum_value,
        )
        .strip()
        .lower()
    )

    return normalized or "development"


@router.get(
    "",
    response_model=HealthResponse,
    response_model_exclude_none=True,
    summary="Health Check",
)
async def health(
    request: Request,
    response: Response,
) -> HealthResponse:
    config_service: object | None = getattr(
        request.app.state,
        "config_service",
        None,
    )

    model_registry: object | None = getattr(
        request.app.state,
        "model_registry",
        None,
    )

    tool_registry: object | None = getattr(
        request.app.state,
        "tool_registry",
        None,
    )

    database: object | None = getattr(
        request.app.state,
        "db",
        None,
    )

    revision = await get_config_revision(
        config_service,
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Health-Schema-Version"] = HEALTH_SCHEMA_VERSION
    response.headers["X-API-Version"] = API_VERSION
    response.headers["X-Config-Revision"] = str(
        revision,
    )

    return HealthResponse(
        environment=get_environment(),
        config_revision=revision,
        security_profile=get_security_profile_data(),
        services={
            "config_service": service_status(
                config_service,
            ),
            "model_registry": service_status(
                model_registry,
            ),
            "tool_registry": service_status(
                tool_registry,
            ),
            "database": service_status(
                database,
            ),
        },
        request_id=get_request_id(
            request,
        ),
    )
