# F:\Kernschmied\backend\app\services\hierarchy\models.py

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import JsonValue


# Keine eigene rekursive JsonValue-Definition – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


def empty_string_set() -> frozenset[str]:
    return frozenset()


def empty_tool_policy() -> dict[str, bool]:
    return {}


def empty_json_object() -> JsonObject:
    return {}


@dataclass(slots=True)
class HierarchyActor:
    user_id: str | None = None

    roles: frozenset[str] = field(
        default_factory=empty_string_set,
    )

    permissions: frozenset[str] = field(
        default_factory=empty_string_set,
    )

    @property
    def is_admin(self) -> bool:
        return (
            "admin" in self.roles
            or "hierarchy.admin" in self.permissions
        )


@dataclass(slots=True)
class EffectiveHierarchyValues:
    prompt: str | None = None

    tools: dict[str, bool] = field(
        default_factory=empty_tool_policy,
    )

    config: JsonObject = field(
        default_factory=empty_json_object,
    )