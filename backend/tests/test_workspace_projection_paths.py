from __future__ import annotations

import tempfile
from pathlib import Path

from app.workspace_projection.paths import _safe_slug, resolve_within_root, user_folder_name
from app.workspace_projection.errors import PathSanitizationError


def test_safe_slug_basic():
    assert _safe_slug("Project Müller") != ""


def test_user_folder_name_contains_id():
    name = user_folder_name("Admin User", "user_123")
    assert "user_123" in name


def test_resolve_within_root_rejects_traversal(tmp_path: Path):
    root = tmp_path
    try:
        _ = resolve_within_root(root, "..", "etc")
        assert False, "Expected PathSanitizationError"
    except PathSanitizationError:
        pass
