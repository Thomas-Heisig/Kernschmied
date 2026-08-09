import json
import sys
import time
from typing import Any

import httpx

BASE = "http://127.0.0.1:8000/api/v1"


def find_first_chat(node: dict[str, Any]) -> dict | None:
    if not node:
        return None
    if node.get("type") == "chat":
        return node
    for c in node.get("children", []) or []:
        found = find_first_chat(c)
        if found:
            return found
    return None


with httpx.Client(timeout=None) as client:
    try:
        r = client.get(f"{BASE}/hierarchy")
        r.raise_for_status()
        tree = r.json()
    except Exception as e:
        print(json.dumps({"error": "hierarchy_fetch_failed", "detail": str(e)}))
        sys.exit(1)

    node = find_first_chat(tree.get("root"))
    if not node:
        print(json.dumps({"error": "no_chat_node_found"}))
        sys.exit(2)

    node_id = node["id"]

    # Post a streaming chat request and collect SSE events
    payload = {
        "message": "persistenz-test-001",
        "conversation_id": None,
        "hierarchy_node_id": node_id,
        "model_id": None,
        "tool_ids": [],
        "metadata": {"client": "persistence-integration-test"},
    }

    conv_id = None
    events = []

    try:
        with client.stream("POST", f"{BASE}/chat/stream", json=payload) as resp:
            resp.raise_for_status()
            buffer = ""
            for raw in resp.iter_bytes():
                try:
                    chunk = raw.decode("utf-8")
                except Exception:
                    continue
                buffer += chunk
                buffer = buffer.replace("\r\n", "\n").replace("\r", "\n")
                parts = buffer.split("\n\n")
                buffer = parts.pop() if parts else ""
                for part in parts:
                    # parse SSE chunk
                    lines = [ln for ln in part.split("\n") if ln and not ln.startswith(":")]
                    data_lines = [ln.split(":", 1)[1].lstrip() if ":" in ln else "" for ln in lines if ln.startswith("data")] 
                    if not data_lines:
                        continue
                    data = "\n".join(data_lines)
                    try:
                        envelope = json.loads(data)
                    except Exception:
                        envelope = None

                    events.append({"raw": part, "envelope": envelope})

                    if isinstance(envelope, dict):
                        if envelope.get("conversation_id") and isinstance(envelope.get("conversation_id"), str):
                            conv_id = envelope.get("conversation_id")

            # remaining buffer
            rem = buffer.strip()
            if rem:
                lines = [ln for ln in rem.split("\n") if ln and not ln.startswith(":")]
                data_lines = [ln.split(":", 1)[1].lstrip() if ":" in ln else "" for ln in lines if ln.startswith("data")]
                if data_lines:
                    data = "\n".join(data_lines)
                    try:
                        envelope = json.loads(data)
                    except Exception:
                        envelope = None
                    events.append({"raw": rem, "envelope": envelope})
                    if isinstance(envelope, dict) and envelope.get("conversation_id"):
                        conv_id = envelope.get("conversation_id")

    except Exception as exc:
        print(json.dumps({"error": "stream_failed", "detail": str(exc)}))
        sys.exit(3)

    # canonical mapping from hierarchy node
    try:
        node_resp = client.get(f"{BASE}/hierarchy/{node_id}")
        node_resp.raise_for_status()
        node_full = node_resp.json()
    except Exception as e:
        node_full = {"error": str(e)}

    # get history if conv id known
    history = None
    history_status = None
    if conv_id:
        try:
            hres = client.get(f"{BASE}/chats/{conv_id}/messages")
            history_status = hres.status_code
            if hres.status_code == 200:
                history = hres.json()
            else:
                history = {"error": hres.text}
        except Exception as e:
            history = {"error": str(e)}

    out = {
        "node_id": node_id,
        "conversation_id_from_stream": conv_id,
        "hierarchy_node": node_full,
        "history_status": history_status,
        "history": history,
        "events_count": len(events),
    }

    print(json.dumps(out, indent=2, ensure_ascii=False))
