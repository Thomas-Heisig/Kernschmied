from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import UserModel


class UserRepository:
    """Simple SQLAlchemy-based user repository.

    Methods do not commit; transaction boundaries are the caller's responsibility.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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
