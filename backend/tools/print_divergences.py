import json
p='f:/Kernschmied/artifacts/config-inventory.json'
with open(p,encoding='utf-8') as f:
    data=json.load(f)
for it in data:
    if it.get('divergence_flag'):
        print(it['config'], ' default=', it.get('default_value'), ' mentions=', len(it.get('files_where_mentioned',[])))
