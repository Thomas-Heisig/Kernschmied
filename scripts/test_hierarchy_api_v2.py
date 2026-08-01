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
            return e.code, {'error': str(e)}
    except Exception as e:
        return None, {'error': str(e)}

# GET tree
status, tree = req(BASE, 'GET')
print('GET status', status)
if status != 200:
    print('GET failed', tree)
    raise SystemExit(1)

root_obj = tree.get('root')
roots = []
if isinstance(root_obj, dict):
    roots = root_obj.get('roots', [])
print('roots count', len(roots))

if not roots:
    # create a root
    payload = {'type':'project','name':'AutoRoot','parent_id':None,'tool_policy':{},'config_overrides':{},'metadata':{}}
    status, created = req(BASE, 'POST', payload)
    print('create root status', status)
    if status not in (200,201):
        print('create root failed', created)
        raise SystemExit(1)
    parent_id = created['id']
    print('created root', parent_id)
else:
    parent_id = roots[0]['id']
    print('using existing root', parent_id)

# create child
payload = {'type':'project','name':'child-for-tests','parent_id':parent_id,'tool_policy':{},'config_overrides':{},'metadata':{}}
status, created = req(BASE, 'POST', payload)
print('create child status', status)
if status not in (200,201):
    print('create child failed', created)
    raise SystemExit(1)
child_id = created['id']
print('child id', child_id)

# PATCH
patch_payload = {'name':'child-for-tests-patched'}
status, patched = req(f"{BASE}/{child_id}", 'PATCH', patch_payload)
print('PATCH status', status)
print('patched name', patched.get('name'))

# MOVE to root (null parent)
move_payload = {'new_parent_id': None}
status, moved = req(f"{BASE}/{child_id}/move", 'POST', move_payload)
print('MOVE status', status)
print('moved parent_id', moved.get('parent_id'))

# DELETE
status, deleted = req(f"{BASE}/{child_id}", 'DELETE')
print('DELETE status', status)

# Verify deletion
status, after = req(BASE, 'GET')
print('GET after', status)
found = False
root_obj = after.get('root')
if isinstance(root_obj, dict):
    def search_nodes(nodes, nid):
        for n in nodes:
            if n.get('id') == nid:
                return True
            if search_nodes(n.get('children', []), nid):
                return True
        return False
    if search_nodes(root_obj.get('roots', []), child_id):
        found = True
print('found after delete?', found)
print('Done')
