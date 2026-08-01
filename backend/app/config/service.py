# F:\Kernschmied\backend\app\config\service.py

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Protocol, cast
from uuid import uuid4

from jsonschema import Draft202012Validator
from jsonschema import ValidationError as JsonSchemaValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.definitions import (
    CONFIG_DEFINITIONS,
    ConfigDefinition,
    ConfigMergeStrategy,
    ConfigScope,
    ConfigVisibility,
)
from app.storage.models.config import ConfigState, SystemConfig

logger = logging.getLogger(__name__)


class JsonSchemaValidatorProtocol(Protocol):
    def validate(
        self,
        instance: object,
    ) -> None: ...


class ModelRegistryEntry(Protocol):
    model_id: str
    provider_type: str | None
    enabled: bool
    manifest: Any | None


class ModelRegistry(Protocol):
    def list_entries(self) -> Awaitable[Sequence[ModelRegistryEntry]]: ...


CONFIG_STATE_ID = 1
SECRET_MASK = "********"


class ConfigServiceError(Exception):
    """
    Basisklasse für fachliche Fehler des ConfigService.
    """


class ConfigValidationError(ConfigServiceError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
    ) -> None:
        self.code = code
        self.message = message

        super().__init__(message)


# Alias auf Modulebene, damit andere Module den Fehler direkt importieren können
ConfigValidationError = ConfigValidationError


class ConfigDefinitionNotFoundError(ConfigServiceError):
    def __init__(
        self,
        *,
        group: str,
        key: str,
    ) -> None:
        self.group = group
        self.key = key

        super().__init__(
            f"Keine Konfigurationsdefinition für '{group}.{key}' vorhanden.",
        )


class ConfigEntryNotFoundError(ConfigServiceError):
    def __init__(
        self,
        *,
        group: str,
        key: str,
    ) -> None:
        self.group = group
        self.key = key

        super().__init__(
            f"Der Konfigurationseintrag '{group}.{key}' wurde nicht gefunden.",
        )


class ConfigValueValidationError(ConfigServiceError):
    def __init__(
        self,
        *,
        group: str,
        key: str,
        reason: str,
        path: tuple[str | int, ...] = (),
    ) -> None:
        self.group = group
        self.key = key
        self.reason = reason
        self.path = path

        location = ".".join(str(part) for part in path) if path else "<root>"

        super().__init__(
            f"Ungültiger Wert für '{group}.{key}' an '{location}': {reason}",
        )


class ConfigNotRuntimeEditableError(ConfigServiceError):
    def __init__(
        self,
        *,
        group: str,
        key: str,
        requires_restart: bool,
    ) -> None:
        self.group = group
        self.key = key
        self.requires_restart = requires_restart

        suffix = " Die Änderung erfordert einen Neustart." if requires_restart else ""

        super().__init__(
            f"Die Konfiguration '{group}.{key}' ist nicht "
            f"zur Laufzeit änderbar.{suffix}",
        )


class ConfigRevisionConflictError(ConfigServiceError):
    def __init__(
        self,
        *,
        expected_revision: int,
        actual_revision: int,
    ) -> None:
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision

        super().__init__(
            "Die Konfiguration wurde zwischenzeitlich geändert. "
            f"Erwartete Revision: {expected_revision}, "
            f"aktuelle Revision: {actual_revision}.",
        )


class ConfigPersistenceError(ConfigServiceError):
    def __init__(
        self,
        *,
        operation: str,
        reason: str,
    ) -> None:
        self.operation = operation
        self.reason = reason

        super().__init__(
            f"Die Konfiguration konnte nicht gespeichert werden: {reason}",
        )


class ConfigSecretAccessError(ConfigServiceError):
    def __init__(
        self,
        *,
        group: str,
        key: str,
    ) -> None:
        self.group = group
        self.key = key

        super().__init__(
            f"Der Secret-Wert '{group}.{key}' darf nicht unmaskiert ausgegeben werden.",
        )


@dataclass(frozen=True, slots=True)
class ConfigUpdateResult:
    """
    Ergebnis einer Konfigurationsänderung.
    """

    group: str
    key: str

    revision: int

    changed: bool
    requires_restart: bool
    runtime_editable: bool

    previous_value: Any
    current_value: Any


@dataclass(frozen=True, slots=True)
class ConfigEntry:
    """
    Vollständige Config-Darstellung für Services und API-Endpunkte.
    """

    group: str
    key: str

    value: Any

    schema_version: str
    revision: int

    is_secret: bool
    requires_restart: bool
    runtime_editable: bool

    display_name: str
    description: str

    allowed_scopes: tuple[str, ...]
    merge_strategy: str

    deprecated: bool


class ConfigService:
    """
    Verwaltet validierte, versionierte Systemkonfiguration.

    Der Service stellt einen synchron lesbaren Cache bereit und kapselt
    sämtliche persistenten Änderungen.

    Eigenschaften:

    - validierte Definitionen als feste Registry
    - atomarer Cache-Austausch
    - globale Config-Revision
    - optimistische Konflikterkennung
    - prozesslokale Schreibsperre für SQLite
    - PostgreSQL-kompatible Row Locks
    - sichere Secret-Maskierung
    - keine externen Zugriffe auf `_cache`
    - keine automatische Freigabe unbekannter Definitionen
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        definitions: Sequence[ConfigDefinition] = CONFIG_DEFINITIONS,
        model_registry: ModelRegistry | None = None,
    ) -> None:
        self.session_factory = session_factory

        self._definitions = self._build_definition_registry(
            definitions,
        )

        # Optional model registry used for provider/model validation
        self._model_registry: ModelRegistry | None = model_registry

        self._cache: dict[tuple[str, str], Any] = {}

        self.revision: int = 0

        self._write_lock = asyncio.Lock()
        self._reload_lock = asyncio.Lock()

    @property
    def definitions(
        self,
    ) -> tuple[ConfigDefinition, ...]:
        return tuple(
            sorted(
                self._definitions.values(),
                key=lambda definition: (
                    definition.group,
                    definition.key,
                ),
            ),
        )

    @property
    def definition_count(self) -> int:
        return len(self._definitions)

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    async def seed_defaults(self) -> None:
        """
        Legt den Revisionsdatensatz und fehlende Config-Einträge an.

        Vorhandene Werte werden nicht überschrieben. Metadaten vorhandener
        Datensätze werden jedoch mit den aktuellen Definitionen
        synchronisiert.
        """

        async with self._write_lock, self.session_factory() as session:
            try:
                state = await session.get(
                    ConfigState,
                    CONFIG_STATE_ID,
                )

                if state is None:
                    state = ConfigState(
                        id=CONFIG_STATE_ID,
                        revision=1,
                    )
                    session.add(state)

                registry_changed = False

                for definition in self.definitions:
                    row = await self._get_config_row(
                        session=session,
                        group=definition.group,
                        key=definition.key,
                    )

                    if row is None:
                        session.add(
                            self._create_system_config(
                                definition,
                            ),
                        )

                        registry_changed = True
                        continue

                    metadata_changed = self._synchronize_row_metadata(
                        row=row,
                        definition=definition,
                    )

                    if metadata_changed:
                        registry_changed = True

                if registry_changed:
                    state.revision = (
                        max(
                            int(state.revision),
                            0,
                        )
                        + 1
                    )

                await session.commit()

            except IntegrityError as exc:
                await session.rollback()

                logger.exception(
                    "Configuration default seeding caused an integrity error",
                )

                raise ConfigPersistenceError(
                    operation="seed_defaults",
                    reason=(
                        "Ein Konfigurationseintrag ist bereits "
                        "vorhanden oder verletzt eine "
                        "Datenbankbedingung."
                    ),
                ) from exc

            except SQLAlchemyError as exc:
                await session.rollback()

                logger.exception(
                    "Configuration default seeding failed",
                )

                raise ConfigPersistenceError(
                    operation="seed_defaults",
                    reason=str(exc),
                ) from exc

        await self.reload()

    async def reload(self) -> None:
        """
        Lädt Werte und Revision vollständig neu.

        Der vorhandene Cache wird erst ersetzt, nachdem alle Daten
        erfolgreich gelesen und validiert wurden.
        """

        async with self._reload_lock:
            async with self.session_factory() as session:
                try:
                    rows = (
                        (
                            await session.execute(
                                select(SystemConfig),
                            )
                        )
                        .scalars()
                        .all()
                    )

                    state = await session.get(
                        ConfigState,
                        CONFIG_STATE_ID,
                    )

                except SQLAlchemyError as exc:
                    logger.exception(
                        "Configuration reload failed",
                    )

                    raise ConfigPersistenceError(
                        operation="reload",
                        reason=str(exc),
                    ) from exc

            new_cache: dict[tuple[str, str], Any] = {}

            for row in rows:
                cache_key = self._normalize_key(
                    row.config_group,
                    row.config_key,
                )

                definition = self._definitions.get(
                    cache_key,
                )

                if definition is None:
                    logger.warning(
                        "Ignoring unknown configuration row",
                        extra={
                            "config_group": row.config_group,
                            "config_key": row.config_key,
                        },
                    )
                    continue

                self._validate_value(
                    definition=definition,
                    value=row.value,
                )

                new_cache[cache_key] = deepcopy(
                    row.value,
                )

            for cache_key, definition in self._definitions.items():
                if cache_key not in new_cache:
                    logger.warning(
                        "Configuration entry missing; using default in local cache",
                        extra={
                            "config_group": definition.group,
                            "config_key": definition.key,
                        },
                    )

                    new_cache[cache_key] = deepcopy(
                        definition.default_value,
                    )

            new_revision = int(state.revision) if state is not None else 0

            self._cache = new_cache
            self.revision = max(
                new_revision,
                0,
            )

    def get(
        self,
        group: str,
        key: str,
        default: Any = None,
        *,
        reveal_secret: bool = False,
    ) -> Any:
        """
        Liest einen Wert aus dem lokalen Cache.

        Secret-Werte werden ohne ausdrückliche Freigabe maskiert. Für
        interne Services, die tatsächlich einen Secret-Wert benötigen,
        steht `get_secret()` zur Verfügung.
        """

        normalized_key = self._normalize_key(
            group,
            key,
        )

        definition = self._definitions.get(
            normalized_key,
        )

        if definition is None:
            return deepcopy(default)

        if normalized_key not in self._cache:
            return deepcopy(default)

        value = self._cache[normalized_key]

        if definition.is_secret and not reveal_secret:
            return self._mask_secret(value)

        return deepcopy(value)

    def get_required(
        self,
        group: str,
        key: str,
        *,
        reveal_secret: bool = False,
    ) -> Any:
        normalized_key = self._normalize_key(
            group,
            key,
        )

        definition = self.get_definition(
            group,
            key,
        )

        if normalized_key not in self._cache:
            raise ConfigEntryNotFoundError(
                group=definition.group,
                key=definition.key,
            )

        value = self._cache[normalized_key]

        if definition.is_secret and not reveal_secret:
            return self._mask_secret(value)

        return deepcopy(value)

    def get_secret(
        self,
        group: str,
        key: str,
    ) -> Any:
        """
        Liefert einen Secret-Wert für vertrauenswürdige interne Services.

        API-Endpunkte dürfen diese Methode nur nach einer ausdrücklichen
        Berechtigungsprüfung verwenden.
        """

        definition = self.get_definition(
            group,
            key,
        )

        if not definition.is_secret:
            raise ConfigSecretAccessError(
                group=definition.group,
                key=definition.key,
            )

        return self.get_required(
            definition.group,
            definition.key,
            reveal_secret=True,
        )

    def get_all(
        self,
        *,
        include_secrets: bool = False,
        reveal_secrets: bool = False,
        include_internal: bool = False,
        include_deprecated: bool = False,
    ) -> dict[str, dict[str, Any]]:
        """
        Liefert Konfigurationen gruppiert nach Config-Gruppe.

        Standardmäßig werden Secret-Definitionen vollständig ausgelassen.
        Mit `include_secrets=True` werden sie maskiert ausgegeben.
        Tatsächliche Secret-Werte erfordern zusätzlich
        `reveal_secrets=True`.
        """

        result: dict[str, dict[str, Any]] = {}

        for definition in self.list_definitions(
            include_internal=include_internal,
            include_deprecated=include_deprecated,
        ):
            cache_key = (
                definition.group,
                definition.key,
            )

            if cache_key not in self._cache:
                continue

            if definition.is_secret and not include_secrets:
                continue

            value = self._cache[cache_key]

            if definition.is_secret and not reveal_secrets:
                value = self._mask_secret(value)

            result.setdefault(
                definition.group,
                {},
            )[definition.key] = deepcopy(value)

        return result

    def get_entries(
        self,
        *,
        group: str | None = None,
        scope: ConfigScope | None = None,
        include_secrets: bool = False,
        reveal_secrets: bool = False,
        include_internal: bool = False,
        include_deprecated: bool = False,
    ) -> tuple[ConfigEntry, ...]:
        """
        Liefert Werte zusammen mit ihren Definitionsmetadaten.

        Diese Methode ist für Admin- und Schema-Endpunkte besser geeignet
        als ein Zugriff auf interne Service-Strukturen.
        """

        entries: list[ConfigEntry] = []

        for definition in self.list_definitions(
            group=group,
            scope=scope,
            include_internal=include_internal,
            include_deprecated=include_deprecated,
        ):
            cache_key = (
                definition.group,
                definition.key,
            )

            if cache_key not in self._cache:
                continue

            if definition.is_secret and not include_secrets:
                continue

            value = self._cache[cache_key]

            if definition.is_secret and not reveal_secrets:
                value = self._mask_secret(value)

            entries.append(
                ConfigEntry(
                    group=definition.group,
                    key=definition.key,
                    value=deepcopy(value),
                    schema_version=definition.schema_version,
                    revision=self.revision,
                    is_secret=definition.is_secret,
                    requires_restart=definition.requires_restart,
                    runtime_editable=definition.runtime_editable,
                    display_name=definition.display_name,
                    description=definition.description,
                    allowed_scopes=tuple(
                        scope_item.value
                        for scope_item in sorted(
                            definition.allowed_scopes,
                            key=lambda item: item.value,
                        )
                    ),
                    merge_strategy=self._merge_strategy_value(
                        definition.merge_strategy,
                    ),
                    deprecated=definition.deprecated,
                ),
            )

        return tuple(entries)

    def get_definition(
        self,
        group: str,
        key: str,
    ) -> ConfigDefinition:
        normalized_key = self._normalize_key(
            group,
            key,
        )

        definition = self._definitions.get(
            normalized_key,
        )

        if definition is None:
            raise ConfigDefinitionNotFoundError(
                group=normalized_key[0],
                key=normalized_key[1],
            )

        return definition

    def list_definitions(
        self,
        *,
        group: str | None = None,
        scope: ConfigScope | None = None,
        include_internal: bool = False,
        include_deprecated: bool = False,
    ) -> tuple[ConfigDefinition, ...]:
        normalized_group = group.strip().lower() if group is not None else None

        result: list[ConfigDefinition] = []

        for definition in self._definitions.values():
            if normalized_group is not None and definition.group != normalized_group:
                continue

            if scope is not None and scope not in definition.allowed_scopes:
                continue

            if (
                not include_internal
                and definition.visibility == ConfigVisibility.INTERNAL
            ):
                continue

            if not include_deprecated and definition.deprecated:
                continue

            result.append(definition)

        return tuple(
            sorted(
                result,
                key=lambda item: (
                    item.ui.category or "",
                    item.ui.section or "",
                    item.ui.order,
                    item.group,
                    item.key,
                ),
            ),
        )

    def has_definition(
        self,
        group: str,
        key: str,
    ) -> bool:
        return (
            self._normalize_key(
                group,
                key,
            )
            in self._definitions
        )

    def has_value(
        self,
        group: str,
        key: str,
    ) -> bool:
        return (
            self._normalize_key(
                group,
                key,
            )
            in self._cache
        )

    async def set(
        self,
        group: str,
        key: str,
        value: Any,
        *,
        changed_by: str = "system",
        expected_revision: int | None = None,
        allow_restart_required: bool = False,
    ) -> ConfigUpdateResult:
        """
        Persistiert einen einzelnen Konfigurationswert.

        `allow_restart_required=True` erlaubt das Speichern einer nicht
        laufzeitänderbaren Einstellung. Die Änderung wird dadurch aber
        nicht automatisch zur Laufzeit wirksam.
        """

        normalized_group, normalized_key = self._normalize_key(
            group,
            key,
        )

        definition = self.get_definition(
            normalized_group,
            normalized_key,
        )

        self._assert_update_allowed(
            definition=definition,
            allow_restart_required=allow_restart_required,
        )

        self._validate_value(
            definition=definition,
            value=value,
        )

        # Special validation for provider/model coherence
        try:
            if definition.group == "models" and definition.key in {
                "default_model",
                "default_provider",
            }:
                # Determine effective model_id and provider_id for validation
                if definition.key == "default_model":
                    model_id = value if isinstance(value, str) else None

                    # provider from current store
                    provider_value = self.get(
                        "models",
                        "default_provider",
                    )
                    provider_id = (
                        provider_value if isinstance(provider_value, str) else None
                    )

                else:  # setting provider
                    provider_id = value if isinstance(value, str) else None

                    current_model = self.get(
                        "models",
                        "default_model",
                    )

                    model_id = current_model if isinstance(current_model, str) else None

                await self._validate_default_model(
                    model_id=model_id,
                    provider_id=provider_id,
                )
        except ConfigValidationError:
            raise

        actor = self._normalize_actor(
            changed_by,
        )

        async with self._write_lock, self.session_factory() as session:
            try:
                state = await self._get_or_create_state(
                    session,
                    for_update=True,
                )

                actual_revision = max(
                    int(state.revision),
                    0,
                )

                self._assert_revision(
                    expected_revision=expected_revision,
                    actual_revision=actual_revision,
                )

                row = await self._get_config_row(
                    session=session,
                    group=normalized_group,
                    key=normalized_key,
                    for_update=True,
                )

                if row is None:
                    raise ConfigEntryNotFoundError(
                        group=normalized_group,
                        key=normalized_key,
                    )

                previous_value = deepcopy(
                    row.value,
                )

                changed = previous_value != value

                if not changed:
                    await session.rollback()

                    return ConfigUpdateResult(
                        group=normalized_group,
                        key=normalized_key,
                        revision=actual_revision,
                        changed=False,
                        requires_restart=(definition.requires_restart),
                        runtime_editable=(definition.runtime_editable),
                        previous_value=self._safe_result_value(
                            definition,
                            previous_value,
                        ),
                        current_value=self._safe_result_value(
                            definition,
                            value,
                        ),
                    )

                row.value = deepcopy(value)
                row.updated_by = actor

                self._synchronize_row_metadata(
                    row=row,
                    definition=definition,
                )

                state.revision = actual_revision + 1
                new_revision = int(state.revision)

                await session.commit()

            except (
                ConfigEntryNotFoundError,
                ConfigRevisionConflictError,
            ):
                await session.rollback()
                raise

            except IntegrityError as exc:
                await session.rollback()

                logger.exception(
                    "Configuration update caused an integrity error",
                    extra={
                        "config_group": normalized_group,
                        "config_key": normalized_key,
                    },
                )

                raise ConfigPersistenceError(
                    operation="set",
                    reason=("Die Änderung verletzt eine Datenbankbedingung."),
                ) from exc

            except SQLAlchemyError as exc:
                await session.rollback()

                logger.exception(
                    "Configuration update failed",
                    extra={
                        "config_group": normalized_group,
                        "config_key": normalized_key,
                    },
                )

                raise ConfigPersistenceError(
                    operation="set",
                    reason=str(exc),
                ) from exc

        await self.reload()

        logger.info(
            "Configuration updated",
            extra={
                "config_group": normalized_group,
                "config_key": normalized_key,
                "changed_by": actor,
                "revision": new_revision,
                "requires_restart": definition.requires_restart,
                "is_secret": definition.is_secret,
            },
        )

        return ConfigUpdateResult(
            group=normalized_group,
            key=normalized_key,
            revision=new_revision,
            changed=True,
            requires_restart=definition.requires_restart,
            runtime_editable=definition.runtime_editable,
            previous_value=self._safe_result_value(
                definition,
                previous_value,
            ),
            current_value=self._safe_result_value(
                definition,
                value,
            ),
        )

    async def set_many(
        self,
        updates: Mapping[
            tuple[str, str],
            Any,
        ],
        *,
        changed_by: str = "system",
        expected_revision: int | None = None,
        allow_restart_required: bool = False,
    ) -> tuple[ConfigUpdateResult, ...]:
        """
        Speichert mehrere Config-Werte in einer Transaktion.

        Die globale Revision wird bei mindestens einer tatsächlichen
        Änderung genau einmal erhöht.
        """

        if not updates:
            return ()

        prepared_updates: list[
            tuple[
                ConfigDefinition,
                Any,
            ]
        ] = []

        for (
            raw_group,
            raw_key,
        ), value in updates.items():
            definition = self.get_definition(
                raw_group,
                raw_key,
            )

            self._assert_update_allowed(
                definition=definition,
                allow_restart_required=allow_restart_required,
            )

            self._validate_value(
                definition=definition,
                value=value,
            )

            prepared_updates.append(
                (
                    definition,
                    deepcopy(value),
                ),
            )

        # Pre-validation: provider/model coherence for models.default_model/provider
        try:
            # helper to extract value from updates mapping
            def lookup(group: str, key: str) -> Any:
                return updates.get((group, key))

            # If default_model is being changed, validate using updated or current provider
            if ("models", "default_model") in updates:
                raw_model = lookup("models", "default_model")

                model_id = raw_model if isinstance(raw_model, str) else None

                if ("models", "default_provider") in updates:
                    raw_provider = lookup("models", "default_provider")
                    provider_id = (
                        raw_provider if isinstance(raw_provider, str) else None
                    )
                else:
                    provider_value = self.get("models", "default_provider")
                    provider_id = (
                        provider_value if isinstance(provider_value, str) else None
                    )

                await self._validate_default_model(
                    model_id=model_id,
                    provider_id=provider_id,
                )

            # If provider changes alone, ensure existing model remains valid
            if ("models", "default_provider") in updates and (
                "models",
                "default_model",
            ) not in updates:
                raw_provider = lookup("models", "default_provider")
                new_provider_id = (
                    raw_provider if isinstance(raw_provider, str) else None
                )

                current_model_value = self.get("models", "default_model")
                current_model_id = (
                    current_model_value
                    if isinstance(current_model_value, str)
                    else None
                )

                await self._validate_default_model(
                    model_id=current_model_id,
                    provider_id=new_provider_id,
                )
        except ConfigValidationError:
            raise

        actor = self._normalize_actor(
            changed_by,
        )

        async with self._write_lock, self.session_factory() as session:
            try:
                state = await self._get_or_create_state(
                    session,
                    for_update=True,
                )

                actual_revision = max(
                    int(state.revision),
                    0,
                )

                self._assert_revision(
                    expected_revision=expected_revision,
                    actual_revision=actual_revision,
                )

                pending_results: list[
                    tuple[
                        ConfigDefinition,
                        Any,
                        Any,
                        bool,
                    ]
                ] = []

                any_changed = False

                for definition, value in prepared_updates:
                    row = await self._get_config_row(
                        session=session,
                        group=definition.group,
                        key=definition.key,
                        for_update=True,
                    )

                    if row is None:
                        raise ConfigEntryNotFoundError(
                            group=definition.group,
                            key=definition.key,
                        )

                    previous_value = deepcopy(
                        row.value,
                    )

                    changed = previous_value != value

                    if changed:
                        any_changed = True

                        row.value = deepcopy(value)
                        row.updated_by = actor

                        self._synchronize_row_metadata(
                            row=row,
                            definition=definition,
                        )

                    pending_results.append(
                        (
                            definition,
                            previous_value,
                            value,
                            changed,
                        ),
                    )

                if any_changed:
                    state.revision = actual_revision + 1
                    new_revision = int(state.revision)

                    await session.commit()
                else:
                    new_revision = actual_revision
                    await session.rollback()

            except (
                ConfigEntryNotFoundError,
                ConfigRevisionConflictError,
            ):
                await session.rollback()
                raise

            except IntegrityError as exc:
                await session.rollback()

                logger.exception(
                    "Bulk configuration update caused an integrity error",
                )

                raise ConfigPersistenceError(
                    operation="set_many",
                    reason=(
                        "Mindestens eine Änderung verletzt eine Datenbankbedingung."
                    ),
                ) from exc

            except SQLAlchemyError as exc:
                await session.rollback()

                logger.exception(
                    "Bulk configuration update failed",
                )

                raise ConfigPersistenceError(
                    operation="set_many",
                    reason=str(exc),
                ) from exc

        if any_changed:
            await self.reload()

        return tuple(
            ConfigUpdateResult(
                group=definition.group,
                key=definition.key,
                revision=new_revision,
                changed=changed,
                requires_restart=definition.requires_restart,
                runtime_editable=definition.runtime_editable,
                previous_value=self._safe_result_value(
                    definition,
                    previous_value,
                ),
                current_value=self._safe_result_value(
                    definition,
                    current_value,
                ),
            )
            for (
                definition,
                previous_value,
                current_value,
                changed,
            ) in pending_results
        )

    async def reset_to_default(
        self,
        group: str,
        key: str,
        *,
        changed_by: str = "system",
        expected_revision: int | None = None,
        allow_restart_required: bool = False,
    ) -> ConfigUpdateResult:
        definition = self.get_definition(
            group,
            key,
        )

        return await self.set(
            group=definition.group,
            key=definition.key,
            value=deepcopy(
                definition.default_value,
            ),
            changed_by=changed_by,
            expected_revision=expected_revision,
            allow_restart_required=allow_restart_required,
        )

    async def refresh_if_stale(
        self,
    ) -> bool:
        """
        Prüft die globale Datenbankrevision.

        Rückgabewert:

        - `True`: Cache wurde neu geladen
        - `False`: Cache war bereits aktuell
        """

        async with self.session_factory() as session:
            try:
                state = await session.get(
                    ConfigState,
                    CONFIG_STATE_ID,
                )
            except SQLAlchemyError as exc:
                raise ConfigPersistenceError(
                    operation="refresh_if_stale",
                    reason=str(exc),
                ) from exc

        database_revision = (
            max(
                int(state.revision),
                0,
            )
            if state is not None
            else 0
        )

        if database_revision == self.revision:
            return False

        await self.reload()

        return True

    def is_runtime_editable(
        self,
        group: str,
        key: str,
    ) -> bool:
        return self.get_definition(
            group,
            key,
        ).runtime_editable

    def requires_restart(
        self,
        group: str,
        key: str,
    ) -> bool:
        return self.get_definition(
            group,
            key,
        ).requires_restart

    def is_secret(
        self,
        group: str,
        key: str,
    ) -> bool:
        return self.get_definition(
            group,
            key,
        ).is_secret

    def validate_value(
        self,
        group: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Öffentliche Validierung ohne persistente Änderung.
        """

        definition = self.get_definition(
            group,
            key,
        )

        self._validate_value(
            definition=definition,
            value=value,
        )

    async def _get_or_create_state(
        self,
        session: AsyncSession,
        *,
        for_update: bool,
    ) -> ConfigState:
        if for_update:
            query = (
                select(ConfigState)
                .where(
                    ConfigState.id == CONFIG_STATE_ID,
                )
                .with_for_update()
            )

            state = (await session.execute(query)).scalar_one_or_none()
        else:
            state = await session.get(
                ConfigState,
                CONFIG_STATE_ID,
            )

        if state is not None:
            return state

        state = ConfigState(
            id=CONFIG_STATE_ID,
            revision=1,
        )

        session.add(state)
        await session.flush()

        return state

    async def _validate_default_model(
        self,
        *,
        model_id: str | None,
        provider_id: str | None,
    ) -> None:
        """
        Prüft, ob das gewählte Modell existiert, verfügbar ist,
        Chat unterstützt und zum gewählten Provider gehört.
        """

        if model_id is None:
            return

        if provider_id is None:
            raise ConfigValidationError(
                code="PROVIDER_MISSING",
                message=(
                    "Es wurde kein Provider ausgewählt, aber ein Modell angegeben."
                ),
            )

        if self._model_registry is None:
            raise ConfigValidationError(
                code="MODEL_REGISTRY_UNAVAILABLE",
                message=(
                    "Die Modellregistrierung ist nicht verfügbar; Validierung nicht möglich."
                ),
            )

        # list entries and normalize
        try:
            entries = await self._model_registry.list_entries()
        except Exception as exc:
            raise ConfigValidationError(
                code="MODEL_REGISTRY_UNAVAILABLE",
                message=("Die Modellregistrierung konnte nicht gelesen werden."),
            ) from exc

        selected: ModelRegistryEntry | None = None

        for entry in entries:
            if entry.model_id == model_id:
                selected = entry
                break

        if selected is None:
            raise ConfigValidationError(
                code="MODEL_NOT_REGISTERED",
                message=(f"Das Modell '{model_id}' ist nicht registriert."),
            )

        entry_provider = selected.provider_type

        if (
            entry_provider is None
            or entry_provider.casefold() != provider_id.casefold()
        ):
            raise ConfigValidationError(
                code="MODEL_PROVIDER_MISMATCH",
                message=(
                    f"Das Modell '{model_id}' gehört zum Provider '{entry_provider}' und nicht zu '{provider_id}'."
                ),
            )

        enabled = selected.enabled
        # Determine runtime availability/selectability from manifest when present.
        manifest = selected.manifest

        selectable = True
        available = True

        if manifest is not None:
            selectable = getattr(manifest, "selectable", True)
            # prefer explicit 'available' attribute, fall back to 'is_enabled'
            available = getattr(manifest, "available", getattr(manifest, "is_enabled", True))

        if not enabled or not available or not selectable:
            raise ConfigValidationError(
                code="MODEL_NOT_SELECTABLE",
                message=(f"Das Modell '{model_id}' ist derzeit nicht auswählbar."),
            )

        # capabilities: manifest may expose supports() or capabilities attribute
        supports_chat = False

        if manifest is not None:
            try:
                supports_chat = bool(manifest.supports("chat"))
            except Exception:
                supports_chat = bool(
                    getattr(manifest, "capabilities", {}).get("chat", False)
                    if getattr(manifest, "capabilities", None) is not None
                    else False
                )

        if not supports_chat:
            raise ConfigValidationError(
                code="MODEL_NO_CHAT_CAPABILITY",
                message=(f"Das Modell '{model_id}' unterstützt keine Chat-Funktion."),
            )

    async def _get_config_row(
        self,
        *,
        session: AsyncSession,
        group: str,
        key: str,
        for_update: bool = False,
    ) -> SystemConfig | None:
        query = select(SystemConfig).where(
            SystemConfig.config_group == group,
            SystemConfig.config_key == key,
        )

        if for_update:
            query = query.with_for_update()

        return (await session.execute(query)).scalar_one_or_none()

    @staticmethod
    def _create_system_config(
        definition: ConfigDefinition,
    ) -> SystemConfig:
        return SystemConfig(
            id=str(uuid4()),
            config_group=definition.group,
            config_key=definition.key,
            value=deepcopy(
                definition.default_value,
            ),
            is_secret=definition.is_secret,
            requires_restart=definition.requires_restart,
            runtime_editable=definition.runtime_editable,
            description=definition.description,
        )

    @staticmethod
    def _synchronize_row_metadata(
        *,
        row: SystemConfig,
        definition: ConfigDefinition,
    ) -> bool:
        changed = False

        metadata_values: dict[str, object] = {
            "is_secret": definition.is_secret,
            "requires_restart": definition.requires_restart,
            "runtime_editable": definition.runtime_editable,
            "description": definition.description,
        }

        for attribute_name, expected_value in metadata_values.items():
            current_value: object = getattr(
                row,
                attribute_name,
                None,
            )

            if current_value == expected_value:
                continue

            setattr(
                row,
                attribute_name,
                expected_value,
            )

            changed = True

        return changed

    @staticmethod
    def _validate_value(
        *,
        definition: ConfigDefinition,
        value: object,
    ) -> None:
        raw_validator: object = Draft202012Validator(
            definition.value_schema,
        )

        validator = cast(
            JsonSchemaValidatorProtocol,
            raw_validator,
        )

        try:
            validator.validate(
                value,
            )

        except JsonSchemaValidationError as exc:
            normalized_path: list[str | int] = []

            raw_path = cast(
                Iterable[object],
                exc.absolute_path,
            )

            for path_part in raw_path:
                if isinstance(
                    path_part,
                    int,
                ):
                    normalized_path.append(
                        path_part,
                    )
                else:
                    normalized_path.append(
                        str(path_part),
                    )

            raise ConfigValueValidationError(
                group=definition.group,
                key=definition.key,
                reason=exc.message,
                path=tuple(
                    normalized_path,
                ),
            ) from exc

    @staticmethod
    def _assert_update_allowed(
        *,
        definition: ConfigDefinition,
        allow_restart_required: bool,
    ) -> None:
        if definition.runtime_editable:
            return

        if allow_restart_required:
            return

        raise ConfigNotRuntimeEditableError(
            group=definition.group,
            key=definition.key,
            requires_restart=definition.requires_restart,
        )

    @staticmethod
    def _assert_revision(
        *,
        expected_revision: int | None,
        actual_revision: int,
    ) -> None:
        if expected_revision is None:
            return

        if expected_revision < 0:
            raise ValueError(
                "expected_revision darf nicht negativ sein.",
            )

        if expected_revision == actual_revision:
            return

        raise ConfigRevisionConflictError(
            expected_revision=expected_revision,
            actual_revision=actual_revision,
        )

    @staticmethod
    def _normalize_key(
        group: str,
        key: str,
    ) -> tuple[str, str]:
        normalized_group = group.strip().lower()
        normalized_key = key.strip().lower()

        if not normalized_group:
            raise ValueError(
                "Die Konfigurationsgruppe darf nicht leer sein.",
            )

        if not normalized_key:
            raise ValueError(
                "Der Konfigurationsschlüssel darf nicht leer sein.",
            )

        return (
            normalized_group,
            normalized_key,
        )

    @staticmethod
    def _normalize_actor(
        changed_by: str,
    ) -> str:
        actor = changed_by.strip()

        if not actor:
            return "system"

        return actor[:255]

    @classmethod
    def _build_definition_registry(
        cls,
        definitions: Sequence[ConfigDefinition],
    ) -> dict[
        tuple[str, str],
        ConfigDefinition,
    ]:
        registry: dict[
            tuple[str, str],
            ConfigDefinition,
        ] = {}

        for definition in definitions:
            registry_key = cls._normalize_key(
                definition.group,
                definition.key,
            )

            if registry_key in registry:
                raise ValueError(
                    "Doppelte Konfigurationsdefinition für "
                    f"'{registry_key[0]}.{registry_key[1]}'.",
                )

            registry[registry_key] = definition

        return registry

    @staticmethod
    def _merge_strategy_value(
        strategy: ConfigMergeStrategy | str,
    ) -> str:
        if isinstance(
            strategy,
            ConfigMergeStrategy,
        ):
            return strategy.value

        return strategy

    @staticmethod
    def _mask_secret(
        value: object,
    ) -> object:
        if value is None:
            return None

        if isinstance(
            value,
            str,
        ):
            return SECRET_MASK if value else ""

        if isinstance(
            value,
            Mapping,
        ):
            typed_mapping = cast(
                Mapping[object, object],
                value,
            )

            masked_mapping: dict[str, str] = {}

            for raw_key in typed_mapping:
                key = str(
                    raw_key,
                )

                masked_mapping[key] = SECRET_MASK

            return masked_mapping

        if isinstance(
            value,
            list,
        ):
            typed_list = cast(
                list[object],
                value,
            )

            masked_list: list[str] = []

            for _item in typed_list:
                masked_list.append(
                    SECRET_MASK,
                )

            return masked_list

        return SECRET_MASK

    @classmethod
    def _safe_result_value(
        cls,
        definition: ConfigDefinition,
        value: object,
    ) -> object:
        if definition.is_secret:
            return cls._mask_secret(
                value,
            )

        return deepcopy(
            value,
        )
