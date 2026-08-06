from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.hierarchy import HierarchyNodeCreate, HierarchyNodeUpdate
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.prompts.errors import (
    BrokenPromptHierarchyError,
    InactivePromptHierarchyNodeError,
    PromptHierarchyCycleError,
    PromptHierarchyDepthError,
    PromptHierarchyNodeNotFoundError,
)

MAX_HIERARCHY_DEPTH = 64


class HierarchyParentNotFoundError(LookupError):
    def __init__(self, parent_id: str) -> None:
        super().__init__(f"Parent node '{parent_id}' not found")


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

        # ensure parent exists when provided
        if data.parent_id is not None:
            parent = await self.get_node(data.parent_id)
            if parent is None:
                raise HierarchyParentNotFoundError(data.parent_id)

        node_id = data.node_id or str(uuid4())

        node = HierarchyNodeModel(
            id=node_id,
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

    async def reorder_nodes(
        self,
        moves: Sequence[tuple[str, str | None, int]],
    ) -> None:
        """
        Atomar mehrere Knoten neu anordnen.

        `moves` ist eine Sequenz von Tupeln `(node_id, new_parent_id, new_position)`.
        Die Methode berechnet für jede betroffene Elternmenge die neue Reihenfolge
        und schreibt die `parent_id` und `position` Werte direkt an die Modelle.
        """
        # Collect node ids and affected parents
        node_ids = {m[0] for m in moves}
        affected_parents = {m[1] for m in moves}

        # Load all involved nodes
        statement = select(HierarchyNodeModel).where(
            HierarchyNodeModel.id.in_(list(node_ids))
        )
        result = await self._session.scalars(statement)
        nodes = {n.id: n for n in result.all()}

        # Load current children for affected parents
        parent_children: dict[str | None, list[HierarchyNodeModel]] = {}
        for parent in affected_parents:
            children = await self.list_children(parent)
            # remove nodes that will be moved away
            parent_children[parent] = [c for c in children if c.id not in node_ids]

        # Insert moved nodes into target parents at requested positions
        for node_id, new_parent_id, new_pos in moves:
            node = nodes.get(node_id)
            if node is None:
                raise LookupError(f"Node '{node_id}' not found")

            target_list = parent_children.get(new_parent_id)
            if target_list is None:
                # if parent had no children previously and not in dict, initialize
                children = await self.list_children(new_parent_id)
                parent_children[new_parent_id] = [
                    c for c in children if c.id not in node_ids
                ]
                target_list = parent_children[new_parent_id]

            # clamp position
            insert_at = max(0, min(len(target_list), int(new_pos)))
            target_list.insert(insert_at, node)

        # Now write back positions and parent_id
        for parent_id, children in parent_children.items():
            for idx, child in enumerate(children):
                child.parent_id = parent_id
                child.position = idx
                self._session.add(child)

        await self._session.flush()

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

        maybe_current: Any = await self.get_node(node_id)
        if maybe_current is None:
            raise PromptHierarchyNodeNotFoundError(f"Node '{node_id}' not found")
        current: HierarchyNodeModel = maybe_current

        depth = 0
        while True:
            if current.id in visited:
                raise PromptHierarchyCycleError("Zyklische Hierarchie erkannt.")

            if depth > MAX_HIERARCHY_DEPTH:
                raise PromptHierarchyDepthError(
                    "Maximale Hierarchietiefe überschritten."
                )

            if not current.is_active:
                raise InactivePromptHierarchyNodeError(
                    f"Node '{current.id}' is inactive"
                )

            visited.add(current.id)
            chain.append(current)

            if current.parent_id is None:
                break

            maybe_parent: Any = await self.get_node(current.parent_id)
            if maybe_parent is None:
                raise BrokenPromptHierarchyError(
                    f"Parent '{current.parent_id}' not found for node '{current.id}'"
                )

            parent: HierarchyNodeModel = maybe_parent

            current = parent
            depth += 1

        chain.reverse()
        return chain

    async def is_descendant(
        self,
        *,
        node_id: str,
        possible_ancestor_id: str,
    ) -> bool:
        maybe_current: Any = await self.get_node(node_id)
        current: HierarchyNodeModel = maybe_current
        visited: set[str] = set()

        while True:
            if current.id in visited:
                raise RuntimeError("Zyklische Hierarchie erkannt.")

            visited.add(current.id)

            if current.parent_id == possible_ancestor_id:
                return True
            if current.parent_id is None:
                return False

            maybe_current = await self.get_node(current.parent_id)
            current = maybe_current

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
