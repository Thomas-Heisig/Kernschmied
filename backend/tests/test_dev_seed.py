from __future__ import annotations

from pathlib import Path

from app.auth.models import UserContext


def test_development_admin_identity():
    admin = UserContext.development_admin()
    assert admin.id == "local-development-admin"
    assert admin.name == "Administrator"
    assert "admin" in admin.roles
    # ensure explicit permissions set (no wildcard)
    assert "*" not in admin.permissions
    assert "hierarchy.read" in admin.permissions


def test_dev_seed_no_personal_names():
    # Ensure personal names are not present in the automatic dev seed
    p = Path(__file__).resolve().parents[2] / "backend" / "app" / "core" / "dev_seed.py"
    text = p.read_text(encoding="utf-8")
    forbidden = ["Thomas Heisig", "Heisig Naturstein", "Angebote", "Angebot Müller"]
    for s in forbidden:
        assert s not in text
