import sys
from pathlib import Path

# Ensure `app` package (backend/app) is importable when running tests from the backend/tests folder.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
