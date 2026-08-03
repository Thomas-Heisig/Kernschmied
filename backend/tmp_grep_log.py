import sys
p = r'F:/Kernschmied/artifacts/logs/backend-20260803_174043.log'
with open(p, 'rb') as f:
    data = f.read()
try:
    text = data.decode('utf-8')
except Exception:
    try:
        text = data.decode('utf-16')
    except Exception:
        text = data.decode('latin-1')

for line in text.splitlines():
    if 'Ollama chat payload prepared' in line or 'system_message_count' in line or 'Ollama' in line:
        print(line)
