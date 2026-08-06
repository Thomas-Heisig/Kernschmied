import sys

fname = "app/services/settings_catalog.py"
stack: list[tuple[int, int, str]] = []
with open(fname, encoding="utf-8") as f:
    for i, line in enumerate(f, start=1):
        for j, ch in enumerate(line, start=1):
            if ch == "(":
                stack.append((i, j, line.strip()))
            elif ch == ")":
                if stack:
                    stack.pop()
                else:
                    print(f"Unmatched ) at line {i} col {j}")
                    sys.exit(0)
if stack:
    print("Unmatched ( count", len(stack))
    line_no, col, text = stack[-1]
    print(f"Top unmatched at line {line_no}, col {col}: {text}")
else:
    print("All matched")
