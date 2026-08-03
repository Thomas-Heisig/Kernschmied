#!/usr/bin/env python3
"""Fix Markdown link target casing under documentation/.

Usage:
  python scripts/fix_doc_link_casing.py [--apply]

Finds markdown links like [text](path/ToFile.md) and if the target does not
exist exactly but a case-insensitive match exists on disk, it updates the
link to the real filename. Runs a dry-run by default.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path.cwd() / "documentation"
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def find_real_path(base: Path, target: str) -> Path | None:
    # ignore absolute URLs
    if target.startswith("http://") or target.startswith("https://"):
        return None
    # strip any anchor or query
    t = target.split('#', 1)[0].split('?', 1)[0]
    parent_rel = Path(t).parent
    name = Path(t).name
    parent = (base.parent / parent_rel).resolve()
    if not parent.exists():
        return None
    # find any entry matching case-insensitively
    for p in parent.iterdir():
        if p.name.lower() == name.lower():
            # if names differ in case, return the correct-cased relative path
            if p.name != name:
                rel = (parent_rel / p.name).as_posix() if str(parent_rel) != '.' else p.name
                return Path(rel)
            else:
                return None
    return None


def scan_and_fix(apply: bool = False) -> int:
    changed = 0
    for md in ROOT.rglob('*.md'):
        text = md.read_text(encoding='utf-8')
        new_text = text
        for m in LINK_RE.finditer(text):
            target = m.group(2)
            real = find_real_path(md, target)
            if real:
                # replace only the target part
                new_target = str(real)
                new_text = new_text.replace(f"]({target})", f"]({new_target})")
                print(f"Will update: {md} -> {target}  ->  {new_target}")
                changed += 1
        if apply and new_text != text:
            md.write_text(new_text, encoding='utf-8')
    return changed


if __name__ == '__main__':
    apply = '--apply' in sys.argv[1:]
    print(f"Scanning documentation/ (apply={apply})")
    n = scan_and_fix(apply=apply)
    print(f"Found {n} potential updates.")
    if apply and n:
        print('You should git add & commit the changes.')
