import json
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8000/api/v1/hierarchy'

def req(url, method='GET', data=None):
    headers = {'Content-Type':'application/json'}
    if data is not None:
        data = json.dumps(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
            return e.code, json.loads(body)
        except Exception:
            return e.code, {'error': body}
    except Exception as e:
        return None, {'error': str(e)}

# 1. GET tree
status, tree = req(BASE, 'GET')
print('GET tree status', status)
if status != 200:
    print('Failed to GET tree:', tree)
    raise SystemExit(1)

root = tree.get('root')
if not root:
    print('No root in tree response')
    raise SystemExit(1)

root_id = root.get('id')
children = root.get('children', [])
print('Root id:', root_id, 'children_count:', len(children))

# 2. Ensure a child exists
if children:
    node = children[0]
    node_id = node['id']
    print('Using existing child', node_id)
else:
    payload = {'type':'project','name':'ChildTest','parent_id':root_id,'tool_policy':{},'config_overrides':{},'metadata':{}}
    status, created = req(BASE, 'POST', payload)
    print('Create child status', status)
    if status not in (200,201):
        print('Create failed', created)
        raise SystemExit(1)
    node_id = created.get('id')
    print('Created child id', node_id)

# 3. PATCH (rename)
patch_payload = {'name':'ChildTest-Patched'}
status, patched = req(f"{BASE}/{node_id}", 'PATCH', patch_payload)
print('PATCH status', status)
print('PATCH response name:', patched.get('name'))

# 4. MOVE (move to root/null)
move_payload = {'new_parent_id': None}
status, moved = req(f"{BASE}/{node_id}/move", 'POST', move_payload)
print('MOVE status', status)
print('MOVE response parent_id:', moved.get('parent_id'))

# 5. DELETE
status, deleted = req(f"{BASE}/{node_id}", 'DELETE')
print('DELETE status', status)

# 6. Verify deletion
status, tree_after = req(BASE, 'GET')
print('GET after status', status)
# simple search
found = False

def search(obj, nid):
    if not obj: return False
    if obj.get('id') == nid: return True
    for c in obj.get('children', []):
        if search(c, nid):
            return True
    return False

found = search(tree_after.get('root'), node_id)
print('Node present after delete?', found)

print('Done')
