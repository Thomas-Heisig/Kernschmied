"""Export documentation/ to a GitHub Wiki-friendly folder layout.

Writes into `artifacts/documentation/github-wiki` and produces a JSON export report.
The export is conservative: only pages marked as `published` in the manifest are exported.
"""
import json
from pathlib import Path
import shutil
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "documentation"
BUILD = ROOT / "artifacts" / "documentation" / "github-wiki"
REPORT = ROOT / "artifacts" / "documentation" / "github-wiki-export.json"


def build_sidebar(manifest: Dict[str, Any]) -> str:
    lines = []
    for sec in manifest.get("sections", []):
        lines.append(f"## {sec.get('title')}")
        for p in sec.get("pages", []):
            if p.get("status") != "published":
                continue
            fname = Path(p["file"]).name
            lines.append(f"- [{p.get('title')}]({fname})")
    return "\n".join(lines)


def normalize_link(link: str) -> str:
    # For now: strip fragment and return basename
    return Path(link.split('#')[0]).name


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    mf = DOCS / "manifest.json"
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    exported = []
    errors = []

    sidebar = build_sidebar(manifest)
    (BUILD / "_Sidebar.md").write_text(sidebar, encoding="utf-8")

    footer_src = DOCS / "_Footer.md"
    if footer_src.exists():
        shutil.copy2(footer_src, BUILD / "_Footer.md")

    home = DOCS / "Home.md"
    if home.exists():
        shutil.copy2(home, BUILD / "Home.md")

    # copy published pages
    for sec in manifest.get("sections", []):
        for p in sec.get("pages", []):
            status = p.get("status", "unknown")
            src = DOCS / p.get("file", "")
            if status != "published":
                continue
            if not src.exists():
                errors.append({"file": p.get("file"), "error": "missing"})
                continue
            # copy to build root with basename
            dst = BUILD / Path(p.get("file")).name
            shutil.copy2(src, dst)
            exported.append(str(dst.relative_to(ROOT)))

    # produce report
    report = {
        "exported_files": exported,
        "errors": errors,
        "build_path": str(BUILD.relative_to(ROOT)),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Export complete. Report:", REPORT)


if __name__ == "__main__":
    main()
