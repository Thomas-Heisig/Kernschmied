from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Request

from app.schemas.settings_catalog import (
    SettingsControl,
    SettingsFieldDescriptor,
)

from .configs_service import get_config_field_descriptor


def validate_confirmation_requirement(
    *, descriptor: SettingsFieldDescriptor, payload: Any, request: Request
) -> None:
    if not descriptor.requires_confirmation:
        return

    if getattr(payload, "reason", None) is not None:
        return

    from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT

    from .configs import structured_http_error

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
    value: Any,
    request: Request,
) -> None:
    from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT

    from .configs import structured_http_error

    raise structured_http_error(
        request=request,
        status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
        code="CONFIG_VALUE_TYPE_INVALID",
        message=("Der Konfigurationswert besitzt einen ungültigen Datentyp."),
        details={
            "group": descriptor.config_group,
            "key": descriptor.config_key,
            "expected_type": expected_type,
            "actual_type": type(value).__name__,
        },
    )


def validate_control_type(
    *, descriptor: SettingsFieldDescriptor, value: Any, request: Request
) -> None:
    control = descriptor.control

    if control in {
        SettingsControl.TEXT,
        SettingsControl.TEXTAREA,
        SettingsControl.SELECT,
    }:
        if not isinstance(value, str):
            raise_invalid_type(
                descriptor=descriptor,
                expected_type="string",
                value=value,
                request=request,
            )
        return

    if control is SettingsControl.BOOLEAN:
        if not isinstance(value, bool):
            raise_invalid_type(
                descriptor=descriptor,
                expected_type="boolean",
                value=value,
                request=request,
            )
        return

    if control is SettingsControl.NUMBER:
        from .configs import normalize_config_number

        numeric_value = normalize_config_number(value)
        if numeric_value is None:
            raise_invalid_type(
                descriptor=descriptor,
                expected_type="number",
                value=value,
                request=request,
            )
        return

    if control is SettingsControl.MULTISELECT:
        from .configs import is_config_string_list

        if not is_config_string_list(value):
            raise_invalid_type(
                descriptor=descriptor,
                expected_type="array[string]",
                value=value,
                request=request,
            )
        return

    from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT

    from .configs import structured_http_error

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
    *, descriptor: SettingsFieldDescriptor, value: Any, request: Request
) -> None:
    options = tuple(descriptor.options or ())
    if not options:
        return

    allowed_values = frozenset(option.value for option in options)

    if descriptor.control is SettingsControl.SELECT:
        if not isinstance(value, str) or value not in allowed_values:
            from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT

            from .configs import structured_http_error

            raise structured_http_error(
                request=request,
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="CONFIG_OPTION_INVALID",
                message=("Der ausgewählte Konfigurationswert ist nicht zulässig."),
                details={
                    "group": descriptor.config_group,
                    "key": descriptor.config_key,
                    "allowed_values": sorted(allowed_values),
                },
            )
        return

    if descriptor.control is SettingsControl.MULTISELECT:
        from .configs import is_config_string_list

        if not is_config_string_list(value):
            return

        invalid_values = [item for item in value if item not in allowed_values]
        if invalid_values:
            from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT

            from .configs import structured_http_error

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
                    "allowed_values": sorted(allowed_values),
                },
            )


def validate_numeric_range(
    *, descriptor: SettingsFieldDescriptor, value: Any, request: Request
) -> None:
    if descriptor.control is not SettingsControl.NUMBER:
        return

    from .configs import normalize_config_number

    numeric_value = normalize_config_number(value)
    if numeric_value is None:
        return

    minimum = descriptor.minimum
    maximum = descriptor.maximum

    if minimum is not None and numeric_value < minimum:
        from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT

        from .configs import structured_http_error

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
        from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT

        from .configs import structured_http_error

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


def validate_identity_value(*, key: str, value: Any, request: Request) -> Any:
    validated_value: Any = value

    from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT

    from .configs import (
        IDENTITY_STRING_LIMITS,
        LANGUAGE_CODE_PATTERN,
        structured_http_error,
    )

    limits = IDENTITY_STRING_LIMITS.get(key)
    if limits is not None:
        if not isinstance(validated_value, str):
            raise structured_http_error(
                request=request,
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="IDENTITY_VALUE_TYPE_INVALID",
                message=("Der Identitätswert muss eine Zeichenkette sein."),
                details={"key": key, "actual_type": type(validated_value).__name__},
            )

        normalized = validated_value.strip()
        min_len, max_len = limits
        if len(normalized) < min_len:
            raise structured_http_error(
                request=request,
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="IDENTITY_VALUE_TOO_SHORT",
                message=("Der Identitätswert ist zu kurz."),
                details={"key": key, "minimum_length": min_len},
            )

        if len(normalized) > max_len:
            raise structured_http_error(
                request=request,
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="IDENTITY_VALUE_TOO_LONG",
                message=("Der Identitätswert ist zu lang."),
                details={"key": key, "maximum_length": max_len},
            )

        validated_value = normalized

    if key == "default_language":
        if not isinstance(validated_value, str):
            raise structured_http_error(
                request=request,
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="IDENTITY_LANGUAGE_TYPE_INVALID",
                message=("Die Standardsprache muss als Zeichenkette angegeben werden."),
                details={"key": key},
            )

        if not LANGUAGE_CODE_PATTERN.fullmatch(validated_value):
            raise structured_http_error(
                request=request,
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="IDENTITY_LANGUAGE_INVALID",
                message=(
                    "Die Standardsprache muss als gültiger Sprachcode angegeben werden."
                ),
                details={"key": key, "value": validated_value, "example": "de"},
            )

    if key == "timezone":
        if not isinstance(validated_value, str):
            raise structured_http_error(
                request=request,
                status_code=(HTTP_422_UNPROCESSABLE_CONTENT),
                code="IDENTITY_TIMEZONE_TYPE_INVALID",
                message=("Die Zeitzone muss als Zeichenkette angegeben werden."),
                details={"key": key},
            )

        try:
            ZoneInfo(validated_value)
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
    *, group: str, key: str, payload: Any, request: Request
) -> tuple[SettingsFieldDescriptor, Any]:
    descriptor: SettingsFieldDescriptor = get_config_field_descriptor(
        group=group, key=key, request=request
    )

    validate_confirmation_requirement(
        descriptor=descriptor, payload=payload, request=request
    )

    validate_control_type(descriptor=descriptor, value=payload.value, request=request)

    validate_allowed_options(
        descriptor=descriptor, value=payload.value, request=request
    )

    validate_numeric_range(descriptor=descriptor, value=payload.value, request=request)

    validated_value = payload.value

    if group == "identity":
        validated_value = validate_identity_value(
            key=key, value=validated_value, request=request
        )

    return (descriptor, validated_value)
