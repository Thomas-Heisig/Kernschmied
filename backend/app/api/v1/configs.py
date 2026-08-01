# F:\Kernschmied\backend\app\api\v1\configs.py

from __future__ import annotations

import inspect
import logging
import math
import re
from collections.abc import (
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from enum import StrEnum
from functools import lru_cache
from typing import (
    Literal,
    TypeAlias,
    TypeGuard,
    cast,
)
from uuid import UUID
from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
)

from app.config.service import ConfigValidationError, ConfigService
from app.core.security_profile import get_security_profile
from app.schemas.settings_catalog import (
    SettingsControl,
    SettingsFieldDescriptor,
    SettingsSource,
)
from app.services.settings_catalog import build_settings_catalog

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Öffentlicher Config-Vertrag
# ============================================================

CONFIG_API_SCHEMA_VERSION = "1.2"

CONFIG_NAME_PATTERN = re.compile(
    r"^[a-z][a-z0-9_-]{0,63}$",
)

LANGUAGE_CODE_PATTERN = re.compile(
    r"^[a-z]{2,3}(?:-[A-Z]{2})?$",
)


# ============================================================
# Sicherheitsgrenzen
# ============================================================

RESERVED_GROUPS: frozenset[str] = frozenset(
    {
        "bootstrap",
        "infrastructure",
        "security_secrets",
        "secrets",
    },
)

SENSITIVE_KEY_PARTS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "private_key",
        "credential",
        "connection_string",
    },
)


# ============================================================
# Zusätzliche Identitätsvalidierung
# ============================================================

IDENTITY_STRING_LIMITS: Mapping[
    str,
    tuple[int, int],
] = {
    "name": (
        1,
        100,
    ),
    "role_description": (
        1,
        2_000,
    ),
    "mission": (
        1,
        10_000,
    ),
    "organization_description": (
        0,
        5_000,
    ),
    "default_language": (
        2,
        20,
    ),
    "timezone": (
        1,
        100,
    ),
    "behavior_principles": (
        1,
        10_000,
    ),
    "tone": (
        1,
        50,
    ),
    "response_depth": (
        1,
        50,
    ),
    "autonomy_level": (
        1,
        100,
    ),
}


# ============================================================
# Typen
# ============================================================

ConfigScalar: TypeAlias = str | int | float | bool | None

ConfigValue: TypeAlias = JsonValue

ConfigIdentifier: TypeAlias = tuple[
    str,
    str,
]

ConfigEntries: TypeAlias = Mapping[
    ConfigIdentifier,
    ConfigValue,
]

DynamicCallable: TypeAlias = Callable[
    ...,
    object,
]


class ConfigOperationStatus(StrEnum):
    UPDATED = "updated"


# ============================================================
# API-Schemas
# ============================================================


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

    value: ConfigValue

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


class ConfigEntryResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    group: str
    key: str
    value: ConfigValue

    editable: bool = True
    sensitive: bool = False
    requires_confirmation: bool = False

    control: str | None = None


class ConfigListResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: str = CONFIG_API_SCHEMA_VERSION

    revision: int = Field(
        ge=0,
    )

    items: list[ConfigEntryResponse]

    request_id: str | None = None


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


# ============================================================
# Type Guards
# ============================================================


def normalize_config_number(
    value: object,
) -> float | None:
    """
    Konvertiert einen zulässigen numerischen JSON-Wert in float.

    Boolesche Werte werden ausgeschlossen, obwohl bool eine
    Unterklasse von int ist.
    """

    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        int,
    ):
        return float(
            value,
        )

    if isinstance(
        value,
        float,
    ):
        if not math.isfinite(
            value,
        ):
            return None

        return value

    return None


def is_config_string_list(
    value: ConfigValue,
) -> TypeGuard[list[str]]:
    if not isinstance(
        value,
        list,
    ):
        return False

    return all(
        isinstance(
            item,
            str,
        )
        for item in value
    )


# ============================================================
# Request-Kontext und Fehler
# ============================================================


def get_request_id(
    request: Request,
) -> str | None:
    request_id: object = getattr(
        request.state,
        "request_id",
        None,
    )

    if request_id is None:
        return None

    normalized = str(
        request_id,
    ).strip()

    return normalized or None


def structured_http_error(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Mapping[str, object] | None = None,
) -> HTTPException:
    normalized_details: dict[str, object] = (
        dict(
            details,
        )
        if details is not None
        else {}
    )

    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "details": normalized_details,
            "request_id": get_request_id(
                request,
            ),
        },
    )


# ============================================================
# ConfigService-Zugriff
# ============================================================


def get_config_service(
    request: Request,
) -> ConfigService:
    service = getattr(
        request.app.state,
        "config_service",
        None,
    )

    if service is None:
        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            code="CONFIG_SERVICE_UNAVAILABLE",
            message=("Der Konfigurationsdienst ist nicht verfügbar."),
        )

    return cast(ConfigService, service)


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


def normalize_revision(
    value: object,
    *,
    default: int = 0,
) -> int:
    if isinstance(
        value,
        bool,
    ):
        return int(
            value,
        )

    if isinstance(
        value,
        int,
    ):
        return max(
            value,
            0,
        )

    if isinstance(
        value,
        str,
    ):
        normalized = value.strip()

        if not normalized:
            return default

        try:
            parsed = int(
                normalized,
            )
        except ValueError:
            return default

        return max(
            parsed,
            0,
        )

    return default


async def get_service_revision(
    service: ConfigService,
    *,
    default: int = 0,
) -> int:
    revision_getter: object = getattr(
        service,
        "get_revision",
        None,
    )

    if callable(
        revision_getter,
    ):
        try:
            raw_revision: object = revision_getter()

            resolved_revision = await resolve_maybe_awaitable(
                raw_revision,
            )

            return normalize_revision(
                resolved_revision,
                default=default,
            )

        except (
            TypeError,
            ValueError,
            RuntimeError,
        ):
            logger.exception(
                "Config revision getter failed",
            )

            return default

    revision_value: object = getattr(
        service,
        "revision",
        default,
    )

    if inspect.isawaitable(
        revision_value,
    ):
        try:
            revision_value = await cast(
                Awaitable[object],
                revision_value,
            )

        except (
            TypeError,
            ValueError,
            RuntimeError,
        ):
            logger.exception(
                "Awaiting config revision failed",
            )

            return default

    return normalize_revision(
        revision_value,
        default=default,
    )


# ============================================================
# Bezeichner und sensible Werte
# ============================================================


def validate_config_name(
    value: str,
    *,
    field_name: Literal[
        "group",
        "key",
    ],
    request: Request,
) -> str:
    normalized = value.strip().lower()

    if not CONFIG_NAME_PATTERN.fullmatch(
        normalized,
    ):
        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            code="INVALID_CONFIG_IDENTIFIER",
            message=(f"Der Konfigurationsbezeichner '{field_name}' ist ungültig."),
            details={
                "field": field_name,
                "value": value,
                "pattern": CONFIG_NAME_PATTERN.pattern,
            },
        )

    return normalized


def is_sensitive_key(
    group: str,
    key: str,
) -> bool:
    normalized = f"{group}.{key}".lower()

    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def is_reserved_group(
    group: str,
) -> bool:
    return group.lower() in RESERVED_GROUPS


# ============================================================
# Principal und Berechtigungen
# ============================================================


def read_mapping_value(
    source: object,
    key: str,
    default: object = None,
) -> object:
    if isinstance(
        source,
        Mapping,
    ):
        typed_mapping = cast(
            Mapping[object, object],
            source,
        )

        return typed_mapping.get(
            key,
            default,
        )

    return getattr(
        source,
        key,
        default,
    )


def get_principal(
    request: Request,
) -> object | None:
    principal: object = getattr(
        request.state,
        "user",
        None,
    )

    if principal is None:
        principal = getattr(
            request.state,
            "principal",
            None,
        )

    return principal


def normalize_optional_identifier(
    value: object,
) -> str | None:
    if value is None:
        return None

    if isinstance(
        value,
        UUID,
    ):
        return str(
            value,
        )

    normalized = str(
        value,
    ).strip()

    return normalized or None


def get_actor_id(
    request: Request,
) -> str | None:
    principal = get_principal(
        request,
    )

    if principal is None:
        return None

    actor_id = read_mapping_value(
        principal,
        "id",
    )

    if actor_id is None:
        actor_id = read_mapping_value(
            principal,
            "user_id",
        )

    if actor_id is None:
        actor_id = read_mapping_value(
            principal,
            "subject",
        )

    return normalize_optional_identifier(
        actor_id,
    )


def normalize_string_collection(
    value: object,
) -> set[str]:
    if value is None:
        return set()

    if isinstance(
        value,
        str,
    ):
        normalized = value.strip()

        return (
            {
                normalized,
            }
            if normalized
            else set()
        )

    if isinstance(
        value,
        Mapping,
    ):
        return set()

    items: Sequence[object]

    if isinstance(
        value,
        Sequence,
    ):
        items = cast(
            Sequence[object],
            value,
        )

    elif isinstance(
        value,
        set | frozenset,
    ):
        items = tuple(
            cast(
                set[object] | frozenset[object],
                value,
            ),
        )

    else:
        return set()

    result: set[str] = set()

    for item in items:
        if item is None:
            continue

        normalized = str(
            item,
        ).strip()

        if normalized:
            result.add(
                normalized,
            )

    return result


def get_permissions(
    request: Request,
) -> set[str]:
    principal = get_principal(
        request,
    )

    if principal is None:
        return set()

    raw_permissions = read_mapping_value(
        principal,
        "permissions",
        [],
    )

    raw_roles = read_mapping_value(
        principal,
        "roles",
        [],
    )

    permissions = normalize_string_collection(
        raw_permissions,
    )

    roles = normalize_string_collection(
        raw_roles,
    )

    if {
        "admin",
        "administrator",
    }.intersection(
        roles,
    ):
        permissions.add(
            "*",
        )

    return permissions


def development_fallback_allowed(
    request: Request,
) -> bool:
    """
    Der vereinfachte Zugriff ist nur im fest konfigurierten
    Development-Profil zulässig.
    """

    security_profile = get_security_profile()

    environment_value: object = getattr(
        security_profile,
        "environment",
        "development",
    )

    raw_environment: object = getattr(
        environment_value,
        "value",
        environment_value,
    )

    return (
        str(
            raw_environment,
        )
        .strip()
        .lower()
        == "development"
    )


def require_config_permission(
    request: Request,
    permission: Literal[
        "config:read",
        "config:write",
    ],
) -> None:
    permissions = get_permissions(
        request,
    )

    if "*" in permissions or permission in permissions:
        return

    if development_fallback_allowed(
        request,
    ):
        logger.warning(
            "Configuration permission granted through development fallback",
            extra={
                "permission": permission,
                "request_id": get_request_id(
                    request,
                ),
            },
        )

        return

    raise structured_http_error(
        request=request,
        status_code=status.HTTP_403_FORBIDDEN,
        code="CONFIG_PERMISSION_DENIED",
        message=("Für diese Konfigurationsaktion fehlt die Berechtigung."),
        details={
            "required_permission": permission,
        },
    )


# ============================================================
# JSON-Normalisierung
# ============================================================


def normalize_config_value(
    value: object,
    *,
    path: str = "value",
) -> ConfigValue:
    """
    Konvertiert einen unbekannten Servicewert in einen gültigen
    JSON-Konfigurationswert.

    Nicht unterstützte Objekte werden abgelehnt und nicht implizit
    in Strings umgewandelt.
    """

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return value

    if isinstance(
        value,
        float,
    ):
        if not math.isfinite(
            value,
        ):
            raise TypeError(
                f"{path} enthält keine endliche Zahl.",
            )

        return value

    if isinstance(
        value,
        str,
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

        result: dict[
            str,
            ConfigValue,
        ] = {}

        for (
            raw_key,
            raw_value,
        ) in typed_mapping.items():
            if not isinstance(
                raw_key,
                str,
            ):
                raise TypeError(
                    f"{path} enthält einen nicht unterstützten Mapping-Schlüssel.",
                )

            result[raw_key] = normalize_config_value(
                raw_value,
                path=f"{path}.{raw_key}",
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
            raise TypeError(
                f"{path} enthält Binärdaten, die nicht als "
                "Konfigurationswert unterstützt werden.",
            )

        typed_sequence = cast(
            Sequence[object],
            value,
        )

        return [
            normalize_config_value(
                item,
                path=f"{path}[{index}]",
            )
            for (
                index,
                item,
            ) in enumerate(
                typed_sequence,
            )
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
            normalize_config_value(
                item,
                path=f"{path}[{index}]",
            )
            for (
                index,
                item,
            ) in enumerate(
                typed_set,
            )
        ]

    raise TypeError(
        f"{path} besitzt den nicht unterstützten Typ '{type(value).__name__}'.",
    )


def normalize_config_identifier(
    identifier: object,
) -> ConfigIdentifier | None:
    if not isinstance(
        identifier,
        tuple,
    ):
        return None

    typed_identifier = cast(
        tuple[object, ...],
        identifier,
    )

    if (
        len(
            typed_identifier,
        )
        != 2
    ):
        return None

    raw_group = typed_identifier[0]
    raw_key = typed_identifier[1]

    if not isinstance(
        raw_group,
        str,
    ):
        return None

    if not isinstance(
        raw_key,
        str,
    ):
        return None

    group = raw_group.strip().lower()
    key = raw_key.strip().lower()

    if not group or not key:
        return None

    return (
        group,
        key,
    )


# ============================================================
# Settings-Katalog als Schreib-Policy
# ============================================================


@lru_cache(
    maxsize=1,
)
def get_settings_field_map() -> dict[
    ConfigIdentifier,
    SettingsFieldDescriptor,
]:
    """
    Erzeugt die serverseitige Schreib-Policy aus dem Settings-Katalog.

    Nur Felder mit:

    - source=config
    - editable=true
    - config_group
    - config_key

    dürfen über die generische Config-API verändert werden.
    """

    catalog = build_settings_catalog()

    result: dict[
        ConfigIdentifier,
        SettingsFieldDescriptor,
    ] = {}

    for settings_group in catalog.groups:
        for section in settings_group.sections:
            for field in section.fields:
                if field.source is not SettingsSource.CONFIG:
                    continue

                if not field.editable:
                    continue

                if field.config_group is None:
                    continue

                if field.config_key is None:
                    continue

                group = field.config_group.strip().lower()

                key = field.config_key.strip().lower()

                if not group or not key:
                    continue

                result[
                    (
                        group,
                        key,
                    )
                ] = field

    return result


def get_config_field_descriptor(
    *,
    group: str,
    key: str,
    request: Request,
) -> SettingsFieldDescriptor:
    descriptor = get_settings_field_map().get(
        (
            group,
            key,
        ),
    )

    if descriptor is None:
        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            code="CONFIG_FIELD_NOT_REGISTERED",
            message=(
                "Dieser Konfigurationswert ist nicht im Settings-Katalog registriert."
            ),
            details={
                "group": group,
                "key": key,
            },
        )

    return descriptor


# ============================================================
# Katalogbasierte Validierung
# ============================================================


def validate_confirmation_requirement(
    *,
    descriptor: SettingsFieldDescriptor,
    payload: ConfigUpdateRequest,
    request: Request,
) -> None:
    if not descriptor.requires_confirmation:
        return

    if payload.reason is not None:
        return

    raise structured_http_error(
        request=request,
        status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
        code="CONFIG_CHANGE_REASON_REQUIRED",
        message=(
            "Für diese sicherheits- oder verhaltensrelevante "
            "Änderung ist eine Begründung erforderlich."
        ),
        details={
            "group": descriptor.config_group,
            "key": descriptor.config_key,
            "field_id": descriptor.id,
        },
    )


def raise_invalid_type(
    *,
    descriptor: SettingsFieldDescriptor,
    expected_type: str,
    value: ConfigValue,
    request: Request,
) -> None:
    raise structured_http_error(
        request=request,
        status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
        code="CONFIG_VALUE_TYPE_INVALID",
        message=("Der Konfigurationswert besitzt einen ungültigen Datentyp."),
        details={
            "group": descriptor.config_group,
            "key": descriptor.config_key,
            "expected_type": expected_type,
            "actual_type": type(
                value,
            ).__name__,
        },
    )


def validate_control_type(
    *,
    descriptor: SettingsFieldDescriptor,
    value: ConfigValue,
    request: Request,
) -> None:
    control = descriptor.control

    if control in {
        SettingsControl.TEXT,
        SettingsControl.TEXTAREA,
        SettingsControl.SELECT,
    }:
        if not isinstance(
            value,
            str,
        ):
            raise_invalid_type(
                descriptor=descriptor,
                expected_type="string",
                value=value,
                request=request,
            )

        return

    if control is SettingsControl.BOOLEAN:
        if not isinstance(
            value,
            bool,
        ):
            raise_invalid_type(
                descriptor=descriptor,
                expected_type="boolean",
                value=value,
                request=request,
            )

        return

    if control is SettingsControl.NUMBER:
        numeric_value = normalize_config_number(
            value,
        )

        if numeric_value is None:
            raise_invalid_type(
                descriptor=descriptor,
                expected_type="number",
                value=value,
                request=request,
            )

        return

    if control is SettingsControl.MULTISELECT:
        if not is_config_string_list(
            value,
        ):
            raise_invalid_type(
                descriptor=descriptor,
                expected_type="array[string]",
                value=value,
                request=request,
            )

        return

    raise structured_http_error(
        request=request,
        status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
        code="CONFIG_CONTROL_NOT_EDITABLE",
        message=(
            "Der konfigurierte Darstellungstyp darf "
            "nicht über die generische Config-API "
            "bearbeitet werden."
        ),
        details={
            "group": descriptor.config_group,
            "key": descriptor.config_key,
            "control": control.value,
        },
    )


def validate_allowed_options(
    *,
    descriptor: SettingsFieldDescriptor,
    value: ConfigValue,
    request: Request,
) -> None:
    options = tuple(
        descriptor.options or (),
    )

    if not options:
        return

    allowed_values: frozenset[str] = frozenset(option.value for option in options)

    if descriptor.control is SettingsControl.SELECT:
        if (
            not isinstance(
                value,
                str,
            )
            or value not in allowed_values
        ):
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                code="CONFIG_OPTION_INVALID",
                message=("Der ausgewählte Konfigurationswert ist nicht zulässig."),
                details={
                    "group": descriptor.config_group,
                    "key": descriptor.config_key,
                    "allowed_values": sorted(
                        allowed_values,
                    ),
                },
            )

        return

    if descriptor.control is SettingsControl.MULTISELECT:
        if not is_config_string_list(
            value,
        ):
            return

        invalid_values: list[str] = [
            item for item in value if item not in allowed_values
        ]

        if invalid_values:
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                code="CONFIG_OPTIONS_INVALID",
                message=(
                    "Mindestens ein ausgewählter Konfigurationswert ist nicht zulässig."
                ),
                details={
                    "group": descriptor.config_group,
                    "key": descriptor.config_key,
                    "invalid_values": invalid_values,
                    "allowed_values": sorted(
                        allowed_values,
                    ),
                },
            )


def validate_numeric_range(
    *,
    descriptor: SettingsFieldDescriptor,
    value: ConfigValue,
    request: Request,
) -> None:
    if descriptor.control is not SettingsControl.NUMBER:
        return

    numeric_value = normalize_config_number(
        value,
    )

    if numeric_value is None:
        return

    minimum = descriptor.minimum
    maximum = descriptor.maximum

    if minimum is not None and numeric_value < minimum:
        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            code="CONFIG_VALUE_BELOW_MINIMUM",
            message=(
                "Der Konfigurationswert unterschreitet den erlaubten Mindestwert."
            ),
            details={
                "group": descriptor.config_group,
                "key": descriptor.config_key,
                "minimum": minimum,
                "actual": numeric_value,
            },
        )

    if maximum is not None and numeric_value > maximum:
        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            code="CONFIG_VALUE_ABOVE_MAXIMUM",
            message=("Der Konfigurationswert überschreitet den erlaubten Höchstwert."),
            details={
                "group": descriptor.config_group,
                "key": descriptor.config_key,
                "maximum": maximum,
                "actual": numeric_value,
            },
        )


# ============================================================
# Identitätsvalidierung
# ============================================================


def validate_identity_value(
    *,
    key: str,
    value: ConfigValue,
    request: Request,
) -> ConfigValue:
    """
    Zusätzliche fachliche Validierung der Identitätskonfiguration.
    """

    validated_value = value

    limits = IDENTITY_STRING_LIMITS.get(
        key,
    )

    if limits is not None:
        if not isinstance(
            validated_value,
            str,
        ):
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                code="IDENTITY_VALUE_TYPE_INVALID",
                message=("Der Identitätswert muss eine Zeichenkette sein."),
                details={
                    "key": key,
                    "actual_type": type(
                        validated_value,
                    ).__name__,
                },
            )

        normalized = validated_value.strip()

        (
            minimum_length,
            maximum_length,
        ) = limits

        if (
            len(
                normalized,
            )
            < minimum_length
        ):
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                code="IDENTITY_VALUE_TOO_SHORT",
                message=("Der Identitätswert ist zu kurz."),
                details={
                    "key": key,
                    "minimum_length": minimum_length,
                },
            )

        if (
            len(
                normalized,
            )
            > maximum_length
        ):
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                code="IDENTITY_VALUE_TOO_LONG",
                message=("Der Identitätswert ist zu lang."),
                details={
                    "key": key,
                    "maximum_length": maximum_length,
                },
            )

        validated_value = normalized

    if key == "default_language":
        if not isinstance(
            validated_value,
            str,
        ):
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                code="IDENTITY_LANGUAGE_TYPE_INVALID",
                message=("Die Standardsprache muss als Zeichenkette angegeben werden."),
                details={
                    "key": key,
                },
            )

        if not LANGUAGE_CODE_PATTERN.fullmatch(
            validated_value,
        ):
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                code="IDENTITY_LANGUAGE_INVALID",
                message=(
                    "Die Standardsprache muss als gültiger Sprachcode angegeben werden."
                ),
                details={
                    "key": key,
                    "value": validated_value,
                    "example": "de",
                },
            )

    if key == "timezone":
        if not isinstance(
            validated_value,
            str,
        ):
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                code="IDENTITY_TIMEZONE_TYPE_INVALID",
                message=("Die Zeitzone muss als Zeichenkette angegeben werden."),
                details={
                    "key": key,
                },
            )

        try:
            ZoneInfo(
                validated_value,
            )

        except ZoneInfoNotFoundError as exc:
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                code="IDENTITY_TIMEZONE_INVALID",
                message=("Die angegebene Zeitzone ist keine gültige IANA-Zeitzone."),
                details={
                    "key": key,
                    "value": validated_value,
                    "example": "Europe/Berlin",
                },
            ) from exc

    return validated_value


def validate_catalog_config_value(
    *,
    group: str,
    key: str,
    payload: ConfigUpdateRequest,
    request: Request,
) -> tuple[
    SettingsFieldDescriptor,
    ConfigValue,
]:
    descriptor = get_config_field_descriptor(
        group=group,
        key=key,
        request=request,
    )

    validate_confirmation_requirement(
        descriptor=descriptor,
        payload=payload,
        request=request,
    )

    validate_control_type(
        descriptor=descriptor,
        value=payload.value,
        request=request,
    )

    validate_allowed_options(
        descriptor=descriptor,
        value=payload.value,
        request=request,
    )

    validate_numeric_range(
        descriptor=descriptor,
        value=payload.value,
        request=request,
    )

    validated_value: ConfigValue = payload.value

    if group == "identity":
        validated_value = validate_identity_value(
            key=key,
            value=validated_value,
            request=request,
        )

    return (
        descriptor,
        validated_value,
    )


# ============================================================
# Lesen der Service-Konfiguration
# ============================================================


def add_normalized_entry(
    *,
    target: dict[
        ConfigIdentifier,
        ConfigValue,
    ],
    group: str,
    key: str,
    value: object,
) -> None:
    normalized_group = group.strip().lower()
    normalized_key = key.strip().lower()

    if not normalized_group or not normalized_key:
        return

    try:
        normalized_value = normalize_config_value(
            value,
            path=(f"{normalized_group}.{normalized_key}"),
        )

    except TypeError:
        logger.exception(
            "Ignoring unsupported config value",
            extra={
                "group": normalized_group,
                "key": normalized_key,
                "value_type": type(
                    value,
                ).__name__,
            },
        )

        return

    target[
        (
            normalized_group,
            normalized_key,
        )
    ] = normalized_value


async def read_config_entries(
    service: ConfigService,
    request: Request,
) -> dict[
    ConfigIdentifier,
    ConfigValue,
]:
    """
    Liest Konfigurationswerte über öffentliche Service-Methoden.

    Unterstützt die aktuelle gruppierte ConfigService-Ausgabe:

        {
            "identity": {
                "name": "Kernschmied",
            },
        }

    sowie die ältere flache Darstellung:

        {
            ("identity", "name"): "Kernschmied",
        }
    """

    get_all_value: object = getattr(
        service,
        "get_all",
        None,
    )

    if callable(
        get_all_value,
    ):
        raw_entries: object = get_all_value()

    else:
        list_values_value: object = getattr(
            service,
            "list_values",
            None,
        )

        if not callable(
            list_values_value,
        ):
            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
                code="CONFIG_SERVICE_CONTRACT_UNSUPPORTED",
                message=(
                    "Der Konfigurationsdienst unterstützt "
                    "keine öffentliche Methode zum Auflisten "
                    "der Konfiguration."
                ),
                details={
                    "required_method": "get_all",
                    "alternative_method": "list_values",
                },
            )

        raw_entries = list_values_value()

    resolved_entries = await resolve_maybe_awaitable(
        raw_entries,
    )

    if not isinstance(
        resolved_entries,
        Mapping,
    ):
        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            code="INVALID_CONFIG_SERVICE_RESPONSE",
            message=("Der Konfigurationsdienst hat ein ungültiges Ergebnis geliefert."),
            details={
                "expected_type": "mapping",
                "actual_type": type(
                    resolved_entries,
                ).__name__,
            },
        )

    typed_entries = cast(
        Mapping[object, object],
        resolved_entries,
    )

    normalized_entries: dict[
        ConfigIdentifier,
        ConfigValue,
    ] = {}

    for (
        raw_identifier,
        raw_value,
    ) in typed_entries.items():
        # Aktuelle ConfigService-Struktur:
        #
        # {
        #     "identity": {
        #         "name": "Kernschmied",
        #     },
        # }

        if isinstance(
            raw_identifier,
            str,
        ) and isinstance(
            raw_value,
            Mapping,
        ):
            normalized_group = raw_identifier.strip().lower()

            if not normalized_group:
                logger.warning(
                    "Ignoring empty config group",
                )

                continue

            group_values = cast(
                Mapping[object, object],
                raw_value,
            )

            for (
                raw_key,
                nested_value,
            ) in group_values.items():
                if not isinstance(
                    raw_key,
                    str,
                ):
                    logger.warning(
                        "Ignoring invalid config key",
                        extra={
                            "group": normalized_group,
                            "key": repr(
                                raw_key,
                            ),
                        },
                    )

                    continue

                add_normalized_entry(
                    target=normalized_entries,
                    group=normalized_group,
                    key=raw_key,
                    value=nested_value,
                )

            continue

        # Kompatible ältere Struktur:
        #
        # {
        #     ("identity", "name"): "Kernschmied",
        # }

        identifier = normalize_config_identifier(
            raw_identifier,
        )

        if identifier is None:
            logger.warning(
                "Ignoring invalid config identifier",
                extra={
                    "identifier": repr(
                        raw_identifier,
                    ),
                },
            )

            continue

        (
            group,
            key,
        ) = identifier

        add_normalized_entry(
            target=normalized_entries,
            group=group,
            key=key,
            value=raw_value,
        )

    return normalized_entries


# ============================================================
# API-Ausgabe
# ============================================================


def build_config_items(
    entries: ConfigEntries,
) -> list[ConfigEntryResponse]:
    items: list[ConfigEntryResponse] = []

    field_map = get_settings_field_map()

    for (
        identifier,
        value,
    ) in entries.items():
        (
            group,
            key,
        ) = identifier

        sensitive = is_sensitive_key(
            group,
            key,
        )

        reserved = is_reserved_group(
            group,
        )

        descriptor = field_map.get(
            identifier,
        )

        catalog_editable = (
            descriptor is not None
            and descriptor.editable
            and (descriptor.source is SettingsSource.CONFIG)
        )

        items.append(
            ConfigEntryResponse(
                group=group,
                key=key,
                value=(None if sensitive else value),
                editable=(catalog_editable and not reserved and not sensitive),
                sensitive=sensitive,
                requires_confirmation=(
                    descriptor.requires_confirmation
                    if descriptor is not None
                    else False
                ),
                control=(descriptor.control.value if descriptor is not None else None),
            ),
        )

    items.sort(
        key=lambda entry: (
            entry.group.casefold(),
            entry.key.casefold(),
        ),
    )

    return items


# ============================================================
# Schreiben über den ConfigService
# ============================================================


def build_config_set_kwargs(
    *,
    setter: Callable[..., object],
    payload: ConfigUpdateRequest,
    actor_id: str | None,
    request_id: str | None,
) -> dict[str, object]:
    """
    Baut die optionalen Schlüsselwortargumente anhand der tatsächlich
    unterstützten Signatur des ConfigService.

    Die Kernparameter group, key und value bleiben immer positional.
    """

    try:
        signature = inspect.signature(
            setter,
        )

    except (
        TypeError,
        ValueError,
    ):
        return {
            "expected_revision": payload.expected_revision,
            "actor_id": actor_id,
            "request_id": request_id,
        }

    parameters = signature.parameters

    accepts_var_keyword = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )

    candidate_values: dict[str, object] = {
        "expected_revision": payload.expected_revision,
        "actor_id": actor_id,
        "request_id": request_id,
        "reason": payload.reason,
    }

    return {
        name: value
        for (
            name,
            value,
        ) in candidate_values.items()
        if (accepts_var_keyword or name in parameters)
    }


async def call_config_set(
    *,
    service: ConfigService,
    group: str,
    key: str,
    value: ConfigValue,
    payload: ConfigUpdateRequest,
    request: Request,
) -> None:
    setter_value: object = getattr(
        service,
        "set",
        None,
    )

    if not callable(
        setter_value,
    ):
        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            code="CONFIG_SERVICE_CONTRACT_UNSUPPORTED",
            message=("Der Konfigurationsdienst unterstützt keine Änderungen."),
            details={
                "required_method": "set",
            },
        )

    setter = setter_value

    actor_id = get_actor_id(
        request,
    )

    request_id = get_request_id(
        request,
    )

    setter_kwargs = build_config_set_kwargs(
        setter=setter,
        payload=payload,
        actor_id=actor_id,
        request_id=request_id,
    )

    try:
        raw_result: object = setter(
            group,
            key,
            value,
            **setter_kwargs,
        )

        await resolve_maybe_awaitable(
            raw_result,
        )

    except TypeError as exc:
        logger.error(
            "ConfigService.set does not support the required contract",
            extra={
                "group": group,
                "key": key,
                "request_id": request_id,
                "supported_kwargs": sorted(
                    setter_kwargs,
                ),
            },
        )

        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            code="CONFIG_SERVICE_CONTRACT_UNSUPPORTED",
            message=(
                "Der Konfigurationsdienst unterstützt "
                "den benötigten versionierten "
                "Änderungsvertrag nicht."
            ),
            details={
                "provided_parameters": sorted(
                    setter_kwargs,
                ),
            },
        ) from exc

    except ValueError as exc:
        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            code="CONFIG_VALUE_INVALID",
            message=("Der Konfigurationswert ist ungültig."),
            details={
                "group": group,
                "key": key,
                "reason": str(
                    exc,
                ),
            },
        ) from exc
    except Exception as exc:
        # Special handling for ConfigValidationError from the service
        if isinstance(exc, ConfigValidationError):
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=exc.code,
                message=exc.message,
                details={
                    "group": group,
                    "key": key,
                },
            ) from exc
        raise


# ============================================================
# API-Endpunkte
# ============================================================


@router.get(
    "",
    response_model=ConfigListResponse,
    response_model_exclude_none=False,
    summary="Konfiguration auflisten",
    description=(
        "Liefert die sichtbare Fachkonfiguration und die aktuelle "
        "Revision. Sensible Werte werden nicht ausgegeben."
    ),
)
async def list_config(
    request: Request,
    response: Response,
) -> ConfigListResponse:
    require_config_permission(
        request,
        "config:read",
    )

    service = get_config_service(
        request,
    )

    revision = await get_service_revision(
        service,
    )

    entries = await read_config_entries(
        service,
        request,
    )

    response.headers["Cache-Control"] = "no-store, private"

    response.headers["Pragma"] = "no-cache"

    response.headers["X-Config-Revision"] = str(
        revision,
    )

    response.headers["X-Config-Schema-Version"] = CONFIG_API_SCHEMA_VERSION

    return ConfigListResponse(
        revision=revision,
        items=build_config_items(
            entries,
        ),
        request_id=get_request_id(
            request,
        ),
    )


class BulkConfigUpdateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    values: Mapping[str, Mapping[str, ConfigValue]] = Field(
        default_factory=dict,
        description="Gruppierte Konfigurationswerte als Objekt { group: { key: value } }",
    )

    expected_revision: int | None = Field(
        default=None,
        ge=0,
        description=("Erwartete Revision zur Vermeidung von Race-Conditions."),
    )


@router.put(
    "",
    summary="Mehrere Konfigurationswerte ändern (Bulk)",
    description=(
        "Nimmt ein gruppiertes `values`-Objekt entgegen und speichert alle enthaltenen Werte in einer Transaktion."
    ),
)
async def bulk_update_config(
    payload: BulkConfigUpdateRequest,
    request: Request,
    response: Response,
) -> dict[str, object]:
    require_config_permission(
        request,
        "config:write",
    )

    service = get_config_service(request)

    # Flatten grouped values into mapping of (group,key) -> value
    updates: dict[tuple[str, str], object] = {}

    for raw_group, raw_group_value in payload.values.items():
        # Payload is already validated to Mapping[str, Mapping[str, ConfigValue]]
        for raw_key, raw_value in raw_group_value.items():
            updates[(raw_group.strip().lower(), raw_key.strip().lower())] = raw_value

    try:
        # Dispatch to service.set_many (supports validation and atomic commit)
        await service.set_many(
            updates,
            expected_revision=payload.expected_revision,
        )
    except ConfigValidationError as exc:
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=exc.code,
            message=exc.message,
            details={},
        ) from exc

    # Return the current configuration values (grouped) and revision
    revision = await get_service_revision(service)

    entries = await read_config_entries(service, request)

    grouped: dict[str, dict[str, object]] = {}

    for (group, key), value in entries.items():
        grouped.setdefault(group, {})[key] = value

    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Config-Revision"] = str(revision)
    response.headers["X-Config-Schema-Version"] = CONFIG_API_SCHEMA_VERSION

    return {"values": grouped, "revision": revision}


@router.put(
    "/{group}/{key}",
    response_model=ConfigUpdateResponse,
    summary="Konfigurationswert ändern",
    description=(
        "Ändert einen registrierten, runtime-editierbaren "
        "Konfigurationswert. Die Änderung wird anhand des "
        "Settings-Katalogs validiert, versioniert und protokolliert."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": ("Konfiguration wurde aktualisiert."),
        },
        status.HTTP_403_FORBIDDEN: {
            "description": ("Keine Berechtigung für die Änderung."),
        },
        status.HTTP_409_CONFLICT: {
            "description": ("Die Konfiguration wurde zwischenzeitlich geändert."),
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": ("Gruppe, Schlüssel oder Wert ist ungültig."),
        },
    },
)
async def update_config(
    group: str,
    key: str,
    payload: ConfigUpdateRequest,
    request: Request,
    response: Response,
) -> ConfigUpdateResponse:
    require_config_permission(
        request,
        "config:write",
    )

    normalized_group = validate_config_name(
        group,
        field_name="group",
        request=request,
    )

    normalized_key = validate_config_name(
        key,
        field_name="key",
        request=request,
    )

    if is_reserved_group(
        normalized_group,
    ):
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_403_FORBIDDEN,
            code="CONFIG_GROUP_NOT_RUNTIME_EDITABLE",
            message=(
                "Diese Konfigurationsgruppe darf nicht zur Laufzeit bearbeitet werden."
            ),
            details={
                "group": normalized_group,
                "key": normalized_key,
            },
        )

    if is_sensitive_key(
        normalized_group,
        normalized_key,
    ):
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_403_FORBIDDEN,
            code="SENSITIVE_CONFIG_NOT_ALLOWED",
            message=(
                "Sensible Werte dürfen nicht über "
                "die Fachkonfiguration gespeichert werden."
            ),
            details={
                "group": normalized_group,
                "key": normalized_key,
            },
        )

    (
        descriptor,
        validated_value,
    ) = validate_catalog_config_value(
        group=normalized_group,
        key=normalized_key,
        payload=payload,
        request=request,
    )

    service = get_config_service(
        request,
    )

    current_revision = await get_service_revision(
        service,
    )

    if payload.expected_revision is not None and (
        payload.expected_revision != current_revision
    ):
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_409_CONFLICT,
            code="CONFIG_REVISION_CONFLICT",
            message=(
                "Die Konfiguration wurde zwischenzeitlich "
                "geändert. Bitte laden Sie die aktuellen "
                "Werte erneut."
            ),
            details={
                "group": normalized_group,
                "key": normalized_key,
                "expected_revision": (payload.expected_revision),
                "current_revision": current_revision,
            },
        )

    await call_config_set(
        service=service,
        group=normalized_group,
        key=normalized_key,
        value=validated_value,
        payload=payload,
        request=request,
    )

    new_revision = await get_service_revision(
        service,
        default=(current_revision + 1),
    )

    if new_revision <= current_revision:
        new_revision = current_revision + 1

    response.headers["Cache-Control"] = "no-store, private"

    response.headers["Pragma"] = "no-cache"

    response.headers["X-Config-Revision"] = str(
        new_revision,
    )

    response.headers["X-Config-Schema-Version"] = CONFIG_API_SCHEMA_VERSION

    logger.info(
        "Configuration value updated",
        extra={
            "group": normalized_group,
            "key": normalized_key,
            "field_id": descriptor.id,
            "control": descriptor.control.value,
            "revision": new_revision,
            "actor_id": get_actor_id(
                request,
            ),
            "request_id": get_request_id(
                request,
            ),
            "reason": payload.reason,
        },
    )

    return ConfigUpdateResponse(
        group=normalized_group,
        key=normalized_key,
        revision=new_revision,
        request_id=get_request_id(
            request,
        ),
    )
