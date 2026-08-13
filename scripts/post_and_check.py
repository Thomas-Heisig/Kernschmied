import json
import sqlite3
import urllib.request
import urllib.error

API = 'http://127.0.0.1:8000'

def post_assignment(node_id, payload):
    url = f"{API}/api/v1/widgets/nodes/{node_id}/assignments"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()
    except urllib.error.HTTPError as e:
        print('HTTPError', e.code, e.read().decode())
        return None
    except Exception as e:
        print('Error posting', e)
        return None


def get_effective(node_id):
    url = f"{API}/api/v1/widgets/nodes/{node_id}/effective"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print('Error getting effective', e)
        return None


def query_db_for_assignments(db_path, node_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT id,node_id,widget_id,name,enabled FROM widget_assignments WHERE node_id=?', (node_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == '__main__':
    payload = {"assignments": [{"id": "calendar", "name": "calendar", "enabled": True, "inherit": False, "position": 10, "configuration": {"view": "month"}}]}
    print('POST workspace-root ->', post_assignment('workspace-root', payload))
    print('GET workspace-root effective ->', json.dumps(get_effective('workspace-root'), indent=2))
    db = 'backend/data/chat.db'
    print('DB rows for workspace-root ->', query_db_for_assignments(db, 'workspace-root'))
