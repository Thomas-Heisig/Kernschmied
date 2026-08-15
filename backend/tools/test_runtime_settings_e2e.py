#!/usr/bin/env python3
"""E2E script: update settings via ConfigService API and call ChatService endpoints.
Requires running backend locally.
"""
import requests
import time

BASE = "http://127.0.0.1:8000"

def set_config(group, key, value):
    url = f"{BASE}/api/v1/admin/config/set"
    resp = requests.post(url, json={"group": group, "key": key, "value": value})
    print(resp.status_code, resp.text)
    return resp

def send_chat(message, model_id=None):
    url = f"{BASE}/api/v1/chat/stream"
    payload = {"message": message}
    if model_id is not None:
        payload["model_id"] = model_id
    r = requests.post(url, json=payload, stream=True)
    print('status', r.status_code)
    for i, line in enumerate(r.iter_lines()):
        if line:
            print(line.decode())
        if i > 10:
            break

if __name__ == '__main__':
    set_config('models','max_output_tokens',1111)
    time.sleep(1)
    send_chat('Hello world')
    set_config('models','max_output_tokens',2222)
    time.sleep(1)
    send_chat('Hello world again')
