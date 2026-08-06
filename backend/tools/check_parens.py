import sys

popen = open("app/services/settings_catalog.py", encoding="utf-8")
count = 0
for i, line in enumerate(popen, start=1):
    for ch in line:
        if ch == "(":
            count += 1
        elif ch == ")":
            count -= 1
    if count < 0:
        print("More ) than ( at line", i)
        sys.exit(0)
print("Final count", count)
if count > 0:
    # find last lines
    popen.seek(0)
    s = 0
    last = None
    for i, line in enumerate(popen, start=1):
        for ch in line:
            if ch == "(":
                s += 1
            elif ch == ")":
                s -= 1
        if s == 0:
            last = i

    if last is not None:
        print("First balanced at line", last)
    else:
        print("No balanced point found")
