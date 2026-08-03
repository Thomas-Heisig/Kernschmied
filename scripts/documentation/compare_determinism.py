import json
import sys
from pathlib import Path

BASE = Path('artifacts/documentation')
A = BASE / 'documentation-inventory.json'
B = BASE / 'documentation-inventory.csv'
C = BASE / 'documentation-duplicates.json'
D = BASE / 'documentation-migration-plan.md'
E = BASE / 'documentation-summary.json'

# load files from current run and from determinism-run-1
RUN1 = BASE / 'determinism-run-1'

files = [A.name, B.name, C.name, D.name, E.name]
results = {}

for name in files:
    cur = BASE / name
    old = RUN1 / name
    if not old.exists():
        results[name] = ('missing-run1', None)
        continue
    if name.endswith('.json'):
        a = json.loads(cur.read_text(encoding='utf-8'))
        b = json.loads(old.read_text(encoding='utf-8'))
        if name == 'documentation-summary.json':
            a.pop('generated_at', None)
            b.pop('generated_at', None)
        identical = a == b
        results[name] = ('identical' if identical else 'different', None)
    else:
        # md or csv: compare normalized text
        ta = cur.read_text(encoding='utf-8').replace('\r\n','\n')
        tb = old.read_text(encoding='utf-8').replace('\r\n','\n')
        identical = ta == tb
        if not identical:
            # produce first differing line
            la = ta.split('\n')
            lb = tb.split('\n')
            for i,(xa,xb) in enumerate(zip(la,lb)):
                if xa!=xb:
                    results[name] = ('different', (i+1, xa, xb))
                    break
            else:
                if len(la)!=len(lb):
                    results[name] = ('different', ('length', len(la), len(lb)))
                else:
                    results[name] = ('different', ('unknown', None, None))
        else:
            results[name] = ('identical', None)

for k,v in results.items():
    state, info = v
    if state=='identical':
        print(f"{k}: identical")
    elif state=='missing-run1':
        print(f"{k}: missing-run1")
    else:
        print(f"{k}: different")
        if info:
            print(f" first diff: {info}")

# exit 0 if all identical
if all(v[0]=='identical' for v in results.values()):
    sys.exit(0)
else:
    sys.exit(2)
