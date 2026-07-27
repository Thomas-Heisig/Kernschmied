from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.hierarchy import HierarchyNodeCreate, HierarchyNodeUpdate
from app.database.models.hierarchy_node import HierarchyNodeModel


class HierarchyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_nodes(
        self,
        *,
        include_inactive: bool = False,
    ) -> Sequence[HierarchyNodeModel]:
        statement = select(HierarchyNodeModel)

        if not include_inactive:
            statement = statement.where(
                HierarchyNodeModel.is_active.is_(True),
            )

        statement = statement.order_by(
            HierarchyNodeModel.parent_id,
            HierarchyNodeModel.position,
            HierarchyNodeModel.name,
        )

        result = await self._session.scalars(statement)
        return result.all()

    async def get_node(self, node_id: str) -> HierarchyNodeModel | None:
        return await self._session.get(HierarchyNodeModel, node_id)

    async def list_children(
        self,
        parent_id: str | None,
    ) -> Sequence[HierarchyNodeModel]:
        statement = (
            select(HierarchyNodeModel)
            .where(
                HierarchyNodeModel.parent_id == parent_id,
                HierarchyNodeModel.is_active.is_(True),
            )
            .order_by(
                HierarchyNodeModel.position,
                HierarchyNodeModel.name,
            )
        )

        result = await self._session.scalars(statement)
        return result.all()

    async def create_node(
        self,
        data: HierarchyNodeCreate,
    ) -> HierarchyNodeModel:
        position = await self._next_position(data.parent_id)

        node = HierarchyNodeModel(
            parent_id=data.parent_id,
            type=data.type.strip().lower(),
            name=data.name.strip(),
            position=position,
            system_prompt=data.system_prompt,
            tool_policy=dict(data.tool_policy),
            config_overrides=dict(data.config_overrides),
            node_metadata=dict(data.metadata),
        )

        self._session.add(node)
        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def update_node(
        self,
        node: HierarchyNodeModel,
        data: HierarchyNodeUpdate,
    ) -> HierarchyNodeModel:
        changes = data.model_dump(exclude_unset=True)

        if "name" in changes:
            node.name = changes["name"].strip()
        if "system_prompt" in changes:
            node.system_prompt = changes["system_prompt"]
        if "tool_policy" in changes:
            node.tool_policy = dict(changes["tool_policy"] or {})
        if "config_overrides" in changes:
            node.config_overrides = dict(changes["config_overrides"] or {})
        if "metadata" in changes:
            node.node_metadata = dict(changes["metadata"] or {})

        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def move_node(
        self,
        node: HierarchyNodeModel,
        *,
        new_parent_id: str | None,
    ) -> HierarchyNodeModel:
        node.parent_id = new_parent_id
        node.position = await self._next_position(new_parent_id)

        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def delete_node(self, node_id: str) -> None:
        await self._session.execute(
            delete(HierarchyNodeModel).where(
                HierarchyNodeModel.id == node_id,
            ),
        )

    async def get_ancestor_chain(
        self,
        node_id: str,
    ) -> list[HierarchyNodeModel]:
        chain: list[HierarchyNodeModel] = []
        visited: set[str] = set()
        current = await self.get_node(node_id)

        while current is not None:
            if current.id in visited:
                raise RuntimeError("Zyklische Hierarchie erkannt.")

            visited.add(current.id)
            chain.append(current)

            if current.parent_id is None:
                break

            current = await self.get_node(current.parent_id)

        chain.reverse()
        return chain

    async def is_descendant(
        self,
        *,
        node_id: str,
        possible_ancestor_id: str,
    ) -> bool:
        current = await self.get_node(node_id)
        visited: set[str] = set()

        while current is not None:
            if current.id in visited:
                raise RuntimeError("Zyklische Hierarchie erkannt.")

            visited.add(current.id)

            if current.parent_id == possible_ancestor_id:
                return True
            if current.parent_id is None:
                return False

            current = await self.get_node(current.parent_id)

        return False

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def _next_position(self, parent_id: str | None) -> int:
        children = await self.list_children(parent_id)
        if not children:
            return 0
        return max(child.position for child in children) + 1
