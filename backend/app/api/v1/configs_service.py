from __future__ import annotations

import inspect
import logging
import os
from collections.abc import Awaitable, Mapping
from functools import lru_cache
from typing import Callable, cast

from fastapi import Request, status

from app.config.service import ConfigService, ConfigValidationError

from app.services.settings_catalog import build_settings_catalog
from app.schemas.settings_catalog import (
    SettingsControl,
    SettingsFieldDescriptor,
    SettingsSource,
    SettingsAvailability,
)
from app.config.definitions import get_config_definition
from app.schemas.configuration import (
    ConfigDynamicOptionsResponse,
    ConfigEntryResponse,
    ConfigGroupResponse,
    ConfigOptionResponse,
    ConfigUIResponse,
)
from .configs_schema import ConfigUpdateRequest
from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT

logger = logging.getLogger(__name__)


# Functions that provide controlled access to the ConfigService and the
# settings catalog. These were extracted from the original `configs.py`
# to keep the router handlers focused on HTTP concerns.


def get_config_service(request: Request) -> ConfigService:
    service = getattr(request.app.state, "config_service", None)

    if service is None:
        from .configs import structured_http_error

        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            code="CONFIG_SERVICE_UNAVAILABLE",
            message=("Der Konfigurationsdienst ist nicht verfügbar."),
        )

    return cast(ConfigService, service)


async def resolve_maybe_awaitable(value: object) -> object:
    if inspect.isawaitable(value):
        return await cast(Awaitable[object], value)

    return value


def normalize_revision(value: object, *, default: int = 0) -> int:
    # keep a lightweight local copy used by get_service_revision
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return max(value, 0)

    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return default
        try:
            parsed = int(normalized)
        except ValueError:
            return default
        return max(parsed, 0)

    return default


async def get_service_revision(service: ConfigService, *, default: int = 0) -> int:
    revision_getter: object = getattr(service, "get_revision", None)

    if callable(revision_getter):
        try:
            raw_revision: object = revision_getter()

            resolved_revision = await resolve_maybe_awaitable(raw_revision)

            return normalize_revision(resolved_revision, default=default)

        except (TypeError, ValueError, RuntimeError):
            logger.exception("Config revision getter failed")
            return default

    revision_value: object = getattr(service, "revision", default)

    if inspect.isawaitable(revision_value):
        try:
            revision_value = await cast(Awaitable[object], revision_value)
        except (TypeError, ValueError, RuntimeError):
            logger.exception("Awaiting config revision failed")
            return default

    return normalize_revision(revision_value, default=default)


def build_config_set_kwargs(
    *,
    setter: Callable[..., object],
    payload: ConfigUpdateRequest,
    actor_id: str | None,
    request_id: str | None,
) -> dict[str, object]:
    try:
        signature = inspect.signature(setter)
    except (TypeError, ValueError):
        return {
            "expected_revision": payload.expected_revision,
            "actor_id": actor_id,
            "request_id": request_id,
        }

    parameters = signature.parameters

    accepts_var_keyword = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
    )

    candidate_values: dict[str, object] = {
        "expected_revision": payload.expected_revision,
        "actor_id": actor_id,
        "request_id": request_id,
        "reason": payload.reason,
    }

    return {name: value for (name, value) in candidate_values.items() if (accepts_var_keyword or name in parameters)}


async def call_config_set(
    *,
    service: ConfigService,
    group: str,
    key: str,
    value: object,
    payload: ConfigUpdateRequest,
    request: Request,
) -> None:
    setter_value: object = getattr(service, "set", None)

    if not callable(setter_value):
        from .configs import structured_http_error

        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            code="CONFIG_SERVICE_CONTRACT_UNSUPPORTED",
            message=("Der Konfigurationsdienst unterstützt keine Änderungen."),
            details={"required_method": "set"},
        )

    setter = setter_value

    actor_id = None
    try:
        from .configs import get_actor_id, get_request_id

        actor_id = get_actor_id(request)
        request_id = get_request_id(request)
    except Exception:
        request_id = None

    setter_kwargs = build_config_set_kwargs(setter=setter, payload=payload, actor_id=actor_id, request_id=request_id)

    try:
        raw_result: object = setter(group, key, value, **setter_kwargs)

        await resolve_maybe_awaitable(raw_result)

    except TypeError as exc:
        logger.error(
            "ConfigService.set does not support the required contract",
            extra={"group": group, "key": key, "request_id": request_id, "supported_kwargs": sorted(setter_kwargs)},
        )

        from .configs import structured_http_error

        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            code="CONFIG_SERVICE_CONTRACT_UNSUPPORTED",
            message=(
                "Der Konfigurationsdienst unterstützt "
                "den benötigten versionierten "
                "Änderungsvertrag nicht."
            ),
            details={"provided_parameters": sorted(setter_kwargs)},
        ) from exc

    except ValueError as exc:
        from .configs import structured_http_error

        raise structured_http_error(
            request=request,
            status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
            code="CONFIG_VALUE_INVALID",
            message=("Der Konfigurationswert ist ungültig."),
            details={"group": group, "key": key, "reason": str(exc)},
        ) from exc
    except Exception as exc:
        # Special handling for ConfigValidationError from the service
        if isinstance(exc, ConfigValidationError):
            from .configs import structured_http_error

            raise structured_http_error(
                request=request,
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                code=exc.code,
                message=exc.message,
                details={"group": group, "key": key},
            ) from exc

        logger.exception(
            "Unexpected error while calling ConfigService.set",
            extra={"group": group, "key": key, "request_id": request_id},
        )

        from .configs import structured_http_error

        raise structured_http_error(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message=("Bei der Verarbeitung der Anfrage ist ein interner Fehler aufgetreten."),
            details={"group": group, "key": key},
        ) from exc


def add_normalized_entry(*, target: dict, group: str, key: str, value: object) -> None:
    from .configs import normalize_config_value

    normalized_group = group.strip().lower()
    normalized_key = key.strip().lower()

    if not normalized_group or not normalized_key:
        return

    try:
        normalized_value = normalize_config_value(value, path=(f"{normalized_group}.{normalized_key}"))
    except TypeError:
        logger.exception("Ignoring unsupported config value", extra={"group": normalized_group, "key": normalized_key, "value_type": type(value).__name__})
        return

    target[(normalized_group, normalized_key)] = normalized_value


async def read_config_entries(service: ConfigService, request: Request) -> dict[tuple[str, str], object]:
    get_all_value: object = getattr(service, "get_all", None)

    if callable(get_all_value):
        raw_entries: object = get_all_value()
    else:
        list_values_value: object = getattr(service, "list_values", None)

        if not callable(list_values_value):
            from .configs import structured_http_error

            raise structured_http_error(
                request=request,
                status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
                code="CONFIG_SERVICE_CONTRACT_UNSUPPORTED",
                message=("Der Konfigurationsdienst unterstützt keine öffentliche Methode zum Auflisten der Konfiguration."),
                details={"required_method": "get_all", "alternative_method": "list_values"},
            )

        raw_entries = list_values_value()

    resolved_entries = await resolve_maybe_awaitable(raw_entries)

    if not isinstance(resolved_entries, Mapping):
        from .configs import structured_http_error

        raise structured_http_error(
            request=request,
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            code="INVALID_CONFIG_SERVICE_RESPONSE",
            message=("Der Konfigurationsdienst hat ein ungültiges Ergebnis geliefert."),
            details={"expected_type": "mapping", "actual_type": type(resolved_entries).__name__},
        )

    typed_entries = cast(Mapping[object, object], resolved_entries)

    normalized_entries: dict[tuple[str, str], object] = {}

    for (raw_identifier, raw_value) in typed_entries.items():
        if isinstance(raw_identifier, str) and isinstance(raw_value, Mapping):
            normalized_group = raw_identifier.strip().lower()
            if not normalized_group:
                logger.warning("Ignoring empty config group")
                continue

            group_values = cast(Mapping[object, object], raw_value)
            for (raw_key, nested_value) in group_values.items():
                if not isinstance(raw_key, str):
                    logger.warning("Ignoring invalid config key", extra={"group": normalized_group, "key": repr(raw_key)})
                    continue

                add_normalized_entry(target=normalized_entries, group=normalized_group, key=raw_key, value=nested_value)

            continue

        # older structure: (group,key) -> value
        from .configs import normalize_config_identifier

        identifier = normalize_config_identifier(raw_identifier)
        if identifier is None:
            logger.warning("Ignoring invalid config identifier", extra={"identifier": repr(raw_identifier)})
            continue

        (group, key) = identifier
        add_normalized_entry(target=normalized_entries, group=group, key=key, value=raw_value)

    return normalized_entries


@lru_cache(maxsize=1)
def get_settings_field_map() -> dict[tuple[str, str], SettingsFieldDescriptor]:
    catalog = build_settings_catalog()

    result: dict[tuple[str, str], SettingsFieldDescriptor] = {}

    for settings_group in catalog.groups:
        for section in settings_group.sections:
            for field in section.fields:
                if field.source is not SettingsSource.CONFIG:
                    continue
                if not field.editable:
                    continue
                if field.config_group is None or field.config_key is None:
                    continue

                group = field.config_group.strip().lower()
                key = field.config_key.strip().lower()
                if not group or not key:
                    continue

                result[(group, key)] = field

    return result


def get_config_field_descriptor(*, group: str, key: str, request: Request) -> SettingsFieldDescriptor:
    descriptor = get_settings_field_map().get((group, key))

    if descriptor is None:
        if os.environ.get("ALLOW_UNREGISTERED_CONFIGS") == "1":
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

        from .configs import structured_http_error

        raise structured_http_error(
            request=request,
            status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
            code="CONFIG_FIELD_NOT_REGISTERED",
            message=("Dieser Konfigurationswert ist nicht im Settings-Katalog registriert."),
            details={"group": group, "key": key},
        )

    return descriptor
