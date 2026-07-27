from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models.config import ConfigState, SystemConfig
from app.storage.repositories.base import Repository


class ConfigRepository(Repository[SystemConfig]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get(
        self,
        config_group: str,
        config_key: str,
    ) -> SystemConfig | None:
        return await self.session.scalar(
            select(SystemConfig).where(
                SystemConfig.config_group == config_group,
                SystemConfig.config_key == config_key,
            )
        )

    async def list_group(
        self,
        config_group: str,
    ) -> Sequence[SystemConfig]:
        result = await self.session.scalars(
            select(SystemConfig)
            .where(SystemConfig.config_group == config_group)
            .order_by(SystemConfig.config_key)
        )
        return result.all()

    async def get_revision(self) -> int:
        state = await self.session.get(ConfigState, 1)
        return state.revision if state is not None else 1

    async def increment_revision(self) -> int:
        state = await self.session.get(ConfigState, 1)

        if state is None:
            state = ConfigState(id=1, revision=1)
            self.session.add(state)
        else:
            state.revision += 1

        await self.session.flush()
        return state.revision
