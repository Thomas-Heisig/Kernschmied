# F:\Kernschmied\backend\app\auth\__init__.py

from app.auth.dependencies import (
    AuthenticatedUser,
    CurrentUser,
    get_current_user,
    require_all_permissions,
    require_any_permission,
    require_authenticated_user,
    require_permission,
    require_role,
)
from app.auth.middleware import AuthenticationContextMiddleware
from app.auth.models import AuthenticationResult, UserContext
from app.auth.permissions import (
    has_all_permissions,
    has_any_permission,
    has_permission,
    has_role,
    permission_matches,
)


__all__ = [
    "AuthenticatedUser",
    "AuthenticationContextMiddleware",
    "AuthenticationResult",
    "CurrentUser",
    "UserContext",
    "get_current_user",
    "has_all_permissions",
    "has_any_permission",
    "has_permission",
    "has_role",
    "permission_matches",
    "require_all_permissions",
    "require_any_permission",
    "require_authenticated_user",
    "require_permission",
    "require_role",
]