# F:\Kernschmied\backend\app\contracts\tool.py

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Protocol, TypeAlias, cast
from uuid import uuid4

from jsonschema import Draft202012Validator
from jsonschema.exceptions import (
    SchemaError,
)
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import JsonValue

TOOL_CONTRACT_VERSION: Final[str] = "1.0"


# Keine eigene rekursive JsonValue-Definition – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]
JsonMapping = Mapping[str, JsonValue]


def _empty_json_object() -> JsonObject:
    return {}


def _empty_permission_set() -> frozenset[str]:
    return frozenset()


def _normalize_validation_path(
    path: Iterable[object],
) -> tuple[str | int, ...]:
    normalized: list[str | int] = []

    for part in path:
        if isinstance(part, int):
            normalized.append(part)
        else:
            normalized.append(str(part))

    return tuple(normalized)


def _copy_json_mapping(
    value: JsonMapping,
) -> JsonObject:
    return deepcopy(dict(value))


class JsonSchemaValidatorProtocol(Protocol):
    """
    Minimaler typisierter Vertrag für einen JSON-Schema-Validator.

    Das Protocol verhindert, dass unvollständige Typinformationen aus
    jsonschema in den restlichen Anwendungscode gelangen.
    """

    def validate(
        self,
        instance: object,
    ) -> None: ...


class ToolContractError(Exception):
    """
    Basisklasse für Fehler innerhalb des Tool-Vertrags.
    """


class ToolDefinitionError(ToolContractError):
    """
    Fehlerhafte oder unvollständige Tool-Definition.
    """


class ToolInputValidationError(ToolContractError):
    """
    Die Eingabedaten entsprechen nicht dem Parameterschema.
    """

    def __init__(
        self,
        *,
        tool_id: str,
        message: str,
        path: tuple[str | int, ...] = (),
    ) -> None:
        self.tool_id = tool_id
        self.message = message
        self.path = path

        location = ".".join(str(part) for part in path) if path else "<root>"

        super().__init__(
            f"Ungültige Eingabe für Tool '{tool_id}' an '{location}': {message}",
        )


class ToolOutputValidationError(ToolContractError):
    """
    Das Tool-Ergebnis entspricht nicht dem Ausgabeschema.
    """

    def __init__(
        self,
        *,
        tool_id: str,
        message: str,
        path: tuple[str | int, ...] = (),
    ) -> None:
        self.tool_id = tool_id
        self.message = message
        self.path = path

        location = ".".join(str(part) for part in path) if path else "<root>"

        super().__init__(
            f"Ungültige Ausgabe von Tool '{tool_id}' an '{location}': {message}",
        )


class ToolExecutionError(ToolContractError):
    """
    Fachlich kontrollierter Fehler während einer Tool-Ausführung.
    """

    def __init__(
        self,
        *,
        tool_id: str,
        code: str,
        message: str,
        details: JsonMapping | None = None,
        retryable: bool = False,
    ) -> None:
        self.tool_id = tool_id
        self.code = code
        self.message = message
        self.details: JsonObject = (
            _copy_json_mapping(details) if details is not None else {}
        )
        self.retryable = retryable

        super().__init__(
            f"Tool '{tool_id}' fehlgeschlagen: {message}",
        )


class ToolAvailabilityError(ToolContractError):
    """
    Das Tool ist aktuell nicht verfügbar.
    """

    def __init__(
        self,
        *,
        tool_id: str,
        reason: str,
    ) -> None:
        self.tool_id = tool_id
        self.reason = reason

        super().__init__(
            f"Tool '{tool_id}' ist nicht verfügbar: {reason}",
        )


class ToolPermissionError(ToolContractError):
    """
    Der Benutzer besitzt nicht die benötigten Berechtigungen.
    """

    def __init__(
        self,
        *,
        tool_id: str,
        missing_permissions: tuple[str, ...],
    ) -> None:
        self.tool_id = tool_id
        self.missing_permissions = missing_permissions

        super().__init__(
            f"Fehlende Berechtigungen für Tool '{tool_id}': "
            f"{', '.join(missing_permissions)}",
        )


class ToolConfirmationRequiredError(ToolContractError):
    """
    Die Ausführung benötigt eine vorherige Benutzerbestätigung.
    """

    def __init__(
        self,
        *,
        tool_id: str,
        confirmation_message: str | None = None,
    ) -> None:
        self.tool_id = tool_id
        self.confirmation_message = confirmation_message

        super().__init__(
            confirmation_message
            or (f"Die Ausführung von Tool '{tool_id}' muss bestätigt werden."),
        )


class ToolRiskLevel(str, Enum):
    """
    Grobe Risikoklassifizierung für Tool-Ausführungen.
    """

    READ_ONLY = "read_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolAvailabilityStatus(str, Enum):
    """
    Aktueller Verfügbarkeitsstatus eines Tools.
    """

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


class ToolExecutionStatus(str, Enum):
    """
    Ergebnisstatus einer Tool-Ausführung.
    """

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolSideEffect(str, Enum):
    """
    Deklarierte Nebenwirkungen eines Tools.

    Die Angaben dienen der Autorisierung, Bestätigung und Darstellung.
    Sie ersetzen keine tatsächliche Sicherheitsprüfung.
    """

    NONE = "none"
    READ_EXTERNAL_DATA = "read_external_data"
    WRITE_EXTERNAL_DATA = "write_external_data"
    CREATE_RESOURCE = "create_resource"
    UPDATE_RESOURCE = "update_resource"
    DELETE_RESOURCE = "delete_resource"
    SEND_MESSAGE = "send_message"
    EXECUTE_CODE = "execute_code"
    ACCESS_FILESYSTEM = "access_filesystem"
    NETWORK_ACCESS = "network_access"
    ACCESS_SECRET = "access_secret"


@dataclass(frozen=True, slots=True)
class ToolAvailability:
    """
    Ergebnis der Verfügbarkeitsprüfung.
    """

    status: ToolAvailabilityStatus
    reason: str | None = None
    details: JsonMapping = field(
        default_factory=_empty_json_object,
    )

    @property
    def is_available(self) -> bool:
        return self.status in {
            ToolAvailabilityStatus.AVAILABLE,
            ToolAvailabilityStatus.DEGRADED,
        }


@dataclass(frozen=True, slots=True)
class ToolExecutionContext:
    """
    Serverseitig erzeugter Kontext einer Tool-Ausführung.

    Tool-Implementierungen dürfen keine Autorisierungsinformationen aus
    den eigentlichen Tool-Parametern übernehmen.
    """

    request_id: str
    execution_id: str

    user_id: str | None = None
    tenant_id: str | None = None

    node_id: str | None = None
    project_id: str | None = None
    chat_id: str | None = None

    granted_permissions: frozenset[str] = field(
        default_factory=_empty_permission_set,
    )

    confirmed: bool = False

    locale: str = "de"
    timezone: str = "Europe/Berlin"

    metadata: JsonMapping = field(
        default_factory=_empty_json_object,
    )

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        user_id: str | None = None,
        tenant_id: str | None = None,
        node_id: str | None = None,
        project_id: str | None = None,
        chat_id: str | None = None,
        granted_permissions: frozenset[str] | None = None,
        confirmed: bool = False,
        locale: str = "de",
        timezone: str = "Europe/Berlin",
        metadata: JsonMapping | None = None,
    ) -> ToolExecutionContext:
        normalized_permissions: frozenset[str] = (
            granted_permissions if granted_permissions is not None else frozenset()
        )

        normalized_metadata: JsonObject = (
            _copy_json_mapping(metadata) if metadata is not None else {}
        )

        return cls(
            request_id=request_id,
            execution_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            node_id=node_id,
            project_id=project_id,
            chat_id=chat_id,
            granted_permissions=normalized_permissions,
            confirmed=confirmed,
            locale=locale,
            timezone=timezone,
            metadata=normalized_metadata,
        )


@dataclass(frozen=True, slots=True)
class ToolResult:
    """
    Einheitliches Ergebnis einer Tool-Ausführung.
    """

    status: ToolExecutionStatus

    data: JsonMapping = field(
        default_factory=_empty_json_object,
    )

    message: str | None = None
    error_code: str | None = None

    details: JsonMapping = field(
        default_factory=_empty_json_object,
    )

    artifacts: tuple[JsonMapping, ...] = ()
    warnings: tuple[str, ...] = ()

    retryable: bool = False

    @classmethod
    def success(
        cls,
        *,
        data: JsonMapping | None = None,
        message: str | None = None,
        artifacts: tuple[JsonMapping, ...] = (),
        warnings: tuple[str, ...] = (),
    ) -> ToolResult:
        normalized_data: JsonObject = (
            _copy_json_mapping(data) if data is not None else {}
        )

        return cls(
            status=ToolExecutionStatus.SUCCESS,
            data=normalized_data,
            message=message,
            artifacts=artifacts,
            warnings=warnings,
        )

    @classmethod
    def partial_success(
        cls,
        *,
        data: JsonMapping | None = None,
        message: str | None = None,
        details: JsonMapping | None = None,
        artifacts: tuple[JsonMapping, ...] = (),
        warnings: tuple[str, ...] = (),
    ) -> ToolResult:
        normalized_data: JsonObject = (
            _copy_json_mapping(data) if data is not None else {}
        )

        normalized_details: JsonObject = (
            _copy_json_mapping(details) if details is not None else {}
        )

        return cls(
            status=ToolExecutionStatus.PARTIAL_SUCCESS,
            data=normalized_data,
            message=message,
            details=normalized_details,
            artifacts=artifacts,
            warnings=warnings,
        )

    @classmethod
    def failure(
        cls,
        *,
        error_code: str,
        message: str,
        details: JsonMapping | None = None,
        retryable: bool = False,
    ) -> ToolResult:
        normalized_details: JsonObject = (
            _copy_json_mapping(details) if details is not None else {}
        )

        return cls(
            status=ToolExecutionStatus.FAILED,
            error_code=error_code,
            message=message,
            details=normalized_details,
            retryable=retryable,
        )


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """
    Versionierter, serialisierbarer Vertrag eines Tools.
    """

    contract_version: str

    id: str
    name: str
    version: str
    description: str

    parameters_schema: JsonMapping
    result_schema: JsonMapping | None

    permissions: tuple[str, ...]

    requires_confirmation: bool
    confirmation_message: str | None

    risk_level: ToolRiskLevel

    side_effects: tuple[ToolSideEffect, ...]

    idempotent: bool
    enabled_by_default: bool

    timeout_seconds: float | None

    tags: tuple[str, ...]

    metadata: JsonMapping

    def as_dict(self) -> JsonObject:
        serialized: JsonObject = {
            "contract_version": self.contract_version,
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "parameters_schema": _copy_json_mapping(
                self.parameters_schema,
            ),
            "result_schema": (
                _copy_json_mapping(self.result_schema)
                if self.result_schema is not None
                else None
            ),
            "permissions": list(self.permissions),
            "requires_confirmation": self.requires_confirmation,
            "confirmation_message": self.confirmation_message,
            "risk_level": self.risk_level.value,
            "side_effects": [side_effect.value for side_effect in self.side_effects],
            "idempotent": self.idempotent,
            "enabled_by_default": self.enabled_by_default,
            "timeout_seconds": self.timeout_seconds,
            "tags": list(self.tags),
            "metadata": _copy_json_mapping(
                self.metadata,
            ),
        }

        return serialized


ToolProgressCallback: TypeAlias = Callable[
    [JsonMapping],
    Awaitable[None],
]


class BaseTool(ABC):
    """
    Einheitlicher Vertrag für alle Kernschmied-Tools.

    Tool-Implementierungen deklarieren ausschließlich Metadaten,
    Eingabe-/Ausgabeschemata und ihre fachliche Ausführung.

    Autorisierung, Bestätigung, Timeout, Idempotenz und Auditierung
    werden zusätzlich durch den serverseitigen Tool-Executor erzwungen.
    """

    tool_id: str
    name: str
    description: str

    version: str = "1.0.0"

    parameters_schema: JsonMapping = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    result_schema: JsonMapping | None = None

    permissions: tuple[str, ...] = ()

    requires_confirmation: bool = False
    confirmation_message: str | None = None

    risk_level: ToolRiskLevel = ToolRiskLevel.READ_ONLY

    side_effects: tuple[ToolSideEffect, ...] = (ToolSideEffect.NONE,)

    idempotent: bool = True
    enabled_by_default: bool = False

    timeout_seconds: float | None = 60.0

    tags: tuple[str, ...] = ()

    metadata: JsonMapping = {}

    def __init__(self) -> None:
        self._validate_definition()

        raw_input_validator: object = Draft202012Validator(
            dict(self.parameters_schema),
        )

        self._input_validator: JsonSchemaValidatorProtocol = cast(
            JsonSchemaValidatorProtocol,
            raw_input_validator,
        )

        if self.result_schema is None:
            self._output_validator: JsonSchemaValidatorProtocol | None = None
        else:
            raw_output_validator: object = Draft202012Validator(
                dict(self.result_schema),
            )

            self._output_validator = cast(
                JsonSchemaValidatorProtocol,
                raw_output_validator,
            )

    def definition(self) -> ToolDefinition:
        """
        Liefert die unveränderliche öffentliche Tool-Definition.
        """

        return ToolDefinition(
            contract_version=TOOL_CONTRACT_VERSION,
            id=self.tool_id,
            name=self.name,
            version=self.version,
            description=self.description,
            parameters_schema=_copy_json_mapping(
                self.parameters_schema,
            ),
            result_schema=(
                _copy_json_mapping(self.result_schema)
                if self.result_schema is not None
                else None
            ),
            permissions=tuple(self.permissions),
            requires_confirmation=self.requires_confirmation,
            confirmation_message=self.confirmation_message,
            risk_level=self.risk_level,
            side_effects=tuple(self.side_effects),
            idempotent=self.idempotent,
            enabled_by_default=self.enabled_by_default,
            timeout_seconds=self.timeout_seconds,
            tags=tuple(self.tags),
            metadata=_copy_json_mapping(
                self.metadata,
            ),
        )

    async def availability(self) -> ToolAvailability:
        """
        Prüft die aktuelle technische Verfügbarkeit.

        Tools mit externen Abhängigkeiten können diese Methode
        überschreiben.
        """

        return ToolAvailability(
            status=ToolAvailabilityStatus.AVAILABLE,
        )

    def validate_input(
        self,
        arguments: JsonMapping,
    ) -> JsonObject:
        """
        Validiert und kopiert die Eingabeparameter.
        """

        input_data = _copy_json_mapping(
            arguments,
        )

        try:
            self._input_validator.validate(
                input_data,
            )

        except JsonSchemaValidationError as exc:
            raw_path = cast(
                Iterable[object],
                exc.absolute_path,
            )

            raise ToolInputValidationError(
                tool_id=self.tool_id,
                message=exc.message,
                path=_normalize_validation_path(
                    raw_path,
                ),
            ) from exc

        return input_data

    def validate_output(
        self,
        result: ToolResult,
    ) -> ToolResult:
        """
        Validiert erfolgreiche Ergebnisdaten gegen das Ausgabeschema.

        Fehlerergebnisse werden nicht gegen das fachliche Result-Schema
        geprüft, da sie dem allgemeinen ToolResult-Vertrag folgen.
        """

        if self._output_validator is None:
            return result

        if result.status not in {
            ToolExecutionStatus.SUCCESS,
            ToolExecutionStatus.PARTIAL_SUCCESS,
        }:
            return result

        output_data = _copy_json_mapping(
            result.data,
        )

        try:
            self._output_validator.validate(
                output_data,
            )

        except JsonSchemaValidationError as exc:
            raw_path = cast(
                Iterable[object],
                exc.absolute_path,
            )

            raise ToolOutputValidationError(
                tool_id=self.tool_id,
                message=exc.message,
                path=_normalize_validation_path(
                    raw_path,
                ),
            ) from exc

        return result

    def assert_permissions(
        self,
        context: ToolExecutionContext,
    ) -> None:
        """
        Zusätzliche defensive Berechtigungsprüfung.

        Die zentrale Autorisierung muss bereits vor dem Tool-Aufruf
        stattfinden. Diese Prüfung verhindert versehentliche direkte
        Ausführungen ohne Berechtigung.
        """

        missing_permissions = tuple(
            permission
            for permission in self.permissions
            if not self._has_permission(
                context.granted_permissions,
                permission,
            )
        )

        if missing_permissions:
            raise ToolPermissionError(
                tool_id=self.tool_id,
                missing_permissions=missing_permissions,
            )

    def assert_confirmation(
        self,
        context: ToolExecutionContext,
    ) -> None:
        """
        Verhindert die Ausführung bestätigungspflichtiger Tools ohne
        serverseitig verifizierte Bestätigung.
        """

        if not self.requires_confirmation:
            return

        if context.confirmed:
            return

        raise ToolConfirmationRequiredError(
            tool_id=self.tool_id,
            confirmation_message=self.confirmation_message,
        )

    async def invoke(
        self,
        arguments: JsonMapping,
        *,
        context: ToolExecutionContext,
        progress: ToolProgressCallback | None = None,
    ) -> ToolResult:
        """
        Standardisierter interner Ausführungsweg.

        Der zentrale Tool-Executor kann zusätzlich Timeout,
        Idempotenzschutz, Audit-Log und Transaktionsgrenzen anwenden.
        """

        availability = await self.availability()

        if not availability.is_available:
            raise ToolAvailabilityError(
                tool_id=self.tool_id,
                reason=(availability.reason or availability.status.value),
            )

        self.assert_permissions(
            context,
        )

        self.assert_confirmation(
            context,
        )

        validated_arguments = self.validate_input(
            arguments,
        )

        result = await self.execute(
            validated_arguments,
            context=context,
            progress=progress,
        )

        return self.validate_output(
            result,
        )

    @abstractmethod
    async def execute(
        self,
        arguments: JsonMapping,
        *,
        context: ToolExecutionContext,
        progress: ToolProgressCallback | None = None,
    ) -> ToolResult:
        """
        Führt die fachliche Tool-Logik aus.

        Implementierungen dürfen sich nicht darauf verlassen, dass Werte
        aus `arguments` autorisiert oder vertrauenswürdig sind. Alle
        sicherheitsrelevanten Informationen stammen aus `context`.
        """

        raise NotImplementedError

    async def shutdown(self) -> None:
        """
        Optionaler Lebenszyklus-Hook zum Freigeben von Ressourcen.
        """

        return

    def _validate_definition(self) -> None:
        required_strings: dict[str, object] = {
            "tool_id": getattr(
                self,
                "tool_id",
                None,
            ),
            "name": getattr(
                self,
                "name",
                None,
            ),
            "version": getattr(
                self,
                "version",
                None,
            ),
            "description": getattr(
                self,
                "description",
                None,
            ),
        }

        for field_name, value in required_strings.items():
            if not isinstance(value, str) or not value.strip():
                raise ToolDefinitionError(
                    f"Tool-Feld '{field_name}' muss ein nicht leerer String sein.",
                )

        if not self._is_valid_identifier(
            self.tool_id,
        ):
            raise ToolDefinitionError(
                "tool_id darf nur Kleinbuchstaben, Ziffern, "
                "Unterstriche, Punkte und Bindestriche enthalten.",
            )

        try:
            Draft202012Validator.check_schema(
                dict(self.parameters_schema),
            )

        except SchemaError as exc:
            raise ToolDefinitionError(
                f"Ungültiges Parameterschema für '{self.tool_id}': {exc.message}",
            ) from exc

        if self.result_schema is not None:
            try:
                Draft202012Validator.check_schema(
                    dict(self.result_schema),
                )

            except SchemaError as exc:
                raise ToolDefinitionError(
                    f"Ungültiges Ergebnisschema für '{self.tool_id}': {exc.message}",
                ) from exc

        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ToolDefinitionError(
                f"timeout_seconds von '{self.tool_id}' muss größer als null sein.",
            )

        if self.requires_confirmation and not self.confirmation_message:
            raise ToolDefinitionError(
                f"Bestätigungspflichtiges Tool '{self.tool_id}' "
                "benötigt eine confirmation_message.",
            )

        if (
            self.risk_level
            in {
                ToolRiskLevel.HIGH,
                ToolRiskLevel.CRITICAL,
            }
            and not self.requires_confirmation
        ):
            raise ToolDefinitionError(
                f"Tool '{self.tool_id}' besitzt das Risiko "
                f"'{self.risk_level.value}', verlangt aber keine "
                "Bestätigung.",
            )

        normalized_permissions = tuple(
            permission.strip() for permission in self.permissions if permission.strip()
        )

        if len(normalized_permissions) != len(
            set(normalized_permissions),
        ):
            raise ToolDefinitionError(
                f"Tool '{self.tool_id}' enthält doppelte Berechtigungen.",
            )

    @staticmethod
    def _is_valid_identifier(
        value: str,
    ) -> bool:
        allowed_characters = set(
            "abcdefghijklmnopqrstuvwxyz0123456789._-",
        )

        return bool(value) and all(
            character in allowed_characters for character in value
        )

    @staticmethod
    def _has_permission(
        granted_permissions: frozenset[str],
        required_permission: str,
    ) -> bool:
        if "*" in granted_permissions:
            return True

        if required_permission in granted_permissions:
            return True

        required_parts = required_permission.split(":")

        for index in range(
            len(required_parts),
            0,
            -1,
        ):
            wildcard_permission = ":".join(required_parts[:index]) + ":*"

            if wildcard_permission in granted_permissions:
                return True

        return False
