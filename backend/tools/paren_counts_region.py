def paren_counts_region(fname: str, start: int, end: int) -> None:
    count = 0
    with open(fname, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if i < start:
                continue
            if i > end:
                break
            # naive counting
            for ch in line:
                if ch == "(":
                    count += 1
                elif ch == ")":
                    count -= 1
            print(i, count, line.rstrip())


if __name__ == "__main__":
    paren_counts_region("app/services/settings_catalog.py", 3350, 3590)
