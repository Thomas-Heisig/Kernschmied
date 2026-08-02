# F:\Kernschmied\backend\app\api\v1\configs.py

from __future__ import annotations

import inspect
import logging
import math
import re
from collections.abc import (
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
    TypedDict,
    cast,
)
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
import os

# Use a typed compatibility constant for the problematic 422 name so
# Pylance can statically resolve the type. The actual integer value is
# exported from `app.status_compat`.
from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT
from pydantic import (
    JsonValue,
)

from app.config.service import ConfigValidationError, ConfigService
from app.core.security_profile import get_security_profile
from app.schemas.settings_catalog import (
    SettingsControl,
    SettingsFieldDescriptor,
    SettingsSource,
    SettingsAvailability,
)
from app.services.settings_catalog import build_settings_catalog
from app.config.definitions import get_config_definition
from app.schemas.configuration import (
    ConfigDynamicOptionsResponse,
    ConfigEntryResponse,
    ConfigGroupResponse,
    ConfigListResponse,
    ConfigOptionResponse,
    ConfigUIResponse,
)

# small utilities reused across api modules
from .tools import read_mapping_value

# Import a small set of service helpers used by this module. We avoid
# importing symbols that are implemented locally to prevent shadowing.
from .configs_service import (
    get_config_service,
    resolve_maybe_awaitable,
    get_service_revision,
)

# Validation helpers are defined in this module (kept local for clarity)

# Service helpers moved to configs_service module
# Service helpers are implemented within this module; avoid importing
# duplicate symbols from `configs_service` which would shadow local
# definitions and confuse static analysis.

# Import request/response schema models from local module
from .configs_schema import (
    ConfigUpdateRequest,
    ConfigUpdateResponse,
    ConfigChangeItem,
    BulkConfigUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Compatibility: some starlette/fastapi versions expose
# `HTTP_422_UNPROCESSABLE_ENTITY` but not the legacy
# `HTTP_422_UNPROCESSABLE_CONTENT` constant. Add the
# attribute only if it's missing and log failures to help
# diagnose reload/import issues.
try:
    if not hasattr(status, "HTTP_422_UNPROCESSABLE_CONTENT"):
        setattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", HTTP_422_UNPROCESSABLE_CONTENT)
except Exception as exc:
    logger.debug(
        "Could not assign status.HTTP_422_UNPROCESSABLE_CONTENT: %s",
        exc,
    )


# ============================================================
# Öffentlicher Config-Vertrag
# ============================================================

CONFIG_API_SCHEMA_VERSION = "2.0"

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
    request: Request | None,
    status_code: int,
    code: str,
    message: str,
    details: Mapping[str, object] | None = None,
) -> HTTPException:
    normalized_details: dict[str, object] = (dict(details) if details is not None else {})

    request_id = get_request_id(request) if request is not None else None

    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "details": normalized_details,
            "request_id": request_id,
        },
    )


def get_principal(
    request: Request,
) -> object | None:
    """Return the principal object stored in request.state by auth middleware."""

    candidates = (
        "principal",
        "user",
        "authenticated_principal",
        "authenticated_user",
        "session_user",
    )

    for name in candidates:
        principal = getattr(request.state, name, None)

        if principal is not None:
            return principal

    return None


def normalize_optional_identifier(value: object) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    return normalized or None


def validate_config_name(value: object, *, field_name: str = "value", request: Request | None = None) -> str:
    if not isinstance(value, str):
        raise structured_http_error(
            request=request,
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            code="CONFIG_NAME_INVALID",
            message=("Der Konfigurationsname ist ungültig."),
            details={"field": field_name},
        )

    # `isinstance` above ensures `value` is a `str` for static analysis

    normalized = value.strip().lower()

    if not CONFIG_NAME_PATTERN.fullmatch(normalized):
        raise structured_http_error(
            request=request,
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            code="CONFIG_NAME_INVALID",
            message=("Der Konfigurationsname erfüllt nicht das erforderliche Format."),
            details={"field": field_name, "value": value},
        )

    return normalized


def is_reserved_group(group: str) -> bool:
    return group.strip().lower() in RESERVED_GROUPS


def is_sensitive_key(group: str, key: str) -> bool:
    if group.strip().lower() in {"secrets", "security_secrets"}:
        return True

    lowered = key.strip().lower()

    for part in SENSITIVE_KEY_PARTS:
        if part in lowered:
            return True

    return False


def get_actor_id(
    request: Request,
) -> str | None:
    principal = get_principal(
        request,
    )

    if principal is None:
        return None

    from typing import cast
    actor_id = read_mapping_value(
        cast(Mapping[object, object], principal),
        "id",
    )

    if actor_id is None:
        actor_id = read_mapping_value(
            cast(Mapping[object, object], principal),
            "user_id",
        )

    if actor_id is None:
        actor_id = read_mapping_value(
            cast(Mapping[object, object], principal),
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

    from typing import cast
    raw_permissions = read_mapping_value(
        cast(Mapping[object, object], principal),
        "permissions",
        [],
    )

    raw_roles = read_mapping_value(
        cast(Mapping[object, object], principal),
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
        # Developer helper: allow unregistered config keys when explicitly enabled
        # via the environment variable `ALLOW_UNREGISTERED_CONFIGS=1`.
        if os.environ.get("ALLOW_UNREGISTERED_CONFIGS") == "1":
            # Synthesize a permissive descriptor for local testing.
            return SettingsFieldDescriptor(
                id=f"dev-{group}-{key}",
                title=f"Dev: {group}.{key}",
                description="Automatically created test descriptor (dev only)",
                source=SettingsSource.CONFIG,
                availability=SettingsAvailability.AVAILABLE,
                control=SettingsControl.TEXT,
                config_group=group,
                config_key=key,
                editable=True,
            )

        raise structured_http_error(
            request=request,
            status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
        status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
        status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
        status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
            status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
            status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="IDENTITY_VALUE_TYPE_INVALID",
                message=("Der Identitätswert muss eine Zeichenkette sein."),
                details={
                    "key": key,
                    "actual_type": type(
                        validated_value,
                    ).__name__,
                },
            )

        # `isinstance` above ensures `validated_value` is a `str`
        normalized = str(validated_value).strip()

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
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="IDENTITY_LANGUAGE_TYPE_INVALID",
                message=("Die Standardsprache muss als Zeichenkette angegeben werden."),
                details={
                    "key": key,
                },
            )

        # `isinstance` above ensures `validated_value` is a `str`
        if not LANGUAGE_CODE_PATTERN.fullmatch(
            str(validated_value),
        ):
            raise structured_http_error(
                request=request,
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="IDENTITY_TIMEZONE_TYPE_INVALID",
                message=("Die Zeitzone muss als Zeichenkette angegeben werden."),
                details={
                    "key": key,
                },
            )

        # `isinstance` above ensures `validated_value` is a `str`
        try:
            ZoneInfo(
                str(validated_value),
            )

        except ZoneInfoNotFoundError as exc:
            raise structured_http_error(
                request=request,
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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


def build_config_groups(entries: ConfigEntries) -> list[ConfigGroupResponse]:
    """
    Erzeugt gruppierte Config-Antworten basierend auf dem Settings-Katalog
    und den aktuell gespeicherten Werten. Fehlende Katalogeinträge werden
    als minimale Einträge mit den gespeicherten Werten dargestellt.
    """

    catalog = build_settings_catalog()

    # helper typed dict for builders
    class _GroupBuilder(TypedDict):
        id: str
        label: str
        description: str | None
        order: int
        entries: list[ConfigEntryResponse]

    # map of group id -> builder
    groups: dict[str, _GroupBuilder] = {}

    # prepare groups from catalog (use normalized lower-case keys)
    for g in catalog.groups:
        group_id = (g.id or "").strip().lower()
        if not group_id:
            continue

        groups[group_id] = {
            "id": g.id,
            "label": g.title,
            "description": g.description,
            "order": g.order,
            "entries": [],
        }

        for section in g.sections:
            for field in section.fields:
                cfg_group = (field.config_group or g.id or "").strip().lower()
                cfg_key = (field.config_key or "").strip().lower()

                if not cfg_group or not cfg_key:
                    continue

                value = entries.get((cfg_group, cfg_key))

                # Prefer authoritative ConfigDefinition metadata when available
                definition = None
                try:
                    definition = get_config_definition(cfg_group, cfg_key)
                except KeyError:
                    definition = None

                if definition is not None:
                    # build options from definition UI
                    options = [
                        ConfigOptionResponse(value=o.value, label=o.label, description=(o.description if hasattr(o, "description") else None), disabled=False)
                        for o in getattr(definition.ui, "options", ())
                    ]

                    # dynamic options (safe access)
                    dyn = None
                    d = getattr(definition.ui, "dynamic_options", None)
                    if d is not None:
                        src = getattr(d, "source", None)
                        src_val = src.value if (src is not None and hasattr(src, "value")) else "server"
                        endpoint_val = getattr(d, "endpoint", None)
                        dyn = ConfigDynamicOptionsResponse(source=src_val, endpoint=endpoint_val)

                    # UI fields (safe access and fallbacks)
                    comp = getattr(definition.ui, "component", None)
                    comp_val = comp.value if (comp is not None and hasattr(comp, "value")) else None
                    category_val = definition.ui.category or g.id
                    section_val = definition.ui.section or section.id
                    order_val = getattr(definition.ui, "order", None)
                    if order_val is None:
                        order_val = 0
                    placeholder_val = getattr(definition.ui, "placeholder", None)
                    help_text_val = definition.ui.help_text or field.description
                    unit_val = getattr(definition.ui, "unit", None)
                    advanced_val = bool(getattr(definition.ui, "advanced", False))
                    hidden_val = bool(getattr(definition.ui, "hidden", False))
                    readonly_val = bool(getattr(definition.ui, "readonly", False))

                    ui = ConfigUIResponse(
                        component=comp_val,
                        category=category_val,
                        section=section_val,
                        order=order_val,
                        placeholder=placeholder_val,
                        help_text=help_text_val,
                        unit=unit_val,
                        advanced=advanced_val,
                        hidden=hidden_val,
                        readonly=readonly_val,
                        options=options,
                        dynamic_options=dyn,
                    )

                    entry = ConfigEntryResponse(
                        group=cfg_group,
                        key=cfg_key,
                        full_key=f"{cfg_group}.{cfg_key}",
                        display_name=definition.display_name,
                        description=definition.description or "",
                        value=(value if not is_sensitive_key(cfg_group, cfg_key) else None),
                        default_value=definition.default_value,
                        schema_version=definition.schema_version or CONFIG_API_SCHEMA_VERSION,
                        # safe access to optional value_type
                        value_type=(getattr(definition.value_type, "name", None) if getattr(definition, "value_type", None) is not None else None),
                        value_schema=(definition.value_schema or {}),
                        editable=definition.runtime_editable,
                        sensitive=definition.is_secret,
                        secret_configured=False,
                        requires_restart=definition.requires_restart,
                        runtime_editable=definition.runtime_editable,
                        nullable=definition.nullable,
                        visibility=(getattr(definition.visibility, "value", "") if getattr(definition, "visibility", None) is not None else ""),
                        allowed_scopes=[(s.value if hasattr(s, "value") else s) for s in getattr(definition, "allowed_scopes", [])],
                        current_scope="application",
                        ui=ui,
                        permissions=(
                            ConfigEntryResponse.ConfigPermissionsResponse(
                                read=getattr(definition.permissions, "read"),
                                write=getattr(definition.permissions, "write"),
                                reveal_secret=getattr(definition.permissions, "reveal_secret", None),
                            )
                            if getattr(definition, "permissions", None) is not None
                            and getattr(definition.permissions, "read", None) is not None
                            and getattr(definition.permissions, "write", None) is not None
                            else None
                        ),
                        deprecated=definition.deprecated,
                    )
                else:
                    # build UI from catalog fallback
                    options: list[ConfigOptionResponse] = []
                    for opt in field.options:
                        options.append(
                            ConfigOptionResponse(
                                value=opt.value,
                                label=opt.label,
                                description=None,
                                disabled=False,
                            )
                        )

                    dynamic_options = None
                    if field.endpoint:
                        dynamic_options = ConfigDynamicOptionsResponse(
                            source="server",
                            endpoint=field.endpoint,
                        )

                    ui = ConfigUIResponse(
                        component=None,
                        category=g.id,
                        section=section.id,
                        order=field.order,
                        placeholder=None,
                        help_text=field.description,
                        unit=None,
                        advanced=False,
                        hidden=False,
                        readonly=not field.editable,
                        options=options,
                        dynamic_options=dynamic_options,
                    )

                    entry = ConfigEntryResponse(
                        group=cfg_group,
                        key=cfg_key,
                        full_key=f"{cfg_group}.{cfg_key}",
                        display_name=field.title,
                        description=field.description or "",
                        value=(value if not is_sensitive_key(cfg_group, cfg_key) else None),
                        default_value=None,
                        schema_version=CONFIG_API_SCHEMA_VERSION,
                        value_type=None,
                        value_schema={},
                        editable=field.editable,
                        sensitive=field.sensitive,
                        secret_configured=False,
                        requires_restart=field.restart_required,
                        runtime_editable=field.editable,
                        nullable=True,
                        visibility="visible",
                        allowed_scopes=[],
                        current_scope="application",
                        ui=ui,
                        permissions=ConfigEntryResponse.ConfigPermissionsResponse(
                            read="config:read",
                            write="config:write",
                            reveal_secret=None,
                        ),
                        deprecated=False,
                    )

                # Ensure the group exists (normalized key used)
                if cfg_group not in groups:
                    groups[cfg_group] = {
                        "id": cfg_group,
                        "label": cfg_group,
                        "description": None,
                        "order": 1000,
                        "entries": [],
                    }

                groups[cfg_group]["entries"].append(entry)

    # include stored entries not present in the catalog
    for (group, key), value in entries.items():
        if group in groups and any(e.key == key for e in groups[group]["entries"]):
            continue

        sensitive = is_sensitive_key(group, key)

        ui = ConfigUIResponse()

        entry = ConfigEntryResponse(
            group=group,
            key=key,
            full_key=f"{group}.{key}",
            display_name=key,
            description="",
            value=(None if sensitive else value),
            default_value=None,
            schema_version=CONFIG_API_SCHEMA_VERSION,
            value_type=None,
            value_schema={},
            editable=False,
            sensitive=sensitive,
            secret_configured=False,
            requires_restart=False,
            runtime_editable=False,
            nullable=True,
            visibility="visible",
            allowed_scopes=[],
            current_scope="application",
            ui=ui,
            permissions=ConfigEntryResponse.ConfigPermissionsResponse(
                read="config:read",
                write="config:write",
                reveal_secret=None,
            ),
            deprecated=False,
        )

        if group not in groups:
            groups[group] = {
                "id": group,
                "label": group,
                "description": None,
                "order": 1000,
                "entries": [entry],
            }
        else:
            groups[group]["entries"].append(entry)

    # convert to ConfigGroupResponse list
    result: list[ConfigGroupResponse] = []
    for g in groups.values():
        result.append(
            ConfigGroupResponse(
                id=g["id"],
                label=g["label"],
                description=g["description"],
                order=g["order"],
                entries=g["entries"],
            )
        )

    result.sort(key=lambda grp: (grp.order, grp.id.casefold()))

    return result


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
            status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
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
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                code=exc.code,
                message=exc.message,
                details={
                    "group": group,
                    "key": key,
                },
            ) from exc
        # Log unexpected exceptions and return a controlled 500 response
        logger.exception(
            "Unexpected error while calling ConfigService.set",
            extra={"group": group, "key": key, "request_id": get_request_id(request)},
        )
        raise structured_http_error(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message=("Bei der Verarbeitung der Anfrage ist ein interner Fehler aufgetreten."),
            details={
                "group": group,
                "key": key,
            },
        ) from exc


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
        groups=build_config_groups(entries),
        request_id=get_request_id(request),
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

    # Flatten into mapping of (group,key) -> value. Support either `values` or `changes`.
    updates: dict[tuple[str, str], object] = {}

    changes_list: list[ConfigChangeItem] = payload.changes
    if changes_list:
        for change in changes_list:
            updates[(change.group.strip().lower(), change.key.strip().lower())] = change.value
    else:
        for raw_group, raw_group_value in payload.values.items():
            # Payload is already validated to Mapping[str, Mapping[str, ConfigValue]]
            normalized_group = raw_group.strip().lower()
            for raw_key, raw_value in raw_group_value.items():
                updates[(normalized_group, raw_key.strip().lower())] = raw_value

    try:
        # Dispatch to service.set_many (supports validation and atomic commit)
        await service.set_many(
            updates,
            expected_revision=payload.expected_revision,
        )
    except ConfigValidationError as exc:
        raise structured_http_error(
            request=request,
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
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
        HTTP_422_UNPROCESSABLE_CONTENT: {
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