import os
import tempfile
from pathlib import Path
import importlib.util
import sys
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def _load_create_application():
    repo_root = Path(__file__).resolve().parents[2]
    main_path = repo_root / "backend" / "main.py"
    # ensure backend directory is on sys.path so `import app` works
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    spec = importlib.util.spec_from_file_location("backend.main", str(main_path))
    mod = importlib.util.module_from_spec(spec)
    # register module name so dataclass string-annotation resolution works
    import sys as _sys

    _sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.create_application


def test_calendars_end_to_end(tmp_path):
    db_file = tmp_path / "kernschmied_integration.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.resolve()}"

    create_application = _load_create_application()
    app = create_application()

    with TestClient(app) as client:
        # Create calendar
        resp = client.post("/api/v1/calendars", json={"name": "Integration Cal"})
        assert resp.status_code == 201
        cal = resp.json()
        cal_id = cal["id"]

        # Create event
        now = datetime.now(timezone.utc)
        start = now.isoformat() + "Z"
        end = (now + timedelta(hours=1)).isoformat() + "Z"

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
