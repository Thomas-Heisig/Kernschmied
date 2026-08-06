import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from fastapi.testclient import TestClient


def _load_create_application() -> ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    main_path = repo_root / "backend" / "main.py"
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    spec = importlib.util.spec_from_file_location("backend.main", str(main_path))
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_hierarchy_endpoint_contract(tmp_path: Path) -> None:
    db_file = tmp_path / "kernschmied_hierarchy.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.resolve()}"

    mod = _load_create_application()
    app = mod.create_application()

    with TestClient(app) as client:
        resp = client.get("/api/v1/hierarchy")
        assert resp.status_code == 200
        data = resp.json()

        # top-level keys
        assert "schema_version" in data
        assert "root" in data

        root = cast(dict[str, Any], data["root"])
        assert isinstance(root, dict)
        # required node fields
        assert "id" in root and isinstance(root["id"], str)
        assert "type" in root and isinstance(root["type"], str)
        assert "name" in root and isinstance(root["name"], str)
        assert "children" in root and isinstance(root["children"], list)

        # every child must have children array and actions array
        def check_children(node: dict[str, Any]) -> None:
            assert "children" in node and isinstance(node["children"], list)
            assert "actions" in node and isinstance(node["actions"], list)
            # ensure old internal key is not present
            assert "available_actions" not in node
            children = cast(list[Any], node["children"])
            for c in children:
                if isinstance(c, dict):
                    c_dict = cast(dict[str, Any], c)
                    check_children(c_dict)

        check_children(root)
