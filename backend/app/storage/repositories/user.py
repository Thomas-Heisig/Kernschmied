from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import UserModel
from app.database.models.user_role import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserRoleModel,
)


class UserRepository:
    """Simple SQLAlchemy-based user repository.

    Methods do not commit; transaction boundaries are the caller's responsibility.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        return await self.load_authorization(result.scalar_one_or_none())

    async def get_by_username(self, username: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self.session.execute(stmt)
        return await self.load_authorization(result.scalar_one_or_none())

    async def get_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return await self.load_authorization(result.scalar_one_or_none())

    async def load_authorization(self, user: UserModel | None) -> UserModel | None:
        if user is None:
            return None

        role_result = await self.session.execute(
            select(RoleModel.id, RoleModel.name)
            .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
            .where(UserRoleModel.user_id == user.id)
        )
        role_rows = role_result.all()
        role_ids = [role_id for role_id, _ in role_rows]
        role_names = tuple(role_name for _, role_name in role_rows)

        permissions: tuple[str, ...] = ()
        if role_ids:
            permission_result = await self.session.execute(
                select(PermissionModel.permission)
                .join(
                    RolePermissionModel,
                    RolePermissionModel.permission_id == PermissionModel.id,
                )
                .where(RolePermissionModel.role_id.in_(role_ids))
            )
            permissions = tuple(permission_result.scalars().all())

        user.__dict__["roles"] = role_names
        user.__dict__["permissions"] = permissions
        return user

    async def create(self, user: Mapping[str, object | None]) -> UserModel:
        obj = UserModel(**user)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: UserModel, changes: Mapping[str, object]) -> UserModel:
        for k, v in changes.items():
            setattr(obj, k, v)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
