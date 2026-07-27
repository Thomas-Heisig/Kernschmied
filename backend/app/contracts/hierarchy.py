# F:\Kernschmied\backend\app\schemas\hierarchy.py

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, JsonValue          # NEU: Pydantic's JsonValue


# Keine eigene rekursive JsonValue-Definition mehr – importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


StringList = Annotated[
    list[str],
    Field(default_factory=list),
]

ToolPolicy = Annotated[
    dict[str, bool],
    Field(default_factory=dict),
]

JsonObjectField = Annotated[
    JsonObject,
    Field(default_factory=dict),
]


class HierarchyNodeCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    type: str = Field(
        min_length=1,
        max_length=100,
    )

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    parent_id: str | None = None

    system_prompt: str | None = None

    tool_policy: ToolPolicy

    config_overrides: JsonObjectField

    metadata: JsonObjectField


class HierarchyNodeUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    system_prompt: str | None = None

    tool_policy: dict[str, bool] | None = None

    config_overrides: JsonObject | None = None

    metadata: JsonObject | None = None


class HierarchyNode(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: str

    type: str

    name: str

    parent_id: str | None = None

    system_prompt: str | None = None

    tool_policy: ToolPolicy

    config_overrides: JsonObjectField

    metadata: JsonObjectField

    effective_prompt: str | None = None

    effective_tools: ToolPolicy

    effective_config: JsonObjectField

    available_actions: StringList

    children: Annotated[
        list["HierarchyNode"],
        Field(default_factory=list),
    ]


class HierarchyTree(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    config_revision: int = Field(
        default=0,
        ge=0,
    )

    roots: Annotated[
        list[HierarchyNode],
        Field(default_factory=list),
    ]


HierarchyNode.model_rebuild()
HierarchyTree.model_rebuild()