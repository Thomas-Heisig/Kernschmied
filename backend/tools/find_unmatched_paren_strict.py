import sys

fname = "app/services/settings_catalog.py"
stack: list[tuple[int, int, str]] = []
with open(fname, encoding="utf-8") as f:
    in_single = False
    in_double = False
    in_triple_single = False
    in_triple_double = False
    prev_char = ""
    for i, line in enumerate(f, start=1):
        j = 0
        while j < len(line):
            ch = line[j]
            # handle triple quotes
            if not (in_single or in_double or in_triple_single or in_triple_double):
                if line.startswith("'''", j):
                    in_triple_single = True
                    j += 3
                    continue
                if line.startswith('"""', j):
                    in_triple_double = True
                    j += 3
                    continue
            else:
                if in_triple_single and line.startswith("'''", j):
                    in_triple_single = False
                    j += 3
                    continue
                if in_triple_double and line.startswith('"""', j):
                    in_triple_double = False
                    j += 3
                    continue
            if not (in_triple_single or in_triple_double):
                if not (in_single or in_double):
                    if ch == "'":
                        in_single = True
                        j += 1
                        continue
                    if ch == '"':
                        in_double = True
                        j += 1
                        continue
                else:
                    if in_single and ch == "'":
                        in_single = False
                        j += 1
                        continue
                    if in_double and ch == '"':
                        in_double = False
                        j += 1
                        continue
            # ignore comments
            if not (in_single or in_double or in_triple_single or in_triple_double):
                if ch == "#":
                    break
                if ch == "(":
                    stack.append((i, j + 1, line.rstrip("\n")))
                elif ch == ")":
                    if stack:
                        stack.pop()
                    else:
                        print("Unmatched ) at", i, j + 1)
                        sys.exit(0)
            j += 1
if stack:
    print("Unmatched ( count", len(stack))
    for item in stack[-5:]:
        line_no, col, text = item
        print(f"Unmatched at line {line_no} col {col}: {text}")
else:
    print("All matched")
