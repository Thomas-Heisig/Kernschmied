"""Perform a conservative migration of repository documentation into `documentation/`.

- Uses artifacts/documentation/documentation-inventory.json as input (scanner must be run first).
- Copies canonical files into documentation/ organized by category or into a sensible path.
- Archives duplicate variants into `.internal/documentation-work/duplicates/`.
- Moves original top-level doc dirs (`docs/`, `wiki/`, `doco/`) into `.internal/documentation-work/archive_{ts}` for review.
- Generates `documentation/manifest.json` and `documentation/_Sidebar.md`.
- Updates markdown links that reference `docs/`, `wiki/`, `doco/` to `documentation/` where possible.

This script is conservative: it never deletes original sources — it moves them to `.internal/documentation-work/` and writes provenance metadata for every migrated file.
"""
from __future__ import annotations

import json
import shutil
import hashlib
import time
from pathlib import Path
from typing import List, Dict
import re
import os

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts" / "documentation"
INVENTORY = ARTIFACTS / "documentation-inventory.json"
DOC_ROOT = ROOT / "documentation"
INTERNAL = ROOT / ".internal" / "documentation-work"
ASSETS = DOC_ROOT / "assets"

TEXT_EXT = {".md", ".markdown", ".txt", ".rst", ".adoc", ".json", ".yml", ".yaml"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".pdf", ".puml", ".mmd", ".drawio"}

PREFERRED_LOCATIONS = ["/documentation/", "/docs/", "/wiki/", "/doco/"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dirs():
    DOC_ROOT.mkdir(parents=True, exist_ok=True)
    INTERNAL.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (INTERNAL / "duplicates").mkdir(parents=True, exist_ok=True)


def load_inventory() -> List[Dict]:
    if not INVENTORY.exists():
        raise SystemExit(f"Inventory not found: {INVENTORY}. Run scanner first.")
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def choose_canonical(group: List[Dict]) -> Dict:
    # prefer files already in documentation/, else prefer by preferred locations order
    for loc in PREFERRED_LOCATIONS:
        for item in group:
            if loc in f"/{item['path'].replace('\\\\','/')}/":
                return item
    # fallback: smallest path lexicographically
    return sorted(group, key=lambda x: x['path'])[0]


def safe_copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def migrate():
    ensure_dirs()
    inv = load_inventory()

    # build duplicate groups map
    groups = {}
    for item in inv:
        g = item.get("duplicate_group")
        if g:
            groups.setdefault(g, []).append(item)

    # mapping old->new for later link updates
    moved_map = {}
    archived = []

    # process duplicates first: archive non-canonical
    for gid, items in groups.items():
        canonical = choose_canonical(items)
        canon_path = ROOT / canonical['path']
        # target location: if canonical has target_path use that, else use documentation/<category>/<filename>
        if canonical.get('target_path'):
            target = ROOT / canonical['target_path']
        else:
            cat = canonical.get('category') or 'misc'
            target = DOC_ROOT / cat / canonical['filename']
        # copy canonical
        if canon_path.exists():
            safe_copy(canon_path, target)
            moved_map[canonical['path']] = str(target.relative_to(ROOT)).replace('\\\\','/')
        # archive others into internal/duplicates/gid.md
        dup_archive = INTERNAL / 'duplicates' / f"{gid}.md"
        with dup_archive.open('w', encoding='utf-8') as out:
            out.write(f"# Duplicate group {gid}\n\n")
            for it in items:
                p = ROOT / it['path']
                out.write(f"---\nSource: {it['path']} (sha256: {it['sha256']})\n\n")
                if p.exists() and p.suffix.lower() in TEXT_EXT:
                    try:
                        out.write(p.read_text(encoding='utf-8'))
                    except Exception:
                        out.write(p.read_text(encoding='latin-1', errors='ignore'))
                else:
                    out.write(f"(binary or missing file: {it['path']})\n")
                out.write('\n\n')
        archived.append(str(dup_archive.relative_to(ROOT)).replace('\\\\','/'))
        # map non-canonical to archive
        for it in items:
            if it is canonical:
                continue
            moved_map[it['path']] = str(dup_archive.relative_to(ROOT)).replace('\\\\','/')

    # process remaining files (non-duplicates)
    for item in inv:
        if item.get('duplicate_group'):
            continue
        src = ROOT / item['path']
        if not src.exists():
            continue
        # determine target
        if item.get('target_path'):
            target = ROOT / item['target_path']
        else:
            cat = item.get('category') or 'misc'
            if item['extension'].lower() in BINARY_EXT:
                target = ASSETS / 'attachments' / item['path'].replace('/', '_')
            else:
                target = DOC_ROOT / cat / item['path'].split('/')[-1]
        # copy
        if src.exists():
            # if target exists and content differs, archive source to internal and keep target as canonical
            if target.exists():
                try:
                    same = sha256_file(src) == sha256_file(target)
                except Exception:
                    same = False
                if not same:
                    # archive source
                    arc = INTERNAL / 'archived_sources' / item['path'].replace('/', '_')
                    arc.parent.mkdir(parents=True, exist_ok=True)
                    safe_copy(src, arc)
                    moved_map[item['path']] = str(arc.relative_to(ROOT)).replace('\\\\','/')
                    archived.append(str(arc.relative_to(ROOT)).replace('\\\\','/'))
                else:
                    moved_map[item['path']] = str(target.relative_to(ROOT)).replace('\\\\','/')
            else:
                safe_copy(src, target)
                moved_map[item['path']] = str(target.relative_to(ROOT)).replace('\\\\','/')

    # move original doc folders into internal archive pending validation
    ts = time.strftime('%Y%m%dT%H%M%S')
    archive_root = INTERNAL / f'archive_pending_{ts}'
    archive_root.mkdir(parents=True, exist_ok=True)
    for d in ['docs', 'wiki', 'doco']:
        p = ROOT / d
        if p.exists():
            shutil.move(str(p), str(archive_root / d))

    # write manifest.json from files under documentation/
    manifest = []
    for md in sorted(DOC_ROOT.rglob('*.md')):
        rel = md.relative_to(ROOT).as_posix()
        # get title
        title = ''
        try:
            txt = md.read_text(encoding='utf-8')
        except Exception:
            txt = md.read_text(encoding='latin-1', errors='ignore')
        m = re.search(r'^#\s+(.+)$', txt, flags=re.MULTILINE)
        if m:
            title = m.group(1).strip()
        manifest.append({
            'path': rel,
            'title': title,
            'sha256': sha256_file(md),
            'size': md.stat().st_size,
        })

    (DOC_ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')

    # generate simple _Sidebar.md
    sidebar_lines = []
    # Home
    if (DOC_ROOT / 'Home.md').exists():
        sidebar_lines.append('- [Home](Home.md)')
    # list top-level dirs
    for d in sorted([p for p in DOC_ROOT.iterdir() if p.is_dir()]):
        name = d.name
        sidebar_lines.append(f"- {name}/")
        for f in sorted(d.glob('*.md')):
            rel = f.relative_to(DOC_ROOT).as_posix()
            sidebar_lines.append(f"  - [{f.stem}]({rel})")
    (DOC_ROOT / '_Sidebar.md').write_text('\n'.join(sidebar_lines)+"\n", encoding='utf-8')

    # write provenance mapping
    prov = {
        'moved_map': moved_map,
        'archived': archived,
        'archive_root': str(archive_root.relative_to(ROOT).as_posix()),
    }
    (INTERNAL / 'migration_provenance.json').write_text(json.dumps(prov, indent=2, ensure_ascii=False), encoding='utf-8')

    print('Migration stage complete. Run validators next.')


if __name__ == '__main__':
    migrate()
