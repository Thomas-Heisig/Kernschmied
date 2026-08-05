from __future__ import annotations

from typing import Mapping, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user_preference import UserPreferenceModel


class UserPreferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: str) -> Optional[UserPreferenceModel]:
        stmt = select(UserPreferenceModel).where(UserPreferenceModel.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_default(self, user_id: str) -> UserPreferenceModel:
        obj = UserPreferenceModel(
            user_id=user_id,
            locale=None,
            timezone=None,
            theme=None,
            accent_color=None,
            compact_mode=0,
            default_model_id=None,
            default_workspace_id=None,
            preferences_json={},
        )
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, preference: UserPreferenceModel, changes: Mapping[str, object]) -> UserPreferenceModel:
        for k, v in changes.items():
            # map known fields directly
            if hasattr(preference, k):
                setattr(preference, k, v)
            else:
                # fall back to preferences_json
                if not isinstance(preference.preferences_json, dict):
                    preference.preferences_json = {}
                preference.preferences_json[k] = v

        self.session.add(preference)
        await self.session.flush()
        await self.session.refresh(preference)
        return preference
