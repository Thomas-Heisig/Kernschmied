import sys, pkgutil, importlib
sys.path.insert(0, 'backend')
mod = importlib.import_module('app.api.v1')
names = [m.name for m in pkgutil.walk_packages(mod.__path__)]
print('modules:', names)
ok = True
for name in names:
    full = 'app.api.v1.' + name
    try:
        importlib.import_module(full)
        print('imported', full)
    except Exception as e:
        print('FAILED', full, e)
        ok = False
if ok:
    print('all imports ok')
