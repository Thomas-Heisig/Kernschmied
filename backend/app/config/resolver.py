# F:\Kernschmied\backend\app\config\resolver.py

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Final, Protocol, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import JsonValue          # NEU: Pydantic's JsonValue

from app.config.definitions import (
    ConfigDefinition,
    ConfigScope,
)


# Keine eigene rekursive JsonValue-Definition mehr – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


_UNSET: Final[object] = object()


class JsonSchemaValidatorProtocol(Protocol):
    """
    Minimaler, vollständig typisierter Vertrag für einen JSON-Schema-Validator.

    Das Protocol verhindert, dass sich unvollständige Typinformationen aus
    dem jsonschema-Paket in die Anwendung ausbreiten.
    """

    def validate(
        self,
        instance: object,
    ) -> None:
        ...


class ConfigResolverError(Exception):
    """
    Basisklasse für fachliche Fehler bei der Konfigurationsauflösung.
    """


class ConfigDefinitionNotFoundError(ConfigResolverError):
    def __init__(
        self,
        *,
        key: str,
    ) -> None:
        self.key = key

        super().__init__(
            f"Für den Konfigurationsschlüssel '{key}' "
            "existiert keine Definition.",
        )


class ConfigScopeNotAllowedError(ConfigResolverError):
    def __init__(
        self,
        *,
        key: str,
        scope: ConfigScope,
    ) -> None:
        self.key = key
        self.scope = scope

        super().__init__(
            f"Der Scope '{scope.value}' ist für die Konfiguration "
            f"'{key}' nicht erlaubt.",
        )


class ConfigMergeError(ConfigResolverError):
    def __init__(
        self,
        *,
        key: str,
        strategy: str,
        base_type: str,
        override_type: str,
        scope: ConfigScope | None = None,
    ) -> None:
        self.key = key
        self.strategy = strategy
        self.base_type = base_type
        self.override_type = override_type
        self.scope = scope

        scope_message = (
            f" im Scope '{scope.value}'"
            if scope is not None
            else ""
        )

        super().__init__(
            f"Die Merge-Strategie '{strategy}' kann für '{key}'"
            f"{scope_message} nicht auf '{base_type}' und "
            f"'{override_type}' angewendet werden.",
        )


class ConfigResolvedValueValidationError(ConfigResolverError):
    def __init__(
        self,
        *,
        key: str,
        reason: str,
        path: tuple[str | int, ...] = (),
    ) -> None:
        self.key = key
        self.reason = reason
        self.path = path

        path_text = (
            ".".join(
                str(part)
                for part in path
            )
            if path
            else "<root>"
        )

        super().__init__(
            f"Der aufgelöste Wert für '{key}' ist ungültig "
            f"an '{path_text}': {reason}",
        )


class ConfigScopeOrderError(ConfigResolverError):
    """
    Fehlerhafte oder unvollständige Scope-Prioritätsreihenfolge.
    """


class ConfigValueTypeError(ConfigResolverError):
    def __init__(
        self,
        *,
        value_type: str,
        path: tuple[str | int, ...] = (),
    ) -> None:
        self.value_type = value_type
        self.path = path

        path_text = (
            ".".join(
                str(part)
                for part in path
            )
            if path
            else "<root>"
        )

        super().__init__(
            "Konfigurationswerte müssen JSON-kompatibel sein. "
            f"Nicht unterstützter Typ '{value_type}' an '{path_text}'.",
        )


@dataclass(frozen=True, slots=True)
class ResolvedConfigValue:
    """
    Ergebnis einer Konfigurationsauflösung mit Herkunftsinformationen.
    """

    key: str
    value: JsonValue
    applied_scopes: tuple[ConfigScope, ...]
    merge_strategy: str


def _as_object_mapping(
    value: object,
) -> Mapping[object, object] | None:
    """
    Wandelt ein unbekannt typisiertes Mapping in ein Mapping mit expliziten
    object-Typparametern um.
    """

    if not isinstance(
        value,
        Mapping,
    ):
        return None

    return cast(
        Mapping[object, object],
        value,
    )


def _as_object_sequence(
    value: object,
) -> Sequence[object] | None:
    """
    Liefert Sequenzen mit explizitem Elementtyp.

    Strings und Bytefolgen werden bewusst nicht als Konfigurationslisten
    behandelt.
    """

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


def normalize_json_value(
    value: object,
    *,
    path: tuple[str | int, ...] = (),
    depth: int = 0,
    max_depth: int = 64,
) -> JsonValue:
    """
    Normalisiert einen beliebigen Eingangswert in einen JSON-kompatiblen Wert.

    Dadurch gelangen keine untypisierten Mapping- oder Listenwerte in die
    Merge-Logik.
    """

    if depth > max_depth:
        raise ConfigValueTypeError(
            value_type="maximum_depth_exceeded",
            path=path,
        )

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        str | int | float,
    ):
        return value

    mapping = _as_object_mapping(
        value,
    )

    if mapping is not None:
        normalized_mapping: JsonObject = {}

        for raw_key, raw_value in mapping.items():
            if not isinstance(
                raw_key,
                str,
            ):
                raise ConfigValueTypeError(
                    value_type=type(raw_key).__name__,
                    path=path,
                )

            normalized_mapping[raw_key] = normalize_json_value(
                raw_value,
                path=(*path, raw_key),
                depth=depth + 1,
                max_depth=max_depth,
            )

        return normalized_mapping

    sequence = _as_object_sequence(
        value,
    )

    if sequence is not None:
        normalized_sequence: list[JsonValue] = []

        for index, item in enumerate(sequence):
            normalized_sequence.append(
                normalize_json_value(
                    item,
                    path=(*path, index),
                    depth=depth + 1,
                    max_depth=max_depth,
                )
            )

        return normalized_sequence

    raise ConfigValueTypeError(
        value_type=type(value).__name__,
        path=path,
    )


def clone_json_value(
    value: JsonValue,
) -> JsonValue:
    """
    Erstellt eine tiefe Kopie eines bereits normalisierten JSON-Werts.
    """

    return deepcopy(
        value,
    )


def _as_json_object(
    value: JsonValue,
) -> JsonObject | None:
    if not isinstance(
        value,
        dict,
    ):
        return None

    return value


def _as_json_list(
    value: JsonValue,
) -> list[JsonValue] | None:
    if not isinstance(
        value,
        list,
    ):
        return None

    return value


def _normalize_merge_strategy(
    strategy: object,
) -> str:
    """
    Normalisiert sowohl String- als auch Enum-basierte Merge-Strategien.
    """

    if isinstance(
        strategy,
        Enum,
    ):
        raw_value = strategy.value

        if isinstance(
            raw_value,
            str,
        ):
            return raw_value.strip()

    if isinstance(
        strategy,
        str,
    ):
        return strategy.strip()

    return str(
        strategy,
    ).strip()


def _normalize_validation_path(
    path: Iterable[object],
) -> tuple[str | int, ...]:
    normalized: list[str | int] = []

    for part in path:
        if isinstance(
            part,
            int,
        ):
            normalized.append(
                part,
            )
        else:
            normalized.append(
                str(part),
            )

    return tuple(
        normalized,
    )


def deep_merge(
    base: Mapping[str, JsonValue],
    override: Mapping[str, JsonValue],
) -> JsonObject:
    """
    Führt zwei verschachtelte Mappings rekursiv zusammen.
    Regeln:
    - Mapping + Mapping wird rekursiv zusammengeführt.
    - Alle anderen Werte werden vollständig ersetzt.
    - Eingabewerte werden nicht verändert.
    - Rückgabewerte werden tief kopiert.
    """
    result: JsonObject = {
        key: clone_json_value(value)
        for key, value in base.items()
    }

    for key, override_value in override.items():
        if key not in result:
            result[key] = clone_json_value(
                override_value,
            )
            continue

        existing_value: JsonValue = result[key]
        existing_mapping = _as_json_object(
            existing_value,
        )
        override_mapping = _as_json_object(
            override_value,
        )

        if (
            existing_mapping is not None
            and override_mapping is not None
        ):
            result[key] = deep_merge(
                existing_mapping,
                override_mapping,
            )
            continue

        result[key] = clone_json_value(
            override_value,
        )

    return result


def normalize_definition_key(
    group: str,
    key: str,
) -> str:
    normalized_group = group.strip()
    normalized_key = key.strip()

    if not normalized_group:
        raise ValueError(
            "Die Konfigurationsgruppe darf nicht leer sein.",
        )

    if not normalized_key:
        raise ValueError(
            "Der Konfigurationsschlüssel darf nicht leer sein.",
        )

    return f"{normalized_group}.{normalized_key}"


class ConfigResolver:
    """
    Löst Konfigurationswerte anhand definierter Scope-Prioritäten auf.

    Der Resolver besitzt keinen Datenbankzugriff. Er arbeitet ausschließlich
    auf validierten Definitionen und den ihm übergebenen Scope-Werten.

    Die Reihenfolge in `scope_order` verläuft von niedriger zu höherer
    Priorität. Spätere Scopes überschreiben oder erweitern frühere Werte.
    """

    SUPPORTED_MERGE_STRATEGIES: Final[frozenset[str]] = frozenset(
        {
            "replace",
            "extend",
            "deep_merge",
        },
    )

    def __init__(
        self,
        definitions: Iterable[ConfigDefinition],
        *,
        scope_order: Sequence[ConfigScope] | None = None,
    ) -> None:
        definition_map: dict[str, ConfigDefinition] = {}

        for definition in definitions:
            definition_key = normalize_definition_key(
                definition.group,
                definition.key,
            )

            if definition_key in definition_map:
                raise ValueError(
                    "Doppelte Konfigurationsdefinition für "
                    f"'{definition_key}'.",
                )

            merge_strategy = _normalize_merge_strategy(
                definition.merge_strategy,
            )

            if (
                merge_strategy
                not in self.SUPPORTED_MERGE_STRATEGIES
            ):
                raise ValueError(
                    "Unbekannte Merge-Strategie "
                    f"'{merge_strategy}' für '{definition_key}'.",
                )

            definition_map[definition_key] = definition

        self._definitions = definition_map

        configured_scope_order = (
            tuple(
                scope_order,
            )
            if scope_order is not None
            else tuple(
                ConfigScope,
            )
        )

        self._scope_order = self._normalize_scope_order(
            configured_scope_order,
        )

    @property
    def scope_order(self) -> tuple[ConfigScope, ...]:
        return self._scope_order

    def has_definition(
        self,
        key: str,
    ) -> bool:
        return key.strip() in self._definitions

    def get_definition(
        self,
        key: str,
    ) -> ConfigDefinition:
        normalized_key = key.strip()

        definition = self._definitions.get(
            normalized_key,
        )

        if definition is None:
            raise ConfigDefinitionNotFoundError(
                key=normalized_key,
            )

        return definition

    def list_definition_keys(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                self._definitions,
            )
        )

    def resolve(
        self,
        key: str,
        values: Mapping[ConfigScope, object],
        *,
        validate_result: bool = True,
    ) -> JsonValue:
        """
        Löst einen einzelnen Konfigurationswert auf.

        `values` enthält ausschließlich Werte, die tatsächlich gesetzt
        wurden. Dadurch kann `None` selbst ein gültiger Override-Wert sein.
        """

        return self.resolve_with_metadata(
            key,
            values,
            validate_result=validate_result,
        ).value

    def resolve_with_metadata(
        self,
        key: str,
        values: Mapping[ConfigScope, object],
        *,
        validate_result: bool = True,
    ) -> ResolvedConfigValue:
        normalized_key = key.strip()

        definition = self.get_definition(
            normalized_key,
        )

        self._validate_provided_scopes(
            key=normalized_key,
            definition=definition,
            values=values,
        )

        result = normalize_json_value(
            definition.default_value,
        )

        applied_scopes: list[ConfigScope] = []

        for scope in self._scope_order:
            if scope not in values:
                continue

            override_value = normalize_json_value(
                values[scope],
            )

            result = self._merge(
                key=normalized_key,
                base=result,
                override=override_value,
                strategy=_normalize_merge_strategy(
                    definition.merge_strategy,
                ),
                scope=scope,
            )

            applied_scopes.append(
                scope,
            )

        if validate_result:
            self._validate_resolved_value(
                key=normalized_key,
                value=result,
                definition=definition,
            )

        return ResolvedConfigValue(
            key=normalized_key,
            value=clone_json_value(
                result,
            ),
            applied_scopes=tuple(
                applied_scopes,
            ),
            merge_strategy=_normalize_merge_strategy(
                definition.merge_strategy,
            ),
        )

    def resolve_by_parts(
        self,
        *,
        group: str,
        key: str,
        values: Mapping[ConfigScope, object],
        validate_result: bool = True,
    ) -> JsonValue:
        definition_key = normalize_definition_key(
            group,
            key,
        )

        return self.resolve(
            definition_key,
            values,
            validate_result=validate_result,
        )

    def resolve_many(
        self,
        values_by_key: Mapping[
            str,
            Mapping[ConfigScope, object],
        ],
        *,
        include_defaults: bool = False,
        validate_result: bool = True,
    ) -> dict[str, JsonValue]:
        """
        Löst mehrere Konfigurationswerte auf.

        `include_defaults=True` ergänzt auch Definitionen, für die keine
        Scope-Werte übergeben wurden.
        """

        if include_defaults:
            keys: set[str] = set(
                self._definitions,
            )

            keys.update(
                values_by_key,
            )
        else:
            keys = set(
                values_by_key,
            )

        result: dict[str, JsonValue] = {}

        for key in sorted(
            keys,
        ):
            empty_scope_values: dict[ConfigScope, object] = {}

            scope_values = values_by_key.get(
                key,
            )

            if scope_values is None:
                scope_values = empty_scope_values

            result[key] = self.resolve(
                key,
                scope_values,
                validate_result=validate_result,
            )

        return result

    def resolve_group(
        self,
        group: str,
        values_by_key: Mapping[
            str,
            Mapping[ConfigScope, object],
        ],
        *,
        include_defaults: bool = True,
        validate_result: bool = True,
    ) -> dict[str, JsonValue]:
        """
        Löst alle Konfigurationen einer Gruppe auf.

        `values_by_key` verwendet nur den kurzen Schlüssel ohne Gruppe.
        """

        normalized_group = group.strip()

        if not normalized_group:
            raise ValueError(
                "Die Konfigurationsgruppe darf nicht leer sein.",
            )

        group_prefix = f"{normalized_group}."

        definition_keys: set[str] = {
            definition_key
            for definition_key in self._definitions
            if definition_key.startswith(
                group_prefix,
            )
        }

        provided_definition_keys: set[str] = {
            normalize_definition_key(
                normalized_group,
                short_key,
            )
            for short_key in values_by_key
        }

        if include_defaults:
            keys = (
                definition_keys
                | provided_definition_keys
            )
        else:
            keys = provided_definition_keys

        resolved: dict[str, JsonValue] = {}

        for definition_key in sorted(
            keys,
        ):
            short_key = definition_key.removeprefix(
                group_prefix,
            )

            empty_scope_values: dict[ConfigScope, object] = {}

            scope_values: Mapping[ConfigScope, object] = (
                values_by_key.get(
                    short_key,
                    empty_scope_values,
                )
            )

            resolved[short_key] = self.resolve(
                definition_key,
                scope_values,
                validate_result=validate_result,
            )

        return resolved

    def _validate_provided_scopes(
        self,
        *,
        key: str,
        definition: ConfigDefinition,
        values: Mapping[ConfigScope, object],
    ) -> None:
        for scope in values:
            if scope not in definition.allowed_scopes:
                raise ConfigScopeNotAllowedError(
                    key=key,
                    scope=scope,
                )

    @classmethod
    def _merge(
        cls,
        *,
        key: str,
        base: JsonValue,
        override: JsonValue,
        strategy: str,
        scope: ConfigScope | None = None,
    ) -> JsonValue:
        normalized_strategy = strategy.strip()

        if normalized_strategy == "replace":
            return clone_json_value(
                override,
            )

        if normalized_strategy == "extend":
            base_list = _as_json_list(
                base,
            )

            override_list = _as_json_list(
                override,
            )

            if (
                base_list is not None
                and override_list is not None
            ):
                merged_values: list[JsonValue] = [
                    clone_json_value(
                        item,
                    )
                    for item in base_list
                ]

                merged_values.extend(
                    clone_json_value(
                        item,
                    )
                    for item in override_list
                )

                return merged_values

            raise ConfigMergeError(
                key=key,
                strategy=normalized_strategy,
                base_type=type(base).__name__,
                override_type=type(override).__name__,
                scope=scope,
            )

        if normalized_strategy == "deep_merge":
            base_mapping = _as_json_object(
                base,
            )

            override_mapping = _as_json_object(
                override,
            )

            if (
                base_mapping is not None
                and override_mapping is not None
            ):
                return deep_merge(
                    base_mapping,
                    override_mapping,
                )

            raise ConfigMergeError(
                key=key,
                strategy=normalized_strategy,
                base_type=type(base).__name__,
                override_type=type(override).__name__,
                scope=scope,
            )

        raise ConfigMergeError(
            key=key,
            strategy=normalized_strategy,
            base_type=type(base).__name__,
            override_type=type(override).__name__,
            scope=scope,
        )

    @staticmethod
    def _validate_resolved_value(
        *,
        key: str,
        value: JsonValue,
        definition: ConfigDefinition,
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
            raw_path: Iterable[object] = cast(
                Iterable[object],
                exc.absolute_path,
            )

            raise ConfigResolvedValueValidationError(
                key=key,
                reason=exc.message,
                path=_normalize_validation_path(
                    raw_path,
                ),
            ) from exc

    @staticmethod
    def _normalize_scope_order(
        scopes: Sequence[ConfigScope],
    ) -> tuple[ConfigScope, ...]:
        normalized: list[ConfigScope] = []

        for scope in scopes:
            if scope in normalized:
                raise ConfigScopeOrderError(
                    f"Der Scope '{scope.value}' ist in der "
                    "Prioritätsreihenfolge doppelt enthalten.",
                )

            normalized.append(
                scope,
            )

        missing_scopes: list[ConfigScope] = [
            scope
            for scope in ConfigScope
            if scope not in normalized
        ]

        if missing_scopes:
            missing_names = ", ".join(
                scope.value
                for scope in missing_scopes
            )

            raise ConfigScopeOrderError(
                "Die Scope-Reihenfolge ist unvollständig. "
                f"Fehlend: {missing_names}.",
            )

        return tuple(
            normalized,
        )