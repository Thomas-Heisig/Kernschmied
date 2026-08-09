import json
import sys
import httpx

if len(sys.argv) < 2:
    print(json.dumps({"error":"missing_node_id"}))
    sys.exit(1)

node_id = sys.argv[1]
BASE = "http://127.0.0.1:8000/api/v1"

with httpx.Client(timeout=10.0) as client:
    try:
        node_res = client.get(f"{BASE}/hierarchy/{node_id}")
        node = node_res.json() if node_res.status_code == 200 else {"error": node_res.text}
    except Exception as e:
        node = {"error": str(e)}

    conv_id = None
    if isinstance(node, dict) and isinstance(node.get('metadata'), dict):
        meta = node.get('metadata')
        if meta.get('entity_type') == 'conversation' and isinstance(meta.get('entity_id'), str):
            conv_id = meta.get('entity_id')

    history = None
    history_status = None
    if conv_id:
        try:
            hres = client.get(f"{BASE}/chats/{conv_id}/messages")
            history_status = hres.status_code
            history = hres.json() if hres.status_code == 200 else {"error": hres.text}
        except Exception as e:
            history = {"error": str(e)}

    out = {"node_id": node_id, "node": node, "conversation_id_from_metadata": conv_id, "history_status": history_status, "history": history}
    print(json.dumps(out, indent=2, ensure_ascii=False))
