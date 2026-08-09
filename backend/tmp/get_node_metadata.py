import json
import sys
import httpx

if len(sys.argv) < 2:
    print(json.dumps({"error":"missing_node_id"}))
    sys.exit(1)

node_id = sys.argv[1]
BASE = "http://127.0.0.1:8000/api/v1"

with httpx.Client(timeout=10.0) as client:
    r = client.get(f"{BASE}/hierarchy")
    if r.status_code != 200:
        print(json.dumps({"error":"hierarchy_failed","status":r.status_code, "text": r.text}))
        sys.exit(2)
    tree = r.json()

    def find(node):
        if not node:
            return None
        if node.get('id') == node_id:
            return node
        for c in node.get('children', []) or []:
            found = find(c)
            if found:
                return found
        return None

    found = find(tree.get('root'))
    print(json.dumps({"node_id": node_id, "found": found}, indent=2, ensure_ascii=False))
