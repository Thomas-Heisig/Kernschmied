import json
import urllib.request

url = 'http://127.0.0.1:8000/api/v1/hierarchy'
with open('payload.json','rb') as f:
    data = f.read()
req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(resp.status)
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print('HTTP_ERROR', e.code)
    print(e.read().decode())
except Exception as e:
    print('ERROR', e)
