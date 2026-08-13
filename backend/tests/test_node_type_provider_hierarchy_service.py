import asyncio
import tempfile

from app.database.base import Base
from app.database.models.hierarchy_node import HierarchyNodeModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.ui.repository import InMemoryUISchemaRepository
from app.contracts.ui_schema import NodeTypeDefinition
from app.services.ui_schema_service import create_ui_schema_service
from app.ui.node_type_provider import NodeTypeProvider

from app.hierarchy.repository import HierarchyRepository
from app.hierarchy.service import HierarchyService, HierarchyChildTypeNotAllowedError
from app.hierarchy.permissions import HierarchyPermissionService
from app.hierarchy.serializer import HierarchySerializer
from app.hierarchy.inheritance import HierarchyInheritanceService
from app.hierarchy.models import HierarchyActor

from app.contracts.hierarchy import HierarchyNodeCreate


async def _setup_engine():
    tmp = tempfile.TemporaryDirectory()
    url = f"sqlite+aiosqlite:///{tmp.name}/db.sqlite3"
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)
    return tmp, engine, session_factory


def _make_node_type(def_id: str, allowed: tuple[str, ...]):
    return NodeTypeDefinition(label=def_id, allowed_child_types=allowed)


async def test_create_allowed_by_registry():
    tmp, engine, session_factory = await _setup_engine()

    async with session_factory() as session:
        # create an existing parent node of type 'workspace'
        parent = HierarchyNodeModel(id="parent-1", type="workspace", name="P", parent_id=None, position=0, tool_policy={}, config_overrides={}, node_metadata={}, widget_assignments=[], is_system=False, is_movable=True, is_deletable=True, prompt_enabled=True, prompt_priority=0, prompt_mode="append", is_active=True)
        session.add(parent)
        await session.commit()

    # Prepare a UISchema repository that allows workspace -> user
    node_types = {
        "workspace": _make_node_type("workspace", ("user",)),
        "user": _make_node_type("user", ()),
    }

    repo = InMemoryUISchemaRepository(node_types=node_types)
    ui_service = create_ui_schema_service(repository=repo)
    provider = NodeTypeProvider(service=ui_service)

    async with session_factory() as session:
        repository = HierarchyRepository(session)

        # Build HierarchyService wiring
        permission_service = HierarchyPermissionService()
        inheritance_service = HierarchyInheritanceService()
        serializer = HierarchySerializer(permission_service=permission_service, inheritance_service=inheritance_service)
        service = HierarchyService(repository=repository, permission_service=permission_service, serializer=serializer, node_type_provider=provider)

        actor = HierarchyActor(user_id="u", roles=frozenset({"admin"}), permissions=frozenset())

        create_payload = HierarchyNodeCreate(type="user", name="Child User", parent_id="parent-1", tool_policy={}, config_overrides={}, metadata={})

        node = await service.create_node(create_payload, actor=actor)
        assert node.type == "user"


async def test_create_blocked_by_registry():
    tmp, engine, session_factory = await _setup_engine()

    async with session_factory() as session:
        parent = HierarchyNodeModel(id="parent-2", type="workspace", name="P2", parent_id=None, position=0, tool_policy={}, config_overrides={}, node_metadata={}, widget_assignments=[], is_system=False, is_movable=True, is_deletable=True, prompt_enabled=True, prompt_priority=0, prompt_mode="append", is_active=True)
        session.add(parent)
        await session.commit()

    # Registry forbids workspace -> user
    node_types = {
        "workspace": _make_node_type("workspace", ("project",)),
        "user": _make_node_type("user", ()),
    }

    repo = InMemoryUISchemaRepository(node_types=node_types)
    ui_service = create_ui_schema_service(repository=repo)
    provider = NodeTypeProvider(service=ui_service)

    async with session_factory() as session:
        repository = HierarchyRepository(session)
        permission_service = HierarchyPermissionService()
        inheritance_service = HierarchyInheritanceService()
        serializer = HierarchySerializer(permission_service=permission_service, inheritance_service=inheritance_service)
        service = HierarchyService(repository=repository, permission_service=permission_service, serializer=serializer, node_type_provider=provider)

        actor = HierarchyActor(user_id="u", roles=frozenset({"admin"}), permissions=frozenset())

        create_payload = HierarchyNodeCreate(type="user", name="Child User", parent_id="parent-2", tool_policy={}, config_overrides={}, metadata={})

        try:
            await service.create_node(create_payload, actor=actor)
            assert False, "Create should have been blocked by registry"
        except HierarchyChildTypeNotAllowedError:
            pass


def test_runner():
    asyncio.run(test_create_allowed_by_registry())
    asyncio.run(test_create_blocked_by_registry())


if __name__ == "__main__":
    test_runner()
