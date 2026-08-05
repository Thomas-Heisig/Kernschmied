import os
import sys

# Ensure repository root is on sys.path so 'app' package is importable
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from main import create_application

app = create_application()
client = TestClient(app)

endpoints = [
    "/api/v1/bootstrap",
    "/api/v1/ui/schema",
    "/api/v1/hierarchy",
]

for ep in endpoints:
    try:
        r = client.get(ep)
        print(ep, r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text[:1000])
    except Exception as e:
        print(ep, 'ERROR', str(e))
