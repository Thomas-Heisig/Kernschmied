import os
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient


def _load_create_application() -> object:
    repo_root = Path(__file__).resolve().parents[2]
    main_path = repo_root / "backend" / "main.py"
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(backend_dir))

    spec = importlib.util.spec_from_file_location("backend.main", str(main_path))
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    # Ensure the module is available in sys.modules so dataclass
    # type checks that rely on module lookups succeed during import.
    import sys as _sys
    _sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_post_assignments_creates_relational_and_effective_includes_calendar(tmp_path: Path):
    db_file = tmp_path / "kernschmied_assignments.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.resolve()}"

    mod = _load_create_application()
    app = mod.create_application()

    with TestClient(app) as client:
        # POST assignment for calendar to workspaces-root
        payload = {"assignments": [{"name": "calendar", "enabled": True}]}
        resp = client.post("/api/v1/widgets/nodes/workspaces-root/assignments", json=payload)
        assert resp.status_code == 200

        # GET effective widgets for workspaces-root should now include calendar
        eff = client.get("/api/v1/widgets/nodes/workspaces-root/effective")
        assert eff.status_code == 200
        data = eff.json()
        items = data.get("items") or []
        cal = None
        for it in items:
            if str(it.get("id") or it.get("name")) == "calendar":
                cal = it
                break
        assert cal is not None, "calendar not found after POST assignment"


def test_post_empty_deletes_relational_assignment_and_effective_excludes_calendar(tmp_path: Path):
    db_file = tmp_path / "kernschmied_assignments_delete.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.resolve()}"

    mod = _load_create_application()
    app = mod.create_application()

    with TestClient(app) as client:
        # Add assignment first
        payload = {"assignments": [{"name": "calendar", "enabled": True}]}
        resp = client.post("/api/v1/widgets/nodes/workspaces-root/assignments", json=payload)
        assert resp.status_code == 200

        # Confirm present
        eff = client.get("/api/v1/widgets/nodes/workspaces-root/effective")
        assert eff.status_code == 200
        items = eff.json().get("items") or []
        assert any((str(i.get("id") or i.get("name")) == "calendar") for i in items)

        # Now post empty assignments to remove
        resp2 = client.post("/api/v1/widgets/nodes/workspaces-root/assignments", json={"assignments": []})
        assert resp2.status_code == 200

        eff2 = client.get("/api/v1/widgets/nodes/workspaces-root/effective")
        assert eff2.status_code == 200
        items2 = eff2.json().get("items") or []
        assert not any((str(i.get("id") or i.get("name")) == "calendar") for i in items2)
