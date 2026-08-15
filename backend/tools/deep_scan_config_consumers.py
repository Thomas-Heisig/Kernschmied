#!/usr/bin/env python3
"""Deep scan for config consumer call-sites for selected keys.
Generates artifacts/config-consumers-top3.json and .md
"""
import re
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
OUT_JSON = REPO_ROOT / "artifacts" / "config-consumers-top3.json"
OUT_MD = REPO_ROOT / "artifacts" / "config-consumers-top3.md"

KEYS = [
    "models.default_model",
    "models.max_output_tokens",
    "chat.system_prompt",
]

# for each key, compile regex patterns to find likely callsites
PATTERNS = {
    "models.default_model": [
        re.compile(r"models\.default_model"),
        re.compile(r"get\(\s*['\"]models['\"]\s*,\s*['\"]default_model['\"]\s*\)"),
        re.compile(r"get_required\(\s*['\"]models['\"]\s*,\s*['\"]default_model['\"]\s*\)"),
    ],
    "models.max_output_tokens": [
        re.compile(r"models\.max_output_tokens"),
        re.compile(r"get\(\s*['\"]models['\"]\s*,\s*['\"]max_output_tokens['\"]\s*\)"),
        re.compile(r"get_required\(\s*['\"]models['\"]\s*,\s*['\"]max_output_tokens['\"]\s*\)"),
    ],
    "chat.system_prompt": [
        re.compile(r"chat\.system_prompt"),
        re.compile(r"get\(\s*['\"]chat['\"]\s*,\s*['\"]system_prompt['\"]\s*\)"),
        re.compile(r"get_required\(\s*['\"]chat['\"]\s*,\s*['\"]system_prompt['\"]\s*\)"),
        re.compile(r"get_system_prompt\(|get_system_prompt\b"),
    ],
}

EXCLUDE_DIRS = {"venv", ".venv", "node_modules"}
FILE_EXT = (".py", ".ini", ".yaml", ".yml", ".json", ".toml")


def scan():
    results = {k: [] for k in KEYS}
    for root, dirs, files in __import__('os').walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            if not fn.endswith(FILE_EXT):
                continue
            fp = Path(root) / fn
            rel = str(fp.relative_to(REPO_ROOT)).replace('\\','/')
            try:
                text = fp.read_text(encoding='utf-8')
            except Exception:
                continue
            lines = text.splitlines()
            for i, line in enumerate(lines, start=1):
                for key in KEYS:
                    for pat in PATTERNS[key]:
                        if pat.search(line):
                            # capture snippet: line +/-2
                            start = max(0, i-3)
                            end = min(len(lines), i+2)
                            snippet = '\n'.join(lines[start:end])
                            results[key].append({
                                "file": rel,
                                "line": i,
                                "snippet": snippet,
                            })
                            break
    return results


def write(results):
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')

    md_lines = ["# Config Consumers Top3\n\n"]
    for k in KEYS:
        md_lines.append(f"## {k}\n\n")
        items = results.get(k, [])
        if not items:
            md_lines.append("No matches found.\n\n")
            continue
        md_lines.append(f"Matches: {len(items)}\n\n")
        # show first 10
        for it in items[:20]:
            md_lines.append(f"- File: {it['file']}  (line {it['line']})\n")
            md_lines.append("```")
            md_lines.append(it['snippet'])
            md_lines.append("```\n")
    OUT_MD.write_text('\n'.join(md_lines), encoding='utf-8')


if __name__ == '__main__':
    res = scan()
    write(res)
    print('Wrote', OUT_JSON, OUT_MD)
