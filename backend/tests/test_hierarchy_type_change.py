import asyncio
import tempfile

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database.base import Base
from app.database.models.hierarchy_node import HierarchyNodeModel

from app.ui.repository import InMemoryUISchemaRepository
from app.services.ui_schema_service import create_ui_schema_service
from app.ui.node_type_provider import NodeTypeProvider

from app.hierarchy.repository import HierarchyRepository
from app.hierarchy.service import (
    HierarchyService,
    HierarchyNodeTypeChangeInvalidError,
)
from app.hierarchy.permissions import HierarchyPermissionService
from app.hierarchy.serializer import HierarchySerializer
from app.hierarchy.inheritance import HierarchyInheritanceService
from app.hierarchy.models import HierarchyActor

from app.contracts.hierarchy import HierarchyNodeCreate, HierarchyNodeUpdate


async def _setup_engine():
    tmp = tempfile.TemporaryDirectory()
    url = f"sqlite+aiosqlite:///{tmp.name}/db.sqlite3"
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)
    return tmp, engine, session_factory


def _make_node_type(def_id: str, allowed: tuple[str, ...]):
    from app.contracts.ui_schema import NodeTypeDefinition

    return NodeTypeDefinition(label=def_id, allowed_child_types=allowed)


async def test_name_change_and_allowed_type_change():
    tmp, engine, session_factory = await _setup_engine()

    async with session_factory() as session:
        root = HierarchyNodeModel(id='root', type='system-root', name='Root', parent_id=None, position=0, tool_policy={}, config_overrides={}, node_metadata={}, widget_assignments=[], is_system=True, is_movable=False, is_deletable=False, prompt_enabled=True, prompt_priority=0, prompt_mode='append', is_active=True)
        child = HierarchyNodeModel(id='n1', type='workspace', name='W', parent_id='root', position=0, tool_policy={}, config_overrides={}, node_metadata={}, widget_assignments=[], is_system=False, is_movable=True, is_deletable=True, prompt_enabled=True, prompt_priority=0, prompt_mode='append', is_active=True)
        session.add_all([root, child])
        await session.commit()

    node_types = {
        'workspace': _make_node_type('workspace', ('project', 'user')),
        'project': _make_node_type('project', ('chat',)),
        'chat': _make_node_type('chat', ()),
        'user': _make_node_type('user', ()),
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

        actor = HierarchyActor(user_id='u', roles=frozenset({'admin'}), permissions=frozenset())

        # change name
        upd = HierarchyNodeUpdate = None
        await service.update_node('n1', type('H', (), {'model_dump': lambda self, **kw: {'name': 'Workspace New'} })(), actor=actor)  # quick name change

        # change type to project (allowed by parent 'root' since root is system-root no restriction)
        class FakeUpdate:
            def model_dump(self, **kw):
                return {'type': 'project'}

        await service.update_node('n1', FakeUpdate(), actor=actor)


async def test_type_change_rejected_due_to_child_incompatibility():
    tmp, engine, session_factory = await _setup_engine()

    async with session_factory() as session:
        root = HierarchyNodeModel(id='root', type='system-root', name='Root', parent_id=None, position=0, tool_policy={}, config_overrides={}, node_metadata={}, widget_assignments=[], is_system=True, is_movable=False, is_deletable=False, prompt_enabled=True, prompt_priority=0, prompt_mode='append', is_active=True)
        parent = HierarchyNodeModel(id='p1', type='workspace', name='P', parent_id='root', position=0, tool_policy={}, config_overrides={}, node_metadata={}, widget_assignments=[], is_system=False, is_movable=True, is_deletable=True, prompt_enabled=True, prompt_priority=0, prompt_mode='append', is_active=True)
        child = HierarchyNodeModel(id='c1', type='user', name='User1', parent_id='p1', position=0, tool_policy={}, config_overrides={}, node_metadata={}, widget_assignments=[], is_system=False, is_movable=True, is_deletable=True, prompt_enabled=True, prompt_priority=0, prompt_mode='append', is_active=True)
        session.add_all([root, parent, child])
        await session.commit()

    node_types = {
        'workspace': _make_node_type('workspace', ('user', 'project')),
        'project': _make_node_type('project', ('chat',)),
        'chat': _make_node_type('chat', ()),
        'user': _make_node_type('user', ()),
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

        actor = HierarchyActor(user_id='u', roles=frozenset({'admin'}), permissions=frozenset())

        class FakeUpdate:
            def model_dump(self, **kw):
                return {'type': 'project'}

        try:
            await service.update_node('p1', FakeUpdate(), actor=actor)
            assert False, 'Expected HierarchyNodeTypeChangeInvalidError'
        except HierarchyNodeTypeChangeInvalidError as exc:
            assert 'invalid_children' in getattr(exc, 'details', {})


def run():
    asyncio.run(test_name_change_and_allowed_type_change())
    asyncio.run(test_type_change_rejected_due_to_child_incompatibility())


if __name__ == '__main__':
    run()
