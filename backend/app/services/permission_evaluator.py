from functools import lru_cache
from typing import Any, Dict, Optional


class PermissionEvaluator:
    """Minimal reference PermissionEvaluator used for development and tests.

    Notes:
    - This is intentionally minimal. Real implementations should consult
      registries, policy engines and caches.
    - The evaluator expects the caller to provide a pre-built EffectiveSecurityContext
      or relevant context keys such as `granted_permissions` for tests.
    """

    def __init__(self):
        pass

    def can(self, actor: Dict[str, Any], permission: str, scope: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evaluate whether `actor` may perform `permission` in `scope`.

        Simple semantics for reference:
        - If `context['granted_permissions']` contains `permission` -> allow
        - Else -> deny

        Returns a decision dict with fields: `allowed`, `reason`, `via`.
        """
        context = context or {}

        granted = context.get("granted_permissions") or []
        if permission in granted:
            return {"allowed": True, "reason": "explicit allow via context", "via": {"direct": True}}

        # Fallback deny
        return {"allowed": False, "reason": "no grant found", "via": {}}


def make_evaluator() -> PermissionEvaluator:
    return PermissionEvaluator()
