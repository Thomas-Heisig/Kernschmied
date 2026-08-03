#!/usr/bin/env python3
"""Validate documentation/ against manifest.json and basic rules.

This is a minimal starter script. It should be extended with the checks described in the project plan.
"""
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "documentation"


def load_manifest():
    mf = DOCS / "manifest.json"
    if not mf.exists():
        print("manifest.json not found", file=sys.stderr)
        return None
    return json.loads(mf.read_text(encoding="utf-8"))


def main():
    manifest = load_manifest()
    if manifest is None:
        return 2
    # Basic validation: check that listed files exist
    missing = []
    for sec in manifest.get("sections", []):
        for p in sec.get("pages", []):
            f = DOCS / p["file"]
            if not f.exists():
                missing.append(str(p["file"]))
    if missing:
        print("Missing pages:")
        for m in missing:
            print(" -", m)
        return 1
    print("Manifest OK — all listed pages exist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
