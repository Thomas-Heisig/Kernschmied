from __future__ import annotations

from app.hierarchy.models import HierarchyActor
from app.auth.models import UserContext


def hierarchy_actor_from_user_context(user: UserContext | None) -> HierarchyActor:
    """Create a HierarchyActor from an authenticated UserContext.

    This converts roles and permissions into the HierarchyActor contract
    used throughout the hierarchy service and prompt resolver.
    """
    if user is None:
        return HierarchyActor()

    return HierarchyActor(
        user_id=(getattr(user, "id", None) or None),
        roles=frozenset(getattr(user, "roles", ()) or ()),
        permissions=frozenset(getattr(user, "permissions", ()) or ()),
    )
