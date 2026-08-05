# F:\Kernschmied\backend\app\api\v1\ui.py

from __future__ import annotations

import inspect
import logging
from collections.abc import (
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from typing import Annotated, Literal, cast

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,  # NEU: Pydantic's JsonValue
    ValidationError,
)

from app.services.ui_schema_service import build_ui_schema

logger = logging.getLogger(__name__)

router = APIRouter()


UI_SCHEMA_VERSION = "1.0"
UI_API_SCHEMA_VERSION = "1.0"

MAX_SCHEMA_DEPTH = 32
MAX_SCHEMA_ITEMS = 10_000


# Keine eigene rekursive JsonValue-Definition mehr – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


class UIComponentDefinition(BaseModel):
    """
    Beschreibung einer bekannten generischen UI-Komponente.

    Der konkrete Komponententyp muss im Frontend in einer festen
    Komponenten-Registry vorhanden sein.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    id: str
    type: str

    title: str | None = None
    description: str | None = None

    props: Annotated[
        JsonObject,
        Field(default_factory=dict),
    ]

    children: Annotated[
        list[UIComponentDefinition],
        Field(default_factory=list),
    ]

    visible: bool = True
    enabled: bool = True


class UIActionDefinition(BaseModel):
    """
    Beschreibung einer frontendseitig bekannten Aktion.

    Eine deklarierte Aktion ersetzt niemals die serverseitige
    Autorisierung des zugehörigen API-Endpunkts.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    id: str
    type: str

    label: str | None = None
    icon: str | None = None

    endpoint: str | None = None

    method: (
        Literal[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        ]
        | None
    ) = None

    required_permissions: list[str] = Field(
        default_factory=list,
    )

    confirmation_required: bool = False
    enabled: bool = True

    payload_schema: JsonObject | None = None


class UIFormDefinition(BaseModel):
    """
    Dynamisch renderbares Formular.

    `form_schema` wird im öffentlichen JSON-Vertrag weiterhin unter
    dem Feldnamen `schema` ausgegeben.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str

    title: str | None = None
    description: str | None = None

    form_schema: JsonObject = Field(
        validation_alias="schema",
        serialization_alias="schema",
    )

    submit_action_id: str | None = None


class UISchemaDocument(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_name: str = Field(default="default")
    schema_version: str = Field(default=UI_SCHEMA_VERSION)

    node_types: JsonObject = Field(default_factory=dict)
    forms: JsonObject = Field(default_factory=dict)
    components: JsonObject = Field(default_factory=dict)
    actions: JsonObject = Field(default_factory=dict)
    metadata: JsonObject = Field(default_factory=dict)


class UISchemaResponse(BaseModel):
    """
    Transportvertrag des API-Endpunkts.

    `ui_schema` wird im öffentlichen JSON-Vertrag weiterhin als
    `schema` serialisiert.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        serialize_by_alias=True,
    )

    api_schema_version: str = UI_API_SCHEMA_VERSION
    ui_schema_version: str

    config_revision: int = Field(
        default=0,
        ge=0,
    )

    ui_schema: UISchemaDocument = Field(
        validation_alias="schema",
        serialization_alias="schema",
    )

    request_id: str | None = None


UIComponentDefinition.model_rebuild()
UIActionDefinition.model_rebuild()
UIFormDefinition.model_rebuild()
UISchemaDocument.model_rebuild()
UISchemaResponse.model_rebuild()


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


def structured_error(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Mapping[str, object] | None = None,
) -> HTTPException:
    normalized_details: dict[str, object] = {}

    if details is not None:
        normalized_details = dict(
            details,
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


def normalize_non_negative_int(
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
        float,
    ):
        if not value.is_integer():
            return default

        return max(
            int(value),
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


async def read_revision(
    source: object | None,
) -> int:
    if source is None:
        return 0

    revision_getter: object = getattr(
        source,
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

            return normalize_non_negative_int(
                resolved_revision,
            )

        except (
            RuntimeError,
            TypeError,
            ValueError,
        ):
            return 0

    raw_revision = getattr(
        source,
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


async def get_config_revision(
    request: Request,
) -> int:
    config_service: object | None = getattr(
        request.app.state,
        "config_service",
        None,
    )

    return await read_revision(
        config_service,
    )


def as_object_mapping(
    value: object,
) -> Mapping[object, object] | None:
    if not isinstance(
        value,
        Mapping,
    ):
        return None

    return cast(
        Mapping[object, object],
        value,
    )


def as_object_sequence(
    value: object,
) -> Sequence[object] | None:
    if isinstance(
        value,
        str | bytes | bytearray,
    ):
        return None

    if not isinstance(
        value,
        Sequence,
    ):
        return None

    return cast(
        Sequence[object],
        value,
    )


def normalize_json_key(
    value: object,
) -> str:
    normalized = str(
        value,
    ).strip()

    return normalized


def sanitize_json_value(
    value: object,
    *,
    depth: int = 0,
    item_counter: list[int] | None = None,
) -> JsonValue:
    """
    Wandelt den Schema-Builder-Output in sichere JSON-Werte um.

    Verhindert unter anderem:

    - unbegrenzte Rekursion
    - nicht serialisierbare Python-Objekte
    - versehentlich ausgegebene Callables
    - extrem große Schema-Strukturen
    """

    if item_counter is None:
        item_counter = [0]

    item_counter[0] += 1

    if item_counter[0] > MAX_SCHEMA_ITEMS:
        raise ValueError("Das UI-Schema überschreitet die maximal erlaubte Größe.")

    if depth > MAX_SCHEMA_DEPTH:
        raise ValueError("Das UI-Schema überschreitet die maximal erlaubte Tiefe.")

    if value is None:
        return None

    if isinstance(
        value,
        str | int | float | bool,
    ):
        return value

    if callable(
        value,
    ):
        raise ValueError("Callables dürfen nicht Bestandteil des UI-Schemas sein.")

    if isinstance(
        value,
        BaseModel,
    ):
        dumped_value: object = value.model_dump(
            mode="json",
            exclude_none=True,
            by_alias=True,
        )

        return sanitize_json_value(
            dumped_value,
            depth=depth + 1,
            item_counter=item_counter,
        )

    mapping = as_object_mapping(
        value,
    )

    if mapping is not None:
        result: JsonObject = {}

        blocked_keys: set[str] = {
            "secret",
            "password",
            "token",
            "api_key",
            "apikey",
            "credential",
            "credentials",
            "authorization",
            "headers",
            "handler",
            "callable",
            "implementation",
            "module",
            "class",
            "import_path",
            "python_path",
            "file_path",
            "local_path",
        }

        for raw_key, raw_value in mapping.items():
            key = normalize_json_key(
                raw_key,
            )

            if not key:
                continue

            if key.casefold() in blocked_keys:
                continue

            result[key] = sanitize_json_value(
                raw_value,
                depth=depth + 1,
                item_counter=item_counter,
            )

        return result

    sequence = as_object_sequence(
        value,
    )

    if sequence is not None:
        return [
            sanitize_json_value(
                item,
                depth=depth + 1,
                item_counter=item_counter,
            )
            for item in sequence
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
            sanitize_json_value(
                item,
                depth=depth + 1,
                item_counter=item_counter,
            )
            for item in typed_set
        ]

    raise ValueError(
        "Das UI-Schema enthält einen nicht unterstützten Wert "
        f"vom Typ '{type(value).__name__}'."
    )


def normalize_json_object(
    value: object,
) -> JsonObject | None:
    sanitized = sanitize_json_value(
        value,
    )

    if not isinstance(
        sanitized,
        dict,
    ):
        return None

    return sanitized


async def call_ui_schema_builder(
    request: Request,
    *,
    include_disabled: bool,
) -> object:
    """
    Ruft den vorhandenen Schema-Builder auf.

    Unterstützt während der Migration mehrere mögliche Signaturen:

    - build_ui_schema()
    - build_ui_schema(request=request)
    - build_ui_schema(app=request.app)
    - build_ui_schema(
          request=request,
          include_disabled=...,
      )

    Neue Implementierungen sollten bevorzugt explizite Dependencies
    statt direkten Zugriff auf globale Zustände verwenden.
    """

    builder = cast(
        Callable[..., object],
        build_ui_schema,
    )

    try:
        signature = inspect.signature(
            builder,
        )

        parameters = signature.parameters

        kwargs: dict[str, object] = {}

        if "request" in parameters:
            kwargs["request"] = request

        if "app" in parameters:
            kwargs["app"] = request.app

        if "include_disabled" in parameters:
            kwargs["include_disabled"] = include_disabled

        raw_result: object = builder(
            **kwargs,
        )

        return await resolve_maybe_awaitable(
            raw_result,
        )

    except TypeError as exc:
        logger.exception(
            "Unsupported UI schema builder signature",
            extra={
                "request_id": get_request_id(
                    request,
                ),
            },
        )

        raise structured_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="UI_SCHEMA_BUILDER_CONTRACT_UNSUPPORTED",
            message=(
                "Der UI-Schema-Builder unterstützt den erwarteten Aufrufvertrag nicht."
            ),
            details={
                "reason": str(
                    exc,
                ),
            },
        ) from exc


def normalize_schema_collection(
    value: JsonValue,
    *,
    field_name: str,
    type_source_field: str,
) -> list[JsonValue]:
    raw_items: list[JsonValue]

    if isinstance(
        value,
        list,
    ):
        raw_items = list(
            value,
        )

    elif isinstance(
        value,
        dict,
    ):
        raw_items = []

        for registry_key, registry_value in value.items():
            if not isinstance(
                registry_value,
                dict,
            ):
                raise ValueError(
                    f"{field_name}.{registry_key} muss ein Objekt sein.",
                )

            normalized_registry_value: JsonObject = dict(
                registry_value,
            )

            normalized_registry_value.setdefault(
                "id",
                registry_key,
            )

            raw_items.append(
                normalized_registry_value,
            )

    else:
        raise ValueError(
            f"{field_name} muss eine Liste oder ein Objekt sein.",
        )

    result: list[JsonValue] = []

    for index, raw_item in enumerate(
        raw_items,
    ):
        if not isinstance(
            raw_item,
            dict,
        ):
            raise ValueError(
                f"{field_name}[{index}] muss ein Objekt sein.",
            )

        normalized_item: JsonObject = dict(
            raw_item,
        )

        if "type" not in normalized_item:
            source_type = normalized_item.get(
                type_source_field,
            )

            if (
                not isinstance(
                    source_type,
                    str,
                )
                or not source_type.strip()
            ):
                raise ValueError(
                    f"{field_name}[{index}] benötigt entweder "
                    f"'type' oder '{type_source_field}'.",
                )

            normalized_item["type"] = source_type.strip()

        normalized_item.pop(
            type_source_field,
            None,
        )

        result.append(
            normalized_item,
        )

    return result


def normalize_ui_schema(
    raw_schema: object,
    *,
    request: Request,
) -> UISchemaDocument:
    try:
        sanitized = sanitize_json_value(raw_schema)
    except ValueError as exc:
        raise structured_error(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="UI_SCHEMA_INVALID",
            message="Das erzeugte UI-Schema ist ungültig.",
            details={"reason": str(exc)},
        ) from exc

    if not isinstance(sanitized, dict):
        raise structured_error(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="UI_SCHEMA_INVALID_ROOT",
            message="Der Wurzelwert des UI-Schemas muss ein Objekt sein.",
            details={"received_type": type(sanitized).__name__},
        )

    schema_data: JsonObject = sanitized

    # Standardwerte für fehlende Felder setzen
    schema_data.setdefault("schema_name", "default")
    schema_data.setdefault("schema_version", UI_SCHEMA_VERSION)
    schema_data.setdefault("node_types", {})
    schema_data.setdefault("forms", {})
    schema_data.setdefault("components", {})
    schema_data.setdefault("actions", {})
    schema_data.setdefault("metadata", {})

    # Normalisiere Listen (falls sie als Listen kommen) – aber node_types ist ein Objekt, keine Liste
    # Für components, actions, forms: wenn sie als Liste kommen, wandle sie in ein dict um,
    # wobei der Typ als Schlüssel dient (ähnlich wie Frontend es erwartet).
    # Oder wir erwarten, dass der Builder bereits ein dict liefert.
    # Ich gehe davon aus, dass der Builder bereits die richtige Struktur liefert.
    # Wir validieren nur mit Pydantic.

    try:
        return UISchemaDocument.model_validate(schema_data)
    except ValidationError as exc:
        validation_errors = [
            cast(dict[str, object], error)
            for error in exc.errors(
                include_url=False,
                include_input=False,
                include_context=False,
            )
        ]
        logger.exception(
            "UI schema validation failed",
            extra={
                "request_id": get_request_id(request),
                "validation_errors": validation_errors,
            },
        )
        raise structured_error(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="UI_SCHEMA_VALIDATION_FAILED",
            message=(
                "Das erzeugte UI-Schema entspricht nicht dem "
                "öffentlichen Schema-Vertrag."
            ),
            details={"errors": validation_errors},
        ) from exc


@router.get(
    "/schema",
    response_model=UISchemaResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
    summary="UI-Schema laden",
    description=(
        "Liefert den versionierten, schema-gesteuerten UI-Vertrag. "
        "Das Frontend darf ausschließlich bekannte Komponenten- und "
        "Aktionstypen aus seinen festen Registries ausführen."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": ("Das UI-Schema wurde erfolgreich erzeugt."),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": ("Das erzeugte UI-Schema ist ungültig."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": ("Der UI-Schema-Builder ist nicht verfügbar."),
        },
    },
)
async def ui_schema(
    request: Request,
    response: Response,
    include_disabled: bool = Query(
        default=False,
        description=(
            "Deaktivierte Schemaelemente mit ausgeben. "
            "Für administrative Ansichten vorgesehen."
        ),
    ),
) -> UISchemaResponse:
    """
    Erzeugt das UI-Schema für das Frontend.

    Wichtig:
    Das Schema beschreibt nur Darstellung und bekannte Aktionen.
    Es kann keine serverseitigen Berechtigungen überschreiben.
    """

    try:
        raw_schema = await call_ui_schema_builder(
            request,
            include_disabled=include_disabled,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "UI schema generation failed",
            extra={
                "request_id": get_request_id(
                    request,
                ),
            },
        )

        raise structured_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="UI_SCHEMA_BUILD_FAILED",
            message="Das UI-Schema konnte nicht erzeugt werden.",
        ) from exc

    normalized_schema = normalize_ui_schema(
        raw_schema,
        request=request,
    )

    config_revision = await get_config_revision(
        request,
    )

    response.headers["Cache-Control"] = "no-store, private"

    response.headers["X-UI-Schema-Version"] = normalized_schema.schema_version

    response.headers["X-UI-API-Schema-Version"] = UI_API_SCHEMA_VERSION

    response.headers["X-Config-Revision"] = str(
        config_revision,
    )

    return UISchemaResponse(
        ui_schema_version=normalized_schema.schema_version,
        config_revision=config_revision,
        ui_schema=normalized_schema,
        request_id=get_request_id(
            request,
        ),
    )
