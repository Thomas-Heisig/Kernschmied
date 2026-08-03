from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / 'documentation'
manifest = {'sections': []}
# collect top-level pages (in documentation root)
root_pages = []
for p in sorted(DOCS.glob('*.md')):
    root_pages.append({'file': p.name, 'title': p.stem})
if root_pages:
    manifest['sections'].append({'title': 'Home', 'pages': root_pages})
# collect directories
for d in sorted([p for p in DOCS.iterdir() if p.is_dir()]):
    pages = []
    for f in sorted(d.glob('*.md')):
        pages.append({'file': f.relative_to(DOCS).as_posix(), 'title': f.stem})
    if pages:
        manifest['sections'].append({'title': d.name, 'pages': pages})
(DOCS / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
print('Wrote documentation/manifest.json')
