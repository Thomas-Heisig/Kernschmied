from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from app.auth.models import normalize_string_collection_value


def _normalize_string_collection(value: object) -> list[str]:
    # Reuse existing normalizer but return list
    tup = normalize_string_collection_value(value)
    return list(tup)


def _extract_role_names(value: object) -> list[str]:
    # Roles may be a sequence of strings, objects with `name`, or a mapping
    if value is None:
        return []

    # Mapping -> treat keys with truthy values as role names
    if isinstance(value, Mapping):
        out: list[str] = []
        mapping = cast(Mapping[object, object], value)
        for k, v in mapping.items():
            if not v:
                continue
            out.append(str(k))
        return out

    # Sequence -> map items
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        out: list[str] = []
        seq = cast(Sequence[object], value)
        for item in seq:
            if item is None:
                continue
            # object with name attribute
            name = getattr(item, "name", None)
            if name is not None:
                out.append(str(name))
                continue
            out.append(str(item))
        return out

    # Fallback: single string
    if isinstance(value, str):
        return [value]

    try:
        return [str(value)]
    except Exception:
        return []


def build_principal_from_user(
    user: object,
    *,
    session_id: str | None = None,
    authentication_method: str | None = None,
) -> dict[str, object]:
    """Create a serializable principal mapping from a DB user model or similar object.

    This deliberately avoids returning ORM objects or lazy-loaded relationships.
    """
    # roles and permissions may be relationship objects; extract names safely
    roles = _extract_role_names(getattr(user, "roles", None))
    permissions = _normalize_string_collection(getattr(user, "permissions", None))

    is_system_admin = bool(
        getattr(user, "is_system_admin", False) or getattr(user, "is_admin", False)
    )

    # If a role named 'admin' exists, treat as system admin
    if any(r and str(r).lower() == "admin" for r in roles):
        is_system_admin = True

    principal: dict[str, object | None] = {
        "id": str(getattr(user, "id", "")),
        "user_id": str(getattr(user, "id", "")),
        "username": (
            getattr(user, "username", None)
            or getattr(user, "name", None)
            or str(getattr(user, "id", ""))
        ),
        "display_name": (
            getattr(user, "display_name", None) or getattr(user, "name", None) or None
        ),
        "email": getattr(user, "email", None),
        "is_active": bool(getattr(user, "is_active", True)),
        "is_system_admin": is_system_admin,
        "roles": roles,
        "permissions": permissions,
        "session_id": session_id,
        "authentication_method": authentication_method,
    }

    return principal
