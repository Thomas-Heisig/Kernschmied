# F:\Kernschmied\backend\app\api\v1\tools.py

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Mapping, Sequence
from typing import Literal, cast

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
)

logger = logging.getLogger(__name__)

router = APIRouter()


TOOL_API_SCHEMA_VERSION = "1.0"


# Keine eigene rekursive JsonValue-Definition mehr – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


class ToolCapabilities(BaseModel):
    """
    Technische Fähigkeiten eines Tools.

    Diese Angaben beschreiben lediglich die Tool-Schnittstelle.
    Sie stellen keine Ausführungsberechtigung dar.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    streaming: bool = False
    confirmation_required: bool = False
    idempotent: bool = False
    read_only: bool = False
    supports_cancellation: bool = False

    additional: list[str] = Field(
        default_factory=list,
    )


class ToolInputSchema(BaseModel):
    """
    Öffentliche Beschreibung des Tool-Eingabeschemas.

    Das Schema bleibt JSON-Schema-artig, damit das Frontend daraus
    generische Formulare erzeugen kann.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    type: str = "object"

    properties: JsonObject = Field(
        default_factory=dict,
    )

    required: list[str] = Field(
        default_factory=list,
    )

    additionalProperties: bool | JsonObject | None = None


class ToolEntry(BaseModel):
    """
    Öffentlicher, frontendfähiger Tool-Eintrag.

    Interne Python-Pfade, Importnamen, Zugangsdaten und ausführbare
    Implementierungsdetails werden nicht ausgegeben.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    name: str
    version: str = "1.0.0"

    description: str | None = None
    category: str | None = None

    enabled: bool = True
    available: bool = True
    selectable: bool = True

    capabilities: ToolCapabilities = Field(
        default_factory=ToolCapabilities,
    )

    input_schema: ToolInputSchema = Field(
        default_factory=ToolInputSchema,
    )

    output_schema: JsonObject | None = None

    required_permissions: list[str] = Field(
        default_factory=list,
    )

    tags: list[str] = Field(
        default_factory=list,
    )

    metadata: JsonObject = Field(
        default_factory=dict,
    )


class ToolListResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: str = TOOL_API_SCHEMA_VERSION

    registry_revision: int = Field(
        default=0,
        ge=0,
    )

    config_revision: int = Field(
        default=0,
        ge=0,
    )

    items: list[ToolEntry]

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


def get_tool_registry(
    request: Request,
) -> object:
    registry: object | None = getattr(
        request.app.state,
        "tool_registry",
        None,
    )

    if registry is None:
        raise structured_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="TOOL_REGISTRY_UNAVAILABLE",
            message="Die Tool-Registry ist nicht verfügbar.",
        )

    return registry


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

    raw_revision: object = getattr(
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


async def get_registry_revision(
    registry: object,
) -> int:
    return await read_revision(
        registry,
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


def read_mapping_value(
    source: Mapping[object, object],
    key: str,
    default: object = None,
) -> object:
    if key not in source:
        return default

    return source[key]


def read_value(
    source: object,
    *keys: str,
    default: object = None,
) -> object:
    source_mapping = as_object_mapping(
        source,
    )

    if source_mapping is not None:
        for key in keys:
            if key in source_mapping:
                return source_mapping[key]

    for key in keys:
        try:
            value: object = getattr(
                source,
                key,
            )
        except AttributeError:
            continue

        return value

    return default


def normalize_string(
    value: object,
    *,
    default: str = "",
) -> str:
    if value is None:
        return default

    normalized = str(
        value,
    ).strip()

    return normalized or default


def normalize_optional_string(
    value: object,
) -> str | None:
    if value is None:
        return None

    normalized = str(
        value,
    ).strip()

    return normalized or None


def normalize_bool(
    value: object,
    *,
    default: bool,
) -> bool:
    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return value != 0

    if isinstance(
        value,
        str,
    ):
        normalized = value.strip().casefold()

        if normalized in {
            "true",
            "1",
            "yes",
            "on",
            "enabled",
        }:
            return True

        if normalized in {
            "false",
            "0",
            "no",
            "off",
            "disabled",
        }:
            return False

    return default


def normalize_string_list(
    value: object,
) -> list[str]:
    if value is None:
        return []

    if isinstance(
        value,
        str,
    ):
        normalized = normalize_string(
            value,
        )

        return [normalized] if normalized else []

    sequence = as_object_sequence(
        value,
    )

    if sequence is not None:
        iterable: tuple[object, ...] = tuple(
            sequence,
        )

    elif isinstance(
        value,
        set | frozenset,
    ):
        typed_set = cast(
            set[object] | frozenset[object],
            value,
        )

        iterable = tuple(
            typed_set,
        )

    else:
        return []

    result: list[str] = []

    for item in iterable:
        normalized = normalize_string(
            item,
        )

        if normalized and normalized not in result:
            result.append(
                normalized,
            )

    return result


def sanitize_schema_value(
    value: object,
    *,
    depth: int = 0,
) -> JsonValue:
    """
    Bereinigt JSON-Schema-Strukturen rekursiv.

    Interne oder sensible Manifestfelder werden an der öffentlichen
    API-Grenze entfernt.
    """

    if depth > 16:
        return None

    if value is None:
        return None

    if isinstance(
        value,
        str | int | float | bool,
    ):
        return value

    mapping = as_object_mapping(
        value,
    )

    if mapping is not None:
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
            "implementation",
            "handler",
            "callable",
            "module",
            "class",
            "import_path",
            "python_path",
            "file_path",
            "local_path",
            "model_path",
        }

        result: JsonObject = {}

        for raw_key, raw_value in mapping.items():
            key = normalize_string(
                raw_key,
            )

            if not key:
                continue

            if key.casefold() in blocked_keys:
                continue

            result[key] = sanitize_schema_value(
                raw_value,
                depth=depth + 1,
            )

        return result

    sequence = as_object_sequence(
        value,
    )

    if sequence is not None:
        return [
            sanitize_schema_value(
                item,
                depth=depth + 1,
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
            sanitize_schema_value(
                item,
                depth=depth + 1,
            )
            for item in typed_set
        ]

    return str(
        value,
    )


def normalize_json_object(
    value: object,
) -> JsonObject | None:
    sanitized = sanitize_schema_value(
        value,
    )

    if not isinstance(
        sanitized,
        dict,
    ):
        return None

    return sanitized


def normalize_metadata(
    value: object,
) -> JsonObject:
    mapping = as_object_mapping(
        value,
    )

    if mapping is None:
        return {}

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
        "implementation",
        "handler",
        "callable",
        "module",
        "class",
        "import_path",
        "python_path",
        "file_path",
        "local_path",
        "base_url",
        "endpoint_url",
    }

    result: JsonObject = {}

    for raw_key, raw_value in mapping.items():
        key = normalize_string(
            raw_key,
        )

        if not key:
            continue

        if key.casefold() in blocked_keys:
            continue

        result[key] = sanitize_schema_value(
            raw_value,
        )

    return result


def normalize_capabilities(
    source: object,
) -> ToolCapabilities:
    raw_capabilities: object = read_value(
        source,
        "capabilities",
        default={},
    )

    capability_mapping = as_object_mapping(
        raw_capabilities,
    )

    if capability_mapping is not None:
        known_names: set[str] = {
            "streaming",
            "confirmation_required",
            "requires_confirmation",
            "idempotent",
            "read_only",
            "readonly",
            "supports_cancellation",
            "cancellable",
        }

        streaming_value = read_mapping_value(
            capability_mapping,
            "streaming",
            False,
        )

        confirmation_value = read_mapping_value(
            capability_mapping,
            "confirmation_required",
            read_mapping_value(
                capability_mapping,
                "requires_confirmation",
                False,
            ),
        )

        idempotent_value = read_mapping_value(
            capability_mapping,
            "idempotent",
            False,
        )

        read_only_value = read_mapping_value(
            capability_mapping,
            "read_only",
            read_mapping_value(
                capability_mapping,
                "readonly",
                False,
            ),
        )

        cancellation_value = read_mapping_value(
            capability_mapping,
            "supports_cancellation",
            read_mapping_value(
                capability_mapping,
                "cancellable",
                False,
            ),
        )

        additional: list[str] = []

        for raw_key, raw_value in capability_mapping.items():
            key = normalize_string(
                raw_key,
            )

            if not key:
                continue

            if key.casefold() in known_names:
                continue

            if not normalize_bool(
                raw_value,
                default=False,
            ):
                continue

            if key not in additional:
                additional.append(
                    key,
                )

        additional.sort(
            key=str.casefold,
        )

        return ToolCapabilities(
            streaming=normalize_bool(
                streaming_value,
                default=False,
            ),
            confirmation_required=normalize_bool(
                confirmation_value,
                default=False,
            ),
            idempotent=normalize_bool(
                idempotent_value,
                default=False,
            ),
            read_only=normalize_bool(
                read_only_value,
                default=False,
            ),
            supports_cancellation=normalize_bool(
                cancellation_value,
                default=False,
            ),
            additional=additional,
        )

    capability_names = normalize_string_list(
        raw_capabilities,
    )

    normalized_names: set[str] = {name.casefold() for name in capability_names}

    aliases: dict[str, set[str]] = {
        "streaming": {
            "stream",
            "streaming",
        },
        "confirmation_required": {
            "confirmation_required",
            "requires_confirmation",
            "confirmation",
        },
        "idempotent": {
            "idempotent",
        },
        "read_only": {
            "read_only",
            "readonly",
            "read-only",
        },
        "supports_cancellation": {
            "supports_cancellation",
            "cancellable",
            "cancellation",
        },
    }

    all_known_aliases: set[str] = set()

    for alias_values in aliases.values():
        all_known_aliases.update(
            alias_values,
        )

    return ToolCapabilities(
        streaming=bool(normalized_names & aliases["streaming"]),
        confirmation_required=bool(normalized_names & aliases["confirmation_required"]),
        idempotent=bool(normalized_names & aliases["idempotent"]),
        read_only=bool(normalized_names & aliases["read_only"]),
        supports_cancellation=bool(normalized_names & aliases["supports_cancellation"]),
        additional=[
            name
            for name in capability_names
            if name.casefold() not in all_known_aliases
        ],
    )


def read_json_value(
    source: JsonObject,
    key: str,
    default: JsonValue = None,
) -> JsonValue:
    if key not in source:
        return default

    return source[key]


def normalize_input_schema(
    source: object,
) -> ToolInputSchema:
    raw_schema: object = read_value(
        source,
        "input_schema",
        "parameters",
        "schema",
        default={},
    )

    sanitized_schema = normalize_json_object(
        raw_schema,
    )

    if sanitized_schema is None:
        return ToolInputSchema()

    raw_type: JsonValue = read_json_value(
        sanitized_schema,
        "type",
        "object",
    )

    schema_type = normalize_string(
        raw_type,
        default="object",
    )

    raw_properties: JsonValue = read_json_value(
        sanitized_schema,
        "properties",
        {},
    )

    properties = normalize_json_object(
        raw_properties,
    )

    if properties is None:
        properties = {}

    raw_required: JsonValue = read_json_value(
        sanitized_schema,
        "required",
        [],
    )

    required = normalize_string_list(
        raw_required,
    )

    raw_additional_properties: JsonValue = read_json_value(
        sanitized_schema,
        "additionalProperties",
        None,
    )

    additional_properties: bool | JsonObject | None

    if isinstance(
        raw_additional_properties,
        bool,
    ):
        additional_properties = raw_additional_properties

    elif raw_additional_properties is None:
        additional_properties = None

    else:
        additional_properties = normalize_json_object(
            raw_additional_properties,
        )

    return ToolInputSchema(
        type=schema_type,
        properties=properties,
        required=required,
        additionalProperties=additional_properties,
    )


def normalize_output_schema(
    source: object,
) -> JsonObject | None:
    raw_schema: object = read_value(
        source,
        "output_schema",
        "result_schema",
        default=None,
    )

    if raw_schema is None:
        return None

    return normalize_json_object(
        raw_schema,
    )


def normalize_tool_entry(
    source: object,
) -> ToolEntry:
    tool_id = normalize_string(
        read_value(
            source,
            "id",
            "tool_id",
            "slug",
        ),
    )

    if not tool_id:
        raise ValueError("Ein Tool besitzt keine gültige ID.")

    name = normalize_string(
        read_value(
            source,
            "name",
            "display_name",
            default=tool_id,
        ),
        default=tool_id,
    )

    return ToolEntry(
        id=tool_id,
        name=name,
        version=normalize_string(
            read_value(
                source,
                "version",
                default="1.0.0",
            ),
            default="1.0.0",
        ),
        description=normalize_optional_string(
            read_value(
                source,
                "description",
            ),
        ),
        category=normalize_optional_string(
            read_value(
                source,
                "category",
                "group",
            ),
        ),
        enabled=normalize_bool(
            read_value(
                source,
                "enabled",
                default=True,
            ),
            default=True,
        ),
        available=normalize_bool(
            read_value(
                source,
                "available",
                "healthy",
                default=True,
            ),
            default=True,
        ),
        selectable=normalize_bool(
            read_value(
                source,
                "selectable",
                default=True,
            ),
            default=True,
        ),
        capabilities=normalize_capabilities(
            source,
        ),
        input_schema=normalize_input_schema(
            source,
        ),
        output_schema=normalize_output_schema(
            source,
        ),
        required_permissions=normalize_string_list(
            read_value(
                source,
                "required_permissions",
                "permissions",
                default=[],
            ),
        ),
        tags=normalize_string_list(
            read_value(
                source,
                "tags",
                default=[],
            ),
        ),
        metadata=normalize_metadata(
            read_value(
                source,
                "metadata",
                default={},
            ),
        ),
    )


async def list_registry_tools(
    registry: object,
) -> list[object]:
    """
    Unterstützt synchrone und asynchrone Tool-Registries.

    Der öffentliche Registry-Vertrag bleibt `list_tools()`.
    """

    list_tools: object = getattr(
        registry,
        "list_tools",
        None,
    )

    if not callable(
        list_tools,
    ):
        raise RuntimeError("Die ToolRegistry implementiert list_tools() nicht.")

    raw_result: object = list_tools()

    result = await resolve_maybe_awaitable(
        raw_result,
    )

    result_mapping = as_object_mapping(
        result,
    )

    if result_mapping is not None:
        return [item for item in result_mapping.values()]

    result_sequence = as_object_sequence(
        result,
    )

    if result_sequence is not None:
        return [item for item in result_sequence]

    raise RuntimeError("Die ToolRegistry hat ein ungültiges Ergebnis geliefert.")


def is_tool_visible(
    tool: ToolEntry,
    *,
    include_disabled: bool,
    include_unavailable: bool,
    category: str | None,
    capability: str | None,
) -> bool:
    if not include_disabled and not tool.enabled:
        return False

    if not include_unavailable and not tool.available:
        return False

    if category is not None and (
        tool.category is None or tool.category.casefold() != category.casefold()
    ):
        return False

    if capability is None:
        return True

    normalized_capability = capability.casefold()

    known_capabilities: dict[str, bool] = {
        "streaming": tool.capabilities.streaming,
        "confirmation_required": (tool.capabilities.confirmation_required),
        "idempotent": tool.capabilities.idempotent,
        "read_only": tool.capabilities.read_only,
        "supports_cancellation": (tool.capabilities.supports_cancellation),
    }

    known_result = known_capabilities.get(
        normalized_capability,
    )

    if known_result is not None:
        return known_result

    return normalized_capability in {
        item.casefold() for item in tool.capabilities.additional
    }


@router.get(
    "",
    response_model=ToolListResponse,
    response_model_exclude_none=True,
    summary="Verfügbare Tools auflisten",
    description=(
        "Liefert die registrierten und für das Frontend sichtbaren "
        "Tools. Die Listung eines Tools stellt keine "
        "Ausführungsfreigabe dar."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Tool-Liste wurde geladen.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": ("Die Tool-Registry ist nicht verfügbar."),
        },
    },
)
async def tools(
    request: Request,
    response: Response,
    include_disabled: bool = Query(
        default=False,
        description=(
            "Deaktivierte Tools mit ausgeben. "
            "Für administrative Oberflächen vorgesehen."
        ),
    ),
    include_unavailable: bool = Query(
        default=False,
        description=("Aktuell nicht verfügbare Tools mit ausgeben."),
    ),
    category: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description=("Optional nach Tool-Kategorie filtern."),
    ),
    capability: (
        Literal[
            "streaming",
            "confirmation_required",
            "idempotent",
            "read_only",
            "supports_cancellation",
        ]
        | None
    ) = Query(
        default=None,
        description=("Optional nach einer Fähigkeit filtern."),
    ),
) -> ToolListResponse:
    registry = get_tool_registry(
        request,
    )

    try:
        raw_tools = await list_registry_tools(
            registry,
        )

    except Exception as exc:
        logger.exception(
            "Tool registry listing failed",
            extra={
                "request_id": get_request_id(
                    request,
                ),
            },
        )

        raise structured_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="TOOL_REGISTRY_LIST_FAILED",
            message=("Die Tool-Liste konnte nicht geladen werden."),
        ) from exc

    normalized_tools: list[ToolEntry] = []

    for raw_tool in raw_tools:
        try:
            tool = normalize_tool_entry(
                raw_tool,
            )

        except (
            TypeError,
            ValueError,
        ):
            logger.exception(
                "Invalid tool registry entry ignored",
                extra={
                    "request_id": get_request_id(
                        request,
                    ),
                    "entry_type": type(
                        raw_tool,
                    ).__name__,
                },
            )

            continue

        if is_tool_visible(
            tool,
            include_disabled=include_disabled,
            include_unavailable=include_unavailable,
            category=category,
            capability=capability,
        ):
            normalized_tools.append(
                tool,
            )

    normalized_tools.sort(
        key=lambda tool: (
            (tool.category.casefold() if tool.category else ""),
            tool.name.casefold(),
            tool.id.casefold(),
        ),
    )

    registry_revision = await get_registry_revision(
        registry,
    )

    config_revision = await get_config_revision(
        request,
    )

    response.headers["Cache-Control"] = "no-store, private"

    response.headers["X-Tool-Schema-Version"] = TOOL_API_SCHEMA_VERSION

    response.headers["X-Tool-Registry-Revision"] = str(
        registry_revision,
    )

    response.headers["X-Config-Revision"] = str(
        config_revision,
    )

    return ToolListResponse(
        registry_revision=registry_revision,
        config_revision=config_revision,
        items=normalized_tools,
        request_id=get_request_id(
            request,
        ),
    )
