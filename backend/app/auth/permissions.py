# F:\Kernschmied\backend\app\auth\permissions.py

from __future__ import annotations

from collections.abc import Iterable

from app.auth.models import UserContext

ADMIN_ROLE = "admin"
GLOBAL_PERMISSION = "*"


def normalize_permission(value: str) -> str:
    return value.strip().lower()


def permission_matches(
    granted_permission: str,
    required_permission: str,
) -> bool:
    """
    Unterstützt:

    - exakte Berechtigungen:
      config:read

    - globale Wildcard:
      *

    - Namespace-Wildcards:
      config:*
      tools:calculator:*
    """

    granted = normalize_permission(granted_permission)
    required = normalize_permission(required_permission)

    if not granted or not required:
        return False

    if granted == GLOBAL_PERMISSION:
        return True

    if granted == required:
        return True

    if granted.endswith(":*"):
        namespace = granted[:-1]
        return required.startswith(namespace)

    return False


def has_role(
    user: UserContext,
    role: str,
) -> bool:
    normalized_role = role.strip().lower()

    return normalized_role in user.roles


def has_permission(
    user: UserContext,
    permission: str,
) -> bool:
    if not user.active:
        return False

    if has_role(user, ADMIN_ROLE):
        return True

    return any(
        permission_matches(
            granted_permission,
            permission,
        )
        for granted_permission in user.permissions
    )


def has_all_permissions(
    user: UserContext,
    permissions: Iterable[str],
) -> bool:
    required_permissions = tuple(permissions)

    return all(has_permission(user, permission) for permission in required_permissions)


def has_any_permission(
    user: UserContext,
    permissions: Iterable[str],
) -> bool:
    required_permissions = tuple(permissions)

    if not required_permissions:
        return True

    return any(has_permission(user, permission) for permission in required_permissions)
