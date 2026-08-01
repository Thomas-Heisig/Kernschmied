# F:\Kernschmied\backend\app\api\v1\models.py

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


MODEL_API_SCHEMA_VERSION = "1.0"


# Keine eigene rekursive JsonValue-Definition mehr – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


class ModelCapability(BaseModel):
    """
    Bekannte technische Fähigkeiten eines Modells.

    Unbekannte Fähigkeiten können zusätzlich über `additional`
    übertragen werden, ohne den stabilen Vertrag zu brechen.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    chat: bool = False
    streaming: bool = False
    tool_calling: bool = False
    vision: bool = False
    embeddings: bool = False
    structured_output: bool = False

    additional: list[str] = Field(
        default_factory=list,
    )


class ModelLimits(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    context_window: int | None = Field(
        default=None,
        ge=1,
    )

    max_output_tokens: int | None = Field(
        default=None,
        ge=1,
    )


class ModelEntry(BaseModel):
    """
    Öffentlicher, frontendfähiger Modelleintrag.

    Interne Dateipfade, Zugangsdaten und Provider-Secrets werden nicht
    an das Frontend weitergegeben.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    name: str
    provider: str

    backend: str | None = None
    description: str | None = None

    enabled: bool = True
    available: bool = True
    selectable: bool = True
    default: bool = False

    capabilities: ModelCapability = Field(
        default_factory=ModelCapability,
    )

    limits: ModelLimits = Field(
        default_factory=ModelLimits,
    )

    tags: list[str] = Field(
        default_factory=list,
    )

    metadata: JsonObject = Field(
        default_factory=dict,
    )


class ModelListResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: str = MODEL_API_SCHEMA_VERSION

    registry_revision: int = Field(
        default=0,
        ge=0,
    )

    config_revision: int = Field(
        default=0,
        ge=0,
    )

    items: list[ModelEntry]

    request_id: str | None = None


class ProviderEntry(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    name: str
    description: str | None = None

    model_count: int = Field(
        default=0,
        ge=0,
    )

    available_model_count: int = Field(
        default=0,
        ge=0,
    )


class ProviderListResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: str = MODEL_API_SCHEMA_VERSION

    registry_revision: int = Field(
        default=0,
        ge=0,
    )

    items: list[ProviderEntry] = Field(
        default_factory=lambda: list[ProviderEntry](),
    )

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


def get_model_registry(
    request: Request,
) -> object:
    registry: object | None = getattr(
        request.app.state,
        "model_registry",
        None,
    )

    if registry is None:
        raise structured_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="MODEL_REGISTRY_UNAVAILABLE",
            message=("Die Modellregistrierung ist nicht verfügbar."),
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
            raw_revision = revision_getter()

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
    service: object | None = getattr(
        request.app.state,
        "config_service",
        None,
    )

    return await read_revision(
        service,
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

    if sequence is None:
        if isinstance(
            value,
            set | frozenset,
        ):
            iterable: tuple[object, ...] = tuple(
                cast(
                    set[object] | frozenset[object],
                    value,
                ),
            )
        else:
            return []
    else:
        iterable = tuple(
            sequence,
        )

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


def normalize_json_value(
    value: object,
) -> JsonValue | None:
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
        result: JsonObject = {}

        for raw_key, raw_value in mapping.items():
            key = normalize_string(
                raw_key,
            )

            if not key:
                continue

            normalized_value = normalize_json_value(
                raw_value,
            )

            result[key] = normalized_value

        return result

    sequence = as_object_sequence(
        value,
    )

    if sequence is not None:
        return [
            normalize_json_value(
                item,
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
            normalize_json_value(
                item,
            )
            for item in typed_set
        ]

    return None


def normalize_metadata(
    value: object,
) -> JsonObject:
    mapping = as_object_mapping(
        value,
    )

    if mapping is None:
        return {}

    blocked_keys: set[str] = {
        "api_key",
        "token",
        "secret",
        "password",
        "credential",
        "credentials",
        "authorization",
        "headers",
        "base_url",
        "path",
        "model_path",
        "local_path",
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

        normalized_value = normalize_json_value(
            raw_value,
        )

        if normalized_value is not None:
            result[key] = normalized_value

    return result


def normalize_capabilities(
    source: object,
) -> ModelCapability:
    raw: object = read_value(
        source,
        "capabilities",
        default={},
    )

    raw_mapping = as_object_mapping(
        raw,
    )

    if raw_mapping is not None:
        chat_value = read_mapping_value(
            raw_mapping,
            "chat",
            False,
        )

        streaming_value = read_mapping_value(
            raw_mapping,
            "streaming",
            False,
        )

        tool_calling_value = read_mapping_value(
            raw_mapping,
            "tool_calling",
            read_mapping_value(
                raw_mapping,
                "tools",
                False,
            ),
        )

        vision_value = read_mapping_value(
            raw_mapping,
            "vision",
            False,
        )

        embeddings_value = read_mapping_value(
            raw_mapping,
            "embeddings",
            read_mapping_value(
                raw_mapping,
                "embedding",
                False,
            ),
        )

        structured_output_value = read_mapping_value(
            raw_mapping,
            "structured_output",
            read_mapping_value(
                raw_mapping,
                "json_mode",
                False,
            ),
        )

        known_names: set[str] = {
            "chat",
            "streaming",
            "tool_calling",
            "tools",
            "vision",
            "embeddings",
            "embedding",
            "structured_output",
            "json_mode",
        }

        additional: list[str] = []

        for raw_key, raw_value in raw_mapping.items():
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

        return ModelCapability(
            chat=normalize_bool(
                chat_value,
                default=False,
            ),
            streaming=normalize_bool(
                streaming_value,
                default=False,
            ),
            tool_calling=normalize_bool(
                tool_calling_value,
                default=False,
            ),
            vision=normalize_bool(
                vision_value,
                default=False,
            ),
            embeddings=normalize_bool(
                embeddings_value,
                default=False,
            ),
            structured_output=normalize_bool(
                structured_output_value,
                default=False,
            ),
            additional=additional,
        )

    names = normalize_string_list(
        raw,
    )

    normalized_names: set[str] = {item.casefold() for item in names}

    known_aliases: dict[str, set[str]] = {
        "chat": {
            "chat",
        },
        "streaming": {
            "streaming",
            "stream",
        },
        "tool_calling": {
            "tool_calling",
            "tools",
            "function_calling",
        },
        "vision": {
            "vision",
            "image",
            "multimodal",
        },
        "embeddings": {
            "embeddings",
            "embedding",
        },
        "structured_output": {
            "structured_output",
            "json_mode",
            "json",
        },
    }

    all_known_aliases: set[str] = set()

    for aliases in known_aliases.values():
        all_known_aliases.update(
            aliases,
        )

    additional = [item for item in names if item.casefold() not in all_known_aliases]

    return ModelCapability(
        chat=bool(normalized_names & known_aliases["chat"]),
        streaming=bool(normalized_names & known_aliases["streaming"]),
        tool_calling=bool(normalized_names & known_aliases["tool_calling"]),
        vision=bool(normalized_names & known_aliases["vision"]),
        embeddings=bool(normalized_names & known_aliases["embeddings"]),
        structured_output=bool(normalized_names & known_aliases["structured_output"]),
        additional=additional,
    )


def normalize_positive_int(
    value: object,
) -> int | None:
    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        int,
    ):
        return value if value > 0 else None

    if isinstance(
        value,
        float,
    ):
        if not value.is_integer():
            return None

        normalized_float = int(
            value,
        )

        return normalized_float if normalized_float > 0 else None

    if isinstance(
        value,
        str,
    ):
        normalized_string = value.strip()

        if not normalized_string:
            return None

        try:
            normalized_int = int(
                normalized_string,
            )
        except ValueError:
            return None

        return normalized_int if normalized_int > 0 else None

    return None


def normalize_limits(
    source: object,
) -> ModelLimits:
    limits: object = read_value(
        source,
        "limits",
        default={},
    )

    context_window: object = read_value(
        limits,
        "context_window",
        "context_length",
        default=read_value(
            source,
            "context_window",
            "context_length",
        ),
    )

    max_output_tokens: object = read_value(
        limits,
        "max_output_tokens",
        "max_tokens",
        default=read_value(
            source,
            "max_output_tokens",
            "max_tokens",
        ),
    )

    return ModelLimits(
        context_window=normalize_positive_int(
            context_window,
        ),
        max_output_tokens=normalize_positive_int(
            max_output_tokens,
        ),
    )


def normalize_model_entry(
    source: object,
) -> ModelEntry:
    model_id = normalize_string(
        read_value(
            source,
            "id",
            "model_id",
            "slug",
        ),
    )

    if not model_id:
        raise ValueError("Ein Modell besitzt keine gültige ID.")

    name = normalize_string(
        read_value(
            source,
            "name",
            "display_name",
            default=model_id,
        ),
        default=model_id,
    )

    provider = normalize_string(
        read_value(
            source,
            "provider",
            default="unknown",
        ),
        default="unknown",
    )

    return ModelEntry(
        id=model_id,
        name=name,
        provider=provider,
        backend=normalize_optional_string(
            read_value(
                source,
                "backend",
            ),
        ),
        description=normalize_optional_string(
            read_value(
                source,
                "description",
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
        default=normalize_bool(
            read_value(
                source,
                "default",
                "is_default",
                default=False,
            ),
            default=False,
        ),
        capabilities=normalize_capabilities(
            source,
        ),
        limits=normalize_limits(
            source,
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


async def list_registry_models(
    registry: object,
) -> list[object]:
    """
    Unterstützt synchrone und asynchrone Registries.

    Der bevorzugte öffentliche Vertrag bleibt `list_models()`.
    """

    list_models: object = getattr(
        registry,
        "list_models",
        None,
    )

    if not callable(
        list_models,
    ):
        raise RuntimeError("Die ModelRegistry implementiert list_models() nicht.")

    raw_result: object = list_models()

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

    raise RuntimeError("Die ModelRegistry hat ein ungültiges Ergebnis geliefert.")


def is_model_visible(
    model: ModelEntry,
    *,
    include_disabled: bool,
    capability: str | None,
    provider: str | None,
) -> bool:
    if not include_disabled and not model.enabled:
        return False

    if provider is not None and model.provider.casefold() != provider.casefold():
        return False

    if capability is None:
        return True

    normalized_capability = capability.casefold()

    known_capabilities: dict[str, bool] = {
        "chat": model.capabilities.chat,
        "streaming": model.capabilities.streaming,
        "tool_calling": model.capabilities.tool_calling,
        "vision": model.capabilities.vision,
        "embeddings": model.capabilities.embeddings,
        "structured_output": (model.capabilities.structured_output),
    }

    known_result = known_capabilities.get(
        normalized_capability,
    )

    if known_result is not None:
        return known_result

    return normalized_capability in {
        item.casefold() for item in model.capabilities.additional
    }


def _provider_display_name(
    provider_id: str,
) -> str:
    known_names: dict[str, str] = {
        "ollama": "Ollama",
        "openai": "OpenAI",
        "openai_compatible": "OpenAI-kompatibel",
        "azure_openai": "Azure OpenAI",
        "anthropic": "Anthropic",
        "google_gemini": "Google Gemini",
        "llama_cpp": "llama.cpp",
        "mlx": "MLX",
        "http_generic": "Generischer HTTP-Provider",
    }

    return known_names.get(
        provider_id.casefold(),
        provider_id.replace("_", " ").title(),
    )


@router.get(
    "/providers",
    response_model=ProviderListResponse,
    response_model_exclude_none=True,
    summary="Verfügbare Modellprovider auflisten",
    description=(
        "Liefert die Provider der registrierten Modelle. "
        "Es werden keine Zugangsdaten oder internen Providerdetails ausgegeben."
    ),
)
async def providers(
    request: Request,
    response: Response,
    include_disabled: bool = Query(
        default=False,
    ),
) -> ProviderListResponse:
    registry = get_model_registry(
        request,
    )

    try:
        raw_models = await list_registry_models(
            registry,
        )
    except Exception as exc:
        logger.exception(
            "Model provider listing failed",
            extra={
                "request_id": get_request_id(
                    request,
                ),
            },
        )

        raise structured_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="MODEL_PROVIDER_LIST_FAILED",
            message="Die Providerliste konnte nicht geladen werden.",
        ) from exc

    provider_models: dict[str, list[ModelEntry]] = {}

    for raw_model in raw_models:
        try:
            model = normalize_model_entry(
                raw_model,
            )
        except (
            TypeError,
            ValueError,
        ):
            logger.exception(
                "Invalid model registry entry ignored",
                extra={
                    "request_id": get_request_id(
                        request,
                    ),
                },
            )
            continue

        if not include_disabled and not model.enabled:
            continue

        provider_models.setdefault(
            model.provider,
            [],
        ).append(
            model,
        )

    entries: list[ProviderEntry] = []

    for provider_id, registered_models in provider_models.items():
        available_count = sum(
            1
            for model in registered_models
            if model.enabled and model.available and model.selectable
        )

        entries.append(
            ProviderEntry(
                id=provider_id,
                name=_provider_display_name(
                    provider_id,
                ),
                description=(
                    f"{len(registered_models)} registrierte Modelle, "
                    f"{available_count} verfügbar."
                ),
                model_count=len(
                    registered_models,
                ),
                available_model_count=available_count,
            ),
        )

    entries.sort(
        key=lambda item: (
            item.name.casefold(),
            item.id.casefold(),
        ),
    )

    registry_revision = await get_registry_revision(
        registry,
    )

    response.headers["Cache-Control"] = "no-store, private"

    return ProviderListResponse(
        registry_revision=registry_revision,
        items=entries,
        request_id=get_request_id(
            request,
        ),
    )


@router.get(
    "",
    response_model=ModelListResponse,
    response_model_exclude_none=True,
    summary="Verfügbare Modelle auflisten",
    description=(
        "Liefert die serverseitig registrierten und für das Frontend "
        "sichtbaren Modelle. Die Sichtbarkeit ersetzt keine "
        "Autorisierung bei einer späteren Modellauswahl."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": ("Modellliste wurde geladen."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": ("Die Modellregistrierung ist nicht verfügbar."),
        },
    },
)
async def models(
    request: Request,
    response: Response,
    include_disabled: bool = Query(
        default=False,
        description=(
            "Deaktivierte Modelle mit ausgeben. Für Admin-Oberflächen vorgesehen."
        ),
    ),
    capability: (
        Literal[
            "chat",
            "streaming",
            "tool_calling",
            "vision",
            "embeddings",
            "structured_output",
        ]
        | None
    ) = Query(
        default=None,
        description=("Optional nach einer Fähigkeit filtern."),
    ),
    provider: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description=("Optional nach Provider filtern."),
    ),
) -> ModelListResponse:
    registry = get_model_registry(
        request,
    )

    try:
        raw_models = await list_registry_models(
            registry,
        )

    except Exception as exc:
        logger.exception(
            "Model registry listing failed",
            extra={
                "request_id": get_request_id(
                    request,
                ),
            },
        )

        raise structured_error(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="MODEL_REGISTRY_LIST_FAILED",
            message=("Die Modellliste konnte nicht geladen werden."),
        ) from exc

    normalized_models: list[ModelEntry] = []

    for raw_model in raw_models:
        try:
            model = normalize_model_entry(
                raw_model,
            )

        except (
            TypeError,
            ValueError,
        ):
            logger.exception(
                "Invalid model registry entry ignored",
                extra={
                    "request_id": get_request_id(
                        request,
                    ),
                    "entry_type": type(
                        raw_model,
                    ).__name__,
                },
            )

            continue

        if is_model_visible(
            model,
            include_disabled=include_disabled,
            capability=capability,
            provider=provider,
        ):
            normalized_models.append(
                model,
            )

    normalized_models.sort(
        key=lambda model: (
            not model.default,
            model.name.casefold(),
            model.id.casefold(),
        ),
    )

    registry_revision = await get_registry_revision(
        registry,
    )

    config_revision = await get_config_revision(
        request,
    )

    response.headers["Cache-Control"] = "no-store, private"

    response.headers["X-Model-Schema-Version"] = MODEL_API_SCHEMA_VERSION

    response.headers["X-Model-Registry-Revision"] = str(
        registry_revision,
    )

    response.headers["X-Config-Revision"] = str(
        config_revision,
    )

    return ModelListResponse(
        registry_revision=registry_revision,
        config_revision=config_revision,
        items=normalized_models,
        request_id=get_request_id(
            request,
        ),
    )
