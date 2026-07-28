# F:\Kernschmied\backend\app\registries\model_registry.py

"""
Registry für validierte Modellmanifeste.

Die ModelRegistry verwaltet ausschließlich bekannte und validierte
Modelldefinitionen. Sie:

- erkennt model.json-Dateien in kontrollierten Verzeichnissen,
- validiert diese über app.models.manifest,
- erkennt doppelte Modell-IDs,
- isoliert Fehler einzelner Manifestdateien,
- speichert keine Provider-Instanzen,
- lädt keine Modelle,
- öffnet keine Netzwerkverbindungen,
- erteilt keine Benutzerberechtigungen.

Wichtige Trennung:

    ModelRegistry
        verwaltet deklarative Modelldefinitionen

    ModelProviderRegistry
        verwaltet freigegebene Provider-Factories

    ModelLifecycleManager
        verwaltet erzeugte Backend-Instanzen

    ModelService
        orchestriert Autorisierung, Secrets, Lifecycle und Generierung

Discovery bedeutet niemals automatische Ausführungsfreigabe.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Final

from app.models.errors import (
    DuplicateModelManifestError,
    DuplicateModelRegistrationError,
    ModelManifestNotFoundError,
    ModelNotRegisteredError,
)
from app.models.manifest import (
    LoadedModelManifest,
    ModelManifest,
    discover_model_manifest_paths,
    load_model_manifest,
)


logger = logging.getLogger(__name__)


DEFAULT_MODEL_DIRECTORY: Final[Path] = Path("model_paths")
DEFAULT_DISCOVERY_RECURSIVE: Final[bool] = True
DEFAULT_FOLLOW_SYMLINKS: Final[bool] = False


class ModelRegistryEntryStatus(StrEnum):
    """
    Zustand eines Registry-Eintrags.

    REGISTERED:
        Manifest wurde erfolgreich registriert.

    DISABLED:
        Manifest ist vorhanden, aber deklarativ deaktiviert.

    INVALID:
        Manifest konnte nicht validiert werden.

    DUPLICATE:
        Modell-ID wurde mehrfach gefunden.
    """

    REGISTERED = "registered"
    DISABLED = "disabled"
    INVALID = "invalid"
    DUPLICATE = "duplicate"


class ModelDiscoveryResultStatus(StrEnum):
    """
    Ergebnisstatus einer einzelnen Discovery-Datei.
    """

    REGISTERED = "registered"
    REPLACED = "replaced"
    SKIPPED = "skipped"
    FAILED = "failed"
    DUPLICATE = "duplicate"


@dataclass(frozen=True, slots=True)
class ModelRegistryEntry:
    """
    Vollständig validierter Registry-Eintrag.
    """

    loaded_manifest: LoadedModelManifest
    status: ModelRegistryEntryStatus
    registration_index: int
    registered_at_monotonic: float

    @property
    def manifest(self) -> ModelManifest:
        return self.loaded_manifest.manifest

    @property
    def model_id(self) -> str:
        return self.manifest.id

    @property
    def provider_type(self) -> str:
        return self.manifest.provider.type

    @property
    def manifest_path(self) -> Path:
        return self.loaded_manifest.manifest_path

    @property
    def enabled(self) -> bool:
        return self.manifest.is_enabled


@dataclass(frozen=True, slots=True)
class ModelDiscoveryResult:
    """
    Ergebnis der Verarbeitung einer Manifestdatei.
    """

    manifest_path: Path
    status: ModelDiscoveryResultStatus

    model_id: str | None = None
    provider_type: str | None = None

    message: str | None = None
    error_type: str | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ModelDiscoveryReport:
    """
    Zusammenfassung eines vollständigen Discovery-Durchlaufs.
    """

    base_directories: tuple[Path, ...]
    discovered_paths: tuple[Path, ...]
    results: tuple[ModelDiscoveryResult, ...]

    started_at_monotonic: float
    finished_at_monotonic: float

    @property
    def duration_seconds(self) -> float:
        return max(
            0.0,
            self.finished_at_monotonic
            - self.started_at_monotonic,
        )

    @property
    def registered_count(self) -> int:
        return sum(
            result.status
            in {
                ModelDiscoveryResultStatus.REGISTERED,
                ModelDiscoveryResultStatus.REPLACED,
            }
            for result in self.results
        )

    @property
    def failed_count(self) -> int:
        return sum(
            result.status
            == ModelDiscoveryResultStatus.FAILED
            for result in self.results
        )

    @property
    def duplicate_count(self) -> int:
        return sum(
            result.status
            == ModelDiscoveryResultStatus.DUPLICATE
            for result in self.results
        )

    @property
    def skipped_count(self) -> int:
        return sum(
            result.status
            == ModelDiscoveryResultStatus.SKIPPED
            for result in self.results
        )


@dataclass(frozen=True, slots=True)
class ModelRegistrySnapshot:
    """
    Sichere Diagnoseansicht eines Registry-Eintrags.
    """

    model_id: str
    display_name: str
    description: str | None

    provider_type: str
    schema_version: str

    enabled: bool
    status: str
    runtime: str

    capabilities: tuple[str, ...]
    tags: tuple[str, ...]

    manifest_path: Path
    registration_index: int
    registered_at_monotonic: float

    metadata: dict[str, Any] = field(default_factory=lambda: {})


class ModelRegistry:
    """
    Thread- beziehungsweise Task-sichere Registry für Modellmanifeste.

    Die Registry speichert nur validierte LoadedModelManifest-Objekte.
    Ungültige Dateien werden nicht als verwendbare Modelle registriert.

    Zusätzlich kann ein explizites Standardmodell (default model) gesetzt
    werden. Dieses wird von get_default() bevorzugt zurückgegeben, sofern
    es registriert und aktiviert ist. Ist kein explizites Standardmodell
    gesetzt oder nicht verfügbar, wird das erste aktivierte Modell als
    Fallback verwendet.
    """

    def __init__(
        self,
        base_dir: Path | None = None,
        *,
        base_directories: Sequence[str | Path] | None = None,
        recursive: bool = DEFAULT_DISCOVERY_RECURSIVE,
        follow_symlinks: bool = DEFAULT_FOLLOW_SYMLINKS,
        default_model_id: str | None = None,  # NEU: explizite Default-ID
    ) -> None:
        if base_directories is not None and base_dir is not None:
            raise ValueError(
                "base_dir und base_directories dürfen nicht gleichzeitig "
                "gesetzt werden.",
            )

        raw_directories: Sequence[str | Path]

        if base_directories is not None:
            raw_directories = base_directories
        elif base_dir is not None:
            raw_directories = (
                base_dir,
            )
        else:
            raw_directories = (
                DEFAULT_MODEL_DIRECTORY,
            )

        self._base_directories = tuple(
            Path(directory).expanduser().resolve()
            for directory in raw_directories
        )

        self._recursive = recursive
        self._follow_symlinks = follow_symlinks

        self._entries: dict[
            str,
            ModelRegistryEntry,
        ] = {}

        self._path_index: dict[
            Path,
            str,
        ] = {}

        self._registration_counter = 0
        self._lock = asyncio.Lock()

        self._last_discovery_report: (
            ModelDiscoveryReport | None
        ) = None

        # NEU: explizite Default-Modell-ID (kann None sein)
        self._default_model_id: str | None = None
        if default_model_id is not None:
            # Normalisierung und erste Validierung
            self._default_model_id = self._normalize_model_id(default_model_id)

    # ========================================================
    # Eigenschaften
    # ========================================================

    @property
    def base_directories(self) -> tuple[Path, ...]:
        return self._base_directories

    @property
    def count(self) -> int:
        return len(self._entries)

    @property
    def last_discovery_report(
        self,
    ) -> ModelDiscoveryReport | None:
        return self._last_discovery_report

    # ========================================================
    # Default-Modell (NEU)
    # ========================================================

    async def set_default_model_id(self, model_id: str | None) -> None:
        """
        Setzt oder entfernt die explizite Default-Modell-ID.

        Die ID wird normalisiert. Existiert das Modell nicht in der Registry,
        wird ein ModelNotRegisteredError ausgelöst (optional könnte man auch
        nur warnen, aber hier wird es als Fehler behandelt, weil der Aufrufer
        eine gültige ID erwarten kann).
        """
        if model_id is None:
            async with self._lock:
                self._default_model_id = None
            return

        normalized = self._normalize_model_id(model_id)
        async with self._lock:
            # Prüfen, ob das Modell registriert ist
            if normalized not in self._entries:
                raise ModelNotRegisteredError(normalized)
            self._default_model_id = normalized

    async def get_default_model_id(self) -> str | None:
        """
        Gibt die explizit gesetzte Default-Modell-ID zurück (oder None).
        """
        async with self._lock:
            return self._default_model_id

    async def get_default(self) -> ModelRegistryEntry | None:
        """
        Liefert den Registry-Eintrag des Standardmodells.

        Priorität:
        1. Explizit gesetzte Default-ID (falls vorhanden und registriert)
        2. Erstes aktiviertes Modell (enabled_only=True) als Fallback
        3. None, wenn kein aktiviertes Modell existiert.

        Diese Methode ist für den 503-Fehler bei model_id=null relevant.
        """
        async with self._lock:
            # 1. Explizites Default
            if self._default_model_id is not None:
                entry = self._entries.get(self._default_model_id)
                if entry is not None and entry.enabled:
                    return entry
                # Falls das explizite Default deaktiviert oder nicht existiert,
                # loggen wir das und fallen auf den ersten aktiven zurück.
                logger.warning(
                    "Explizites Default-Modell %s ist nicht aktiv oder nicht registriert",
                    self._default_model_id,
                )

            # 2. Fallback: erstes aktiviertes Modell
            for entry in self._entries.values():
                if entry.enabled:
                    return entry

            # 3. Kein aktiviertes Modell
            return None

    # ========================================================
    # Discovery
    # ========================================================

    async def discover(
        self,
        *,
        replace_existing: bool = True,
        clear_missing: bool = True,
        continue_on_error: bool = True,
    ) -> ModelDiscoveryReport:
        """
        Durchsucht die konfigurierten Basisverzeichnisse.

        replace_existing:
            Bereits registrierte Modell-IDs werden durch das neu gefundene
            Manifest ersetzt.

        clear_missing:
            Registry-Einträge, deren Manifestdatei nicht mehr vorhanden
            beziehungsweise nicht mehr entdeckt wurde, werden entfernt.

        continue_on_error:
            Fehler einzelner Dateien werden im Report gesammelt. Bei False
            wird der erste Fehler weitergereicht.
        """

        started_at = time.monotonic()

        discovered_paths = discover_model_manifest_paths(
            self._base_directories,
            recursive=self._recursive,
            follow_symlinks=self._follow_symlinks,
        )

        results: list[ModelDiscoveryResult] = []
        loaded_by_model_id: dict[
            str,
            list[LoadedModelManifest],
        ] = {}

        for manifest_path in discovered_paths:
            try:
                loaded_manifest = load_model_manifest(
                    manifest_path,
                    allowed_base_directories=(
                        self._base_directories
                    ),
                )

                loaded_by_model_id.setdefault(
                    loaded_manifest.model_id,
                    [],
                ).append(
                    loaded_manifest,
                )

            except Exception as exc:
                results.append(
                    self._create_error_result(
                        manifest_path=manifest_path,
                        error=exc,
                    ),
                )

                logger.warning(
                    "Model manifest validation failed",
                    extra={
                        "manifest_path": str(
                            manifest_path,
                        ),
                        "error_type": (
                            exc.__class__.__name__
                        ),
                        "error_code": getattr(
                            exc,
                            "code",
                            None,
                        ),
                    },
                    exc_info=exc,
                )

                if not continue_on_error:
                    raise

        valid_manifests: list[
            LoadedModelManifest
        ] = []

        for model_id, manifests in sorted(
            loaded_by_model_id.items(),
        ):
            if len(manifests) == 1:
                valid_manifests.append(
                    manifests[0],
                )
                continue

            duplicate_error = DuplicateModelManifestError(
                model_id,
                manifest_paths=[
                    str(item.manifest_path)
                    for item in manifests
                ],
            )

            for loaded_manifest in manifests:
                results.append(
                    ModelDiscoveryResult(
                        manifest_path=(
                            loaded_manifest.manifest_path
                        ),
                        model_id=model_id,
                        provider_type=(
                            loaded_manifest.manifest.provider.type
                        ),
                        status=(
                            ModelDiscoveryResultStatus.DUPLICATE
                        ),
                        message=str(duplicate_error),
                        error_type=(
                            duplicate_error.__class__.__name__
                        ),
                        error_code=str(
                            duplicate_error.code,
                        ),
                    ),
                )

            if not continue_on_error:
                raise duplicate_error

        discovered_valid_paths = {
            item.manifest_path
            for item in valid_manifests
        }

        if clear_missing:
            await self._remove_missing_paths(
                discovered_valid_paths,
            )

        for loaded_manifest in sorted(
            valid_manifests,
            key=lambda item: (
                item.manifest.presentation.sort_order,
                item.manifest.display_name.lower(),
                item.manifest.id,
            ),
        ):
            try:
                replaced = await self.register(
                    loaded_manifest,
                    replace=replace_existing,
                )

                results.append(
                    ModelDiscoveryResult(
                        manifest_path=(
                            loaded_manifest.manifest_path
                        ),
                        model_id=loaded_manifest.model_id,
                        provider_type=(
                            loaded_manifest.manifest.provider.type
                        ),
                        status=(
                            ModelDiscoveryResultStatus.REPLACED
                            if replaced
                            else ModelDiscoveryResultStatus.REGISTERED
                        ),
                    ),
                )

            except DuplicateModelRegistrationError as exc:
                results.append(
                    ModelDiscoveryResult(
                        manifest_path=(
                            loaded_manifest.manifest_path
                        ),
                        model_id=loaded_manifest.model_id,
                        provider_type=(
                            loaded_manifest.manifest.provider.type
                        ),
                        status=(
                            ModelDiscoveryResultStatus.SKIPPED
                        ),
                        message=str(exc),
                        error_type=(
                            exc.__class__.__name__
                        ),
                        error_code=str(exc.code),
                    ),
                )

                if not continue_on_error:
                    raise

            except Exception as exc:
                results.append(
                    self._create_error_result(
                        manifest_path=(
                            loaded_manifest.manifest_path
                        ),
                        error=exc,
                        model_id=loaded_manifest.model_id,
                        provider_type=(
                            loaded_manifest.manifest.provider.type
                        ),
                    ),
                )

                if not continue_on_error:
                    raise

        report = ModelDiscoveryReport(
            base_directories=self._base_directories,
            discovered_paths=discovered_paths,
            results=tuple(results),
            started_at_monotonic=started_at,
            finished_at_monotonic=time.monotonic(),
        )

        self._last_discovery_report = report

        return report

    # ========================================================
    # Registrierung
    # ========================================================

    async def register(
        self,
        loaded_manifest: LoadedModelManifest,
        *,
        replace: bool = False,
    ) -> bool:
        """
        Registriert ein validiertes Manifest.

        Rückgabe:

        - False: neue Registrierung
        - True: vorhandener Eintrag wurde ersetzt
        """

        model_id = self._normalize_model_id(
            loaded_manifest.model_id,
        )

        async with self._lock:
            existing = self._entries.get(
                model_id,
            )

            if existing is not None and not replace:
                raise DuplicateModelRegistrationError(
                    model_id,
                )

            self._registration_counter += 1

            entry = ModelRegistryEntry(
                loaded_manifest=loaded_manifest,
                status=(
                    ModelRegistryEntryStatus.REGISTERED
                    if loaded_manifest.manifest.is_enabled
                    else ModelRegistryEntryStatus.DISABLED
                ),
                registration_index=(
                    self._registration_counter
                ),
                registered_at_monotonic=(
                    time.monotonic()
                ),
            )

            if existing is not None:
                self._path_index.pop(
                    existing.manifest_path,
                    None,
                )

            self._entries[model_id] = entry
            self._path_index[
                loaded_manifest.manifest_path
            ] = model_id

            # NEU: Wenn das Default-Modell deaktiviert oder nicht existiert,
            # wird es nicht automatisch zurückgesetzt – der Aufrufer kann
            # über set_default_model_id() nachsteuern.
            # Wir geben nur eine Warnung, falls das Default nicht mehr aktiv ist.
            if (
                self._default_model_id is not None
                and self._default_model_id == model_id
                and not entry.enabled
            ):
                logger.warning(
                    "Default-Modell %s wurde als deaktiviert registriert",
                    model_id,
                )

            return existing is not None

    async def register_file(
        self,
        manifest_path: str | Path,
        *,
        replace: bool = False,
    ) -> ModelRegistryEntry:
        """
        Lädt und registriert eine einzelne model.json-Datei.
        """

        loaded_manifest = load_model_manifest(
            manifest_path,
            allowed_base_directories=(
                self._base_directories
            ),
        )

        await self.register(
            loaded_manifest,
            replace=replace,
        )

        return self.get_entry(
            loaded_manifest.model_id,
        )

    async def unregister(
        self,
        model_id: str,
    ) -> bool:
        """
        Entfernt ein Modell aus der Registry.
        """

        normalized = self._normalize_model_id(
            model_id,
        )

        async with self._lock:
            entry = self._entries.pop(
                normalized,
                None,
            )

            if entry is None:
                return False

            self._path_index.pop(
                entry.manifest_path,
                None,
            )

            # NEU: Wenn das Default-Modell entfernt wurde, setzen wir es zurück.
            if (
                self._default_model_id is not None
                and self._default_model_id == normalized
            ):
                self._default_model_id = None
                logger.info(
                    "Default-Modell %s wurde entfernt, Default zurückgesetzt",
                    normalized,
                )

            return True

    async def clear(self) -> None:
        """
        Leert die Registry vollständig.
        """

        async with self._lock:
            self._entries.clear()
            self._path_index.clear()
            # NEU: Auch Default zurücksetzen
            self._default_model_id = None

    async def _remove_missing_paths(
        self,
        discovered_paths: set[Path],
    ) -> None:
        async with self._lock:
            missing_model_ids = [
                model_id
                for model_id, entry in self._entries.items()
                if entry.manifest_path
                not in discovered_paths
            ]

            for model_id in missing_model_ids:
                entry = self._entries.pop(
                    model_id,
                )

                self._path_index.pop(
                    entry.manifest_path,
                    None,
                )

                # NEU: Wenn ein entferntes Modell das Default war, zurücksetzen
                if (
                    self._default_model_id is not None
                    and self._default_model_id == model_id
                ):
                    self._default_model_id = None
                    logger.info(
                        "Default-Modell %s wurde wegen fehlender Manifestdatei entfernt",
                        model_id,
                    )

    # ========================================================
    # Zugriff
    # ========================================================

    def has(
        self,
        model_id: str,
    ) -> bool:
        normalized = self._normalize_model_id(
            model_id,
        )

        return normalized in self._entries

    def get_entry(
        self,
        model_id: str,
    ) -> ModelRegistryEntry:
        normalized = self._normalize_model_id(
            model_id,
        )

        entry = self._entries.get(
            normalized,
        )

        if entry is None:
            raise ModelNotRegisteredError(
                normalized,
            )

        return entry

    # NEU: Alias für get_entry, um die geforderte get(model_id)-Schnittstelle zu erfüllen
    def get(self, model_id: str) -> ModelRegistryEntry:
        """
        Alias für get_entry – löst ein Modell anhand seiner ID auf.
        """
        return self.get_entry(model_id)

    def get_manifest(
        self,
        model_id: str,
    ) -> ModelManifest:
        return self.get_entry(
            model_id,
        ).manifest

    def get_loaded_manifest(
        self,
        model_id: str,
    ) -> LoadedModelManifest:
        return self.get_entry(
            model_id,
        ).loaded_manifest

    def get_by_path(
        self,
        manifest_path: str | Path,
    ) -> ModelRegistryEntry:
        path = Path(
            manifest_path,
        ).expanduser().resolve()

        model_id = self._path_index.get(
            path,
        )

        if model_id is None:
            raise ModelManifestNotFoundError(
                str(path),
            )

        return self.get_entry(
            model_id,
        )

    def list_entries(
        self,
        *,
        enabled_only: bool = False,
        provider_type: str | None = None,
        capability: str | None = None,
        tags: Iterable[str] | None = None,
    ) -> tuple[ModelRegistryEntry, ...]:
        """
        Liefert gefilterte Registry-Einträge.
        """

        normalized_provider_type = (
            provider_type.strip().lower()
            if provider_type is not None
            else None
        )

        normalized_capability = (
            capability.strip().lower()
            if capability is not None
            else None
        )

        required_tags = frozenset(
            str(tag).strip().lower()
            for tag in (tags or ())
            if str(tag).strip()
        )

        entries: list[ModelRegistryEntry] = []

        for entry in self._entries.values():
            manifest = entry.manifest

            if enabled_only and not manifest.is_enabled:
                continue

            if (
                normalized_provider_type is not None
                and entry.provider_type
                != normalized_provider_type
            ):
                continue

            if (
                normalized_capability is not None
                and not manifest.supports(
                    normalized_capability,
                )
            ):
                continue

            if (
                required_tags
                and not required_tags.issubset(
                    manifest.tags,
                )
            ):
                continue

            entries.append(entry)

        return tuple(
            sorted(
                entries,
                key=lambda item: (
                    item.manifest.presentation.sort_order,
                    item.manifest.display_name.lower(),
                    item.model_id,
                ),
            ),
        )

    def list_model_ids(
        self,
        *,
        enabled_only: bool = False,
    ) -> tuple[str, ...]:
        return tuple(
            entry.model_id
            for entry in self.list_entries(
                enabled_only=enabled_only,
            )
        )

    def list_snapshots(
        self,
        *,
        enabled_only: bool = False,
    ) -> tuple[ModelRegistrySnapshot, ...]:
        return tuple(
            self._create_snapshot(entry)
            for entry in self.list_entries(
                enabled_only=enabled_only,
            )
        )

    def get_snapshot(
        self,
        model_id: str,
    ) -> ModelRegistrySnapshot:
        return self._create_snapshot(
            self.get_entry(model_id),
        )

    # ========================================================
    # Kompatible API
    # ========================================================

    def list_models(
        self,
        *,
        enabled_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Kompatible Ausgabe für bestehende Aufrufer.

        Anders als die frühere Implementierung werden ausschließlich
        validierte und sichere Daten ausgegeben.
        """

        return [
            self._snapshot_to_dict(snapshot)
            for snapshot in self.list_snapshots(
                enabled_only=enabled_only,
            )
        ]

    # ========================================================
    # Diagnose
    # ========================================================

    @staticmethod
    def _create_snapshot(
        entry: ModelRegistryEntry,
    ) -> ModelRegistrySnapshot:
        manifest = entry.manifest

        # Explizite Typisierung, um Pylance-Warnung zu vermeiden
        metadata: dict[str, Any] = {
            "registry_status": entry.status.value,
            "presentation": (
                manifest.presentation.model_dump(
                    mode="json",
                    exclude_none=True,
                )
            ),
            "limits": (
                manifest.limits.model_dump(
                    mode="json",
                    exclude_none=True,
                )
            ),
            "manifest_metadata": dict(
                manifest.metadata,
            ),
        }

        return ModelRegistrySnapshot(
            model_id=manifest.id,
            display_name=manifest.display_name,
            description=manifest.description,
            provider_type=manifest.provider.type,
            schema_version=manifest.schema_version,
            enabled=manifest.is_enabled,
            status=manifest.status.value,
            runtime=manifest.runtime.value,
            capabilities=tuple(
                sorted(manifest.capabilities),
            ),
            tags=tuple(
                sorted(manifest.tags),
            ),
            manifest_path=entry.manifest_path,
            registration_index=(
                entry.registration_index
            ),
            registered_at_monotonic=(
                entry.registered_at_monotonic
            ),
            metadata=metadata,
        )

    @staticmethod
    def _snapshot_to_dict(
        snapshot: ModelRegistrySnapshot,
    ) -> dict[str, Any]:
        """
        Wandelt einen Snapshot in ein API-freundliches Mapping um.

        provider wird zusätzlich als Zeichenkette ausgegeben, damit ältere
        Aufrufer mit dem früheren Vertrag weiterarbeiten können.
        """

        return {
            "id": snapshot.model_id,
            "name": snapshot.display_name,
            "display_name": snapshot.display_name,
            "description": snapshot.description,
            "provider": snapshot.provider_type,
            "provider_type": snapshot.provider_type,
            "schema_version": snapshot.schema_version,
            "available": snapshot.enabled,
            "enabled": snapshot.enabled,
            "status": snapshot.status,
            "runtime": snapshot.runtime,
            "capabilities": {
                capability: True
                for capability in snapshot.capabilities
            },
            "capability_list": list(
                snapshot.capabilities,
            ),
            "tags": list(snapshot.tags),
            "manifest_path": str(
                snapshot.manifest_path,
            ),
            "metadata": dict(
                snapshot.metadata,
            ),
        }

    @staticmethod
    def _create_error_result(
        *,
        manifest_path: Path,
        error: BaseException,
        model_id: str | None = None,
        provider_type: str | None = None,
    ) -> ModelDiscoveryResult:
        resolved_model_id = (
            model_id
            or getattr(
                error,
                "model_id",
                None,
            )
        )

        resolved_provider_type = (
            provider_type
            or getattr(
                error,
                "provider_type",
                None,
            )
        )

        error_code = getattr(
            error,
            "code",
            None,
        )

        return ModelDiscoveryResult(
            manifest_path=manifest_path,
            model_id=resolved_model_id,
            provider_type=resolved_provider_type,
            status=ModelDiscoveryResultStatus.FAILED,
            message=str(error),
            error_type=error.__class__.__name__,
            error_code=(
                str(error_code)
                if error_code is not None
                else None
            ),
        )

    # ========================================================
    # Validierung
    # ========================================================

    @staticmethod
    def _normalize_model_id(
        model_id: str,
    ) -> str:
        # Der Parameter ist bereits als str typisiert – wir prüfen nur auf Leerheit.
        normalized = model_id.strip().lower()

        if not normalized:
            raise ValueError(
                "model_id darf nicht leer sein.",
            )

        return normalized


__all__ = [
    "DEFAULT_MODEL_DIRECTORY",
    "ModelDiscoveryReport",
    "ModelDiscoveryResult",
    "ModelDiscoveryResultStatus",
    "ModelRegistry",
    "ModelRegistryEntry",
    "ModelRegistryEntryStatus",
    "ModelRegistrySnapshot",
]