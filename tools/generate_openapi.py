"""Generate OpenAPI JSON files from the FastAPI app.

Usage: run from repo root: `python tools/generate_openapi.py`

The script will attempt to import the application's `app` object by
adding `backend` to sys.path (so that `main.py` can initialize the app).
"""
import json
import sys
from pathlib import Path
from importlib import util

repo_root: Path = Path(__file__).resolve().parents[1]
backend_path = str(repo_root / "backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    module_name = "backend.main"
    path = str(repo_root / "backend" / "main.py")
    spec = util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError("Could not create import spec for backend/main.py")
    app_module = util.module_from_spec(spec)
    # Ensure the module is available under its package-style name so
    # dataclass/type lookups that consult sys.modules succeed during
    # runtime initialization of classes.
    sys.modules[module_name] = app_module
    spec.loader.exec_module(app_module)
except Exception as exc:
    print("Failed to import application module from backend/main.py:", exc)
    raise

app = getattr(app_module, "app", None)
if app is None:
    print("No `app` object found in main.py")
    raise SystemExit(1)

openapi = app.openapi()

out1 = repo_root / "docs" / "openapi.json"
out2 = repo_root / "docs" / "openapi-formatted.json"

# Write compact and pretty versions
with open(out1, "w", encoding="utf-8") as f:
    json.dump(openapi, f, ensure_ascii=False, separators=(",", ":"))

with open(out2, "w", encoding="utf-8") as f:
    json.dump(openapi, f, ensure_ascii=False, indent=2)

print(f"Wrote OpenAPI to: {out1}\nWrote formatted OpenAPI to: {out2}")
