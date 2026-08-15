from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from app.contracts.hierarchy import HierarchyNodeCreate
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.hierarchy.models import HierarchyActor
from app.hierarchy.repository import HierarchyRepository


class ConfigReader(Protocol):
    def get(self, group: str, key: str, default: Any = None) -> Any: ...


DEFAULT_HIERARCHY_QUOTAS: dict[str, dict[str, int]] = {
    "guest": {"workspace": 1, "project": 2, "chat": 5},
    "internal": {"workspace": 5, "project": 10, "chat": 25},
}


class HierarchyQuotaExceededError(RuntimeError):
    code = "HIERARCHY_QUOTA_EXCEEDED"

    def __init__(self, *, node_type: str, limit: int, used: int) -> None:
        labels = {
            "workspace": "Bereiche",
            "project": "Projekte",
            "chat": "Chats",
        }
        label = labels.get(node_type, node_type)
        super().__init__(f"Das Limit für {label} ist erreicht ({used}/{limit}).")
        self.details: dict[str, object] = {
            "node_type": node_type,
            "limit": limit,
            "used": used,
        }


class HierarchyQuotaService:
    def __init__(
        self,
        repository: HierarchyRepository,
        config_service: ConfigReader | None = None,
    ) -> None:
        self._repository = repository
        self._config = config_service

    async def prepare_create(
        self,
        data: HierarchyNodeCreate,
        *,
        actor: HierarchyActor,
        parent: HierarchyNodeModel | None,
    ) -> HierarchyNodeCreate:
        access_level = self._access_level(actor)
        if actor.is_admin or access_level is None:
            return data

        if actor.user_id is None or parent is None:
            raise PermissionError(
                "Eigene Hierarchieknoten benötigen einen Benutzerkontext."
            )

        node_type = data.type.strip().lower()
        if node_type not in DEFAULT_HIERARCHY_QUOTAS[access_level]:
            raise PermissionError(
                "Benutzer dürfen nur Bereiche, Projekte und Chats erstellen."
            )

        owned_nodes = await self._owned_nodes(actor.user_id)
        owned_ids = {node.id for node in owned_nodes}
        if parent.id not in owned_ids:
            raise PermissionError(
                "Neue Hierarchieknoten dürfen nur im eigenen Bereich erstellt werden."
            )

        usage = self._usage(owned_nodes)
        limit = await self._limit(access_level, node_type, actor.user_id)
        if limit is not None and usage[node_type] >= limit:
            raise HierarchyQuotaExceededError(
                node_type=node_type,
                limit=limit,
                used=usage[node_type],
            )

        metadata = dict(data.metadata)
        metadata.pop("assigned_user_ids", None)
        metadata["owner_user_id"] = actor.user_id
        metadata["visibility"] = "private"
        return data.model_copy(update={"metadata": metadata})

    async def status(self, actor: HierarchyActor) -> dict[str, object]:
        access_level = self._access_level(actor)
        if actor.is_admin:
            return {
                "access_level": "admin",
                "limits": None,
                "usage": None,
                "remaining": None,
            }
        if access_level is None or actor.user_id is None:
            raise PermissionError(
                "Für Hierarchie-Quoten ist eine Anmeldung erforderlich."
            )

        usage = self._usage(await self._owned_nodes(actor.user_id))
        limits = {
            node_type: await self._limit(access_level, node_type, actor.user_id)
            for node_type in DEFAULT_HIERARCHY_QUOTAS[access_level]
        }
        return {
            "access_level": access_level,
            "limits": limits,
            "usage": usage,
            "remaining": {
                node_type: (
                    None
                    if limits[node_type] is None
                    else max(limits[node_type] - usage[node_type], 0)
                )
                for node_type in limits
            },
        }

    async def _owned_nodes(self, user_id: str) -> list[HierarchyNodeModel]:
        nodes: Sequence[HierarchyNodeModel] = await self._repository.list_nodes()
        owned_ids = {f"user-{user_id}"}
        pending = list(nodes)
        changed = True
        while changed:
            changed = False
            for node in pending:
                metadata = dict(node.node_metadata or {})
                belongs_to_user = (
                    metadata.get("owner_user_id") == user_id
                    or node.parent_id in owned_ids
                )
                if belongs_to_user and node.id not in owned_ids:
                    owned_ids.add(node.id)
                    changed = True
        return [node for node in nodes if node.id in owned_ids]

    @staticmethod
    def _usage(nodes: Sequence[HierarchyNodeModel]) -> dict[str, int]:
        usage = {"workspace": 0, "project": 0, "chat": 0}
        for node in nodes:
            node_type = node.type.strip().lower()
            if node_type in usage:
                usage[node_type] += 1
        return usage

    async def _limit(
        self,
        access_level: str,
        node_type: str,
        user_id: str,
    ) -> int | None:
        load_overrides = getattr(self._repository, "get_user_quota_overrides", None)
        if load_overrides is not None:
            overrides = await load_overrides(user_id)
            if overrides is not None:
                override = overrides.get(node_type)
                if override == -1:
                    return None
                if override is not None:
                    return max(int(override), 0)

        default = DEFAULT_HIERARCHY_QUOTAS[access_level][node_type]
        if self._config is None:
            return default
        value = self._config.get(
            "security",
            f"{access_level}_{node_type}_limit",
            default,
        )
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _access_level(actor: HierarchyActor) -> str | None:
        roles = {role.strip().casefold() for role in actor.roles}
        if roles.intersection({"internal", "intern", "user"}):
            return "internal"
        if "guest" in roles:
            return "guest"
        return None