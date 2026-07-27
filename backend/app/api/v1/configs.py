# F:\Kernschmied\backend\app\api\v1\configs.py

from __future__ import annotations

import inspect
import logging
import re
from collections.abc import (
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from enum import StrEnum
from typing import Literal, TypeAlias, cast
from uuid import UUID

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
    JsonValue,          # <-- NEU: Pydantic's JsonValue
    field_validator,
)

from app.core.security_profile import get_security_profile


logger = logging.getLogger(__name__)

router = APIRouter()


CONFIG_API_SCHEMA_VERSION = "1.1"

CONFIG_NAME_PATTERN = re.compile(
    r"^[a-z][a-z0-9_-]{0,63}$",
)

RESERVED_GROUPS: frozenset[str] = frozenset(
    {
        "bootstrap",
        "infrastructure",
        "security",
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


# Eigene rekursive Definition ENTFERNEN – stattdessen Pydantic's JsonValue verwenden
ConfigScalar = str | int | float | bool | None
ConfigValue = JsonValue                    # JsonValue kommt jetzt aus pydantic
ConfigIdentifier: TypeAlias = tuple[str, str]
ConfigEntries: TypeAlias = Mapping[ConfigIdentifier, ConfigValue]

DynamicCallable: TypeAlias = Callable[..., object]


class ConfigOperationStatus(StrEnum):
    UPDATED = "updated"


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
        description="Optionale Begründung für das Audit-Log.",
    )

    @field_validator("reason")
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
        dict(details)
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


def get_config_service(
    request: Request,
) -> object:
    service: object = getattr(
        request.app.state,
        "config_service",
        None,
    )

    if service is None:
        raise structured_http_error(
            request=request,
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            code="CONFIG_SERVICE_UNAVAILABLE",
            message=(
                "Der Konfigurationsdienst ist nicht verfügbar."
            ),
        )

    return service


async def resolve_maybe_awaitable(
    value: object,
) -> object:
    if inspect.isawaitable(value):
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
    if isinstance(value, bool):
        return int(value)

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


async def get_service_revision(
    service: object,
    *,
    default: int = 0,
) -> int:
    revision_getter: object = getattr(
        service,
        "get_revision",
        None,
    )

    if callable(revision_getter):
        try:
            raw_revision = revision_getter()
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
            return default

    revision_value: object = getattr(
        service,
        "revision",
        default,
    )

    if inspect.isawaitable(revision_value):
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
            return default

    return normalize_revision(
        revision_value,
        default=default,
    )


def validate_config_name(
    value: str,
    *,
    field_name: Literal["group", "key"],
    request: Request,
) -> str:
    normalized = value.strip().lower()

    if not CONFIG_NAME_PATTERN.fullmatch(
        normalized,
    ):
        raise structured_http_error(
            request=request,
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            code="INVALID_CONFIG_IDENTIFIER",
            message=(
                f"Der Konfigurationsbezeichner "
                f"'{field_name}' ist ungültig."
            ),
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

    return any(
        part in normalized
        for part in SENSITIVE_KEY_PARTS
    )


def is_reserved_group(
    group: str,
) -> bool:
    return group.lower() in RESERVED_GROUPS


def read_mapping_value(
    source: object,
    key: str,
    default: object = None,
) -> object:
    if isinstance(source, Mapping):
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

    if isinstance(value, UUID):
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
    """
    Liest den durch die Authentifizierungs-Middleware gesetzten
    Benutzerbezeichner.

    Unterstützt sowohl Mapping- als auch Objekt-Principals.
    """

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

    if isinstance(value, str):
        normalized = value.strip()

        return {
            normalized,
        } if normalized else set()

    if isinstance(value, Mapping):
        return set()

    if isinstance(value, Sequence):
        items: Sequence[object] = cast(
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

    raw_permissions: object = read_mapping_value(
        principal,
        "permissions",
        [],
    )

    raw_roles: object = read_mapping_value(
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
    }.intersection(roles):
        permissions.add(
            "*",
        )

    return permissions


def development_fallback_allowed(
    request: Request,
) -> bool:
    """
    Der vereinfachte lokale Zugriff ist ausschließlich im festen
    Development-Sicherheitsprofil zulässig.

    Die Datenbankkonfiguration darf diese Sicherheitsgrenze nicht
    verändern oder abschwächen.
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
        str(raw_environment).strip().lower()
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

    if (
        "*" in permissions
        or permission in permissions
    ):
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
        message=(
            "Für diese Konfigurationsaktion fehlt "
            "die Berechtigung."
        ),
        details={
            "required_permission": permission,
        },
    )


def normalize_config_value(
    value: object,
    *,
    path: str = "value",
) -> ConfigValue:
    """
    Wandelt einen unbekannten Servicewert in den erlaubten
    ConfigValue-Vertrag um.

    Nicht unterstützte Objekte werden sichtbar abgelehnt und nicht
    stillschweigend per `str()` serialisiert.
    """

    if value is None:
        return None

    if isinstance(
        value,
        str | int | float | bool,
    ):
        return value

    if isinstance(value, Mapping):
        typed_mapping = cast(
            Mapping[object, object],
            value,
        )

        result: dict[str, ConfigValue] = {}

        for raw_key, raw_value in typed_mapping.items():
            if not isinstance(raw_key, str):
                raise TypeError(
                    f"{path} enthält einen nicht unterstützten "
                    "Mapping-Schlüssel."
                )

            result[raw_key] = normalize_config_value(
                raw_value,
                path=f"{path}.{raw_key}",
            )

        return result

    if isinstance(value, Sequence):
        if isinstance(
            value,
            bytes | bytearray,
        ):
            raise TypeError(
                f"{path} enthält Binärdaten, die nicht als "
                "Konfigurationswert unterstützt werden."
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
            for index, item in enumerate(
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
            for index, item in enumerate(
                typed_set,
            )
        ]

    raise TypeError(
        f"{path} besitzt den nicht unterstützten Typ "
        f"'{type(value).__name__}'."
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

    if len(typed_identifier) != 2:
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

    group = raw_group.strip()
    key = raw_key.strip()

    if not group or not key:
        return None

    return (
        group,
        key,
    )


async def read_config_entries(
    service: object,
    request: Request,
) -> dict[ConfigIdentifier, ConfigValue]:
    """
    Verwendet ausschließlich öffentliche Lesemethoden.

    Bevorzugt wird `get_all()`. `list_values()` wird als kompatible
    Alternative unterstützt. Beide Methoden dürfen synchron oder
    asynchron implementiert sein.
    """

    get_all_value: object = getattr(
        service,
        "get_all",
        None,
    )

    if callable(get_all_value):
        raw_entries = get_all_value()

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
                status_code=(
                    status.HTTP_503_SERVICE_UNAVAILABLE
                ),
                code=(
                    "CONFIG_SERVICE_CONTRACT_UNSUPPORTED"
                ),
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
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            code="INVALID_CONFIG_SERVICE_RESPONSE",
            message=(
                "Der Konfigurationsdienst hat ein "
                "ungültiges Ergebnis geliefert."
            ),
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

    for raw_identifier, raw_value in typed_entries.items():
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

        group, key = identifier

        try:
            normalized_value = normalize_config_value(
                raw_value,
                path=f"{group}.{key}",
            )

        except TypeError:
            logger.exception(
                "Ignoring unsupported config value",
                extra={
                    "group": group,
                    "key": key,
                    "value_type": type(
                        raw_value,
                    ).__name__,
                },
            )
            continue

        normalized_entries[identifier] = (
            normalized_value
        )

    return normalized_entries


def build_config_items(
    entries: ConfigEntries,
) -> list[ConfigEntryResponse]:
    items: list[ConfigEntryResponse] = []

    for identifier, value in entries.items():
        group, key = identifier

        sensitive = is_sensitive_key(
            group,
            key,
        )

        reserved = is_reserved_group(
            group,
        )

        items.append(
            ConfigEntryResponse(
                group=group,
                key=key,
                value=(
                    None
                    if sensitive
                    else value
                ),
                editable=(
                    not reserved
                    and not sensitive
                ),
                sensitive=sensitive,
            ),
        )

    items.sort(
        key=lambda entry: (
            entry.group.casefold(),
            entry.key.casefold(),
        ),
    )

    return items


async def call_config_set(
    *,
    service: object,
    group: str,
    key: str,
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
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            code="CONFIG_SERVICE_CONTRACT_UNSUPPORTED",
            message=(
                "Der Konfigurationsdienst unterstützt "
                "keine Änderungen."
            ),
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

    try:
        raw_result = setter(
            group,
            key,
            payload.value,
            expected_revision=(
                payload.expected_revision
            ),
            actor_id=actor_id,
            request_id=request_id,
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
            },
        )

        raise structured_http_error(
            request=request,
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            code=(
                "CONFIG_SERVICE_CONTRACT_UNSUPPORTED"
            ),
            message=(
                "Der Konfigurationsdienst unterstützt "
                "den benötigten versionierten "
                "Änderungsvertrag noch nicht."
            ),
            details={
                "required_parameters": [
                    "expected_revision",
                    "actor_id",
                    "request_id",
                ],
            },
        ) from exc

    except ValueError as exc:
        raise structured_http_error(
            request=request,
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            code="CONFIG_VALUE_INVALID",
            message=(
                "Der Konfigurationswert ist ungültig."
            ),
            details={
                "group": group,
                "key": key,
                "reason": str(
                    exc,
                ),
            },
        ) from exc


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

    response.headers["Cache-Control"] = (
        "no-store, private"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Config-Revision"] = str(
        revision,
    )
    response.headers["X-Config-Schema-Version"] = (
        CONFIG_API_SCHEMA_VERSION
    )

    return ConfigListResponse(
        revision=revision,
        items=build_config_items(
            entries,
        ),
        request_id=get_request_id(
            request,
        ),
    )


@router.put(
    "/{group}/{key}",
    response_model=ConfigUpdateResponse,
    summary="Konfigurationswert ändern",
    description=(
        "Ändert einen runtime-editierbaren Konfigurationswert. "
        "Die Änderung muss durch den ConfigService validiert, "
        "versioniert und protokolliert werden."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Konfiguration wurde aktualisiert."
            ),
        },
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "Keine Berechtigung für die Änderung."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "Die Konfiguration wurde "
                "zwischenzeitlich geändert."
            ),
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": (
                "Gruppe, Schlüssel oder Wert ist ungültig."
            ),
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
                "Diese Konfigurationsgruppe darf "
                "nicht zur Laufzeit bearbeitet werden."
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

    service = get_config_service(
        request,
    )

    current_revision = await get_service_revision(
        service,
    )

    if (
        payload.expected_revision is not None
        and payload.expected_revision
        != current_revision
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
                "expected_revision": (
                    payload.expected_revision
                ),
                "current_revision": current_revision,
            },
        )

    await call_config_set(
        service=service,
        group=normalized_group,
        key=normalized_key,
        payload=payload,
        request=request,
    )

    new_revision = await get_service_revision(
        service,
        default=current_revision + 1,
    )

    if new_revision <= current_revision:
        new_revision = current_revision + 1

    response.headers["Cache-Control"] = (
        "no-store, private"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Config-Revision"] = str(
        new_revision,
    )
    response.headers["X-Config-Schema-Version"] = (
        CONFIG_API_SCHEMA_VERSION
    )

    logger.info(
        "Configuration value updated",
        extra={
            "group": normalized_group,
            "key": normalized_key,
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