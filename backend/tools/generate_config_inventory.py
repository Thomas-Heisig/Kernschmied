"""Generiere ein Inventar aller Config-Definitionen und einfache Abgleiche

Schreibt `artifacts/config-inventory.json` mit einer Liste von Einträgen:
 - group.key
 - default_value (aus definitions.py)
 - files_where_mentioned (einfache Textsuche nach group/key Verwendung)
 - code_defaults_files (Dateien mit "DEFAULT_" Vorkommen)

Dieses Skript ist bewusst einfach und heuristisch; es hilft bei Phase-1
der Konfigurations-Aufräumarbeit.
"""

from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFINITIONS = REPO_ROOT / "backend" / "app" / "config" / "definitions.py"
OUT = REPO_ROOT / "artifacts" / "config-inventory.json"


def load_definitions(path: Path) -> list[dict[str, Any]]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    entries: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr

            if name == "config_definition":
                group = None
                key = None
                default_value = None
                for kw in node.keywords:
                    if kw.arg == "group":
                        try:
                            group = ast.literal_eval(kw.value)
                        except Exception:
                            group = None
                    if kw.arg == "key":
                        try:
                            key = ast.literal_eval(kw.value)
                        except Exception:
                            key = None
                    if kw.arg == "default_value":
                        try:
                            default_value = ast.literal_eval(kw.value)
                        except Exception:
                            # fallback: record source snippet
                            default_value = ast.get_source_segment(src, kw.value)

                if group is not None and key is not None:
                    entries.append(
                        {
                            "group": str(group),
                            "key": str(key),
                            "default_value": default_value,
                        }
                    )

    return entries


def search_usages(group: str, key: str) -> list[str]:
    pattern1 = f'get_required("{group}", "{key}")'
    pattern2 = f'get("{group}", "{key}"'
    pattern3 = f"get_required('{group}', '{key}')"
    pattern4 = f"get('{group}', '{key}'"

    matches: set[str] = set()
    for p in REPO_ROOT.rglob("**/*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if pattern1 in txt or pattern2 in txt or pattern3 in txt or pattern4 in txt:
            matches.add(str(p.relative_to(REPO_ROOT)))

    return sorted(matches)


def find_code_default_files() -> list[str]:
    matches: set[str] = set()
    for p in REPO_ROOT.rglob("**/*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "DEFAULT_" in txt:
            matches.add(str(p.relative_to(REPO_ROOT)))
    return sorted(matches)


def extract_constant_value(name: str) -> Any:
    # simple regex scan for assignments like NAME = value
    for p in REPO_ROOT.rglob("**/*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        m = re.search(rf"\b{name}\s*=\s*(.+)", txt)
        if m:
            expr = m.group(1).strip()
            # strip trailing comments
            expr = expr.split("#")[0].strip()
            # try literal eval
            try:
                val = ast.literal_eval(expr)
                return val
            except Exception:
                return expr
    return None


def main() -> None:
    items = load_definitions(DEFINITIONS)
    code_default_files = find_code_default_files()

    # constants of interest
    constants = [
        "DEFAULT_CHAT_MAX_OUTPUT_TOKENS",
        "DEFAULT_CHAT_TEMPERATURE",
        "DEFAULT_MODEL_ID",
        "DEFAULT_CHAT_STREAM_IDLE_TIMEOUT_SECONDS",
    ]
    const_values = {c: extract_constant_value(c) for c in constants}

    result = []
    for it in items:
        group = it["group"]
        key = it["key"]
        full = f"{group}.{key}"
        usages = search_usages(group, key)

        divergence = False
        # heuristic divergences
        if full in ("models.max_output_tokens", "models.default_model", "chat.system_prompt"):
            divergence = True

        result.append(
            {
                "config": full,
                "group": group,
                "key": key,
                "default_value": it.get("default_value"),
                "files_where_mentioned": usages,
                "code_defaults_files": code_default_files,
                "detected_constants": const_values,
                "divergence_flag": divergence,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
