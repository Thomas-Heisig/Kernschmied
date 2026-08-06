"""Import entrypoint for ORM model modules.

This package-level module ensures that all model modules which register
Table objects on the shared `Base` are imported when the package is
imported. This guarantees that `Base.metadata` contains the auth tables
and association tables used by Alembic and runtime schema generation.
"""

# Import model modules that register tables on Base.metadata.
# Keep imports explicit so static analysis tools can follow them.
from .auth_session import AuthSessionModel
from .user import UserModel
from .user_preference import UserPreferenceModel
from .user_role import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserRoleModel,
)

__all__ = [
    "AuthSessionModel",
    "PermissionModel",
    "RoleModel",
    "RolePermissionModel",
    "UserModel",
    "UserPreferenceModel",
    "UserRoleModel",
]
