"""Basic link checker for documentation/ (skeleton).

Extend with markdown parsing, internal/external link checks, and image existence.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "documentation"


def find_links(text):
    # naive markdown link finder [text](target)
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def main():
    for md in DOCS.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for link in find_links(text):
            if link.startswith("http"):
                continue
            # relative link
            target = (md.parent / link).resolve()
            if not target.exists():
                print("Broken link in", md, "->", link)


if __name__ == "__main__":
    main()
