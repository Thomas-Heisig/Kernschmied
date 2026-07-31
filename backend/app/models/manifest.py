# F:\Kernschmied\backend\app\models\manifest.py

"""
Versionierter Modellmanifest-Vertrag von Kernschmied.

Ein Modellmanifest beschreibt ein Modell ausschließlich deklarativ.

Es darf:

- keine Python-Importpfade bestimmen,
- keine Klassen- oder Factory-Namen enthalten,
- keine beliebigen Module laden,
- keine Secrets im Klartext enthalten,
- keine automatische Freigabe eines Providers bewirken.

Die technische Ausführung bleibt vollständig unter Kontrolle der
serverseitigen ModelProviderRegistry.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Final, Self, TypeAlias, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)

from app.models.errors import (
    InvalidModelManifestError,
    ModelManifestNotFoundError,
    ModelManifestSecurityError,
    UnsupportedModelManifestVersionError,
)

# ============================================================
# JSON-Typen
# ============================================================


JsonPrimitive: TypeAlias = str | int | float | bool | None
# JsonValue wird von pydantic importiert – nicht rekursiv definiert
JsonObject: TypeAlias = dict[str, JsonValue]
ValidationErrorItem: TypeAlias = dict[str, JsonValue]


_JSON_OBJECT_ADAPTER: Final[TypeAdapter[JsonObject]] = TypeAdapter(
    JsonObject,
)

_STRING_LIST_ADAPTER: Final[TypeAdapter[list[str]]] = TypeAdapter(
    list[str],
)

_ERROR_LOCATION_ADAPTER: Final[TypeAdapter[list[str | int]]] = TypeAdapter(
    list[str | int],
)


def _create_empty_json_object() -> JsonObject:
    return {}


# ============================================================
# Versionen und Konstanten
# ============================================================


CURRENT_MODEL_MANIFEST_VERSION: Final[str] = "1.0"

SUPPORTED_MODEL_MANIFEST_VERSIONS: Final[frozenset[str]] = frozenset(
    {
        CURRENT_MODEL_MANIFEST_VERSION,
    },
)

DEFAULT_MODEL_MANIFEST_FILENAME: Final[str] = "model.json"

MAX_MANIFEST_FILE_SIZE_BYTES: Final[int] = 2 * 1024 * 1024

MAX_MODEL_ID_LENGTH: Final[int] = 128
MAX_DISPLAY_NAME_LENGTH: Final[int] = 255
MAX_DESCRIPTION_LENGTH: Final[int] = 8_000
MAX_PROVIDER_TYPE_LENGTH: Final[int] = 64
MAX_TAG_LENGTH: Final[int] = 64
MAX_TAG_COUNT: Final[int] = 64
MAX_CAPABILITY_COUNT: Final[int] = 64
MAX_METADATA_ENTRIES: Final[int] = 128

_MODEL_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,127}$",
)

_PROVIDER_TYPE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,63}$",
)

_CAPABILITY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,63}$",
)

_TAG_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,63}$",
)

_SECRET_KEY_FRAGMENTS: Final[tuple[str, ...]] = (
    "api_key",
    "apikey",
    "secret",
    "password",
    "passwd",
    "token",
    "authorization",
    "private_key",
    "client_secret",
    "access_key",
    "refresh_token",
)

_FORBIDDEN_PROVIDER_CONFIG_KEYS: Final[frozenset[str]] = frozenset(
    {
        "module",
        "module_name",
        "module_path",
        "python_module",
        "python_path",
        "import",
        "import_path",
        "class",
        "class_name",
        "factory",
        "factory_name",
        "callable",
        "entrypoint",
        "entry_point",
        "plugin_path",
        "code_path",
    },
)

_ALLOWED_SECRET_REFERENCE_PREFIXES: Final[tuple[str, ...]] = (
    "env:",
    "secret:",
    "vault:",
    "keyring:",
    "credential:",
)


# ============================================================
# Enums
# ============================================================


class ModelManifestStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


class ModelRuntimeKind(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"
    HYBRID = "hybrid"


class ModelSecretSource(StrEnum):
    ENV = "env"
    SECRET = "secret"
    VAULT = "vault"
    KEYRING = "keyring"
    CREDENTIAL = "credential"


class ModelManifestCapability(StrEnum):
    CHAT = "chat"
    STREAMING = "streaming"
    TOOLS = "tools"
    VISION = "vision"
    AUDIO_INPUT = "audio_input"
    AUDIO_OUTPUT = "audio_output"
    STRUCTURED_OUTPUT = "structured_output"
    EMBEDDINGS = "embeddings"
    REASONING = "reasoning"


# ============================================================
# Basismodell
# ============================================================


class ManifestBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_default=True,
        use_enum_values=False,
    )


# ============================================================
# Secret-Referenzen
# ============================================================


class ModelSecretReference(ManifestBaseModel):
    source: ModelSecretSource

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    required: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Der Name einer Secret-Referenz darf nicht leer sein.",
            )

        if any(
            character in normalized
            for character in (
                "\x00",
                "\r",
                "\n",
            )
        ):
            raise ValueError(
                "Der Name einer Secret-Referenz enthält unzulässige Steuerzeichen.",
            )

        return normalized

    @property
    def reference(self) -> str:
        return f"{self.source.value}:{self.name}"


# ============================================================
# Provider
# ============================================================


class ModelProviderManifest(ManifestBaseModel):
    type: str = Field(
        min_length=1,
        max_length=MAX_PROVIDER_TYPE_LENGTH,
    )

    config: JsonObject = Field(
        default_factory=_create_empty_json_object,
    )

    secrets: dict[str, ModelSecretReference] = Field(
        default_factory=dict,
    )

    @field_validator("type")
    @classmethod
    def validate_provider_type(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().lower()

        if not _PROVIDER_TYPE_PATTERN.fullmatch(
            normalized,
        ):
            raise ValueError(
                "Der Provider-Typ darf nur Kleinbuchstaben, Ziffern, "
                "Punkte, Bindestriche und Unterstriche enthalten.",
            )

        return normalized

    @field_validator("config", mode="before")
    @classmethod
    def validate_provider_config(
        cls,
        value: object,
    ) -> JsonObject:
        normalized = _normalize_json_object(
            value,
            path="provider.config",
        )

        _validate_provider_config_security(
            normalized,
            path="provider.config",
        )

        return normalized

    @field_validator("secrets")
    @classmethod
    def validate_secret_keys(
        cls,
        value: dict[str, ModelSecretReference],
    ) -> dict[str, ModelSecretReference]:
        result: dict[str, ModelSecretReference] = {}

        for key, reference in value.items():
            normalized_key = key.strip().lower()

            if not _PROVIDER_TYPE_PATTERN.fullmatch(
                normalized_key,
            ):
                raise ValueError(
                    f"Ungültiger Secret-Schlüssel '{key}'.",
                )

            if normalized_key in result:
                raise ValueError(
                    f"Der Secret-Schlüssel '{normalized_key}' ist mehrfach vorhanden.",
                )

            result[normalized_key] = reference

        return result

    @model_validator(mode="after")
    def validate_secret_separation(
        self,
    ) -> Self:
        config_keys = {key.lower() for key in self.config}

        for secret_name in self.secrets:
            if secret_name in config_keys:
                raise ValueError(
                    f"'{secret_name}' darf nicht gleichzeitig in "
                    "provider.config und provider.secrets vorkommen.",
                )

        return self


# ============================================================
# Modellgrenzen
# ============================================================


class ModelLimitsManifest(ManifestBaseModel):
    context_window: int | None = Field(
        default=None,
        ge=1,
        le=10_000_000,
    )

    max_output_tokens: int | None = Field(
        default=None,
        ge=1,
        le=10_000_000,
    )

    max_input_tokens: int | None = Field(
        default=None,
        ge=1,
        le=10_000_000,
    )

    max_images: int | None = Field(
        default=None,
        ge=0,
        le=10_000,
    )

    max_audio_seconds: int | None = Field(
        default=None,
        ge=0,
        le=86_400,
    )

    max_tool_calls: int | None = Field(
        default=None,
        ge=0,
        le=10_000,
    )

    @model_validator(mode="after")
    def validate_token_limits(
        self,
    ) -> Self:
        if (
            self.context_window is not None
            and self.max_input_tokens is not None
            and self.max_input_tokens > self.context_window
        ):
            raise ValueError(
                "max_input_tokens darf context_window nicht überschreiten.",
            )

        if (
            self.context_window is not None
            and self.max_output_tokens is not None
            and self.max_output_tokens > self.context_window
        ):
            raise ValueError(
                "max_output_tokens darf context_window nicht überschreiten.",
            )

        return self


# ============================================================
# Lifecycle
# ============================================================


class ModelLifecycleManifest(ManifestBaseModel):
    eager_create: bool = False
    eager_load: bool = False

    unload_when_idle: bool = False

    idle_unload_seconds: float | None = Field(
        default=None,
        gt=0,
        le=31_536_000,
    )

    generation_timeout_seconds: float | None = Field(
        default=None,
        gt=0,
        le=86_400,
    )

    stream_idle_timeout_seconds: float | None = Field(
        default=None,
        gt=0,
        le=86_400,
    )

    shutdown_timeout_seconds: float | None = Field(
        default=None,
        gt=0,
        le=3_600,
    )

    @model_validator(mode="after")
    def validate_lifecycle(
        self,
    ) -> Self:
        if self.eager_load and not self.eager_create:
            raise ValueError(
                "eager_load erfordert eager_create=true.",
            )

        if self.unload_when_idle and self.idle_unload_seconds is None:
            raise ValueError(
                "unload_when_idle erfordert idle_unload_seconds.",
            )

        if not self.unload_when_idle and self.idle_unload_seconds is not None:
            raise ValueError(
                "idle_unload_seconds darf nur zusammen mit "
                "unload_when_idle=true gesetzt werden.",
            )

        return self


# ============================================================
# Darstellung
# ============================================================


class ModelPresentationManifest(ManifestBaseModel):
    icon: str | None = Field(
        default=None,
        max_length=512,
    )

    category: str | None = Field(
        default=None,
        max_length=128,
    )

    sort_order: int = Field(
        default=0,
        ge=-1_000_000,
        le=1_000_000,
    )

    hidden: bool = False

    badge: str | None = Field(
        default=None,
        max_length=64,
    )

    @field_validator("icon")
    @classmethod
    def validate_icon(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        lowered = normalized.lower()

        if lowered.startswith(
            (
                "javascript:",
                "data:text/html",
                "file:",
            ),
        ):
            raise ValueError(
                "Der Icon-Verweis verwendet ein nicht erlaubtes Schema.",
            )

        return normalized


# ============================================================
# Hauptmanifest
# ============================================================


class ModelManifest(ManifestBaseModel):
    schema_version: str = Field(
        default=CURRENT_MODEL_MANIFEST_VERSION,
        min_length=1,
        max_length=32,
    )

    id: str = Field(
        min_length=1,
        max_length=MAX_MODEL_ID_LENGTH,
    )

    display_name: str = Field(
        min_length=1,
        max_length=MAX_DISPLAY_NAME_LENGTH,
    )

    description: str | None = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
    )

    status: ModelManifestStatus = ModelManifestStatus.ACTIVE
    enabled: bool = True
    runtime: ModelRuntimeKind = ModelRuntimeKind.REMOTE

    provider: ModelProviderManifest

    capabilities: frozenset[str] = Field(
        default_factory=frozenset,
    )

    tags: frozenset[str] = Field(
        default_factory=frozenset,
    )

    limits: ModelLimitsManifest = Field(
        default_factory=ModelLimitsManifest,
    )

    lifecycle: ModelLifecycleManifest = Field(
        default_factory=ModelLifecycleManifest,
    )

    presentation: ModelPresentationManifest = Field(
        default_factory=ModelPresentationManifest,
    )

    metadata: JsonObject = Field(
        default_factory=_create_empty_json_object,
    )

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if normalized not in SUPPORTED_MODEL_MANIFEST_VERSIONS:
            raise UnsupportedModelManifestVersionError(
                normalized,
                supported_versions=sorted(
                    SUPPORTED_MODEL_MANIFEST_VERSIONS,
                ),
            )

        return normalized

    @field_validator("id")
    @classmethod
    def validate_model_id(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().lower()

        if not _MODEL_ID_PATTERN.fullmatch(
            normalized,
        ):
            raise ValueError(
                "Die Modell-ID muss mit einem Kleinbuchstaben oder einer "
                "Ziffer beginnen und darf nur Kleinbuchstaben, Ziffern, "
                "Punkte, Bindestriche und Unterstriche enthalten.",
            )

        return normalized

    @field_validator("display_name")
    @classmethod
    def validate_display_name(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "display_name darf nicht leer sein.",
            )

        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    @field_validator("capabilities", mode="before")
    @classmethod
    def normalize_capabilities(
        cls,
        value: object,
    ) -> frozenset[str]:
        return frozenset(
            _normalize_string_collection(
                value,
                field_name="capabilities",
                pattern=_CAPABILITY_PATTERN,
                maximum_count=MAX_CAPABILITY_COUNT,
            ),
        )

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(
        cls,
        value: object,
    ) -> frozenset[str]:
        return frozenset(
            _normalize_string_collection(
                value,
                field_name="tags",
                pattern=_TAG_PATTERN,
                maximum_count=MAX_TAG_COUNT,
            ),
        )

    @field_validator("metadata", mode="before")
    @classmethod
    def validate_metadata(
        cls,
        value: object,
    ) -> JsonObject:
        normalized = _normalize_json_object(
            value,
            path="metadata",
        )

        if len(normalized) > MAX_METADATA_ENTRIES:
            raise ValueError(
                f"metadata darf höchstens {MAX_METADATA_ENTRIES} Einträge enthalten.",
            )

        _validate_no_secret_values(
            normalized,
            path="metadata",
        )

        return normalized

    @model_validator(mode="after")
    def validate_manifest_consistency(
        self,
    ) -> Self:
        capabilities = self.capabilities

        for required_capability in (
            ModelManifestCapability.STREAMING.value,
            ModelManifestCapability.TOOLS.value,
            ModelManifestCapability.REASONING.value,
        ):
            if (
                required_capability in capabilities
                and ModelManifestCapability.CHAT.value not in capabilities
            ):
                raise ValueError(
                    f"Die Capability '{required_capability}' erfordert 'chat'.",
                )

        if self.status == ModelManifestStatus.DISABLED and self.enabled:
            raise ValueError(
                "Ein Manifest mit status='disabled' muss enabled=false verwenden.",
            )

        if self.runtime == ModelRuntimeKind.LOCAL and self.provider.type in {
            "openai",
            "anthropic",
            "azure_openai",
            "google_gemini",
        }:
            raise ValueError(
                f"Der Provider '{self.provider.type}' ist nicht mit "
                "runtime='local' vereinbar.",
            )

        return self

    @property
    def is_enabled(self) -> bool:
        return self.enabled and self.status != ModelManifestStatus.DISABLED

    @property
    def is_deprecated(self) -> bool:
        return self.status == ModelManifestStatus.DEPRECATED

    @property
    def is_experimental(self) -> bool:
        return self.status == ModelManifestStatus.EXPERIMENTAL

    def supports(
        self,
        capability: str | ModelManifestCapability,
    ) -> bool:
        normalized = (
            capability.value
            if isinstance(
                capability,
                ModelManifestCapability,
            )
            else capability.strip().lower()
        )

        return normalized in self.capabilities

    def safe_summary(self) -> JsonObject:
        """
        Liefert eine sichere Diagnoseansicht ohne Secret-Werte.
        """

        limits = _normalize_json_object(
            self.limits.model_dump(
                mode="json",
                exclude_none=True,
            ),
            path="limits",
        )

        lifecycle = _normalize_json_object(
            self.lifecycle.model_dump(
                mode="json",
                exclude_none=True,
            ),
            path="lifecycle",
        )

        presentation = _normalize_json_object(
            self.presentation.model_dump(
                mode="json",
                exclude_none=True,
            ),
            path="presentation",
        )

        provider_config_keys: list[JsonValue] = [
            key
            for key in sorted(
                self.provider.config,
            )
        ]

        capabilities: list[JsonValue] = [
            capability
            for capability in sorted(
                self.capabilities,
            )
        ]

        tags: list[JsonValue] = [
            tag
            for tag in sorted(
                self.tags,
            )
        ]

        secret_references: JsonObject = {
            name: reference.reference
            for name, reference in self.provider.secrets.items()
        }

        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "status": self.status.value,
            "enabled": self.enabled,
            "effective_enabled": self.is_enabled,
            "runtime": self.runtime.value,
            "provider_type": self.provider.type,
            "provider_config_keys": provider_config_keys,
            "secret_references": secret_references,
            "capabilities": capabilities,
            "tags": tags,
            "limits": limits,
            "lifecycle": lifecycle,
            "presentation": presentation,
            "metadata": dict(self.metadata),
        }


# ============================================================
# Geladenes Manifest
# ============================================================


class LoadedModelManifest(ManifestBaseModel):
    manifest: ModelManifest
    manifest_path: Path
    manifest_directory: Path

    @field_validator(
        "manifest_path",
        "manifest_directory",
        mode="before",
    )
    @classmethod
    def normalize_paths(
        cls,
        value: object,
    ) -> Path:
        return (
            Path(
                str(value),
            )
            .expanduser()
            .resolve()
        )

    @model_validator(mode="after")
    def validate_paths(
        self,
    ) -> Self:
        expected_directory = self.manifest_path.parent

        if self.manifest_directory != expected_directory:
            raise ValueError(
                "manifest_directory muss dem Elternverzeichnis von "
                "manifest_path entsprechen.",
            )

        return self

    @property
    def model_id(self) -> str:
        return self.manifest.id


# ============================================================
# Laden
# ============================================================


def load_model_manifest(
    manifest_path: str | Path,
    *,
    allowed_base_directories: Sequence[str | Path] | None = None,
    maximum_file_size_bytes: int = MAX_MANIFEST_FILE_SIZE_BYTES,
) -> LoadedModelManifest:
    path = (
        Path(
            manifest_path,
        )
        .expanduser()
        .resolve()
    )

    if not path.is_file():
        raise ModelManifestNotFoundError(
            str(path),
        )

    if path.name.lower() != DEFAULT_MODEL_MANIFEST_FILENAME:
        raise InvalidModelManifestError(
            manifest_path=str(path),
            message=(
                f"Ein Modellmanifest muss '{DEFAULT_MODEL_MANIFEST_FILENAME}' heißen."
            ),
        )

    _validate_path_within_allowed_directories(
        path,
        allowed_base_directories=allowed_base_directories,
    )

    if maximum_file_size_bytes <= 0:
        raise ValueError(
            "maximum_file_size_bytes muss größer als 0 sein.",
        )

    try:
        file_size = path.stat().st_size
    except OSError as exc:
        raise InvalidModelManifestError(
            manifest_path=str(path),
            message=("Die Größe des Modellmanifests konnte nicht gelesen werden."),
            cause=exc,
        ) from exc

    if file_size > maximum_file_size_bytes:
        raise InvalidModelManifestError(
            manifest_path=str(path),
            message=(
                "Das Modellmanifest überschreitet die erlaubte "
                f"Dateigröße von {maximum_file_size_bytes} Bytes."
            ),
        )

    try:
        raw_text = path.read_text(
            encoding="utf-8",
        )
    except UnicodeDecodeError as exc:
        raise InvalidModelManifestError(
            manifest_path=str(path),
            message="Das Modellmanifest muss UTF-8-codiert sein.",
            cause=exc,
        ) from exc
    except OSError as exc:
        raise InvalidModelManifestError(
            manifest_path=str(path),
            message="Das Modellmanifest konnte nicht gelesen werden.",
            cause=exc,
        ) from exc

    try:
        raw_data = _JSON_OBJECT_ADAPTER.validate_json(
            raw_text,
        )
    except ValidationError as exc:
        raise InvalidModelManifestError(
            manifest_path=str(path),
            message="Das Modellmanifest enthält ungültiges JSON.",
            validation_errors=_serialize_validation_errors(
                exc,
            ),
            cause=exc,
        ) from exc

    raw_schema_version = raw_data.get(
        "schema_version",
        CURRENT_MODEL_MANIFEST_VERSION,
    )

    schema_version = str(
        raw_schema_version,
    ).strip()

    if schema_version not in SUPPORTED_MODEL_MANIFEST_VERSIONS:
        raise UnsupportedModelManifestVersionError(
            schema_version,
            supported_versions=sorted(
                SUPPORTED_MODEL_MANIFEST_VERSIONS,
            ),
            manifest_path=str(path),
        )

    try:
        manifest = ModelManifest.model_validate(
            raw_data,
        )
    except UnsupportedModelManifestVersionError:
        raise
    except ValidationError as exc:
        raise InvalidModelManifestError(
            manifest_path=str(path),
            validation_errors=_serialize_validation_errors(
                exc,
            ),
            cause=exc,
        ) from exc
    except ModelManifestSecurityError:
        raise
    except ValueError as exc:
        raise InvalidModelManifestError(
            manifest_path=str(path),
            message=str(exc),
            cause=exc,
        ) from exc

    return LoadedModelManifest(
        manifest=manifest,
        manifest_path=path,
        manifest_directory=path.parent,
    )


def load_model_manifest_directory(
    directory: str | Path,
    *,
    allowed_base_directories: Sequence[str | Path] | None = None,
    maximum_file_size_bytes: int = MAX_MANIFEST_FILE_SIZE_BYTES,
) -> LoadedModelManifest:
    directory_path = (
        Path(
            directory,
        )
        .expanduser()
        .resolve()
    )

    return load_model_manifest(
        directory_path / DEFAULT_MODEL_MANIFEST_FILENAME,
        allowed_base_directories=allowed_base_directories,
        maximum_file_size_bytes=maximum_file_size_bytes,
    )


# ============================================================
# Discovery
# ============================================================


def discover_model_manifest_paths(
    base_directories: Sequence[str | Path],
    *,
    recursive: bool = True,
    follow_symlinks: bool = False,
) -> tuple[Path, ...]:
    discovered: set[Path] = set()

    for raw_base_directory in base_directories:
        base_directory = (
            Path(
                raw_base_directory,
            )
            .expanduser()
            .resolve()
        )

        if not base_directory.is_dir():
            continue

        iterator = (
            base_directory.rglob(
                DEFAULT_MODEL_MANIFEST_FILENAME,
            )
            if recursive
            else base_directory.glob(
                DEFAULT_MODEL_MANIFEST_FILENAME,
            )
        )

        for candidate in iterator:
            try:
                if not candidate.is_file():
                    continue

                if candidate.is_symlink() and not follow_symlinks:
                    continue

                resolved_candidate = candidate.resolve()

                if not _is_relative_to(
                    resolved_candidate,
                    base_directory,
                ):
                    continue

                discovered.add(
                    resolved_candidate,
                )

            except OSError:
                continue

    return tuple(
        sorted(
            discovered,
            key=lambda item: str(item).lower(),
        ),
    )


def load_discovered_model_manifests(
    base_directories: Sequence[str | Path],
    *,
    recursive: bool = True,
    follow_symlinks: bool = False,
    maximum_file_size_bytes: int = MAX_MANIFEST_FILE_SIZE_BYTES,
) -> tuple[LoadedModelManifest, ...]:
    paths = discover_model_manifest_paths(
        base_directories,
        recursive=recursive,
        follow_symlinks=follow_symlinks,
    )

    return tuple(
        load_model_manifest(
            path,
            allowed_base_directories=base_directories,
            maximum_file_size_bytes=maximum_file_size_bytes,
        )
        for path in paths
    )


# ============================================================
# Serialisierung
# ============================================================


def dump_model_manifest(
    manifest: ModelManifest,
    *,
    indent: int = 2,
) -> str:
    if indent < 0:
        raise ValueError(
            "indent darf nicht negativ sein.",
        )

    return json.dumps(
        manifest.model_dump(
            mode="json",
            exclude_none=True,
        ),
        ensure_ascii=False,
        indent=indent,
        sort_keys=True,
    )


def write_model_manifest(
    manifest: ModelManifest,
    manifest_path: str | Path,
    *,
    overwrite: bool = False,
    allowed_base_directories: Sequence[str | Path] | None = None,
) -> Path:
    path = (
        Path(
            manifest_path,
        )
        .expanduser()
        .resolve()
    )

    if path.name.lower() != DEFAULT_MODEL_MANIFEST_FILENAME:
        raise InvalidModelManifestError(
            manifest_path=str(path),
            message=(
                f"Ein Modellmanifest muss '{DEFAULT_MODEL_MANIFEST_FILENAME}' heißen."
            ),
        )

    _validate_path_within_allowed_directories(
        path,
        allowed_base_directories=allowed_base_directories,
        require_existing_path=False,
    )

    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Das Modellmanifest existiert bereits: {path}",
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp",
    )

    content = dump_model_manifest(
        manifest,
    )

    try:
        temporary_path.write_text(
            content + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(
            path,
        )
    except Exception:
        try:
            temporary_path.unlink(
                missing_ok=True,
            )
        except OSError:
            pass

        raise

    return path


# ============================================================
# Validierungshelfer
# ============================================================


def _normalize_string_collection(
    value: object,
    *,
    field_name: str,
    pattern: re.Pattern[str],
    maximum_count: int,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, str):
        raw_values: list[str] = [
            value,
        ]
    else:
        try:
            raw_values = _STRING_LIST_ADAPTER.validate_python(
                value,
            )
        except ValidationError as exc:
            raise ValueError(
                f"{field_name} muss eine Liste von Zeichenketten sein.",
            ) from exc

    normalized_values: list[str] = []
    seen: set[str] = set()

    for raw_value in raw_values:
        normalized = raw_value.strip().lower()

        if not normalized:
            raise ValueError(
                f"{field_name} darf keine leeren Werte enthalten.",
            )

        if not pattern.fullmatch(
            normalized,
        ):
            raise ValueError(
                f"Ungültiger Wert '{normalized}' in {field_name}.",
            )

        if normalized in seen:
            continue

        seen.add(
            normalized,
        )
        normalized_values.append(
            normalized,
        )

    if len(normalized_values) > maximum_count:
        raise ValueError(
            f"{field_name} darf höchstens {maximum_count} Werte enthalten.",
        )

    return tuple(
        sorted(normalized_values),
    )


def _normalize_json_object(
    value: object,
    *,
    path: str,
) -> JsonObject:
    try:
        return _JSON_OBJECT_ADAPTER.validate_python(
            value,
        )
    except ValidationError as exc:
        raise ValueError(
            f"{path} muss ein JSON-Objekt sein.",
        ) from exc


def _validate_provider_config_security(
    value: Mapping[str, JsonValue],
    *,
    path: str,
) -> None:
    for key, nested_value in value.items():
        normalized_key = key.strip().lower()

        if normalized_key in _FORBIDDEN_PROVIDER_CONFIG_KEYS:
            raise ModelManifestSecurityError(
                reason=(
                    f"Der Schlüssel '{path}.{key}' darf keinen "
                    "Python-Import oder ausführbaren Einstiegspunkt "
                    "definieren."
                ),
            )

        if _looks_like_secret_key(
            normalized_key,
        ):
            if nested_value in (
                None,
                "",
            ):
                continue

            if isinstance(nested_value, str) and nested_value.lower().startswith(
                _ALLOWED_SECRET_REFERENCE_PREFIXES,
            ):
                continue

            raise ModelManifestSecurityError(
                reason=(
                    f"Der Schlüssel '{path}.{key}' scheint ein Secret "
                    "zu enthalten. Secrets müssen über provider.secrets "
                    "referenziert werden."
                ),
            )

        if isinstance(nested_value, dict):
            _validate_provider_config_security(
                nested_value,
                path=f"{path}.{key}",
            )

        elif isinstance(nested_value, list):
            for index, item in enumerate(
                nested_value,
            ):
                if isinstance(item, dict):
                    _validate_provider_config_security(
                        item,
                        path=f"{path}.{key}[{index}]",
                    )


def _validate_no_secret_values(
    value: Mapping[str, JsonValue],
    *,
    path: str,
) -> None:
    for key, nested_value in value.items():
        normalized_key = key.strip().lower()

        if _looks_like_secret_key(
            normalized_key,
        ):
            raise ModelManifestSecurityError(
                reason=(f"'{path}.{key}' darf keine Secret-Informationen enthalten."),
            )

        if isinstance(nested_value, dict):
            _validate_no_secret_values(
                nested_value,
                path=f"{path}.{key}",
            )

        elif isinstance(nested_value, list):
            for index, item in enumerate(
                nested_value,
            ):
                if isinstance(item, dict):
                    _validate_no_secret_values(
                        item,
                        path=f"{path}.{key}[{index}]",
                    )


def _looks_like_secret_key(
    key: str,
) -> bool:
    compact_key = key.replace(
        "-",
        "_",
    ).replace(
        ".",
        "_",
    )

    return any(fragment in compact_key for fragment in _SECRET_KEY_FRAGMENTS)


def _validate_path_within_allowed_directories(
    path: Path,
    *,
    allowed_base_directories: Sequence[str | Path] | None,
    require_existing_path: bool = True,
) -> None:
    if not allowed_base_directories:
        return

    resolved_path = (
        path.resolve()
        if require_existing_path or path.exists()
        else path.parent.resolve() / path.name
    )

    allowed_directories = tuple(
        Path(directory).expanduser().resolve() for directory in allowed_base_directories
    )

    if not any(
        _is_relative_to(
            resolved_path,
            allowed_directory,
        )
        for allowed_directory in allowed_directories
    ):
        raise ModelManifestSecurityError(
            reason=(
                "Das Modellmanifest liegt außerhalb der erlaubten "
                "Manifestverzeichnisse."
            ),
            manifest_path=str(resolved_path),
        )


def _is_relative_to(
    path: Path,
    parent: Path,
) -> bool:
    try:
        path.relative_to(
            parent,
        )
        return True
    except ValueError:
        return False


def _serialize_validation_errors(
    error: ValidationError,
) -> list[ValidationErrorItem]:
    result: list[ValidationErrorItem] = []

    for item in error.errors(
        include_url=False,
        include_context=True,
        include_input=False,
    ):
        raw_location: object = item.get(
            "loc",
            (),
        )

        location_parts = _normalize_error_location(
            raw_location,
        )

        error_type = str(
            item.get(
                "type",
                "",
            ),
        )

        message = str(
            item.get(
                "msg",
                "",
            ),
        )

        raw_context: object = item.get(
            "ctx",
        )

        context = (
            _make_json_compatible_object(
                raw_context,
            )
            if raw_context is not None
            else None
        )

        result.append(
            {
                "path": ".".join(
                    location_parts,
                ),
                "type": error_type,
                "message": message,
                "context": context,
            },
        )

    return result


def _make_json_compatible_object(
    value: object,
) -> JsonObject:
    if isinstance(
        value,
        Mapping,
    ):
        typed_mapping = cast(
            Mapping[object, object],
            value,
        )

        result: JsonObject = {}

        for key, nested_value in typed_mapping.items():
            result[str(key)] = _make_json_compatible_value(
                nested_value,
            )

        return result

    return {
        "value": _make_json_compatible_value(
            value,
        ),
    }


def _make_json_compatible_value(
    value: object,
) -> JsonValue:
    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(
        value,
        StrEnum,
    ):
        return value.value

    if isinstance(
        value,
        Mapping,
    ):
        typed_mapping = cast(
            Mapping[object, object],
            value,
        )

        result: JsonObject = {}

        for key, nested_value in typed_mapping.items():
            result[str(key)] = _make_json_compatible_value(
                nested_value,
            )

        return result

    if isinstance(
        value,
        Sequence,
    ) and not isinstance(
        value,
        (
            str,
            bytes,
            bytearray,
        ),
    ):
        typed_sequence = cast(
            Sequence[object],
            value,
        )

        return [
            _make_json_compatible_value(
                item,
            )
            for item in typed_sequence
        ]

    if isinstance(
        value,
        BaseException,
    ):
        return {
            "type": value.__class__.__name__,
            "message": str(
                value,
            ),
        }

    return str(
        value,
    )


def _normalize_error_location(
    value: object,
) -> tuple[str, ...]:
    if value is None:
        return ()

    try:
        parts = _ERROR_LOCATION_ADAPTER.validate_python(
            value,
        )
    except ValidationError:
        return (str(value),)

    return tuple(str(part) for part in parts)


__all__ = [
    "CURRENT_MODEL_MANIFEST_VERSION",
    "DEFAULT_MODEL_MANIFEST_FILENAME",
    "MAX_MANIFEST_FILE_SIZE_BYTES",
    "SUPPORTED_MODEL_MANIFEST_VERSIONS",
    "LoadedModelManifest",
    "ModelLifecycleManifest",
    "ModelLimitsManifest",
    "ModelManifest",
    "ModelManifestCapability",
    "ModelManifestStatus",
    "ModelPresentationManifest",
    "ModelProviderManifest",
    "ModelRuntimeKind",
    "ModelSecretReference",
    "ModelSecretSource",
    "discover_model_manifest_paths",
    "dump_model_manifest",
    "load_discovered_model_manifests",
    "load_model_manifest",
    "load_model_manifest_directory",
    "write_model_manifest",
]
