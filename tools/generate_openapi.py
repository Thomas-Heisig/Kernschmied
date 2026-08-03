"""Generate OpenAPI JSON files from the FastAPI app.

Usage: run from repo root: `python tools/generate_openapi.py`

The script will attempt to import the application's `app` object by
adding `backend` to sys.path (so that `main.py` can initialize the app).
"""
import json
import pathlib
from importlib import util

repo_root = pathlib.Path(__file__).resolve().parents[1]
main_file = repo_root / "backend" / "main.py"

if not main_file.exists():
    print(f"backend main.py not found at: {main_file}")
    raise SystemExit(1)

try:
    spec = util.spec_from_file_location("backend_main", str(main_file))
    if spec is None or spec.loader is None:
        raise ImportError("Could not create import spec for backend/main.py")
    app_module = util.module_from_spec(spec)
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
