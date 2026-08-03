import os
import json
from pathlib import Path
import shutil
import tempfile
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'documentation' / 'build_documentation_index.py'


def run_scan(root: Path):
    env = os.environ.copy()
    env['DOCUMENTATION_SCAN_ROOT'] = str(root)
    # run script
    subprocess.check_call([str(root / '.venv' / 'Scripts' / 'python.exe') if (root / '.venv' / 'Scripts' / 'python.exe').exists() else 'python', str(SCRIPT)], env=env)


@pytest.fixture()
def sample_repo(tmp_path):
    # create a minimal repo structure
    (tmp_path / 'documentation').mkdir()
    (tmp_path / 'documentation' / 'Home.md').write_text('# Home\n')
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs' / 'ROADMAP.md').write_text('# Roadmap\n')
    (tmp_path / 'wiki').mkdir()
    (tmp_path / 'wiki' / 'Home.md').write_text('# Wiki Home\n')
    # excluded dirs
    (tmp_path / '.venv' / 'Lib' / 'site-packages').mkdir(parents=True)
    (tmp_path / '.venv' / 'Lib' / 'site-packages' / 'LICENSE.md').write_text('License')
    (tmp_path / 'node_modules').mkdir()
    (tmp_path / 'node_modules' / 'pkg' / 'README.md').mkdir(parents=True)
    # frontend public external content
    (tmp_path / 'frontend' / 'public').mkdir(parents=True)
    (tmp_path / 'frontend' / 'public' / 'template.html').write_text('<html>Third party template</html>')
    # backend doc reference
    (tmp_path / 'backend').mkdir()
    (tmp_path / 'backend' / 'HELP.md').write_text('Documentation: see docs/')
    # create duplicate in documentation
    (tmp_path / 'documentation' / 'INSTALL.md').write_text('# Install\nInstructions')
    (tmp_path / 'docs' / 'INSTALL.md').write_text('# Install\nInstructions')
    return tmp_path


def test_scan_and_exclusions(sample_repo, tmp_path):
    root = sample_repo
    env = os.environ.copy()
    env['DOCUMENTATION_SCAN_ROOT'] = str(root)
    # run script with python from PATH
    subprocess.check_call(['python', str(SCRIPT)], env=env)
    art = root / 'artifacts' / 'documentation'
    assert art.exists()
    inv = art / 'documentation-inventory.json'
    summary = art / 'documentation-summary.json'
    dup = art / 'documentation-duplicates.json'
    assert inv.exists()
    j = json.loads(inv.read_text(encoding='utf-8'))
    s = json.loads(summary.read_text(encoding='utf-8'))
    d = json.loads(dup.read_text(encoding='utf-8'))
    # ensure excluded .venv files are not in inventory
    assert not any('.venv' in f['path'] for f in j)
    # ensure frontend/public template marked as generated/internal
    assert any(f for f in j if f['path'].startswith('frontend/public') and (f['category'] == 'generated' or f['publication_status'] == 'internal'))
    # ensure duplicate group detected for INSTALL.md (docs vs documentation)
    assert any(g for g in d if any('INSTALL.md' in p for p in g['files']))
    # summary counts sensible
    assert s['total_files'] >= 3
