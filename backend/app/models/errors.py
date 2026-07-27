# F:\Kernschmied\backend\app\models\errors.py

"""
Zentrale Fehlerhierarchie des Kernschmied-Modellsystems.

Dieses Modul definiert stabile, providerunabhängige Fehler für:

- Modellmanifeste
- Modellregistrierung
- Provider-Auflösung
- Modell-Lifecycle
- Modellverfügbarkeit
- Generierung
- Streaming
- Tool-Calling
- Kontext- und Eingabevalidierung
- Sicherheits- und Berechtigungsfehler

Provider dürfen eigene interne Ausnahmen besitzen. An der Grenze zum
ModelService oder zur API sollten diese jedoch in die hier definierten
Fehler übersetzt werden.

Die Fehlercodes dieses Moduls sind Teil des stabilen API-Vertrags und
dürfen nur bewusst und versioniert geändert werden.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from http import HTTPStatus
from typing import Any, ClassVar, Final

from app.core.exceptions import ApplicationError


# ============================================================
# Fehlercodes
# ============================================================


class ModelErrorCode(StrEnum):
    """
    Stabile Fehlercodes des Modellsystems.

    Die Werte werden über strukturierte API-Fehlerantworten ausgegeben.
    """

    MODEL_ERROR = "MODEL_ERROR"

    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    MODEL_NOT_REGISTERED = "MODEL_NOT_REGISTERED"
    MODEL_ALREADY_REGISTERED = "MODEL_ALREADY_REGISTERED"
    MODEL_DISABLED = "MODEL_DISABLED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_NOT_READY = "MODEL_NOT_READY"

    MODEL_MANIFEST_INVALID = "MODEL_MANIFEST_INVALID"
    MODEL_MANIFEST_NOT_FOUND = "MODEL_MANIFEST_NOT_FOUND"
    MODEL_MANIFEST_UNSUPPORTED_VERSION = (
        "MODEL_MANIFEST_UNSUPPORTED_VERSION"
    )
    MODEL_MANIFEST_DUPLICATE = "MODEL_MANIFEST_DUPLICATE"
    MODEL_MANIFEST_SECURITY_VIOLATION = (
        "MODEL_MANIFEST_SECURITY_VIOLATION"
    )

    MODEL_PROVIDER_UNKNOWN = "MODEL_PROVIDER_UNKNOWN"
    MODEL_PROVIDER_DUPLICATE = "MODEL_PROVIDER_DUPLICATE"
    MODEL_PROVIDER_IMPORT_FAILED = "MODEL_PROVIDER_IMPORT_FAILED"
    MODEL_PROVIDER_FACTORY_INVALID = "MODEL_PROVIDER_FACTORY_INVALID"
    MODEL_PROVIDER_CREATION_FAILED = "MODEL_PROVIDER_CREATION_FAILED"
    MODEL_PROVIDER_CONFIGURATION_INVALID = (
        "MODEL_PROVIDER_CONFIGURATION_INVALID"
    )
    MODEL_PROVIDER_DEPENDENCY_MISSING = (
        "MODEL_PROVIDER_DEPENDENCY_MISSING"
    )
    MODEL_PROVIDER_CONNECTION_FAILED = (
        "MODEL_PROVIDER_CONNECTION_FAILED"
    )
    MODEL_PROVIDER_AUTHENTICATION_FAILED = (
        "MODEL_PROVIDER_AUTHENTICATION_FAILED"
    )
    MODEL_PROVIDER_PERMISSION_DENIED = (
        "MODEL_PROVIDER_PERMISSION_DENIED"
    )
    MODEL_PROVIDER_RATE_LIMITED = "MODEL_PROVIDER_RATE_LIMITED"
    MODEL_PROVIDER_RESPONSE_INVALID = (
        "MODEL_PROVIDER_RESPONSE_INVALID"
    )
    MODEL_PROVIDER_SERVER_ERROR = "MODEL_PROVIDER_SERVER_ERROR"

    MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"
    MODEL_UNLOAD_FAILED = "MODEL_UNLOAD_FAILED"
    MODEL_ALREADY_LOADED = "MODEL_ALREADY_LOADED"
    MODEL_NOT_LOADED = "MODEL_NOT_LOADED"
    MODEL_SHUTDOWN_FAILED = "MODEL_SHUTDOWN_FAILED"

    MODEL_REQUEST_INVALID = "MODEL_REQUEST_INVALID"
    MODEL_MESSAGE_INVALID = "MODEL_MESSAGE_INVALID"
    MODEL_CONTEXT_LIMIT_EXCEEDED = (
        "MODEL_CONTEXT_LIMIT_EXCEEDED"
    )
    MODEL_OUTPUT_LIMIT_EXCEEDED = "MODEL_OUTPUT_LIMIT_EXCEEDED"
    MODEL_CAPABILITY_NOT_SUPPORTED = (
        "MODEL_CAPABILITY_NOT_SUPPORTED"
    )

    MODEL_GENERATION_FAILED = "MODEL_GENERATION_FAILED"
    MODEL_GENERATION_TIMEOUT = "MODEL_GENERATION_TIMEOUT"
    MODEL_GENERATION_CANCELLED = "MODEL_GENERATION_CANCELLED"

    MODEL_STREAM_FAILED = "MODEL_STREAM_FAILED"
    MODEL_STREAM_TIMEOUT = "MODEL_STREAM_TIMEOUT"
    MODEL_STREAM_PROTOCOL_ERROR = "MODEL_STREAM_PROTOCOL_ERROR"
    MODEL_STREAM_CANCELLED = "MODEL_STREAM_CANCELLED"

    MODEL_TOOL_CALL_INVALID = "MODEL_TOOL_CALL_INVALID"
    MODEL_TOOL_CALL_UNSUPPORTED = "MODEL_TOOL_CALL_UNSUPPORTED"
    MODEL_STRUCTURED_OUTPUT_INVALID = (
        "MODEL_STRUCTURED_OUTPUT_INVALID"
    )

    MODEL_ACCESS_DENIED = "MODEL_ACCESS_DENIED"
    MODEL_OPERATION_CONFLICT = "MODEL_OPERATION_CONFLICT"


# ============================================================
# Basisklasse
# ============================================================


class ModelError(ApplicationError):
    """
    Basisklasse aller providerunabhängigen Modellfehler.

    details darf ausschließlich serialisierbare und nicht geheime
    Informationen enthalten. API-Schlüssel, Tokens, vollständige
    Authorization-Header oder sensible Prompt-Inhalte dürfen hier niemals
    abgelegt werden.
    """

    code: ClassVar[str] = ModelErrorCode.MODEL_ERROR.value
    status_code: ClassVar[int] = int(
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    default_message: ClassVar[str] = (
        "Im Modellsystem ist ein Fehler aufgetreten."
    )
    expose_details: ClassVar[bool] = True

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Mapping[str, Any] | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.cause = cause

        super().__init__(
            message=message or self.default_message,
            details=dict(details or {}),
            request_id=request_id,
        )


# ============================================================
# Modellauflösung und Registry
# ============================================================


class ModelNotFoundError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_NOT_FOUND.value
    status_code: ClassVar[int] = int(
        HTTPStatus.NOT_FOUND,
    )
    default_message: ClassVar[str] = (
        "Das angeforderte Modell wurde nicht gefunden."
    )

    def __init__(
        self,
        model_id: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id

        super().__init__(
            details={
                "model_id": model_id,
            },
            request_id=request_id,
        )


class ModelNotRegisteredError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_NOT_REGISTERED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.NOT_FOUND,
    )
    default_message: ClassVar[str] = (
        "Das angeforderte Modell ist nicht registriert."
    )

    def __init__(
        self,
        model_id: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id

        super().__init__(
            details={
                "model_id": model_id,
            },
            request_id=request_id,
        )


class DuplicateModelRegistrationError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_ALREADY_REGISTERED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.CONFLICT,
    )
    default_message: ClassVar[str] = (
        "Das Modell ist bereits registriert."
    )

    def __init__(
        self,
        model_id: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id

        super().__init__(
            details={
                "model_id": model_id,
            },
            request_id=request_id,
        )


class ModelDisabledError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_DISABLED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.CONFLICT,
    )
    default_message: ClassVar[str] = (
        "Das angeforderte Modell ist deaktiviert."
    )

    def __init__(
        self,
        model_id: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id

        super().__init__(
            details={
                "model_id": model_id,
            },
            request_id=request_id,
        )


class ModelUnavailableError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_UNAVAILABLE.value
    status_code: ClassVar[int] = int(
        HTTPStatus.SERVICE_UNAVAILABLE,
    )
    default_message: ClassVar[str] = (
        "Das angeforderte Modell ist derzeit nicht verfügbar."
    )

    def __init__(
        self,
        model_id: str,
        *,
        provider_type: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.model_id = model_id
        self.provider_type = provider_type
        self.reason = reason

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if provider_type:
            details["provider_type"] = provider_type

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelNotReadyError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_NOT_READY.value
    status_code: ClassVar[int] = int(
        HTTPStatus.SERVICE_UNAVAILABLE,
    )
    default_message: ClassVar[str] = (
        "Das Modell ist noch nicht einsatzbereit."
    )

    def __init__(
        self,
        model_id: str,
        *,
        lifecycle_state: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.lifecycle_state = lifecycle_state

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if lifecycle_state:
            details["lifecycle_state"] = lifecycle_state

        super().__init__(
            details=details,
            request_id=request_id,
        )


# ============================================================
# Manifestfehler
# ============================================================


class ModelManifestError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_MANIFEST_INVALID.value
    status_code: ClassVar[int] = int(
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )
    default_message: ClassVar[str] = (
        "Das Modellmanifest ist ungültig."
    )


class ModelManifestNotFoundError(ModelManifestError):
    code: ClassVar[str] = ModelErrorCode.MODEL_MANIFEST_NOT_FOUND.value
    status_code: ClassVar[int] = int(
        HTTPStatus.NOT_FOUND,
    )
    default_message: ClassVar[str] = (
        "Das Modellmanifest wurde nicht gefunden."
    )

    def __init__(
        self,
        manifest_path: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.manifest_path = manifest_path

        super().__init__(
            details={
                "manifest_path": manifest_path,
            },
            request_id=request_id,
        )


class InvalidModelManifestError(ModelManifestError):
    code: ClassVar[str] = ModelErrorCode.MODEL_MANIFEST_INVALID.value

    def __init__(
        self,
        *,
        manifest_path: str | None = None,
        validation_errors: Sequence[
            Mapping[str, Any] | str
        ] | None = None,
        message: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.manifest_path = manifest_path
        self.validation_errors = tuple(validation_errors or ())

        details: dict[str, Any] = {}

        if manifest_path:
            details["manifest_path"] = manifest_path

        if self.validation_errors:
            details["validation_errors"] = [
                (
                    dict(error)
                    if isinstance(error, Mapping)
                    else str(error)
                )
                for error in self.validation_errors
            ]

        super().__init__(
            message=message,
            details=details,
            request_id=request_id,
            cause=cause,
        )


class UnsupportedModelManifestVersionError(ModelManifestError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_MANIFEST_UNSUPPORTED_VERSION.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )
    default_message: ClassVar[str] = (
        "Die Version des Modellmanifests wird nicht unterstützt."
    )

    def __init__(
        self,
        version: str,
        *,
        supported_versions: Sequence[str],
        manifest_path: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.version = version
        self.supported_versions = tuple(supported_versions)
        self.manifest_path = manifest_path

        details: dict[str, Any] = {
            "version": version,
            "supported_versions": list(self.supported_versions),
        }

        if manifest_path:
            details["manifest_path"] = manifest_path

        super().__init__(
            details=details,
            request_id=request_id,
        )


class DuplicateModelManifestError(ModelManifestError):
    code: ClassVar[str] = ModelErrorCode.MODEL_MANIFEST_DUPLICATE.value
    status_code: ClassVar[int] = int(
        HTTPStatus.CONFLICT,
    )
    default_message: ClassVar[str] = (
        "Mehrere Modellmanifeste verwenden dieselbe Modell-ID."
    )

    def __init__(
        self,
        model_id: str,
        *,
        manifest_paths: Sequence[str],
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.manifest_paths = tuple(manifest_paths)

        super().__init__(
            details={
                "model_id": model_id,
                "manifest_paths": list(self.manifest_paths),
            },
            request_id=request_id,
        )


class ModelManifestSecurityError(ModelManifestError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_MANIFEST_SECURITY_VIOLATION.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.FORBIDDEN,
    )
    default_message: ClassVar[str] = (
        "Das Modellmanifest verletzt eine Sicherheitsrichtlinie."
    )

    def __init__(
        self,
        *,
        reason: str,
        manifest_path: str | None = None,
        model_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.reason = reason
        self.manifest_path = manifest_path
        self.model_id = model_id

        details: dict[str, Any] = {
            "reason": reason,
        }

        if manifest_path:
            details["manifest_path"] = manifest_path

        if model_id:
            details["model_id"] = model_id

        super().__init__(
            details=details,
            request_id=request_id,
        )


# ============================================================
# Providerfehler
# ============================================================


class ModelProviderError(ModelError):
    """
    Basisklasse aller providerbezogenen Fehler.
    """


class UnknownModelProviderError(ModelProviderError):
    code: ClassVar[str] = ModelErrorCode.MODEL_PROVIDER_UNKNOWN.value
    status_code: ClassVar[int] = int(
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )
    default_message: ClassVar[str] = (
        "Der angegebene Modell-Provider ist nicht registriert."
    )

    def __init__(
        self,
        provider_type: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.provider_type = provider_type

        super().__init__(
            details={
                "provider_type": provider_type,
            },
            request_id=request_id,
        )


class DuplicateModelProviderError(ModelProviderError):
    code: ClassVar[str] = ModelErrorCode.MODEL_PROVIDER_DUPLICATE.value
    status_code: ClassVar[int] = int(
        HTTPStatus.CONFLICT,
    )
    default_message: ClassVar[str] = (
        "Der Modell-Provider ist bereits registriert."
    )

    def __init__(
        self,
        provider_type: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.provider_type = provider_type

        super().__init__(
            details={
                "provider_type": provider_type,
            },
            request_id=request_id,
        )


class ModelProviderImportError(ModelProviderError):
    code: ClassVar[str] = ModelErrorCode.MODEL_PROVIDER_IMPORT_FAILED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.SERVICE_UNAVAILABLE,
    )
    default_message: ClassVar[str] = (
        "Der Modell-Provider konnte nicht geladen werden."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        module_name: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.module_name = module_name
        self.reason = reason

        details: dict[str, Any] = {
            "provider_type": provider_type,
        }

        if module_name:
            details["module_name"] = module_name

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class InvalidModelProviderFactoryError(ModelProviderError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_PROVIDER_FACTORY_INVALID.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    default_message: ClassVar[str] = (
        "Die Modell-Provider-Factory ist ungültig."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        reason: str,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.reason = reason

        super().__init__(
            details={
                "provider_type": provider_type,
                "reason": reason,
            },
            request_id=request_id,
            cause=cause,
        )


class ModelProviderCreationError(ModelProviderError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_PROVIDER_CREATION_FAILED.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    default_message: ClassVar[str] = (
        "Der Modell-Provider konnte nicht erzeugt werden."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        model_id: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.model_id = model_id
        self.reason = reason

        details: dict[str, Any] = {
            "provider_type": provider_type,
        }

        if model_id:
            details["model_id"] = model_id

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class InvalidModelProviderConfigurationError(ModelProviderError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_PROVIDER_CONFIGURATION_INVALID.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )
    default_message: ClassVar[str] = (
        "Die Konfiguration des Modell-Providers ist ungültig."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        model_id: str | None = None,
        field: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.model_id = model_id
        self.field = field
        self.reason = reason

        details: dict[str, Any] = {
            "provider_type": provider_type,
        }

        if model_id:
            details["model_id"] = model_id

        if field:
            details["field"] = field

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelProviderDependencyError(ModelProviderError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_PROVIDER_DEPENDENCY_MISSING.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.SERVICE_UNAVAILABLE,
    )
    default_message: ClassVar[str] = (
        "Eine erforderliche Abhängigkeit des Modell-Providers fehlt."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        dependency: str,
        model_id: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.dependency = dependency
        self.model_id = model_id

        details: dict[str, Any] = {
            "provider_type": provider_type,
            "dependency": dependency,
        }

        if model_id:
            details["model_id"] = model_id

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelProviderConnectionError(ModelProviderError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_PROVIDER_CONNECTION_FAILED.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.BAD_GATEWAY,
    )
    default_message: ClassVar[str] = (
        "Der Modell-Provider konnte nicht erreicht werden."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        model_id: str | None = None,
        endpoint: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.model_id = model_id
        self.endpoint = endpoint
        self.reason = reason

        details: dict[str, Any] = {
            "provider_type": provider_type,
        }

        if model_id:
            details["model_id"] = model_id

        if endpoint:
            details["endpoint"] = endpoint

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelProviderAuthenticationError(ModelProviderError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_PROVIDER_AUTHENTICATION_FAILED.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.BAD_GATEWAY,
    )
    default_message: ClassVar[str] = (
        "Der Modell-Provider hat die Authentifizierung abgelehnt."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        model_id: str | None = None,
        remote_request_id: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.model_id = model_id
        self.remote_request_id = remote_request_id

        details: dict[str, Any] = {
            "provider_type": provider_type,
        }

        if model_id:
            details["model_id"] = model_id

        if remote_request_id:
            details["remote_request_id"] = remote_request_id

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelProviderPermissionError(ModelProviderError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_PROVIDER_PERMISSION_DENIED.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.BAD_GATEWAY,
    )
    default_message: ClassVar[str] = (
        "Der Modell-Provider hat den Zugriff verweigert."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        model_id: str | None = None,
        remote_request_id: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.model_id = model_id
        self.remote_request_id = remote_request_id

        details: dict[str, Any] = {
            "provider_type": provider_type,
        }

        if model_id:
            details["model_id"] = model_id

        if remote_request_id:
            details["remote_request_id"] = remote_request_id

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelProviderRateLimitError(ModelProviderError):
    code: ClassVar[str] = ModelErrorCode.MODEL_PROVIDER_RATE_LIMITED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.TOO_MANY_REQUESTS,
    )
    default_message: ClassVar[str] = (
        "Der Modell-Provider hat die Anfrage begrenzt."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        model_id: str | None = None,
        retry_after_seconds: float | None = None,
        remote_request_id: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.model_id = model_id
        self.retry_after_seconds = retry_after_seconds
        self.remote_request_id = remote_request_id

        details: dict[str, Any] = {
            "provider_type": provider_type,
        }

        if model_id:
            details["model_id"] = model_id

        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds

        if remote_request_id:
            details["remote_request_id"] = remote_request_id

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class InvalidModelProviderResponseError(ModelProviderError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_PROVIDER_RESPONSE_INVALID.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.BAD_GATEWAY,
    )
    default_message: ClassVar[str] = (
        "Der Modell-Provider hat eine ungültige Antwort geliefert."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        model_id: str | None = None,
        reason: str | None = None,
        remote_request_id: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.model_id = model_id
        self.reason = reason
        self.remote_request_id = remote_request_id

        details: dict[str, Any] = {
            "provider_type": provider_type,
        }

        if model_id:
            details["model_id"] = model_id

        if reason:
            details["reason"] = reason

        if remote_request_id:
            details["remote_request_id"] = remote_request_id

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelProviderServerError(ModelProviderError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_PROVIDER_SERVER_ERROR.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.BAD_GATEWAY,
    )
    default_message: ClassVar[str] = (
        "Der Modell-Provider hat einen Serverfehler gemeldet."
    )

    def __init__(
        self,
        *,
        provider_type: str,
        model_id: str | None = None,
        remote_status_code: int | None = None,
        remote_request_id: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.provider_type = provider_type
        self.model_id = model_id
        self.remote_status_code = remote_status_code
        self.remote_request_id = remote_request_id
        self.reason = reason

        details: dict[str, Any] = {
            "provider_type": provider_type,
        }

        if model_id:
            details["model_id"] = model_id

        if remote_status_code is not None:
            details["remote_status_code"] = remote_status_code

        if remote_request_id:
            details["remote_request_id"] = remote_request_id

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


# ============================================================
# Lifecycle
# ============================================================


class ModelLifecycleError(ModelError):
    """
    Basisklasse für Lade-, Entlade- und Shutdown-Fehler.
    """


class ModelLoadError(ModelLifecycleError):
    code: ClassVar[str] = ModelErrorCode.MODEL_LOAD_FAILED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.SERVICE_UNAVAILABLE,
    )
    default_message: ClassVar[str] = (
        "Das Modell konnte nicht geladen werden."
    )

    def __init__(
        self,
        model_id: str,
        *,
        provider_type: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.model_id = model_id
        self.provider_type = provider_type
        self.reason = reason

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if provider_type:
            details["provider_type"] = provider_type

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelUnloadError(ModelLifecycleError):
    code: ClassVar[str] = ModelErrorCode.MODEL_UNLOAD_FAILED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    default_message: ClassVar[str] = (
        "Das Modell konnte nicht entladen werden."
    )

    def __init__(
        self,
        model_id: str,
        *,
        provider_type: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.model_id = model_id
        self.provider_type = provider_type
        self.reason = reason

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if provider_type:
            details["provider_type"] = provider_type

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelAlreadyLoadedError(ModelLifecycleError):
    code: ClassVar[str] = ModelErrorCode.MODEL_ALREADY_LOADED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.CONFLICT,
    )
    default_message: ClassVar[str] = (
        "Das Modell ist bereits geladen."
    )

    def __init__(
        self,
        model_id: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id

        super().__init__(
            details={
                "model_id": model_id,
            },
            request_id=request_id,
        )


class ModelNotLoadedError(ModelLifecycleError):
    code: ClassVar[str] = ModelErrorCode.MODEL_NOT_LOADED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.CONFLICT,
    )
    default_message: ClassVar[str] = (
        "Das Modell ist nicht geladen."
    )

    def __init__(
        self,
        model_id: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id

        super().__init__(
            details={
                "model_id": model_id,
            },
            request_id=request_id,
        )


class ModelShutdownError(ModelLifecycleError):
    code: ClassVar[str] = ModelErrorCode.MODEL_SHUTDOWN_FAILED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    default_message: ClassVar[str] = (
        "Das Modell-Backend konnte nicht beendet werden."
    )

    def __init__(
        self,
        model_id: str,
        *,
        provider_type: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.model_id = model_id
        self.provider_type = provider_type
        self.reason = reason

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if provider_type:
            details["provider_type"] = provider_type

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


# ============================================================
# Anfrage- und Capability-Fehler
# ============================================================


class ModelRequestError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_REQUEST_INVALID.value
    status_code: ClassVar[int] = int(
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )
    default_message: ClassVar[str] = (
        "Die Modellanfrage ist ungültig."
    )


class InvalidModelRequestError(ModelRequestError):
    def __init__(
        self,
        *,
        model_id: str | None = None,
        field: str | None = None,
        reason: str | None = None,
        validation_errors: Sequence[
            Mapping[str, Any] | str
        ] | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.model_id = model_id
        self.field = field
        self.reason = reason
        self.validation_errors = tuple(validation_errors or ())

        details: dict[str, Any] = {}

        if model_id:
            details["model_id"] = model_id

        if field:
            details["field"] = field

        if reason:
            details["reason"] = reason

        if self.validation_errors:
            details["validation_errors"] = [
                (
                    dict(error)
                    if isinstance(error, Mapping)
                    else str(error)
                )
                for error in self.validation_errors
            ]

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class InvalidModelMessageError(ModelRequestError):
    code: ClassVar[str] = ModelErrorCode.MODEL_MESSAGE_INVALID.value
    default_message: ClassVar[str] = (
        "Eine Nachricht der Modellanfrage ist ungültig."
    )

    def __init__(
        self,
        *,
        message_index: int | None = None,
        role: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.message_index = message_index
        self.role = role
        self.reason = reason

        details: dict[str, Any] = {}

        if message_index is not None:
            details["message_index"] = message_index

        if role:
            details["role"] = role

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
        )


class ModelContextLimitError(ModelRequestError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_CONTEXT_LIMIT_EXCEEDED.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    )
    default_message: ClassVar[str] = (
        "Die Modellanfrage überschreitet das Kontextfenster."
    )

    def __init__(
        self,
        *,
        model_id: str,
        requested_tokens: int | None = None,
        context_window: int | None = None,
        prompt_tokens: int | None = None,
        reserved_output_tokens: int | None = None,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.requested_tokens = requested_tokens
        self.context_window = context_window
        self.prompt_tokens = prompt_tokens
        self.reserved_output_tokens = reserved_output_tokens

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if requested_tokens is not None:
            details["requested_tokens"] = requested_tokens

        if context_window is not None:
            details["context_window"] = context_window

        if prompt_tokens is not None:
            details["prompt_tokens"] = prompt_tokens

        if reserved_output_tokens is not None:
            details["reserved_output_tokens"] = (
                reserved_output_tokens
            )

        super().__init__(
            details=details,
            request_id=request_id,
        )


class ModelOutputLimitError(ModelRequestError):
    code: ClassVar[str] = ModelErrorCode.MODEL_OUTPUT_LIMIT_EXCEEDED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )
    default_message: ClassVar[str] = (
        "Die angeforderte Ausgabelänge ist nicht zulässig."
    )

    def __init__(
        self,
        *,
        model_id: str,
        requested_tokens: int,
        maximum_tokens: int,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.requested_tokens = requested_tokens
        self.maximum_tokens = maximum_tokens

        super().__init__(
            details={
                "model_id": model_id,
                "requested_tokens": requested_tokens,
                "maximum_tokens": maximum_tokens,
            },
            request_id=request_id,
        )


class ModelCapabilityNotSupportedError(ModelRequestError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_CAPABILITY_NOT_SUPPORTED.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )
    default_message: ClassVar[str] = (
        "Das Modell unterstützt die angeforderte Fähigkeit nicht."
    )

    def __init__(
        self,
        *,
        model_id: str,
        capability: str,
        provider_type: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.capability = capability
        self.provider_type = provider_type

        details: dict[str, Any] = {
            "model_id": model_id,
            "capability": capability,
        }

        if provider_type:
            details["provider_type"] = provider_type

        super().__init__(
            details=details,
            request_id=request_id,
        )


# ============================================================
# Generierung und Streaming
# ============================================================


class ModelGenerationError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_GENERATION_FAILED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.BAD_GATEWAY,
    )
    default_message: ClassVar[str] = (
        "Die Modellgenerierung ist fehlgeschlagen."
    )

    def __init__(
        self,
        *,
        model_id: str,
        provider_type: str | None = None,
        reason: str | None = None,
        remote_request_id: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.model_id = model_id
        self.provider_type = provider_type
        self.reason = reason
        self.remote_request_id = remote_request_id

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if provider_type:
            details["provider_type"] = provider_type

        if reason:
            details["reason"] = reason

        if remote_request_id:
            details["remote_request_id"] = remote_request_id

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelGenerationTimeoutError(ModelGenerationError):
    code: ClassVar[str] = ModelErrorCode.MODEL_GENERATION_TIMEOUT.value
    status_code: ClassVar[int] = int(
        HTTPStatus.GATEWAY_TIMEOUT,
    )
    default_message: ClassVar[str] = (
        "Die Modellgenerierung hat das Zeitlimit überschritten."
    )

    def __init__(
        self,
        *,
        model_id: str,
        timeout_seconds: float,
        provider_type: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds

        super().__init__(
            model_id=model_id,
            provider_type=provider_type,
            reason=None,
            request_id=request_id,
            cause=cause,
        )

        self.details["timeout_seconds"] = timeout_seconds


class ModelGenerationCancelledError(ModelGenerationError):
    code: ClassVar[str] = ModelErrorCode.MODEL_GENERATION_CANCELLED.value
    status_code: ClassVar[int] = 499
    default_message: ClassVar[str] = (
        "Die Modellgenerierung wurde abgebrochen."
    )


class ModelStreamError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_STREAM_FAILED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.BAD_GATEWAY,
    )
    default_message: ClassVar[str] = (
        "Der Modellstream ist fehlgeschlagen."
    )

    def __init__(
        self,
        *,
        model_id: str,
        provider_type: str | None = None,
        reason: str | None = None,
        remote_request_id: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.model_id = model_id
        self.provider_type = provider_type
        self.reason = reason
        self.remote_request_id = remote_request_id

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if provider_type:
            details["provider_type"] = provider_type

        if reason:
            details["reason"] = reason

        if remote_request_id:
            details["remote_request_id"] = remote_request_id

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelStreamTimeoutError(ModelStreamError):
    code: ClassVar[str] = ModelErrorCode.MODEL_STREAM_TIMEOUT.value
    status_code: ClassVar[int] = int(
        HTTPStatus.GATEWAY_TIMEOUT,
    )
    default_message: ClassVar[str] = (
        "Der Modellstream hat das Zeitlimit überschritten."
    )

    def __init__(
        self,
        *,
        model_id: str,
        timeout_seconds: float,
        provider_type: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds

        super().__init__(
            model_id=model_id,
            provider_type=provider_type,
            request_id=request_id,
            cause=cause,
        )

        self.details["timeout_seconds"] = timeout_seconds


class ModelStreamProtocolError(ModelStreamError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_STREAM_PROTOCOL_ERROR.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.BAD_GATEWAY,
    )
    default_message: ClassVar[str] = (
        "Der Modellstream verletzt das erwartete Protokoll."
    )

    def __init__(
        self,
        *,
        model_id: str,
        provider_type: str | None = None,
        reason: str,
        event_index: int | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.event_index = event_index

        super().__init__(
            model_id=model_id,
            provider_type=provider_type,
            reason=reason,
            request_id=request_id,
            cause=cause,
        )

        if event_index is not None:
            self.details["event_index"] = event_index


class ModelStreamCancelledError(ModelStreamError):
    code: ClassVar[str] = ModelErrorCode.MODEL_STREAM_CANCELLED.value
    status_code: ClassVar[int] = 499
    default_message: ClassVar[str] = (
        "Der Modellstream wurde abgebrochen."
    )


# ============================================================
# Tool Calls und strukturierte Ausgabe
# ============================================================


class InvalidModelToolCallError(ModelRequestError):
    code: ClassVar[str] = ModelErrorCode.MODEL_TOOL_CALL_INVALID.value
    default_message: ClassVar[str] = (
        "Das Modell hat einen ungültigen Tool-Aufruf erzeugt."
    )

    def __init__(
        self,
        *,
        model_id: str,
        tool_name: str | None = None,
        tool_call_id: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.model_id = model_id
        self.tool_name = tool_name
        self.tool_call_id = tool_call_id
        self.reason = reason

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if tool_name:
            details["tool_name"] = tool_name

        if tool_call_id:
            details["tool_call_id"] = tool_call_id

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ModelToolCallUnsupportedError(ModelRequestError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_TOOL_CALL_UNSUPPORTED.value
    )
    default_message: ClassVar[str] = (
        "Das Modell unterstützt keine Tool-Aufrufe."
    )

    def __init__(
        self,
        *,
        model_id: str,
        provider_type: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.provider_type = provider_type

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if provider_type:
            details["provider_type"] = provider_type

        super().__init__(
            details=details,
            request_id=request_id,
        )


class InvalidStructuredModelOutputError(ModelError):
    code: ClassVar[str] = (
        ModelErrorCode.MODEL_STRUCTURED_OUTPUT_INVALID.value
    )
    status_code: ClassVar[int] = int(
        HTTPStatus.BAD_GATEWAY,
    )
    default_message: ClassVar[str] = (
        "Die strukturierte Modellausgabe entspricht nicht dem Schema."
    )

    def __init__(
        self,
        *,
        model_id: str,
        schema_name: str | None = None,
        validation_errors: Sequence[
            Mapping[str, Any] | str
        ] | None = None,
        request_id: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.model_id = model_id
        self.schema_name = schema_name
        self.validation_errors = tuple(validation_errors or ())

        details: dict[str, Any] = {
            "model_id": model_id,
        }

        if schema_name:
            details["schema_name"] = schema_name

        if self.validation_errors:
            details["validation_errors"] = [
                (
                    dict(error)
                    if isinstance(error, Mapping)
                    else str(error)
                )
                for error in self.validation_errors
            ]

        super().__init__(
            details=details,
            request_id=request_id,
            cause=cause,
        )


# ============================================================
# Autorisierung und Konflikte
# ============================================================


class ModelAccessDeniedError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_ACCESS_DENIED.value
    status_code: ClassVar[int] = int(
        HTTPStatus.FORBIDDEN,
    )
    default_message: ClassVar[str] = (
        "Der Zugriff auf das Modell wurde verweigert."
    )

    def __init__(
        self,
        *,
        model_id: str,
        action: str,
        subject_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.action = action
        self.subject_id = subject_id

        details: dict[str, Any] = {
            "model_id": model_id,
            "action": action,
        }

        if subject_id:
            details["subject_id"] = subject_id

        super().__init__(
            details=details,
            request_id=request_id,
        )


class ModelOperationConflictError(ModelError):
    code: ClassVar[str] = ModelErrorCode.MODEL_OPERATION_CONFLICT.value
    status_code: ClassVar[int] = int(
        HTTPStatus.CONFLICT,
    )
    default_message: ClassVar[str] = (
        "Die Modelloperation steht im Konflikt mit dem aktuellen Zustand."
    )

    def __init__(
        self,
        *,
        model_id: str,
        operation: str,
        lifecycle_state: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.operation = operation
        self.lifecycle_state = lifecycle_state
        self.reason = reason

        details: dict[str, Any] = {
            "model_id": model_id,
            "operation": operation,
        }

        if lifecycle_state:
            details["lifecycle_state"] = lifecycle_state

        if reason:
            details["reason"] = reason

        super().__init__(
            details=details,
            request_id=request_id,
        )


# ============================================================
# Providerfehler-Übersetzung
# ============================================================


_PROVIDER_ERROR_NAME_MAP: Final[
    dict[str, type[ModelError]]
] = {
    "authenticationerror": ModelProviderAuthenticationError,
    "permissionerror": ModelProviderPermissionError,
    "ratelimiterror": ModelProviderRateLimitError,
    "connectionerror": ModelProviderConnectionError,
    "dependencyerror": ModelProviderDependencyError,
    "configurationerror": InvalidModelProviderConfigurationError,
    "responseerror": InvalidModelProviderResponseError,
    "servererror": ModelProviderServerError,
    "modelloaderror": ModelLoadError,
    "modelnotfounderror": ModelNotFoundError,
    "generationerror": ModelGenerationError,
    "streamtimeouterror": ModelStreamTimeoutError,
}


def translate_provider_error(
    error: BaseException,
    *,
    provider_type: str,
    model_id: str,
    request_id: str | None = None,
) -> ModelError:
    """
    Übersetzt eine providerspezifische Ausnahme in einen stabilen
    Kernschmied-Modellfehler.

    Provider sollten möglichst schon im ModelService explizit übersetzt
    werden. Diese Funktion dient als sichere gemeinsame Rückfallstrategie.

    Bereits übersetzte ModelError-Instanzen werden unverändert
    zurückgegeben.
    """

    if isinstance(error, ModelError):
        return error

    normalized_name = error.__class__.__name__.lower()
    error_message = str(error).strip() or error.__class__.__name__

    for suffix, target_type in _PROVIDER_ERROR_NAME_MAP.items():
        if not normalized_name.endswith(suffix):
            continue

        if target_type is ModelProviderAuthenticationError:
            return ModelProviderAuthenticationError(
                provider_type=provider_type,
                model_id=model_id,
                request_id=request_id,
                cause=error,
            )

        if target_type is ModelProviderPermissionError:
            return ModelProviderPermissionError(
                provider_type=provider_type,
                model_id=model_id,
                request_id=request_id,
                cause=error,
            )

        if target_type is ModelProviderRateLimitError:
            return ModelProviderRateLimitError(
                provider_type=provider_type,
                model_id=model_id,
                request_id=request_id,
                cause=error,
            )

        if target_type is ModelProviderConnectionError:
            return ModelProviderConnectionError(
                provider_type=provider_type,
                model_id=model_id,
                reason=error_message,
                request_id=request_id,
                cause=error,
            )

        if target_type is ModelProviderDependencyError:
            return ModelProviderDependencyError(
                provider_type=provider_type,
                model_id=model_id,
                dependency=error_message,
                request_id=request_id,
                cause=error,
            )

        if target_type is InvalidModelProviderConfigurationError:
            return InvalidModelProviderConfigurationError(
                provider_type=provider_type,
                model_id=model_id,
                reason=error_message,
                request_id=request_id,
                cause=error,
            )

        if target_type is InvalidModelProviderResponseError:
            return InvalidModelProviderResponseError(
                provider_type=provider_type,
                model_id=model_id,
                reason=error_message,
                request_id=request_id,
                cause=error,
            )

        if target_type is ModelProviderServerError:
            return ModelProviderServerError(
                provider_type=provider_type,
                model_id=model_id,
                reason=error_message,
                request_id=request_id,
                cause=error,
            )

        if target_type is ModelLoadError:
            return ModelLoadError(
                model_id=model_id,
                provider_type=provider_type,
                reason=error_message,
                request_id=request_id,
                cause=error,
            )

        if target_type is ModelNotFoundError:
            return ModelNotFoundError(
                model_id=model_id,
                request_id=request_id,
            )

        if target_type is ModelStreamTimeoutError:
            return ModelStreamTimeoutError(
                model_id=model_id,
                provider_type=provider_type,
                timeout_seconds=0.0,
                request_id=request_id,
                cause=error,
            )

        if target_type is ModelGenerationError:
            return ModelGenerationError(
                model_id=model_id,
                provider_type=provider_type,
                reason=error_message,
                request_id=request_id,
                cause=error,
            )

    return ModelGenerationError(
        model_id=model_id,
        provider_type=provider_type,
        reason=error_message,
        request_id=request_id,
        cause=error,
    )


__all__ = [
    "DuplicateModelManifestError",
    "DuplicateModelProviderError",
    "DuplicateModelRegistrationError",
    "InvalidModelManifestError",
    "InvalidModelMessageError",
    "InvalidModelProviderConfigurationError",
    "InvalidModelProviderFactoryError",
    "InvalidModelProviderResponseError",
    "InvalidModelRequestError",
    "InvalidModelToolCallError",
    "InvalidStructuredModelOutputError",
    "ModelAccessDeniedError",
    "ModelAlreadyLoadedError",
    "ModelCapabilityNotSupportedError",
    "ModelContextLimitError",
    "ModelDisabledError",
    "ModelError",
    "ModelErrorCode",
    "ModelGenerationCancelledError",
    "ModelGenerationError",
    "ModelGenerationTimeoutError",
    "ModelLifecycleError",
    "ModelLoadError",
    "ModelManifestError",
    "ModelManifestNotFoundError",
    "ModelManifestSecurityError",
    "ModelNotFoundError",
    "ModelNotLoadedError",
    "ModelNotReadyError",
    "ModelNotRegisteredError",
    "ModelOperationConflictError",
    "ModelOutputLimitError",
    "ModelProviderAuthenticationError",
    "ModelProviderConnectionError",
    "ModelProviderCreationError",
    "ModelProviderDependencyError",
    "ModelProviderError",
    "ModelProviderImportError",
    "ModelProviderPermissionError",
    "ModelProviderRateLimitError",
    "ModelProviderServerError",
    "ModelRequestError",
    "ModelShutdownError",
    "ModelStreamCancelledError",
    "ModelStreamError",
    "ModelStreamProtocolError",
    "ModelStreamTimeoutError",
    "ModelToolCallUnsupportedError",
    "ModelUnavailableError",
    "ModelUnloadError",
    "UnsupportedModelManifestVersionError",
    "UnknownModelProviderError",
    "translate_provider_error",
]