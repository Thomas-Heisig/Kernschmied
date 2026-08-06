from __future__ import annotations

from datetime import UTC, datetime

from app.database.models.user import UserModel
from app.storage.repositories.user import UserRepository
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession


class ProfileServiceError(Exception):
    pass


class ProfileEmailExists(ProfileServiceError):
    pass


class ProfileNotFound(ProfileServiceError):
    pass


async def get_current_profile(session: AsyncSession, user_id: str) -> UserModel:
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise ProfileNotFound()
    return user


async def update_current_profile(
    session: AsyncSession,
    user_id: str,
    *,
    display_name: str | None = None,
    email: EmailStr | None = None,
) -> UserModel:
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise ProfileNotFound()

    changes: dict[str, object | None] = {}

    if display_name is not None:
        normalized = display_name.strip()
        if normalized:
            changes["display_name"] = normalized

    if email is not None:
        normalized_email = str(email).strip().lower()
        # check duplicate
        existing = await repo.get_by_email(normalized_email)
        if existing is not None and existing.id != user.id:
            raise ProfileEmailExists()
        changes["email"] = normalized_email or None

    if not changes:
        return user

    # Update last modified metadata
    changes["updated_at"] = datetime.now(tz=UTC)

    updated = await repo.update(user, changes)
    return updated
