import pytest

from types import SimpleNamespace
from typing import Any, Dict, List, Optional, cast

from app.hierarchy.service import HierarchyService
from app.hierarchy.permissions import HierarchyPermissionService
from app.hierarchy.models import HierarchyActor
from app.contracts.hierarchy import HierarchyNodeCreate
from app.hierarchy.repository import HierarchyRepository
from app.hierarchy.serializer import HierarchySerializer


class FakeRepository:
    def __init__(self, nodes: Optional[Dict[str, Any]] = None) -> None:
        self._nodes: Dict[str, Any] = nodes or {}

    async def get_node(self, node_id: str) -> Any | None:
        return self._nodes.get(node_id)

    async def list_nodes(self) -> List[Any]:
        return list(self._nodes.values())

    async def create_node(self, data: HierarchyNodeCreate) -> Any:
        # simplistic creation: return object with id
        node = SimpleNamespace(**{"id": data.node_id or "generated-id", "is_system": False, "is_movable": True, "is_deletable": True})
        self._nodes[node.id] = node
        return node

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def move_node(self, node: Any, new_parent_id: Optional[str] = None) -> None:
        node.parent_id = new_parent_id

    async def reorder_nodes(self, moves: List[tuple[str, Optional[str], int]]) -> None:
        return None

    async def delete_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)

    async def is_descendant(self, node_id: str, possible_ancestor_id: Optional[str]) -> bool:
        return False


class DummySerializer:
    def __init__(self):
        pass


@pytest.mark.asyncio
async def test_system_root_cannot_be_deleted():
    node = SimpleNamespace(id="system-root", is_system=True, is_deletable=False)
    repo = FakeRepository({"system-root": node})
    perm = HierarchyPermissionService()
    service = HierarchyService(repository=cast(HierarchyRepository, repo), permission_service=perm, serializer=cast(HierarchySerializer, DummySerializer()))
    actor = HierarchyActor(roles=frozenset({"admin"}))

    with pytest.raises(PermissionError):
        await service.delete_node("system-root", actor=actor)


@pytest.mark.asyncio
async def test_node_not_movable_cannot_be_moved():
    node = SimpleNamespace(id="n1", is_system=False, is_movable=False)
    repo = FakeRepository({"n1": node, "p1": SimpleNamespace(id="p1")})
    perm = HierarchyPermissionService()
    service = HierarchyService(repository=cast(HierarchyRepository, repo), permission_service=perm, serializer=cast(HierarchySerializer, DummySerializer()))
    actor = HierarchyActor(roles=frozenset({"admin"}))

    with pytest.raises(PermissionError):
        await service.move_node("n1", new_parent_id="p1", actor=actor)


@pytest.mark.asyncio
async def test_create_without_parent_forbidden():
    repo = FakeRepository()
    perm = HierarchyPermissionService()
    service = HierarchyService(repository=cast(HierarchyRepository, repo), permission_service=perm, serializer=cast(HierarchySerializer, DummySerializer()))
    actor = HierarchyActor(roles=frozenset({"admin"}))

    data = HierarchyNodeCreate(type="workspace", name="X", parent_id=None, tool_policy={}, config_overrides={}, metadata={}, node_id="not-system")

    with pytest.raises(ValueError):
        await service.create_node(data, actor=actor)


@pytest.mark.asyncio
async def test_create_under_system_root_requires_admin():
    parent = SimpleNamespace(id="system-root")
    repo = FakeRepository({"system-root": parent})
    perm = HierarchyPermissionService()
    service = HierarchyService(repository=cast(HierarchyRepository, repo), permission_service=perm, serializer=cast(HierarchySerializer, DummySerializer()))
    actor = HierarchyActor(roles=frozenset())

    data = HierarchyNodeCreate(type="workspace", name="X", parent_id="system-root", tool_policy={}, config_overrides={}, metadata={}, node_id="w1")

    with pytest.raises(PermissionError):
        await service.create_node(data, actor=actor)


@pytest.mark.asyncio
async def test_reorder_immovable_nodes_forbidden():
    node = SimpleNamespace(id="n1", is_system=False, is_movable=False)
    repo = FakeRepository({"n1": node, "p1": SimpleNamespace(id="p1")})
    perm = HierarchyPermissionService()
    service = HierarchyService(repository=cast(HierarchyRepository, repo), permission_service=perm, serializer=cast(HierarchySerializer, DummySerializer()))
    actor = HierarchyActor(roles=frozenset({"admin"}))

    moves: List[tuple[str, Optional[str], int]] = [("n1", "p1", 0)]

    with pytest.raises(PermissionError):
        await service.reorder_nodes(moves, actor=actor)
