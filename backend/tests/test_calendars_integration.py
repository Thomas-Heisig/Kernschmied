import importlib.util
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

from fastapi.testclient import TestClient


def _load_create_application() -> ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    main_path = repo_root / "backend" / "main.py"
    # ensure backend directory is on sys.path so `import app` works
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    spec = importlib.util.spec_from_file_location("backend.main", str(main_path))
    assert spec is not None, f"Could not load spec from {main_path}"
    mod = importlib.util.module_from_spec(spec)
    # register module name so dataclass string-annotation resolution works
    sys.modules[spec.name] = mod
    assert spec.loader is not None, "Loader is None"
    spec.loader.exec_module(mod)
    return mod


def test_calendars_end_to_end(tmp_path: Path) -> None:
    db_file = tmp_path / "kernschmied_integration.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.resolve()}"

    mod = _load_create_application()
    app = mod.create_application()

    with TestClient(app) as client:
        # Create calendar
        resp = client.post("/api/v1/calendars", json={"name": "Integration Cal"})
        assert resp.status_code == 201
        cal = resp.json()
        cal_id = cal["id"]

        # Create event
        now = datetime.now(UTC)
        # produce RFC3339/ISO datetimes acceptable to FastAPI/Pydantic
        start = now.isoformat()
        end = (now + timedelta(hours=1)).isoformat()

        ev_payload = {
            "title": "Integration Meeting",
            "start": start,
            "end": end,
        }

        resp2 = client.post(f"/api/v1/calendars/{cal_id}/events", json=ev_payload)
        assert resp2.status_code == 201
        event = resp2.json()
        assert event["title"] == "Integration Meeting"

        # List events
        resp3 = client.get(f"/api/v1/calendars/{cal_id}/events")
        assert resp3.status_code == 200
        items = resp3.json()
        assert any(i["id"] == event["id"] for i in items)