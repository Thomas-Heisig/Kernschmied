#!/usr/bin/env python3
"""Enrich config inventory with simple codebase consumer detection and produce a summary.

Writes:
- artifacts/config-effectiveness.json
- artifacts/config-effectiveness-summary.md

Heuristics:
- Search for exact key occurrences (group.key) in backend/ files (excluding venv).
- If found, mark as 'wired'. If referenced in definitions.py, include definition lines.
"""
import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "artifacts" / "config-effectiveness.json"
SUMMARY = REPO_ROOT / "artifacts" / "config-effectiveness-summary.md"
INVENTORY = REPO_ROOT / "artifacts" / "config-inventory.json"
BACKEND_DIR = REPO_ROOT / "backend"

EXCLUDE_DIRS = {"venv", ".venv", "node_modules"}


def scan_for_key(key: str) -> list[str]:
    """Return list of backend file paths that mention the key."""
    matches = []
    pattern = re.escape(key)
    for root, dirs, files in os.walk(BACKEND_DIR):
        # skip venvs
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            if not fn.endswith((".py", ".ini", ".yaml", ".yml", ".json", ".toml")):
                continue
            fp = Path(root) / fn
            try:
                text = fp.read_text(encoding="utf-8")
            except Exception:
                continue
            if re.search(pattern, text):
                matches.append(str(fp.relative_to(REPO_ROOT)).replace('\\', '/'))
    return matches


def read_definitions_snippet(config_group: str, config_key: str) -> list[str]:
    defs = BACKEND_DIR / "app" / "config" / "definitions.py"
    if not defs.exists():
        return []
    try:
        text = defs.read_text(encoding="utf-8")
    except Exception:
        return []
    snippets = []
    # naive search for key="<key>" near group declaration
    pattern = rf"\bkey\s*=\s*\"{re.escape(config_key)}\""
    for m in re.finditer(pattern, text):
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 200)
        snippets.append(text[start:end].replace('\n', ' '))
        if len(snippets) >= 3:
            break
    return snippets


def main():
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    enriched = []
    wired_count = 0
    divergence = []
    for entry in inv:
        cfg = entry.get("config") or f"{entry.get('group')}.{entry.get('key')}"
        group = entry.get("group")
        key = entry.get("key")
        consumers = scan_for_key(cfg)
        definition_snippets = read_definitions_snippet(group, key)
        status = "UNWIRED"
        if consumers:
            status = "WIRED"
            wired_count += 1
        if entry.get("divergence_flag"):
            divergence.append(cfg)
        enriched_entry = {
            **entry,
            "consumers": consumers,
            "definition_snippets": definition_snippets,
            "effectiveness_status": status,
        }
        enriched.append(enriched_entry)

    summary_lines = [
        "# Config Effectiveness Summary\n",
        f"Total entries: {len(enriched)}\n",
        f"Wired (found consumers): {wired_count}\n",
        "\n",
        "## Top divergence candidates\n",
    ]
    # highlight specific keys of interest if present
    priority = [
        "models.default_model",
        "models.max_output_tokens",
        "chat.system_prompt",
    ]
    for p in priority:
        found = [e for e in enriched if e.get("config") == p]
        if found:
            e = found[0]
            summary_lines.append(f"- {p}: status={e.get('effectiveness_status')}, consumers={len(e.get('consumers', []))}\n")
        else:
            summary_lines.append(f"- {p}: NOT FOUND IN INVENTORY\n")

    # list first 20 divergence flagged
    if divergence:
        summary_lines.append("\n## Divergence flagged entries (sample)\n")
        for d in divergence[:20]:
            summary_lines.append(f"- {d}\n")

    # write outputs
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    SUMMARY.write_text("".join(summary_lines), encoding="utf-8")
    print("Wrote:", ARTIFACT, SUMMARY)


if __name__ == "__main__":
    main()
