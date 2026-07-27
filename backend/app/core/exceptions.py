# F:\Kernschmied\backend\app\core\exceptions.py

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from http import HTTPStatus
from typing import Any, ClassVar


class ApplicationError(Exception):
    """
    Basisklasse für erwartbare Anwendungsfehler.

    Diese Fehler können durch die zentrale FastAPI-Fehlerbehandlung in eine
    strukturierte API-Antwort überführt werden.

    Interne technische Ausnahmen wie SQLAlchemyError, OSError oder
    unerwartete RuntimeError dürfen nicht ungeprüft als ApplicationError
    an Clients weitergegeben werden.
    """

    code: ClassVar[str] = "APPLICATION_ERROR"
    status_code: ClassVar[int] = HTTPStatus.INTERNAL_SERVER_ERROR
    default_message: ClassVar[str] = (
        "Bei der Verarbeitung ist ein Anwendungsfehler aufgetreten."
    )
    expose_details: ClassVar[bool] = True

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Mapping[str, Any] | None = None,
        request_id: str | None = None,
        status_code: int | None = None,
    ) -> None:
        resolved_message = (
            message.strip()
            if isinstance(message, str) and message.strip()
            else self.default_message
        )

        self.message = resolved_message
        self.details = deepcopy(dict(details or {}))
        self.request_id = request_id
        self._status_code = status_code

        super().__init__(resolved_message)

    @property
    def effective_status_code(self) -> int:
        if self._status_code is not None:
            return int(self._status_code)

        return int(self.status_code)

    def with_request_id(
        self,
        request_id: str,
    ) -> ApplicationError:
        """
        Ergänzt eine Request-ID, sofern noch keine gesetzt wurde.
        """

        if not self.request_id:
            self.request_id = request_id

        return self

    def to_response_body(
        self,
        *,
        fallback_request_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Erzeugt die einheitliche öffentliche Fehlerstruktur.
        """

        response_details = (
            deepcopy(self.details)
            if self.expose_details
            else {}
        )

        return {
            "code": self.code,
            "message": self.message,
            "details": response_details,
            "request_id": (
                self.request_id
                or fallback_request_id
            ),
        }


class BadRequestError(ApplicationError):
    code = "BAD_REQUEST"
    status_code = HTTPStatus.BAD_REQUEST
    default_message = "Die Anfrage ist ungültig."


class AuthenticationRequiredError(ApplicationError):
    code = "AUTHENTICATION_REQUIRED"
    status_code = HTTPStatus.UNAUTHORIZED
    default_message = "Für diese Aktion ist eine Anmeldung erforderlich."


class PermissionDeniedError(ApplicationError):
    code = "PERMISSION_DENIED"
    status_code = HTTPStatus.FORBIDDEN
    default_message = "Für diese Aktion fehlt die erforderliche Berechtigung."


class ResourceNotFoundError(ApplicationError):
    code = "RESOURCE_NOT_FOUND"
    status_code = HTTPStatus.NOT_FOUND
    default_message = "Die angeforderte Ressource wurde nicht gefunden."


class ResourceConflictError(ApplicationError):
    code = "RESOURCE_CONFLICT"
    status_code = HTTPStatus.CONFLICT
    default_message = (
        "Die Aktion steht im Konflikt mit dem aktuellen Zustand."
    )


class ValidationFailedError(ApplicationError):
    code = "VALIDATION_FAILED"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = "Die übermittelten Daten sind ungültig."


class ServiceUnavailableError(ApplicationError):
    code = "SERVICE_UNAVAILABLE"
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    default_message = "Der angeforderte Dienst ist derzeit nicht verfügbar."


class UnsupportedSchemaError(ApplicationError):
    code = "UNSUPPORTED_SCHEMA"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = "Das angegebene Schema wird nicht unterstützt."

    def __init__(
        self,
        *,
        schema_name: str,
        schema_version: str | None = None,
        supported_versions: tuple[str, ...] = (),
        request_id: str | None = None,
    ) -> None:
        details: dict[str, Any] = {
            "schema_name": schema_name,
            "supported_versions": list(
                supported_versions,
            ),
        }

        if schema_version is not None:
            details["schema_version"] = schema_version

        version_text = (
            f" in Version '{schema_version}'"
            if schema_version
            else ""
        )

        super().__init__(
            f"Das Schema '{schema_name}'{version_text} "
            "wird nicht unterstützt.",
            details=details,
            request_id=request_id,
        )


class UnsupportedComponentError(ApplicationError):
    code = "UNSUPPORTED_UI_COMPONENT"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = "Der UI-Komponententyp wird nicht unterstützt."

    def __init__(
        self,
        *,
        component_type: str,
        component_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        details: dict[str, Any] = {
            "component_type": component_type,
        }

        if component_id is not None:
            details["component_id"] = component_id

        super().__init__(
            f"Der UI-Komponententyp '{component_type}' "
            "wird nicht unterstützt.",
            details=details,
            request_id=request_id,
        )


class UnsupportedActionError(ApplicationError):
    code = "UNSUPPORTED_UI_ACTION"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = "Der UI-Aktionstyp wird nicht unterstützt."

    def __init__(
        self,
        *,
        action_type: str,
        action_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        details: dict[str, Any] = {
            "action_type": action_type,
        }

        if action_id is not None:
            details["action_id"] = action_id

        super().__init__(
            f"Der UI-Aktionstyp '{action_type}' "
            "wird nicht unterstützt.",
            details=details,
            request_id=request_id,
        )


class ConfigError(ApplicationError):
    """
    Basisklasse für fachliche Konfigurationsfehler.
    """

    code = "CONFIG_ERROR"
    status_code = HTTPStatus.BAD_REQUEST
    default_message = "Die Konfiguration konnte nicht verarbeitet werden."


class ConfigNotDefinedError(ConfigError):
    code = "CONFIG_NOT_DEFINED"
    status_code = HTTPStatus.NOT_FOUND
    default_message = "Die angeforderte Konfiguration ist nicht definiert."

    def __init__(
        self,
        *,
        group: str,
        key: str,
        request_id: str | None = None,
    ) -> None:
        self.group = group
        self.key = key

        super().__init__(
            f"Die Konfiguration '{group}.{key}' ist nicht definiert.",
            details={
                "group": group,
                "key": key,
            },
            request_id=request_id,
        )


class ConfigEntryNotFoundError(ConfigError):
    code = "CONFIG_ENTRY_NOT_FOUND"
    status_code = HTTPStatus.NOT_FOUND
    default_message = (
        "Der gespeicherte Konfigurationseintrag wurde nicht gefunden."
    )

    def __init__(
        self,
        *,
        group: str,
        key: str,
        request_id: str | None = None,
    ) -> None:
        self.group = group
        self.key = key

        super().__init__(
            f"Der Konfigurationseintrag '{group}.{key}' "
            "wurde nicht gefunden.",
            details={
                "group": group,
                "key": key,
            },
            request_id=request_id,
        )


class ConfigValueInvalidError(ConfigError):
    code = "CONFIG_VALUE_INVALID"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = "Der Konfigurationswert ist ungültig."

    def __init__(
        self,
        *,
        group: str,
        key: str,
        reason: str,
        path: tuple[str | int, ...] = (),
        request_id: str | None = None,
    ) -> None:
        self.group = group
        self.key = key
        self.reason = reason
        self.path = path

        details: dict[str, Any] = {
            "group": group,
            "key": key,
            "reason": reason,
            "path": list(path),
        }

        location = (
            ".".join(str(part) for part in path)
            if path
            else "<root>"
        )

        super().__init__(
            f"Der Wert für '{group}.{key}' ist an "
            f"'{location}' ungültig: {reason}",
            details=details,
            request_id=request_id,
        )


class ConfigNotRuntimeEditableError(ConfigError):
    code = "CONFIG_NOT_RUNTIME_EDITABLE"
    status_code = HTTPStatus.CONFLICT
    default_message = (
        "Die Konfiguration kann nicht zur Laufzeit geändert werden."
    )

    def __init__(
        self,
        *,
        group: str,
        key: str,
        requires_restart: bool = False,
        request_id: str | None = None,
    ) -> None:
        self.group = group
        self.key = key
        self.requires_restart = requires_restart

        message = (
            f"Die Konfiguration '{group}.{key}' ist nicht "
            "zur Laufzeit änderbar."
        )

        if requires_restart:
            message += " Die Änderung erfordert einen Neustart."

        super().__init__(
            message,
            details={
                "group": group,
                "key": key,
                "requires_restart": requires_restart,
            },
            request_id=request_id,
        )


class ConfigRevisionConflictError(ConfigError):
    code = "CONFIG_REVISION_CONFLICT"
    status_code = HTTPStatus.CONFLICT
    default_message = (
        "Die Konfiguration wurde zwischenzeitlich geändert."
    )

    def __init__(
        self,
        *,
        expected_revision: int,
        actual_revision: int,
        request_id: str | None = None,
    ) -> None:
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision

        super().__init__(
            "Die Konfiguration wurde zwischenzeitlich geändert. "
            f"Erwartete Revision: {expected_revision}, "
            f"aktuelle Revision: {actual_revision}.",
            details={
                "expected_revision": expected_revision,
                "actual_revision": actual_revision,
            },
            request_id=request_id,
        )


class ScopeNotAllowedError(ConfigError):
    code = "CONFIG_SCOPE_NOT_ALLOWED"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = (
        "Der angegebene Gültigkeitsbereich ist für diese "
        "Konfiguration nicht zulässig."
    )

    def __init__(
        self,
        *,
        group: str,
        key: str,
        scope: str,
        allowed_scopes: tuple[str, ...] = (),
        request_id: str | None = None,
    ) -> None:
        self.group = group
        self.key = key
        self.scope = scope
        self.allowed_scopes = allowed_scopes

        super().__init__(
            f"Der Scope '{scope}' ist für die Konfiguration "
            f"'{group}.{key}' nicht zulässig.",
            details={
                "group": group,
                "key": key,
                "scope": scope,
                "allowed_scopes": list(
                    allowed_scopes,
                ),
            },
            request_id=request_id,
        )


class SecretAccessDeniedError(ConfigError):
    code = "CONFIG_SECRET_ACCESS_DENIED"
    status_code = HTTPStatus.FORBIDDEN
    default_message = (
        "Der Zugriff auf den Secret-Wert ist nicht erlaubt."
    )

    def __init__(
        self,
        *,
        group: str,
        key: str,
        request_id: str | None = None,
    ) -> None:
        self.group = group
        self.key = key

        super().__init__(
            f"Der Secret-Wert '{group}.{key}' darf nicht "
            "ausgegeben werden.",
            details={
                "group": group,
                "key": key,
            },
            request_id=request_id,
        )


class ModelError(ApplicationError):
    code = "MODEL_ERROR"
    status_code = HTTPStatus.BAD_GATEWAY
    default_message = "Das Modell konnte die Anfrage nicht verarbeiten."


class ModelNotFoundError(ModelError):
    code = "MODEL_NOT_FOUND"
    status_code = HTTPStatus.NOT_FOUND
    default_message = "Das angeforderte Modell wurde nicht gefunden."

    def __init__(
        self,
        *,
        model_id: str,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id

        super().__init__(
            f"Das Modell '{model_id}' wurde nicht gefunden.",
            details={
                "model_id": model_id,
            },
            request_id=request_id,
        )


class ModelUnavailableError(ModelError):
    code = "MODEL_UNAVAILABLE"
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    default_message = "Das Modell ist derzeit nicht verfügbar."

    def __init__(
        self,
        *,
        model_id: str,
        reason: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.reason = reason

        message = f"Das Modell '{model_id}' ist derzeit nicht verfügbar."

        if reason:
            message += f" Grund: {reason}"

        super().__init__(
            message,
            details={
                "model_id": model_id,
                "reason": reason,
            },
            request_id=request_id,
        )


class ModelCapabilityNotSupportedError(ModelError):
    code = "MODEL_CAPABILITY_NOT_SUPPORTED"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = (
        "Das Modell unterstützt die angeforderte Fähigkeit nicht."
    )

    def __init__(
        self,
        *,
        model_id: str,
        capability: str,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.capability = capability

        super().__init__(
            f"Das Modell '{model_id}' unterstützt die Fähigkeit "
            f"'{capability}' nicht.",
            details={
                "model_id": model_id,
                "capability": capability,
            },
            request_id=request_id,
        )


class ToolError(ApplicationError):
    code = "TOOL_ERROR"
    status_code = HTTPStatus.BAD_GATEWAY
    default_message = "Das Tool konnte nicht ausgeführt werden."


class ToolNotFoundError(ToolError):
    code = "TOOL_NOT_FOUND"
    status_code = HTTPStatus.NOT_FOUND
    default_message = "Das angeforderte Tool wurde nicht gefunden."

    def __init__(
        self,
        *,
        tool_id: str,
        request_id: str | None = None,
    ) -> None:
        self.tool_id = tool_id

        super().__init__(
            f"Das Tool '{tool_id}' wurde nicht gefunden.",
            details={
                "tool_id": tool_id,
            },
            request_id=request_id,
        )


class ToolUnavailableError(ToolError):
    code = "TOOL_UNAVAILABLE"
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    default_message = "Das Tool ist derzeit nicht verfügbar."

    def __init__(
        self,
        *,
        tool_id: str,
        reason: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.tool_id = tool_id
        self.reason = reason

        message = f"Das Tool '{tool_id}' ist derzeit nicht verfügbar."

        if reason:
            message += f" Grund: {reason}"

        super().__init__(
            message,
            details={
                "tool_id": tool_id,
                "reason": reason,
            },
            request_id=request_id,
        )


class ToolConfirmationRequiredError(ToolError):
    code = "TOOL_CONFIRMATION_REQUIRED"
    status_code = HTTPStatus.CONFLICT
    default_message = (
        "Die Tool-Ausführung muss vorab bestätigt werden."
    )

    def __init__(
        self,
        *,
        tool_id: str,
        confirmation_message: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.tool_id = tool_id
        self.confirmation_message = confirmation_message

        super().__init__(
            confirmation_message
            or (
                f"Die Ausführung des Tools '{tool_id}' "
                "muss bestätigt werden."
            ),
            details={
                "tool_id": tool_id,
                "requires_confirmation": True,
            },
            request_id=request_id,
        )


class ToolExecutionFailedError(ToolError):
    code = "TOOL_EXECUTION_FAILED"
    status_code = HTTPStatus.BAD_GATEWAY
    default_message = "Die Tool-Ausführung ist fehlgeschlagen."

    def __init__(
        self,
        *,
        tool_id: str,
        reason: str,
        retryable: bool = False,
        details: Mapping[str, object] | None = None,
        request_id: str | None = None,
    ) -> None:
        self.tool_id = tool_id
        self.reason = reason
        self.retryable = retryable

        response_details: dict[str, object] = {
            "tool_id": tool_id,
            "reason": reason,
            "retryable": retryable,
        }

        if details is not None:
            for key, value in details.items():
                response_details[str(key)] = value

        super().__init__(
            f"Die Ausführung des Tools '{tool_id}' ist "
            f"fehlgeschlagen: {reason}",
            details=response_details,
            request_id=request_id,
        )