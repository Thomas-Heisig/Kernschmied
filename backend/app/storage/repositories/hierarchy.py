from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models.hierarchy import HierarchyNode
from app.storage.repositories.base import Repository


class HierarchyRepository(Repository[HierarchyNode]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get(self, node_id: str) -> HierarchyNode | None:
        return await self.session.get(HierarchyNode, node_id)

    async def list_all(self) -> Sequence[HierarchyNode]:
        result = await self.session.scalars(
            select(HierarchyNode)
            .where(HierarchyNode.is_active.is_(True))
            .order_by(
                HierarchyNode.parent_id,
                HierarchyNode.position,
                HierarchyNode.name,
            )
        )
        return result.all()

    async def add(self, node: HierarchyNode) -> HierarchyNode:
        self.session.add(node)
        await self.session.flush()
        await self.session.refresh(node)
        return node
