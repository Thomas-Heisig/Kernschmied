from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.hierarchy_node import HierarchyNodeModel
from app.storage.repositories.base import Repository


class HierarchyRepository(Repository[HierarchyNodeModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get(self, node_id: str) -> HierarchyNodeModel | None:
        return await self.session.get(HierarchyNodeModel, node_id)

    async def list_all(self) -> Sequence[HierarchyNodeModel]:
        result = await self.session.scalars(
            select(HierarchyNodeModel)
            .where(HierarchyNodeModel.is_active.is_(True))
            .order_by(
                HierarchyNodeModel.parent_id,
                HierarchyNodeModel.position,
                HierarchyNodeModel.name,
            )
        )
        return result.all()

    async def add(self, node: HierarchyNodeModel) -> HierarchyNodeModel:
        self.session.add(node)
        await self.session.flush()
        await self.session.refresh(node)
        return node
