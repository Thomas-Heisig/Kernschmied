p='artifacts/logs/backend-20260810_160708.log'
with open(p,'rb') as f:
    data=f.read()
try:
    txt=data.decode('utf-16')
except Exception:
    try:
        txt=data.decode('utf-8')
    except Exception:
        txt=str(data[-4000:])

print('\n'.join(txt.splitlines()[-200:]))
