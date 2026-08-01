import json,urllib.request,sys
url='http://127.0.0.1:8000/api/v1/hierarchy'
payload={'type':'project','name':'RootFromInline','parent_id':None,'tool_policy':{},'config_overrides':{},'metadata':{}}
req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(resp.status)
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print('HTTP_ERROR', e.code)
    try:
        print(e.read().decode())
    except:
        pass
except Exception as e:
    print('ERROR', e)
    sys.exit(1)
