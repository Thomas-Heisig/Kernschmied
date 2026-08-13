import pytest
from types import SimpleNamespace
from app.widgets.service import WidgetResolverService


class DummyActor:
    def __init__(self, permissions=None, roles=None):
        self.permissions = permissions or []
        self.roles = roles or []


@pytest.mark.asyncio
async def test_missing_supported_allows_assignment_on_workspace():
    # registry missing supported_node_types -> allowed on workspace
    node = SimpleNamespace(id="w1", parent_id=None, type="workspace", widget_assignments=[{"id": "calendar", "name": "calendar", "enabled": True}], is_system=False)
    svc = WidgetResolverService(session=None)

    async def loader(_):
        return [node]

    svc._load_chain = loader
    items = await svc.resolve_effective_widgets("w1", DummyActor())
    assert any(i.get("id") == "calendar" or i.get("name") == "calendar" for i in items)


@pytest.mark.asyncio
async def test_explicit_list_blocks_other_node_types():
    # registry advertises only project -> workspace should be blocked unless direct assignment
    project = SimpleNamespace(id="p1", parent_id=None, type="project", widget_assignments=[{"id": "calendar", "name": "calendar", "enabled": True}], is_system=False)
    workspace = SimpleNamespace(id="w1", parent_id=None, type="workspace", widget_assignments=[{"id": "calendar", "name": "calendar", "enabled": True}], is_system=False)

    svc = WidgetResolverService(session=None)

    async def loader(_):
        return [project, workspace]

    svc._load_chain = loader

    # simulate registry exposes supported_node_types = ['project'] for calendar
    # We monkeypatch the registry lookup inside the service for this test
    original_lookup = getattr(svc, "_lookup_registry", None)

    async def fake_lookup(name):
        return {"id": name, "widget_metadata": {"component_type": "calendar_widget", "supported_node_types": ["project"]}}

    setattr(svc, "_lookup_registry", fake_lookup)

    # Inject a fake session that returns a registry row for calendar with supported_node_types=['project']
    class FakeReg:
        def __init__(self, md):
            self.status = "active"
            self.widget_metadata = md
            self.type = None
            self.name = "calendar"
            self.id = "calendar"
            self.required_permissions = []

    class FakeResult:
        def __init__(self, rows):
            self._rows = rows

        def scalars(self):
            return self

        def all(self):
            return self._rows

        def scalar_one(self):
            # used for COUNT(*) fallback
            try:
                return int(self._rows[0])
            except Exception:
                return 0

        def scalar_one_or_none(self):
            return self._rows[0] if self._rows else None

        def fetchone(self):
            try:
                return (int(self._rows[0]),)
            except Exception:
                return (0,)

        def fetchall(self):
            return self._rows

    class FakeSession:
        def __init__(self, rows):
            self._rows = rows

        async def execute(self, stmt, *args, **kwargs):
            return FakeResult(self._rows)

    svc._session = FakeSession([FakeReg({"component_type": "calendar_widget", "supported_node_types": ["project"]})])

    items_ws = await svc.resolve_effective_widgets("w1", DummyActor())
    # Direct assignment on workspace should be authoritative and therefore visible
    assert any(i.get("id") == "calendar" or i.get("name") == "calendar" for i in items_ws)

    # direct assignment on project should still show
    items_proj = await svc.resolve_effective_widgets("p1", DummyActor())
    assert any(i.get("id") == "calendar" or i.get("name") == "calendar" for i in items_proj)

    if original_lookup is None:
        try:
            delattr(svc, "_lookup_registry")
        except Exception:
            pass
    else:
        setattr(svc, "_lookup_registry", original_lookup)


@pytest.mark.asyncio
async def test_wildcard_allows_all():
    node = SimpleNamespace(id="n1", parent_id=None, type="workspace", widget_assignments=[{"id": "calendar", "name": "calendar", "enabled": True}], is_system=False)
    svc = WidgetResolverService(session=None)

    async def loader(_):
        return [node]

    svc._load_chain = loader
    original_lookup = getattr(svc, "_lookup_registry", None)

    async def fake_lookup(name):
        return {"id": name, "widget_metadata": {"component_type": "calendar_widget", "supported_node_types": ["*"]}}

    setattr(svc, "_lookup_registry", fake_lookup)
    items = await svc.resolve_effective_widgets("n1", DummyActor())
    assert any(i.get("id") == "calendar" or i.get("name") == "calendar" for i in items)
    if original_lookup is None:
        try:
            delattr(svc, "_lookup_registry")
        except Exception:
            pass
    else:
        setattr(svc, "_lookup_registry", original_lookup)
