#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path.cwd() / "documentation"

FENCE_RE = re.compile(r"(^```)(\s*)(\n|$)", re.MULTILINE)
FENCE_BLOCK_RE = re.compile(r"^```\n(.*?)\n```", re.DOTALL | re.MULTILINE)

def guess_language(snippet: str) -> str | None:
    s = snippet.strip()
    if not s:
        return None
    first = s.splitlines()[0].lstrip()
    if first.startswith('{') or first.startswith('[') or first.startswith('"'):
        return 'json'
    if first.startswith('---') or ':' in first.splitlines()[0] and '\n' in s[:200]:
        return 'yaml'
    if first.startswith('<') and (first.startswith('<!DOCTYPE') or first.startswith('<html') or first.startswith('<div')):
        return 'html'
    if first.startswith('$') or first.startswith('PS ') or 'Get-' in s or 'Set-' in s:
        return 'powershell'
    if first.startswith('#!') or first.startswith('import ') or 'const ' in s.splitlines()[0] or 'function ' in s[:200]:
        return 'bash'
    # heuristics for openapi/json-like
    if 'openapi:' in s[:200] or 'paths:' in s[:200]:
        return 'yaml'
    return None


def process_file(path: Path, apply: bool = False) -> int:
    text = path.read_text(encoding='utf-8')
    changed = 0

    # find fences without language: ```\n...\n```
    def replace(match):
        nonlocal changed
        start = match.start()
        # find the closing fence
        rest = text[start:]
        mblock = re.match(r"```\n(.*?)\n```", rest, re.DOTALL)
        if not mblock:
            return match.group(0)
        snippet = mblock.group(1)
        lang = guess_language(snippet)
        if lang:
            changed += 1
            return f"```{lang}\n"
        return match.group(0)

    new_text = re.sub(r"^```\n", lambda m: replace(m), text, flags=re.MULTILINE)

    if changed and apply:
        path.write_text(new_text, encoding='utf-8')

    return changed


def main():
    apply = '--apply' in sys.argv[1:]
    total = 0
    for md in ROOT.rglob('*.md'):
        c = process_file(md, apply=apply)
        if c:
            print(f"{md}: will add {c} language tag(s)")
        total += c
    print(f"Total fenced code languages to add: {total} (apply={apply})")
    if apply and total:
        print("Files updated. Run git add & commit to record changes.")


if __name__ == '__main__':
    main()
