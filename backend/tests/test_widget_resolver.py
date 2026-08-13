import pytest
import asyncio
from types import SimpleNamespace

from app.widgets.service import WidgetResolverService


class DummyActor:
    def __init__(self, permissions=None, roles=None):
        self.permissions = permissions or []
        self.roles = roles or []


@pytest.mark.asyncio
async def test_direct_assignment_visible():
    # A. direct assignment -> visible
    node = SimpleNamespace(id="n1", parent_id=None, type="folder", widget_assignments=[{"id": "w1", "name": "w1", "enabled": True, "position": 1}], is_system=False)
    svc = WidgetResolverService(session=None)
    async def loader(_):
        return [node]
    svc._load_chain = loader
    items = await svc.resolve_effective_widgets("n1", DummyActor())
    assert any(i.get("id") == "w1" or i.get("name") == "w1" for i in items)


@pytest.mark.asyncio
async def test_parent_inherit_true_child_gets_widget():
    # B. parent inherit=true -> child gets widget
    parent = SimpleNamespace(id="p", parent_id=None, type="folder", widget_assignments=[{"id": "wf", "name": "wf", "enabled": True, "inherit": True, "position": 5}], is_system=False)
    child = SimpleNamespace(id="c", parent_id="p", type="folder", widget_assignments=[], is_system=False)
    svc = WidgetResolverService(session=None)
    async def loader(_):
        return [parent, child]
    svc._load_chain = loader
    items = await svc.resolve_effective_widgets("c", DummyActor())
    assert any(i.get("id") == "wf" or i.get("name") == "wf" for i in items)


@pytest.mark.asyncio
async def test_inherit_false_parent_not_propagated():
    # C. inherit=false on parent -> child does not get widget
    parent = SimpleNamespace(id="p", parent_id=None, type="folder", widget_assignments=[{"id": "wf", "name": "wf", "enabled": True, "inherit": False}], is_system=False)
    child = SimpleNamespace(id="c", parent_id="p", type="folder", widget_assignments=[], is_system=False)
    svc = WidgetResolverService(session=None)
    async def loader(_):
        return [parent, child]
    svc._load_chain = loader
    items = await svc.resolve_effective_widgets("c", DummyActor())
    assert not any(i.get("id") == "wf" or i.get("name") == "wf" for i in items)


@pytest.mark.asyncio
async def test_enabled_false_disables_widget():
    # D. enabled=false on child disables inherited
    parent = SimpleNamespace(id="p", parent_id=None, type="folder", widget_assignments=[{"id": "wf", "name": "wf", "enabled": True}], is_system=False)
    child = SimpleNamespace(id="c", parent_id="p", type="folder", widget_assignments=[{"id": "wf", "name": "wf", "enabled": False}], is_system=False)
    svc = WidgetResolverService(session=None)
    async def loader(_):
        return [parent, child]
    svc._load_chain = loader
    items = await svc.resolve_effective_widgets("c", DummyActor())
    assert not any(i.get("id") == "wf" or i.get("name") == "wf" for i in items)


@pytest.mark.asyncio
async def test_child_override_wins():
    # G. parent and child same widget_id -> child wins (configuration)
    parent = SimpleNamespace(id="p", parent_id=None, type="folder", widget_assignments=[{"id": "wf", "name": "wf", "enabled": True, "configuration": {"x": 1}}], is_system=False)
    child = SimpleNamespace(id="c", parent_id="p", type="folder", widget_assignments=[{"id": "wf", "name": "wf", "enabled": True, "configuration": {"x": 2}}], is_system=False)
    svc = WidgetResolverService(session=None)
    async def loader(_):
        return [parent, child]
    svc._load_chain = loader
    items = await svc.resolve_effective_widgets("c", DummyActor())
    found = [i for i in items if (i.get("id") == "wf" or i.get("name") == "wf")]
    assert len(found) == 1
    assert found[0].get("configuration", {}).get("x") == 2


@pytest.mark.asyncio
async def test_broken_widget_does_not_stop_others():
    # J. broken widget (non-dict) should not break resolution of others
    parent = SimpleNamespace(id="p", parent_id=None, type="folder", widget_assignments=["not-a-dict", {"id": "ok", "name": "ok", "enabled": True}], is_system=False)
    svc = WidgetResolverService(session=None)
    async def loader(_):
        return [parent]
    svc._load_chain = loader
    items = await svc.resolve_effective_widgets("p", DummyActor())
    assert any(i.get("id") == "ok" or i.get("name") == "ok" for i in items)
