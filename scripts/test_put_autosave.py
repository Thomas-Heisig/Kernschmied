import json
import urllib.request
import urllib.error

url = "http://127.0.0.1:8000/api/v1/config"
payload = {"values": {"ui": {"autosave_enabled": True}}}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="PUT")

try:
    with urllib.request.urlopen(req) as resp:
        print("STATUS", resp.status)
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print("ERROR", e.code)
    try:
        print(e.read().decode())
    except Exception:
        pass
except Exception as exc:
    print("EXC", exc)
