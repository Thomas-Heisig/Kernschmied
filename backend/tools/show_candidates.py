import json
p='f:/Kernschmied/artifacts/config-inventory.json'
with open(p,encoding='utf-8') as f:
    data=json.load(f)
for it in data:
    if it['config'] in ('models.default_model','models.max_output_tokens','chat.system_prompt'):
        print('\nCONFIG:',it['config'])
        print('default:',it.get('default_value'))
        print('mentioned in',len(it.get('files_where_mentioned',[])),'files')
        for f in it.get('files_where_mentioned',[]):
            print(' -',f)
