import requests

urls = [
    'http://127.0.0.1:8000/api/v1/models/providers',
    'http://127.0.0.1:8000/api/v1/models?provider=ollama&capability=chat',
    'http://127.0.0.1:8000/api/v1/config',
]

for u in urls:
    try:
        r = requests.get(u, timeout=5)
        print(u, '->', r.status_code)
        try:
            print(r.json())
        except Exception as e:
            print('no json:', e)
    except Exception as e:
        print(u, 'ERROR', e)
