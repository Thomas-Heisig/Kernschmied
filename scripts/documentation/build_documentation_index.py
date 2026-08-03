"""Inventory documentation files and build reports.

Produces:
 - artifacts/documentation/documentation-inventory.json
 - artifacts/documentation/documentation-inventory.csv
 - artifacts/documentation/documentation-duplicates.json
 - artifacts/documentation/documentation-migration-plan.md

This script collects metadata for documentation-related files and performs
duplicate detection and a conservative migration plan. It is intentionally
conservative: when unsure it sets `category = unknown` and `migration_action = review`.
"""
import csv
import hashlib
import json
import os
import re
from pathlib import Path
from typing import List, Dict
from difflib import SequenceMatcher


# Allow tests to override the repository root via env var
ROOT = Path(os.environ.get("DOCUMENTATION_SCAN_ROOT") or Path(__file__).resolve().parents[2])
DOCS = ROOT / "documentation"
ARTIFACTS = ROOT / "artifacts" / "documentation"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


MARKDOWN_EXT = {".md", ".markdown", ".mdx", ".rst", ".adoc"}

# Allowed text-based doc extensions
ALLOWED_TEXT_EXT = {".md", ".markdown", ".mdx", ".rst", ".txt", ".adoc", ".json", ".yml", ".yaml", ".toml"}

# Allowed binary/documentation asset extensions (only when under documentation/docs/wiki paths)
ALLOWED_BINARY_EXT = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".pdf", ".puml", ".mmd", ".mermaid", ".drawio"}

# Paths and names to exclude entirely from scanning
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    ".cache",
    ".vscode",
    ".idea",
    "tmp",
    "temp",
    # repo-specific
    "artifacts/documentation/github-wiki",
}

# File patterns to exclude
EXCLUDED_FILE_PATTERNS = ("*.pyc", "*.pyo", "*.log", "*.lock", "*.sqlite", "*.sqlite3", "*.db", "*.map", "*.min.js", "*.min.css", "package-lock.json", "npm-debug.log")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_headings(text: str) -> List[str]:
    return re.findall(r"^#{1,6}\s+(.*)$", text, flags=re.MULTILINE)


def find_links(text: str) -> List[str]:
    # find markdown links [text](target)
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    return links


def find_image_links(text: str) -> List[Dict[str, str]]:
    # ![alt](path)
    imgs = []
    for m in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text):
        imgs.append({"alt": m[0].strip(), "path": m[1].strip()})
    return imgs


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        # Fallback: try with errors='replace' to avoid crashes on bad encodings
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            try:
                return path.read_text(encoding="latin-1", errors="ignore")
            except Exception:
                print(f"Warning: failed to read {path}: {e}")
                return ""


def classify(path: Path) -> (str, str, str):
    """Return (category, publication_status, migration_action).

    Conservative defaults: unknown / unknown / review
    Apply deterministic assignments for well-known files and documentation/.
    """
    name = path.name.lower() if isinstance(path, Path) else str(path).lower()
    parts = [p.lower() for p in path.parts] if isinstance(path, Path) else []
    # Defaults
    category = "unknown"
    publication_status = "unknown"
    migration_action = "review"

    # Repository-level known files
    if name in ("changelog.md",):
        category = "changelog"
        publication_status = "published"
        migration_action = "move"
    if name in ("contributing.md",):
        category = "contributing"
        publication_status = "published"
        migration_action = "move"
    if name in ("security.md",):
        category = "security"
        publication_status = "published"
        migration_action = "move"
    if name.startswith("readme") or name.endswith("readme.md"):
        category = "repository-entry"
        publication_status = "published"
        migration_action = "keep"
    if name in ("support.md",):
        category = "unknown"
        publication_status = "published"
        migration_action = "move"

    # Files already in documentation/ -> likely canonical
    if "documentation" in parts:
        publication_status = "published"
        migration_action = "keep"
        # try to infer category from deeper path
        if "architecture" in parts:
            category = "architecture"
        elif "api" in parts or "openapi" in name:
            category = "api"
        elif "user-guide" in parts or "user-guide" in str(path.parent):
            category = "user-guide"
        elif "administration" in parts or "admin" in parts:
            category = "administrator-guide"
        elif "adr" in parts or "adrs" in parts:
            category = "decision-record"
        elif category == "unknown":
            category = "repository-entry"

    # docs/ and wiki/ are uncertain -> review; attempt stronger heuristics
    if "docs" in parts or "wiki" in parts:
        publication_status = "unknown"
        migration_action = "review"
        # detect common subfolders
        if "architecture" in parts:
            category = "architecture"
        elif "api" in parts:
            category = "api"
        elif "user-manual" in parts or "user-manual" in str(path.parent) or "user-guide" in parts:
            category = "user-guide"
        elif "work-documents" in parts or "work-in-progress" in parts:
            category = "internal-work"

    # generated patterns
    if name.lower().endswith('.txt') and ("file_tree" in name or "frontend-current" in name):
        category = "generated"
        publication_status = "generated"
        migration_action = "archive"
    if "artifacts" in parts:
        category = "generated"
        publication_status = "generated"
        migration_action = "archive"

    return category, publication_status, migration_action


def scan_files() -> List[Dict]:
    files = []
    # Build an explicit crawl list to limit scope
    start_files = [
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        ROOT / "SUPPORT.md",
        ROOT / "LICENSE",
    ]
    start_dirs = [
        ROOT / "documentation",
        ROOT / "docs",
        ROOT / "wiki",
        ROOT / ".github",
        ROOT / "scripts" / "documentation",
        ROOT / "backend",
        ROOT / "frontend",
    ]

    seen = set()

    def add_file(p: Path):
        # only add regular files
        if not p.exists() or not p.is_file():
            return
        # compute path relative to ROOT when possible
        try:
            rel = p.relative_to(ROOT)
        except Exception:
            rel = None
        rel_str = str(rel).replace('\\', '/').lower() if rel else str(p).lower()

        # exclude by excluded dir names or explicit substrings
        if rel:
            rel_parts = [part.lower() for part in rel.parts]
            for ex in EXCLUDED_DIRS:
                ex_l = ex.lower()
                if '/' in ex_l or '\\' in ex_l:
                    # explicit path substring match
                    if ex_l in rel_str:
                        return
                else:
                    # match whole path segment only
                    if ex_l in rel_parts:
                        return

        # exclude by filename patterns
        for pat in EXCLUDED_FILE_PATTERNS:
            if p.name.lower().endswith(pat.replace('*', '')):
                return

        if not rel:
            return

        # prevent duplicates
        rels = rel_str
        if rels in seen:
            return
        seen.add(rels)

        ext = p.suffix.lower()
        # binary assets only if under docs/wiki/documentation
        allowed = False
        if ext in ALLOWED_TEXT_EXT:
            allowed = True
        elif ext in ALLOWED_BINARY_EXT:
            parts = [pp.lower() for pp in rel.parts]
            if any(x in parts for x in ("documentation", "docs", "wiki")):
                allowed = True

        # special-case: frontend/public may contain external html/templates — capture as external-content
        if rel_str.startswith('frontend/public'):
            allowed = True

        if not allowed:
            return

        text = read_text_safe(p) if ext in ALLOWED_TEXT_EXT else ""
        headings = extract_headings(text) if text else []
        links = find_links(text) if text else []
        imgs = find_image_links(text) if text else []
        sha = sha256_file(p)
        size = p.stat().st_size
        title = headings[0] if headings else (p.stem.replace('-', ' ').replace('_', ' ').title())
        category, pub_status, mig = classify(rel)
        note = ""

        # detect external content in frontend/public
        if rel_str.startswith('frontend/public'):
            category = 'generated'
            pub_status = 'internal'
            mig = 'review'
            note = 'Fremdinhalt, nicht Teil der Kernschmied-Dokumentation'

        files.append({
            "path": rels,
            "filename": p.name,
            "extension": p.suffix,
            "size_bytes": size,
            "sha256": sha,
            "title": title,
            "first_heading": headings[0] if headings else "",
            "heading_count": len(headings),
            "relative_links": [l for l in links if not l.startswith(('http://', 'https://', 'mailto:'))],
            "image_links": imgs,
            "external_links": [l for l in links if l.startswith(('http://', 'https://'))],
            "referenced_by": [],
            "category": category,
            "publication_status": pub_status,
            "migration_action": mig,
            "target_path": "",
            "duplicate_group": "",
            "notes": note,
        })

    # Add explicit files
    for sf in start_files:
        add_file(sf)

    # Walk allowed directories with filtering
    for sd in start_dirs:
        if not sd.exists():
            continue
        # backend/frontend: restrict to relevant extensions and files referencing docs
        if sd.name in ("backend", "frontend"):
            for p in sd.rglob("**/*"):
                if p.is_file():
                    ext = p.suffix.lower()
                    # include frontend/public files regardless of extension (external assets/templates)
                    try:
                        rel_to_sd = p.relative_to(sd)
                    except Exception:
                        rel_to_sd = p
                    if sd.name == 'frontend' and any(part.lower() == 'public' for part in rel_to_sd.parts):
                        add_file(p)
                        continue
                    # allow markdown and config/openapi files and files that mention documentation keywords
                    if ext in ALLOWED_TEXT_EXT:
                        # include only if in documentation paths or contains keywords
                        try:
                            txt = read_text_safe(p).lower()
                        except Exception:
                            txt = ""
                        if any(k in txt for k in ("documentation", "docs/", "wiki/", "benutzerhandbuch", "dokumentation")) or any(x in (str(p.parent).lower()) for x in ("documentation", "docs", "wiki")):
                            add_file(p)
                    # allow openapi snapshots
                    if p.name.lower().startswith('openapi') and ext in ('.json', '.yaml', '.yml'):
                        add_file(p)
        else:
            for p in sd.rglob("**/*"):
                if p.is_file():
                    add_file(p)

    return files


def build_reference_map(files: List[Dict]) -> None:
    path_map = {f['path']: f for f in files}
    for f in files:
        for link in f['relative_links']:
            # normalize
            link_path = (Path(f['path']).parent / link).resolve()
            try:
                rel = str(link_path.relative_to(ROOT)).replace('\\', '/')
            except Exception:
                rel = None
            if rel and rel in path_map:
                path_map[rel]['referenced_by'].append(f['path'])


def detect_duplicates(files: List[Dict]) -> List[Dict]:
    # identical groups by sha256
    sha_map = {}
    for f in files:
        # skip duplicates that are in excluded directories by design
        if any(ex in f['path'] for ex in (".venv/", "node_modules/", "artifacts/documentation/github-wiki")):
            continue
        sha_map.setdefault(f['sha256'], []).append(f)
    groups = []
    gid = 1
    for sha, fl in sha_map.items():
        if len(fl) > 1:
            # filter out groups that are clearly third-party (licenses in site-packages)
            if all(('site-packages' in x['path'] or 'dist-info' in x['path'] or x['filename'].lower().startswith('license') for x in fl)):
                # ignore these
                continue
            # preserve original filename casing in reported file paths
            def reported_path(x):
                parent = Path(x['path']).parent.as_posix()
                if parent in ('.', ''):
                    return x['filename']
                return f"{parent}/{x['filename']}"

            group = {
                "group_id": f"duplicate-{gid:03d}",
                "match_type": "exact",
                "topic": "identical",
                "files": [reported_path(x) for x in fl],
                "recommended_source": reported_path(fl[0]),
                "recommended_target": "documentation/",
                "reason": "identical sha256",
                "requires_manual_review": False,
            }
            for x in fl:
                x['duplicate_group'] = group['group_id']
            groups.append(group)
            gid += 1

    # fuzzy similarity for markdown files (near-duplicates)
    md_files = [f for f in files if f['extension'].lower() in MARKDOWN_EXT and 'site-packages' not in f['path']]
    n = len(md_files)
    for i in range(n):
        for j in range(i + 1, n):
            try:
                a = read_text_safe(ROOT / md_files[i]['path'])
                b = read_text_safe(ROOT / md_files[j]['path'])
            except Exception:
                continue
            ratio = SequenceMatcher(None, a, b).ratio()
            if ratio > 0.95:
                # preserve original filename casing in reported file paths
                def reported_path(x):
                    parent = Path(x['path']).parent.as_posix()
                    if parent in ('.', ''):
                        return x['filename']
                    return f"{parent}/{x['filename']}"

                group = {
                    "group_id": f"duplicate-{gid:03d}",
                    "match_type": "near-duplicate",
                    "topic": "very-similar",
                    "files": [reported_path(md_files[i]), reported_path(md_files[j])],
                    "recommended_source": reported_path(md_files[i]),
                    "recommended_target": "documentation/",
                    "reason": f"similarity {ratio:.2f}",
                    "requires_manual_review": True,
                }
                md_files[i]['duplicate_group'] = group['group_id']
                md_files[j]['duplicate_group'] = group['group_id']
                groups.append(group)
                gid += 1
    return groups


def build_migration_plan(files: List[Dict], duplicates: List[Dict]) -> str:
    lines = ["# Dokumentations-Migrationsplan\n"]
    lines.append("## Zusammenfassung\n")
    lines.append(f"Gesamtdateien gescannt: {len(files)}\n")
    lines.append("## Aktuelle Dokumentationsquellen\n")
    # list common roots
    roots = {}
    for f in files:
        root = Path(f['path']).parts[0]
        roots.setdefault(root, 0)
        roots[root] += 1
    for r, c in roots.items():
        lines.append(f"- {r}: {c} Dateien\n")

    lines.append("## Kanonischer Zieldokumentensatz\n")
    lines.append("`documentation/` ist der kanonische Ort.\n")

    lines.append("## Dateien, die unverändert übernommen werden\n")
    for f in files:
        if f['migration_action'] == 'keep':
            lines.append(f"- {f['path']} -> {f.get('target_path') or f['path']}\n")

    lines.append("## Dateien, die verschoben werden\n")
    for f in files:
        if f['migration_action'] == 'move':
            suggested = f"documentation/{f['filename']}"
            f['target_path'] = suggested
            lines.append(f"- {f['path']} -> {suggested} (move)\n")

    lines.append("## Dateien, die zusammengeführt werden\n")
    for g in duplicates:
        if g['topic'] in ('identical', 'very-similar'):
            lines.append(f"- Gruppe {g['group_id']}: {g['files']} -> empfohlen: {g['recommended_target']} (requires review)\n")

    lines.append("## Interne Arbeitsdokumente\n")
    for f in files:
        if f['category'] == 'internal-work':
            lines.append(f"- {f['path']}\n")

    lines.append("## Generierte Artefakte\n")
    for f in files:
        if f['category'] == 'generated' or f['publication_status'] == 'generated':
            lines.append(f"- {f['path']} (generated)\n")

    lines.append("## Archivierte Inhalte\n")
    # placeholder
    lines.append("(keine automatisch archivierten Dateien)\n")

    lines.append("## Später zu löschende Dateien\n")
    for f in files:
        if f['migration_action'] == 'delete-later':
            lines.append(f"- {f['path']}\n")

    lines.append("## Nicht auflösbare Konflikte\n")
    for g in duplicates:
        if g['requires_manual_review']:
            lines.append(f"- {g['group_id']}: {g['files']}\n")

    lines.append("## Defekte Links\n")
    # Link checking is separate; placeholder
    lines.append("(Linkprüfung separat)\n")

    lines.append("## Fehlende Zielseiten\n")
    lines.append("(keine automatisch ermittelt)\n")

    lines.append("## Vorgeschlagene Manifest-Struktur\n")
    lines.append("Siehe documentation/manifest.json als Vorlage.\n")

    lines.append("## Reihenfolge der Migration\n")
    lines.append("1. Inventar und Duplikatklärung\n2. Migration der eindeutig zu verschiebenden Dateien mit `git mv`\n3. Manuelle Review und Merge\n4. Export und Validierung\n")

    return "\n".join(lines)


def write_outputs(files: List[Dict], duplicates: List[Dict], migration_md: str):
    jpath = ARTIFACTS / "documentation-inventory.json"
    cpath = ARTIFACTS / "documentation-inventory.csv"
    dpath = ARTIFACTS / "documentation-duplicates.json"
    mpath = ARTIFACTS / "documentation-migration-plan.md"
    spath = ARTIFACTS / "documentation-summary.json"

    jpath.write_text(json.dumps(files, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV header
    headers = list(files[0].keys()) if files else []
    with cpath.open("w", encoding="utf-8", newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for f in files:
            # flatten image_links to JSON string
            row = dict(f)
            row['image_links'] = json.dumps(row.get('image_links', []), ensure_ascii=False)
            row['relative_links'] = json.dumps(row.get('relative_links', []), ensure_ascii=False)
            row['external_links'] = json.dumps(row.get('external_links', []), ensure_ascii=False)
            writer.writerow(row)

    dpath.write_text(json.dumps(duplicates, ensure_ascii=False, indent=2), encoding="utf-8")
    mpath.write_text(migration_md, encoding="utf-8")
    # build summary
    from collections import Counter
    cat = Counter(); status = Counter(); mig = Counter(); excluded_dirs = Counter(); excluded_files = Counter()
    for f in files:
        cat[f.get('category','unknown')] += 1
        status[f.get('publication_status','unknown')] += 1
        mig[f.get('migration_action','unknown')] += 1
    # quick scan for excluded counts (best-effort)
    # walk excluded dirs under ROOT
    for ex in EXCLUDED_DIRS:
        p = ROOT / ex
        if p.exists() and p.is_dir():
            cnt = sum(1 for _ in p.rglob('*') if _.is_file())
            excluded_dirs[str(ex)] = cnt
    summary = {
        "schema_version": "1.0",
        "total_files": sum(cat.values()),
        "category_counts": dict(cat),
        "publication_status_counts": dict(status),
        "migration_action_counts": dict(mig),
        "duplicate_group_count": len(duplicates),
        "broken_link_count": 0,
        "unknown_file_count": cat.get('unknown', 0),
        "excluded_directory_counts": dict(excluded_dirs),
        "excluded_file_counts": dict(excluded_files),
        "generated_at": __import__('datetime').datetime.utcnow().isoformat() + 'Z'
    }
    spath.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote:", jpath, cpath, dpath, mpath)
    print("Wrote summary:", spath)


def main():
    files = scan_files()
    build_reference_map(files)
    duplicates = detect_duplicates(files)
    migration_md = build_migration_plan(files, duplicates)
    write_outputs(files, duplicates, migration_md)


if __name__ == "__main__":
    main()
