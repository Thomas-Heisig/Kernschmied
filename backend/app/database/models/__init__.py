"""Import entrypoint for ORM model modules.

This package-level module ensures that all model modules which register
Table objects on the shared `Base` are imported when the package is
imported. This guarantees that `Base.metadata` contains the auth tables
and association tables used by Alembic and runtime schema generation.
"""

# Import model modules that register tables on Base.metadata.
# Keep imports explicit so static analysis tools can follow them.
from .user import UserModel  # noqa: F401
from .auth_session import AuthSessionModel  # noqa: F401
from .user_preference import UserPreferenceModel  # noqa: F401
from .user_role import (
	RoleModel,
	PermissionModel,
	UserRoleModel,
	RolePermissionModel,
)

__all__ = [
	"UserModel",
	"AuthSessionModel",
	"UserPreferenceModel",
	"RoleModel",
	"PermissionModel",
	"UserRoleModel",
	"RolePermissionModel",
]
