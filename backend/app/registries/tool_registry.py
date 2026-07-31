# F:\Kernschmied\backend\app\registries\tool_registry.py

"""
Sichere Registry für Kernschmied-Tools.

Die Registry:

- erkennt und validiert deklarative tool.json-Dateien,
- registriert nur Tools, deren tool_type in der festen FactoryRegistry
  freigegeben ist,
- erzeugt Tool-Instanzen über registrierte Factories,
- speichert keine Secrets,
- lädt keinen Python-Code aus Manifesten,
- ist kein globales Singleton.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import re
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final, Protocol, TypeAlias, runtime_checkable

from pydantic import JsonValue, TypeAdapter  # <-- JsonValue von pydantic importiert

from app.contracts.tool import (
    BaseTool,
    ToolAvailability,
    ToolAvailabilityStatus,
    ToolRiskLevel,
)

logger = logging.getLogger(__name__)


# ============================================================
# Strikte Datentypen
# ============================================================

JsonObject: TypeAlias = dict[str, JsonValue]
ToolDependencies: TypeAlias = Mapping[str, object]


_JSON_OBJECT_ADAPTER: Final[TypeAdapter[JsonObject]] = TypeAdapter(
    JsonObject,
)

_JSON_VALUE_ADAPTER: Final[TypeAdapter[JsonValue]] = TypeAdapter(
    JsonValue,
)

_STRING_LIST_ADAPTER: Final[TypeAdapter[list[str]]] = TypeAdapter(
    list[str],
)


def _create_empty_json_object() -> JsonObject:
    return {}


def _normalize_json_object(
    value: object,
) -> JsonObject:
    return _JSON_OBJECT_ADAPTER.validate_python(
        value,
    )


def _normalize_json_value_adapter(
    value: object,
) -> JsonValue:
    return _JSON_VALUE_ADAPTER.validate_python(
        value,
    )


# ============================================================
# Konstanten
# ============================================================

DEFAULT_TOOL_DIRECTORY: Final[Path] = Path("tools")
DEFAULT_TOOL_MANIFEST_FILENAME: Final[str] = "tool.json"
DEFAULT_TOOL_MANIFEST_VERSION: Final[str] = "1.0"

SUPPORTED_TOOL_MANIFEST_VERSIONS: Final[frozenset[str]] = frozenset(
    {
        DEFAULT_TOOL_MANIFEST_VERSION,
    },
)

MAX_TOOL_MANIFEST_SIZE_BYTES: Final[int] = 2 * 1024 * 1024
MAX_TOOL_ID_LENGTH: Final[int] = 128
MAX_TOOL_NAME_LENGTH: Final[int] = 255
MAX_TOOL_DESCRIPTION_LENGTH: Final[int] = 8_000
MAX_TOOL_TAGS: Final[int] = 64
MAX_TOOL_TAG_LENGTH: Final[int] = 64

_TOOL_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,127}$",
)

_TOOL_TYPE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,127}$",
)

_TAG_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,63}$",
)

_FORBIDDEN_MANIFEST_KEYS: Final[frozenset[str]] = frozenset(
    {
        "entrypoint",
        "entry_point",
        "module",
        "module_name",
        "module_path",
        "python_module",
        "python_path",
        "class",
        "class_name",
        "factory",
        "factory_name",
        "callable",
        "code_path",
        "plugin_path",
        "import",
        "import_path",
    },
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


# ============================================================
# Fehler
# ============================================================


class ToolRegistryError(RuntimeError):
    code = "TOOL_REGISTRY_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(message)
        self.details: JsonObject = dict(details or {})


class ToolNotRegisteredError(ToolRegistryError):
    code = "TOOL_NOT_REGISTERED"

    def __init__(self, tool_id: str) -> None:
        self.tool_id = tool_id
        super().__init__(
            f"Das Tool '{tool_id}' ist nicht registriert.",
            details={"tool_id": tool_id},
        )


class DuplicateToolRegistrationError(ToolRegistryError):
    code = "TOOL_ALREADY_REGISTERED"

    def __init__(self, tool_id: str) -> None:
        self.tool_id = tool_id
        super().__init__(
            f"Das Tool '{tool_id}' ist bereits registriert.",
            details={"tool_id": tool_id},
        )


class UnknownToolTypeError(ToolRegistryError):
    code = "TOOL_TYPE_UNKNOWN"

    def __init__(self, tool_type: str) -> None:
        self.tool_type = tool_type
        super().__init__(
            f"Der Tool-Typ '{tool_type}' ist nicht freigegeben.",
            details={"tool_type": tool_type},
        )


class DuplicateToolFactoryError(ToolRegistryError):
    code = "TOOL_FACTORY_DUPLICATE"

    def __init__(self, tool_type: str) -> None:
        self.tool_type = tool_type
        super().__init__(
            f"Für den Tool-Typ '{tool_type}' ist bereits eine Factory registriert.",
            details={"tool_type": tool_type},
        )


class InvalidToolManifestError(ToolRegistryError):
    code = "TOOL_MANIFEST_INVALID"

    def __init__(
        self,
        message: str,
        *,
        manifest_path: Path | None = None,
        details: Mapping[str, JsonValue] | None = None,
    ) -> None:
        merged_details: JsonObject = dict(details or {})
        if manifest_path is not None:
            merged_details["manifest_path"] = str(manifest_path)
        super().__init__(message, details=merged_details)
        self.manifest_path = manifest_path


class ToolFactoryCreationError(ToolRegistryError):
    code = "TOOL_FACTORY_CREATION_FAILED"

    def __init__(
        self,
        *,
        tool_id: str,
        tool_type: str,
        reason: str,
    ) -> None:
        self.tool_id = tool_id
        self.tool_type = tool_type
        self.reason = reason
        super().__init__(
            f"Das Tool '{tool_id}' konnte nicht erzeugt werden: {reason}",
            details={
                "tool_id": tool_id,
                "tool_type": tool_type,
                "reason": reason,
            },
        )


# ============================================================
# Manifest
# ============================================================


class ToolManifestStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class ToolManifest:
    schema_version: str
    tool_id: str
    tool_type: str
    display_name: str
    description: str | None
    status: ToolManifestStatus
    enabled: bool
    config: Mapping[str, JsonValue]
    tags: frozenset[str]
    metadata: Mapping[str, JsonValue]
    manifest_path: Path

    @property
    def is_enabled(self) -> bool:
        return self.enabled and self.status != ToolManifestStatus.DISABLED


# ============================================================
# Factory-Registry
# ============================================================

ToolFactory: TypeAlias = Callable[
    [ToolManifest, ToolDependencies],
    BaseTool | Awaitable[BaseTool],
]


@dataclass(frozen=True, slots=True)
class ToolFactoryDefinition:
    tool_type: str
    factory: ToolFactory
    description: str | None = None


class ToolFactoryRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ToolFactoryDefinition] = {}

    def register(
        self,
        tool_type: str,
        factory: ToolFactory,
        *,
        description: str | None = None,
        replace: bool = False,
    ) -> None:
        normalized_tool_type = _normalize_tool_type(tool_type)
        if not callable(factory):
            raise TypeError("factory muss aufrufbar sein.")
        if normalized_tool_type in self._factories and not replace:
            raise DuplicateToolFactoryError(normalized_tool_type)
        self._factories[normalized_tool_type] = ToolFactoryDefinition(
            tool_type=normalized_tool_type,
            factory=factory,
            description=description,
        )

    def unregister(self, tool_type: str) -> bool:
        normalized_tool_type = _normalize_tool_type(tool_type)
        return self._factories.pop(normalized_tool_type, None) is not None

    def has(self, tool_type: str) -> bool:
        normalized_tool_type = _normalize_tool_type(tool_type)
        return normalized_tool_type in self._factories

    def get(self, tool_type: str) -> ToolFactoryDefinition:
        normalized_tool_type = _normalize_tool_type(tool_type)
        definition = self._factories.get(normalized_tool_type)
        if definition is None:
            raise UnknownToolTypeError(normalized_tool_type)
        return definition

    def list_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))

    async def create(
        self,
        manifest: ToolManifest,
        dependencies: ToolDependencies,
    ) -> BaseTool:
        definition = self.get(manifest.tool_type)
        try:
            result = definition.factory(manifest, dependencies)
            if inspect.isawaitable(result):
                tool = await result
            else:
                tool = result
        except ToolRegistryError:
            raise
        except Exception as exc:
            raise ToolFactoryCreationError(
                tool_id=manifest.tool_id,
                tool_type=manifest.tool_type,
                reason=str(exc) or exc.__class__.__name__,
            ) from exc

        # Vertragssicherheit: Die Factory muss ein BaseTool zurückgeben.
        if not isinstance(tool, BaseTool):  # type: ignore[reportUnnecessaryIsInstance]
            raise ToolFactoryCreationError(
                tool_id=manifest.tool_id,
                tool_type=manifest.tool_type,
                reason="Die Factory gab keine BaseTool-Instanz zurück.",
            )
        return tool


# ============================================================
# Registry-Datenmodelle
# ============================================================


class ToolRegistrationStatus(StrEnum):
    REGISTERED = "registered"
    REPLACED = "replaced"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ToolRegistryEntry:
    manifest: ToolManifest
    tool: BaseTool
    registration_index: int
    registered_at_monotonic: float

    @property
    def tool_id(self) -> str:
        return self.manifest.tool_id

    @property
    def tool_type(self) -> str:
        return self.manifest.tool_type

    @property
    def enabled(self) -> bool:
        return self.manifest.is_enabled


@dataclass(frozen=True, slots=True)
class ToolRegistrationResult:
    manifest_path: Path
    status: ToolRegistrationStatus
    tool_id: str | None = None
    tool_type: str | None = None
    message: str | None = None
    error_type: str | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ToolDiscoveryReport:
    base_directories: tuple[Path, ...]
    discovered_paths: tuple[Path, ...]
    results: tuple[ToolRegistrationResult, ...]
    started_at_monotonic: float
    finished_at_monotonic: float

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.finished_at_monotonic - self.started_at_monotonic)

    @property
    def registered_count(self) -> int:
        return sum(
            1
            for r in self.results
            if r.status
            in {ToolRegistrationStatus.REGISTERED, ToolRegistrationStatus.REPLACED}
        )

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == ToolRegistrationStatus.FAILED)

    @property
    def skipped_count(self) -> int:
        return sum(
            1 for r in self.results if r.status == ToolRegistrationStatus.SKIPPED
        )


@dataclass(frozen=True, slots=True)
class ToolRegistrySnapshot:
    tool_id: str
    tool_type: str
    display_name: str
    description: str | None
    enabled: bool
    status: str
    risk_level: str | None
    available: bool
    availability_reason: str | None
    tags: tuple[str, ...]
    manifest_path: Path
    registration_index: int
    registered_at_monotonic: float
    metadata: Mapping[str, JsonValue] = field(
        default_factory=_create_empty_json_object,
    )


# ============================================================
# ToolRegistry
# ============================================================


class ToolRegistry:
    def __init__(
        self,
        base_dir: Path | None = None,
        *,
        base_directories: Sequence[str | Path] | None = None,
        factory_registry: ToolFactoryRegistry | None = None,
        common_dependencies: ToolDependencies | None = None,
        recursive: bool = True,
        follow_symlinks: bool = False,
    ) -> None:
        if base_dir is not None and base_directories is not None:
            raise ValueError(
                "base_dir und base_directories dürfen nicht gleichzeitig "
                "gesetzt werden."
            )

        raw_directories: Sequence[str | Path]
        if base_directories is not None:
            raw_directories = base_directories
        elif base_dir is not None:
            raw_directories = (base_dir,)
        else:
            raw_directories = (DEFAULT_TOOL_DIRECTORY,)

        self._base_directories = tuple(
            Path(d).expanduser().resolve() for d in raw_directories
        )
        self._recursive = recursive
        self._follow_symlinks = follow_symlinks

        self._factory_registry = factory_registry or ToolFactoryRegistry()
        self._common_dependencies: dict[str, object] = dict(common_dependencies or {})

        self._tools: dict[str, ToolRegistryEntry] = {}
        self._path_index: dict[Path, str] = {}
        self._registration_counter = 0
        self._lock = asyncio.Lock()
        self._last_discovery_report: ToolDiscoveryReport | None = None

    # ---- Eigenschaften ----

    @property
    def base_directories(self) -> tuple[Path, ...]:
        return self._base_directories

    @property
    def factory_registry(self) -> ToolFactoryRegistry:
        return self._factory_registry

    @property
    def count(self) -> int:
        return len(self._tools)

    @property
    def last_discovery_report(self) -> ToolDiscoveryReport | None:
        return self._last_discovery_report

    # ---- Discovery ----

    async def discover(
        self,
        *,
        replace_existing: bool = True,
        clear_missing: bool = True,
        continue_on_error: bool = True,
    ) -> ToolDiscoveryReport:
        started_at = time.monotonic()

        discovered_paths = discover_tool_manifest_paths(
            self._base_directories,
            recursive=self._recursive,
            follow_symlinks=self._follow_symlinks,
        )

        results: list[ToolRegistrationResult] = []
        loaded_manifests: list[ToolManifest] = []
        ids_seen: dict[str, Path] = {}

        for manifest_path in discovered_paths:
            try:
                manifest = load_tool_manifest(
                    manifest_path,
                    allowed_base_directories=self._base_directories,
                )
                if manifest.tool_id in ids_seen:
                    raise DuplicateToolRegistrationError(manifest.tool_id)
                ids_seen[manifest.tool_id] = manifest_path
                loaded_manifests.append(manifest)
            except Exception as exc:
                results.append(
                    _create_error_result(manifest_path=manifest_path, error=exc)
                )
                logger.warning(
                    "Tool manifest validation failed",
                    extra={"manifest_path": str(manifest_path), "error": exc},
                    exc_info=exc,
                )
                if not continue_on_error:
                    raise

        valid_paths = {m.manifest_path for m in loaded_manifests}

        if clear_missing:
            await self._remove_missing_paths(valid_paths)

        for manifest in sorted(
            loaded_manifests,
            key=lambda m: (m.display_name.lower(), m.tool_id),
        ):
            try:
                replaced = await self.register_manifest(
                    manifest, replace=replace_existing
                )
                results.append(
                    ToolRegistrationResult(
                        manifest_path=manifest.manifest_path,
                        status=(
                            ToolRegistrationStatus.REPLACED
                            if replaced
                            else ToolRegistrationStatus.REGISTERED
                        ),
                        tool_id=manifest.tool_id,
                        tool_type=manifest.tool_type,
                    )
                )
            except DuplicateToolRegistrationError as exc:
                results.append(
                    ToolRegistrationResult(
                        manifest_path=manifest.manifest_path,
                        status=ToolRegistrationStatus.SKIPPED,
                        tool_id=manifest.tool_id,
                        tool_type=manifest.tool_type,
                        message=str(exc),
                        error_type=exc.__class__.__name__,
                        error_code=exc.code,
                    )
                )
                if not continue_on_error:
                    raise
            except Exception as exc:
                results.append(
                    _create_error_result(
                        manifest_path=manifest.manifest_path,
                        error=exc,
                        tool_id=manifest.tool_id,
                        tool_type=manifest.tool_type,
                    )
                )
                if not continue_on_error:
                    raise

        report = ToolDiscoveryReport(
            base_directories=self._base_directories,
            discovered_paths=discovered_paths,
            results=tuple(results),
            started_at_monotonic=started_at,
            finished_at_monotonic=time.monotonic(),
        )
        self._last_discovery_report = report
        return report

    # ---- Registrierung ----

    async def register_manifest(
        self,
        manifest: ToolManifest,
        *,
        replace: bool = False,
        dependencies: ToolDependencies | None = None,
    ) -> bool:
        tool_id = _normalize_tool_id(manifest.tool_id)

        if not self._factory_registry.has(manifest.tool_type):
            raise UnknownToolTypeError(manifest.tool_type)

        merged_dependencies: dict[str, object] = dict(self._common_dependencies)
        if dependencies is not None:
            merged_dependencies.update(dependencies)
        merged_dependencies.setdefault("manifest", manifest)
        merged_dependencies.setdefault("tool_id", manifest.tool_id)
        merged_dependencies.setdefault("tool_type", manifest.tool_type)

        tool = await self._factory_registry.create(manifest, merged_dependencies)
        definition = tool.definition()
        _validate_tool_definition(manifest=manifest, definition=definition)

        async with self._lock:
            existing = self._tools.get(tool_id)
            if existing is not None and not replace:
                raise DuplicateToolRegistrationError(tool_id)

            self._registration_counter += 1
            entry = ToolRegistryEntry(
                manifest=manifest,
                tool=tool,
                registration_index=self._registration_counter,
                registered_at_monotonic=time.monotonic(),
            )

            if existing is not None:
                self._path_index.pop(existing.manifest.manifest_path, None)

            self._tools[tool_id] = entry
            self._path_index[manifest.manifest_path] = tool_id
            return existing is not None

    async def register_instance(
        self,
        tool: BaseTool,
        *,
        tool_id: str | None = None,
        tool_type: str = "builtin",
        display_name: str | None = None,
        description: str | None = None,
        enabled: bool = True,
        replace: bool = False,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> bool:
        definition = tool.definition()

        resolved_tool_id = _normalize_tool_id(
            tool_id
            or _definition_value(definition, "name")
            or _definition_value(definition, "id")
            or tool.__class__.__name__
        )

        resolved_display_name = (
            display_name
            or _definition_value(definition, "display_name")
            or _definition_value(definition, "name")
            or resolved_tool_id
        )
        if not isinstance(resolved_display_name, str):
            resolved_display_name = str(resolved_display_name)

        virtual_path = Path(f"<builtin>/{resolved_tool_id}/tool.json")

        manifest = ToolManifest(
            schema_version=DEFAULT_TOOL_MANIFEST_VERSION,
            tool_id=resolved_tool_id,
            tool_type=_normalize_tool_type(tool_type),
            display_name=resolved_display_name,
            description=description,
            status=ToolManifestStatus.ACTIVE,
            enabled=enabled,
            config={},
            tags=frozenset(),
            metadata=dict(metadata or {}),
            manifest_path=virtual_path,
        )

        _validate_tool_definition(manifest=manifest, definition=definition)

        async with self._lock:
            existing = self._tools.get(resolved_tool_id)
            if existing is not None and not replace:
                raise DuplicateToolRegistrationError(resolved_tool_id)

            self._registration_counter += 1
            entry = ToolRegistryEntry(
                manifest=manifest,
                tool=tool,
                registration_index=self._registration_counter,
                registered_at_monotonic=time.monotonic(),
            )
            self._tools[resolved_tool_id] = entry
            return existing is not None

    async def unregister(self, tool_id: str) -> bool:
        normalized = _normalize_tool_id(tool_id)
        async with self._lock:
            entry = self._tools.pop(normalized, None)
            if entry is None:
                return False
            self._path_index.pop(entry.manifest.manifest_path, None)
            return True

    async def clear(self) -> None:
        async with self._lock:
            self._tools.clear()
            self._path_index.clear()

    async def _remove_missing_paths(self, valid_paths: set[Path]) -> None:
        async with self._lock:
            to_remove = [
                tid
                for tid, entry in self._tools.items()
                if not str(entry.manifest.manifest_path).startswith("<builtin>")
                and entry.manifest.manifest_path not in valid_paths
            ]
            for tid in to_remove:
                entry = self._tools.pop(tid, None)
                if entry:
                    self._path_index.pop(entry.manifest.manifest_path, None)

    # ---- Zugriff ----

    def has(self, tool_id: str) -> bool:
        normalized = _normalize_tool_id(tool_id)
        return normalized in self._tools

    def get_entry(self, tool_id: str) -> ToolRegistryEntry:
        normalized = _normalize_tool_id(tool_id)
        entry = self._tools.get(normalized)
        if entry is None:
            raise ToolNotRegisteredError(normalized)
        return entry

    def get_tool(self, tool_id: str) -> BaseTool:
        return self.get_entry(tool_id).tool

    def get_manifest(self, tool_id: str) -> ToolManifest:
        return self.get_entry(tool_id).manifest

    def list_entries(
        self,
        *,
        enabled_only: bool = False,
        tool_type: str | None = None,
        risk_level: ToolRiskLevel | str | None = None,
        tags: Sequence[str] | None = None,
    ) -> tuple[ToolRegistryEntry, ...]:
        normalized_tool_type = (
            _normalize_tool_type(tool_type) if tool_type is not None else None
        )
        normalized_risk = (
            risk_level.value
            if isinstance(risk_level, ToolRiskLevel)
            else str(risk_level).strip().lower()
            if risk_level is not None
            else None
        )
        required_tags = frozenset(
            str(t).strip().lower() for t in (tags or ()) if str(t).strip()
        )

        result: list[ToolRegistryEntry] = []
        for entry in self._tools.values():
            if enabled_only and not entry.enabled:
                continue
            if (
                normalized_tool_type is not None
                and entry.tool_type != normalized_tool_type
            ):
                continue
            if required_tags and not required_tags.issubset(entry.manifest.tags):
                continue
            if normalized_risk is not None:
                def_risk = _definition_value(entry.tool.definition(), "risk_level")
                if isinstance(def_risk, ToolRiskLevel):
                    def_risk = def_risk.value
                elif def_risk is None:
                    def_risk = None
                else:
                    def_risk = str(def_risk).lower()
                if def_risk != normalized_risk:
                    continue
            result.append(entry)

        return tuple(
            sorted(result, key=lambda e: (e.manifest.display_name.lower(), e.tool_id))
        )

    def list_tools(self, *, enabled_only: bool = False) -> list[JsonObject]:
        return [
            self._snapshot_to_dict(self._create_snapshot(entry))
            for entry in self.list_entries(enabled_only=enabled_only)
        ]

    def list_snapshots(
        self, *, enabled_only: bool = False
    ) -> tuple[ToolRegistrySnapshot, ...]:
        return tuple(
            self._create_snapshot(e)
            for e in self.list_entries(enabled_only=enabled_only)
        )

    def get_snapshot(self, tool_id: str) -> ToolRegistrySnapshot:
        return self._create_snapshot(self.get_entry(tool_id))

    # ---- Diagnose ----

    @staticmethod
    def _create_snapshot(entry: ToolRegistryEntry) -> ToolRegistrySnapshot:
        definition = entry.tool.definition()
        availability = _read_tool_availability(entry.tool)

        risk_level = _definition_value(definition, "risk_level")
        if isinstance(risk_level, ToolRiskLevel):
            risk_level_value = risk_level.value
        elif isinstance(risk_level, str):
            risk_level_value = risk_level
        else:
            risk_level_value = None

        available = availability.status == ToolAvailabilityStatus.AVAILABLE

        serialized_definition = _serialize_definition(definition)

        return ToolRegistrySnapshot(
            tool_id=entry.tool_id,
            tool_type=entry.tool_type,
            display_name=entry.manifest.display_name,
            description=entry.manifest.description,
            enabled=entry.enabled,
            status=entry.manifest.status.value,
            risk_level=risk_level_value,
            available=available,
            availability_reason=availability.reason,
            tags=tuple(sorted(entry.manifest.tags)),
            manifest_path=entry.manifest.manifest_path,
            registration_index=entry.registration_index,
            registered_at_monotonic=entry.registered_at_monotonic,
            metadata={
                "manifest_metadata": dict(entry.manifest.metadata),
                "definition": serialized_definition,
            },
        )

    @staticmethod
    def _snapshot_to_dict(snapshot: ToolRegistrySnapshot) -> JsonObject:
        return {
            "id": snapshot.tool_id,
            "name": snapshot.tool_id,
            "display_name": snapshot.display_name,
            "description": snapshot.description,
            "tool_type": snapshot.tool_type,
            "enabled": snapshot.enabled,
            "available": snapshot.available,
            "availability_reason": snapshot.availability_reason,
            "status": snapshot.status,
            "risk_level": snapshot.risk_level,
            "tags": list(snapshot.tags),
            "manifest_path": str(snapshot.manifest_path),
            "metadata": dict(snapshot.metadata),
        }


# ============================================================
# Manifest-Discovery und -Ladung
# ============================================================


def discover_tool_manifest_paths(
    base_directories: Sequence[str | Path],
    *,
    recursive: bool = True,
    follow_symlinks: bool = False,
) -> tuple[Path, ...]:
    discovered: set[Path] = set()
    for raw in base_directories:
        base = Path(raw).expanduser().resolve()
        if not base.is_dir():
            continue
        iterator = (
            base.rglob(DEFAULT_TOOL_MANIFEST_FILENAME)
            if recursive
            else base.glob(DEFAULT_TOOL_MANIFEST_FILENAME)
        )
        for candidate in iterator:
            try:
                if not candidate.is_file():
                    continue
                if candidate.is_symlink() and not follow_symlinks:
                    continue
                resolved = candidate.resolve()
                if not _is_relative_to(resolved, base):
                    continue
                discovered.add(resolved)
            except OSError:
                continue
    return tuple(sorted(discovered, key=lambda p: str(p).lower()))


def load_tool_manifest(
    manifest_path: str | Path,
    *,
    allowed_base_directories: Sequence[str | Path] | None = None,
    maximum_file_size_bytes: int = MAX_TOOL_MANIFEST_SIZE_BYTES,
) -> ToolManifest:
    path = Path(manifest_path).expanduser().resolve()

    if not path.is_file():
        raise InvalidToolManifestError(
            "Das Tool-Manifest wurde nicht gefunden.", manifest_path=path
        )

    if path.name.lower() != DEFAULT_TOOL_MANIFEST_FILENAME:
        raise InvalidToolManifestError(
            f"Das Tool-Manifest muss '{DEFAULT_TOOL_MANIFEST_FILENAME}' heißen.",
            manifest_path=path,
        )

    _validate_manifest_path(path, allowed_base_directories=allowed_base_directories)

    try:
        file_size = path.stat().st_size
    except OSError as exc:
        raise InvalidToolManifestError(
            "Die Größe des Tool-Manifests konnte nicht gelesen werden.",
            manifest_path=path,
        ) from exc

    if file_size > maximum_file_size_bytes:
        raise InvalidToolManifestError(
            "Das Tool-Manifest überschreitet die erlaubte Dateigröße.",
            manifest_path=path,
            details={
                "maximum_file_size_bytes": maximum_file_size_bytes,
                "actual_file_size_bytes": file_size,
            },
        )

    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidToolManifestError(
            "Das Tool-Manifest muss UTF-8-codiert sein.",
            manifest_path=path,
        ) from exc
    except OSError as exc:
        raise InvalidToolManifestError(
            "Das Tool-Manifest konnte nicht gelesen werden.",
            manifest_path=path,
        ) from exc

    try:
        raw_data = _JSON_OBJECT_ADAPTER.validate_json(raw_text)
    except ValueError as exc:
        raise InvalidToolManifestError(
            "Das Tool-Manifest enthält ungültiges JSON.",
            manifest_path=path,
            details={"validation_error": str(exc)},  # type: ignore[arg-type]
        ) from exc

    return _parse_tool_manifest(raw_data, manifest_path=path)  # type: ignore[arg-type]


def _parse_tool_manifest(
    raw_data: JsonObject,
    *,
    manifest_path: Path,
) -> ToolManifest:
    _validate_forbidden_keys(raw_data, path="manifest", manifest_path=manifest_path)

    schema_version = str(
        raw_data.get("schema_version", DEFAULT_TOOL_MANIFEST_VERSION)
    ).strip()
    if schema_version not in SUPPORTED_TOOL_MANIFEST_VERSIONS:
        raise InvalidToolManifestError(
            "Die Version des Tool-Manifests wird nicht unterstützt.",
            manifest_path=manifest_path,
            details={
                "schema_version": schema_version,
                "supported_versions": list(
                    SUPPORTED_TOOL_MANIFEST_VERSIONS
                ),  # in Liste umwandeln
            },
        )

    tool_id = _normalize_tool_id(raw_data.get("id"))

    raw_tool_type = raw_data.get("tool_type", raw_data.get("type"))
    if raw_tool_type is None:
        raise InvalidToolManifestError(
            "Das Tool-Manifest benötigt 'tool_type'.",
            manifest_path=manifest_path,
        )
    tool_type = _normalize_tool_type(raw_tool_type)

    raw_display_name = raw_data.get("display_name", raw_data.get("name", tool_id))
    display_name = str(raw_display_name).strip()
    if not display_name:
        raise InvalidToolManifestError(
            "display_name darf nicht leer sein.", manifest_path=manifest_path
        )
    if len(display_name) > MAX_TOOL_NAME_LENGTH:
        raise InvalidToolManifestError(
            "display_name ist zu lang.", manifest_path=manifest_path
        )

    raw_description = raw_data.get("description")
    description = str(raw_description).strip() if raw_description is not None else None
    if description == "":
        description = None
    if description is not None and len(description) > MAX_TOOL_DESCRIPTION_LENGTH:
        raise InvalidToolManifestError(
            "description ist zu lang.", manifest_path=manifest_path
        )

    raw_status = raw_data.get("status", ToolManifestStatus.ACTIVE.value)
    try:
        status = ToolManifestStatus(str(raw_status).strip().lower())
    except ValueError as exc:
        raise InvalidToolManifestError(
            "Das Tool-Manifest enthält einen ungültigen Status.",
            manifest_path=manifest_path,
        ) from exc

    raw_enabled = raw_data.get("enabled", True)
    if not isinstance(raw_enabled, bool):
        raise InvalidToolManifestError(
            "enabled muss ein boolescher Wert sein.",
            manifest_path=manifest_path,
        )
    enabled = raw_enabled
    if status == ToolManifestStatus.DISABLED and enabled:
        raise InvalidToolManifestError(
            "Ein deaktiviertes Tool muss enabled=false verwenden.",
            manifest_path=manifest_path,
        )

    raw_config = raw_data.get("config", {})
    config = _require_json_object(
        raw_config, field_name="config", manifest_path=manifest_path
    )
    _validate_no_secrets(config, path="config", manifest_path=manifest_path)

    tags = _normalize_tags(raw_data.get("tags", []), manifest_path=manifest_path)

    raw_metadata = raw_data.get("metadata", {})
    metadata = _require_json_object(
        raw_metadata, field_name="metadata", manifest_path=manifest_path
    )
    _validate_no_secrets(metadata, path="metadata", manifest_path=manifest_path)

    return ToolManifest(
        schema_version=schema_version,
        tool_id=tool_id,
        tool_type=tool_type,
        display_name=display_name,
        description=description,
        status=status,
        enabled=enabled,
        config=config,
        tags=tags,
        metadata=metadata,
        manifest_path=manifest_path,
    )


# ============================================================
# Validierungshilfen
# ============================================================


def _require_json_object(
    value: JsonValue,
    *,
    field_name: str,
    manifest_path: Path,
) -> JsonObject:
    if not isinstance(value, dict):
        raise InvalidToolManifestError(
            f"{field_name} muss ein JSON-Objekt sein.",
            manifest_path=manifest_path,
        )
    return value


def _validate_forbidden_keys(
    value: Mapping[str, JsonValue],
    *,
    path: str,
    manifest_path: Path,
) -> None:
    for key, nested_value in value.items():
        normalized_key = key.strip().lower()
        if normalized_key in _FORBIDDEN_MANIFEST_KEYS:
            raise InvalidToolManifestError(
                f"'{path}.{key}' darf keinen Python-Import oder "
                "ausführbaren Einstiegspunkt definieren.",
                manifest_path=manifest_path,
            )

        if isinstance(nested_value, dict):
            _validate_forbidden_keys(
                nested_value,
                path=f"{path}.{key}",
                manifest_path=manifest_path,
            )
        elif isinstance(nested_value, list):
            for idx, item in enumerate(nested_value):
                if isinstance(item, dict):
                    _validate_forbidden_keys(
                        item,
                        path=f"{path}.{key}[{idx}]",
                        manifest_path=manifest_path,
                    )


def _validate_no_secrets(
    value: Mapping[str, JsonValue],
    *,
    path: str,
    manifest_path: Path,
) -> None:
    for key, nested_value in value.items():
        normalized_key = key.strip().lower().replace("-", "_").replace(".", "_")
        if any(fragment in normalized_key for fragment in _SECRET_KEY_FRAGMENTS):
            raise InvalidToolManifestError(
                f"'{path}.{key}' darf keine Secrets enthalten.",
                manifest_path=manifest_path,
            )

        if isinstance(nested_value, dict):
            _validate_no_secrets(
                nested_value,
                path=f"{path}.{key}",
                manifest_path=manifest_path,
            )
        elif isinstance(nested_value, list):
            for idx, item in enumerate(nested_value):
                if isinstance(item, dict):
                    _validate_no_secrets(
                        item,
                        path=f"{path}.{key}[{idx}]",
                        manifest_path=manifest_path,
                    )


def _validate_manifest_path(
    path: Path,
    *,
    allowed_base_directories: Sequence[str | Path] | None,
) -> None:
    if not allowed_base_directories:
        return
    allowed = tuple(Path(d).expanduser().resolve() for d in allowed_base_directories)
    if not any(_is_relative_to(path, base) for base in allowed):
        raise InvalidToolManifestError(
            "Das Tool-Manifest liegt außerhalb der erlaubten Tool-Verzeichnisse.",
            manifest_path=path,
        )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


# ============================================================
# Tool-Definitions-Zugriff und Serialisierung
# ============================================================


@runtime_checkable
class SupportsModelDump(Protocol):
    def model_dump(self, *, mode: str, exclude_none: bool) -> object: ...


def _definition_value(definition: object, key: str) -> object | None:
    if isinstance(definition, Mapping):
        try:
            normalized = _normalize_json_object(dict(definition))  # type: ignore[arg-type]
            return normalized.get(key)
        except ValueError:
            return None
    return getattr(definition, key, None)


def _serialize_definition(definition: object) -> JsonObject:
    if isinstance(definition, Mapping):
        return _normalize_json_object(dict(definition))  # type: ignore[arg-type]

    if isinstance(definition, SupportsModelDump):
        dumped = definition.model_dump(mode="json", exclude_none=True)
        return _normalize_json_object(dict(dumped))  # type: ignore[arg-type]

    return {"value": str(definition)}


def _serialize_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, StrEnum):
        return value.value

    if isinstance(value, Mapping):
        return _normalize_json_object(dict(value))  # type: ignore[arg-type]

    if isinstance(value, (list, tuple, set, frozenset)):
        return [_serialize_value(item) for item in value]  # type: ignore[arg-type]

    if isinstance(value, SupportsModelDump):
        dumped = value.model_dump(mode="json", exclude_none=True)
        return _normalize_json_value_adapter(dict(dumped))  # type: ignore[arg-type]

    return str(value)


def _validate_tool_definition(
    *,
    manifest: ToolManifest,
    definition: object,
) -> None:
    definition_name = _definition_value(definition, "name") or _definition_value(
        definition, "id"
    )
    if definition_name is None:
        raise ToolFactoryCreationError(
            tool_id=manifest.tool_id,
            tool_type=manifest.tool_type,
            reason="Die Tool-Definition enthält weder 'name' noch 'id'.",
        )

    normalized_definition_name = _normalize_tool_id(definition_name)
    if normalized_definition_name != manifest.tool_id:
        raise ToolFactoryCreationError(
            tool_id=manifest.tool_id,
            tool_type=manifest.tool_type,
            reason=(
                f"Die Tool-Definition verwendet die ID "
                f"'{normalized_definition_name}', erwartet wurde "
                f"'{manifest.tool_id}'."
            ),
        )


# ============================================================
# Verfügbarkeitsprüfung
# ============================================================


def _read_tool_availability(tool: BaseTool) -> ToolAvailability:
    availability_method = getattr(tool, "availability", None)
    if not callable(availability_method):
        return ToolAvailability(
            status=ToolAvailabilityStatus.AVAILABLE,
            reason=None,
        )

    try:
        result = availability_method()
        if inspect.isawaitable(result):
            return ToolAvailability(
                status=ToolAvailabilityStatus.UNAVAILABLE,
                reason=(
                    "Die asynchrone Verfügbarkeitsprüfung kann in der "
                    "synchronen Registry-Diagnose nicht ausgeführt werden."
                ),
            )

        if isinstance(result, ToolAvailability):
            return result

        if isinstance(result, bool):
            return ToolAvailability(
                status=(
                    ToolAvailabilityStatus.AVAILABLE
                    if result
                    else ToolAvailabilityStatus.UNAVAILABLE
                ),
                reason=None,
            )

        return ToolAvailability(
            status=ToolAvailabilityStatus.UNAVAILABLE,
            reason="Die Verfügbarkeitsprüfung lieferte einen nicht unterstützten Rückgabewert.",
        )

    except Exception as exc:
        return ToolAvailability(
            status=ToolAvailabilityStatus.UNAVAILABLE,
            reason=str(exc) or exc.__class__.__name__,
        )


# ============================================================
# Normalisierung von IDs, Typen, Tags
# ============================================================


def _normalize_tool_id(value: object) -> str:
    if value is None:
        raise ValueError("Die Tool-ID fehlt.")
    normalized = str(value).strip().lower()
    if not normalized:
        raise ValueError("Die Tool-ID darf nicht leer sein.")
    if len(normalized) > MAX_TOOL_ID_LENGTH:
        raise ValueError("Die Tool-ID ist zu lang.")
    if not _TOOL_ID_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Die Tool-ID darf nur Kleinbuchstaben, Ziffern, Punkte, "
            "Bindestriche und Unterstriche enthalten."
        )
    return normalized


def _normalize_tool_type(value: object) -> str:
    if value is None:
        raise ValueError("Der Tool-Typ fehlt.")
    normalized = str(value).strip().lower()
    if not normalized:
        raise ValueError("Der Tool-Typ darf nicht leer sein.")
    if not _TOOL_TYPE_PATTERN.fullmatch(normalized):
        raise ValueError("Der Tool-Typ besitzt ein ungültiges Format.")
    return normalized


def _normalize_tags(
    value: JsonValue,
    *,
    manifest_path: Path,
) -> frozenset[str]:
    if value is None:
        return frozenset()

    if isinstance(value, str):
        raw_tags: list[str] = [value]
    elif isinstance(value, list):
        try:
            raw_tags = _STRING_LIST_ADAPTER.validate_python(value)
        except ValueError as exc:
            raise InvalidToolManifestError(
                "tags muss ausschließlich Zeichenketten enthalten.",
                manifest_path=manifest_path,
            ) from exc
    else:
        raise InvalidToolManifestError(
            "tags muss eine Liste von Zeichenketten sein.",
            manifest_path=manifest_path,
        )

    normalized_tags: set[str] = set()
    for raw_tag in raw_tags:
        tag = raw_tag.strip().lower()
        if not tag:
            raise InvalidToolManifestError(
                "tags darf keine leeren Werte enthalten.",
                manifest_path=manifest_path,
            )
        if len(tag) > MAX_TOOL_TAG_LENGTH:
            raise InvalidToolManifestError(
                f"Der Tag '{tag}' ist zu lang.",
                manifest_path=manifest_path,
            )
        if not _TAG_PATTERN.fullmatch(tag):
            raise InvalidToolManifestError(
                f"Der Tag '{tag}' ist ungültig.",
                manifest_path=manifest_path,
            )
        normalized_tags.add(tag)

    if len(normalized_tags) > MAX_TOOL_TAGS:
        raise InvalidToolManifestError(
            f"Ein Tool darf höchstens {MAX_TOOL_TAGS} Tags besitzen.",
            manifest_path=manifest_path,
        )
    return frozenset(normalized_tags)


def _read_optional_string_attribute(
    value: object,
    attribute_name: str,
) -> str | None:
    attr = getattr(value, attribute_name, None)
    if attr is None:
        return None
    return str(attr)


def _create_error_result(
    *,
    manifest_path: Path,
    error: BaseException,
    tool_id: str | None = None,
    tool_type: str | None = None,
) -> ToolRegistrationResult:
    error_tool_id = _read_optional_string_attribute(error, "tool_id")
    error_tool_type = _read_optional_string_attribute(error, "tool_type")
    error_code = _read_optional_string_attribute(error, "code")

    return ToolRegistrationResult(
        manifest_path=manifest_path,
        status=ToolRegistrationStatus.FAILED,
        tool_id=tool_id or error_tool_id,
        tool_type=tool_type or error_tool_type,
        message=str(error),
        error_type=error.__class__.__name__,
        error_code=error_code,
    )


__all__ = [
    "DEFAULT_TOOL_DIRECTORY",
    "DEFAULT_TOOL_MANIFEST_FILENAME",
    "DEFAULT_TOOL_MANIFEST_VERSION",
    "DuplicateToolFactoryError",
    "DuplicateToolRegistrationError",
    "InvalidToolManifestError",
    "ToolDiscoveryReport",
    "ToolFactory",
    "ToolFactoryCreationError",
    "ToolFactoryDefinition",
    "ToolFactoryRegistry",
    "ToolManifest",
    "ToolManifestStatus",
    "ToolNotRegisteredError",
    "ToolRegistrationResult",
    "ToolRegistrationStatus",
    "ToolRegistry",
    "ToolRegistryEntry",
    "ToolRegistryError",
    "ToolRegistrySnapshot",
    "UnknownToolTypeError",
    "discover_tool_manifest_paths",
    "load_tool_manifest",
]
