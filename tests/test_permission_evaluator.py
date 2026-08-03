import os
import sys

# Ensure backend package is importable when running tests from workspace root
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from app.services.permission_evaluator import make_evaluator


def test_denies_when_no_permission_granted():
    ev = make_evaluator()
    decision = ev.can({"identity_id": "user:1"}, "resource.delete", {"level": "project", "id": "p1"}, context={})
    assert decision["allowed"] is False


def test_allows_when_permission_in_context():
    ev = make_evaluator()
    ctx = {"granted_permissions": ["resource.delete"]}
    decision = ev.can({"identity_id": "user:1"}, "resource.delete", {"level": "project", "id": "p1"}, context=ctx)
    assert decision["allowed"] is True
