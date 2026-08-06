from app.api.v1 import documentation
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
app.include_router(documentation.router, prefix="/api/v1/documentation")

client = TestClient(app)

print("Requesting /api/v1/documentation")
resp = client.get("/api/v1/documentation")
print("Status:", resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)

if resp.status_code == 200:
    data = resp.json()
    default = data.get("default_page_id") or data.get("home_page_id") or None
    print("default_page_id:", default)
    if default:
        p = client.get(f"/api/v1/documentation/pages/{default}")
        print("Page status:", p.status_code)
        try:
            print(p.json())
        except Exception:
            print(p.text)
else:
    print("Documentation index did not return 200; see details above")
