import json
import httpx

conv='conversation_89e47c3e78254f4db96304ddb8dde449'
BASE='http://127.0.0.1:8000/api/v1'
with httpx.Client(timeout=10.0) as c:
    r=c.get(f"{BASE}/chats/{conv}/messages")
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)
