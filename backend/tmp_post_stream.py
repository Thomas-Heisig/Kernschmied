import httpx
import sys

url = "http://127.0.0.1:8000/api/v1/chat/stream"
payload = {
    "message": "Testing system_message_count",
    "hierarchy_node_id": "9e4a64fb-52ab-43d5-9d84-cc121d8f2a24"
}

with httpx.stream("POST", url, json=payload, timeout=20.0) as r:
    print('status:', r.status_code)
    try:
        for i, line in enumerate(r.iter_lines()):
            if not line:
                continue
            # decode if bytes
            if isinstance(line, bytes):
                line = line.decode('utf-8', errors='replace')
            print(line)
            sys.stdout.flush()
            if i > 200:
                break
    except Exception as e:
        print('stream-error:', e)

print('done')
