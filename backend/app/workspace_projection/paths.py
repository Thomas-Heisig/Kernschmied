from __future__ import annotations

import re
from pathlib import Path
from typing import Final

from .errors import PathSanitizationError

_RESERVED_WINDOWS_NAMES: Final[set[str]] = {
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "lpt1",
}


def _safe_slug(value: str) -> str:
    """Produce a filesystem-safe slug for display names.

    Keep it readable but remove path separators and suspicious chars.
    """
    if not value:
        return ""

    # normalize whitespace
    s = value.strip()

    # replace path separators and control chars
    s = re.sub(r"[\\/\0-\x1f]+", "-", s)

    # collapse multiple non-alnum into single dash
    s = re.sub(r"[^\w\d-]+", "-", s, flags=re.UNICODE)

    s = s.strip("-_")

    s = s[:128]

    lower = s.lower()
    if lower in _RESERVED_WINDOWS_NAMES:
        s = f"_{s}"

    if not s:
        raise PathSanitizationError("Cannot produce safe slug from empty value")

    return s


def user_folder_name(display_name: str | None, user_id: str) -> str:
    display = display_name or "user"
    slug = _safe_slug(display)
    return f"{slug}__{user_id}"


def node_folder_name(node_title: str | None, node_id: str, prefix: str | None = None) -> str:
    title = node_title or "node"
    slug = _safe_slug(title)
    name = f"{slug}__{node_id}"
    if prefix:
        return f"{prefix}__{name}"
    return name


def resolve_within_root(root: Path, *segments: str) -> Path:
    """Resolve path and ensure it is inside `root`.

    Raises PathSanitizationError on violation.
    """
    root = root.resolve()
    candidate = root.joinpath(*segments)
    try:
        resolved = candidate.resolve()
    except Exception as exc:
        raise PathSanitizationError(str(exc)) from exc

    try:
        resolved.relative_to(root)
    except Exception:
        raise PathSanitizationError(f"Resolved path escapes projection root: {resolved}")

    return resolved


__all__ = ["user_folder_name", "node_folder_name", "resolve_within_root", "_safe_slug"]
