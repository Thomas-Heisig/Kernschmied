from __future__ import annotations

import contextlib
import logging
from collections.abc import Mapping
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.auth_session import AuthSessionModel

logger = logging.getLogger(__name__)


class AuthSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: Mapping[str, object | None]) -> AuthSessionModel:
        obj = AuthSessionModel(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        with contextlib.suppress(Exception):
            # Avoid logging sensitive token hashes. Keep only non-sensitive identifiers.
            logger.debug(
                "Created auth session",
                extra={
                    "session_id": getattr(obj, "id", None),
                    "user_id": getattr(obj, "user_id", None),
                },
            )
        return obj

    async def get_by_token_hash(self, token_hash: str) -> AuthSessionModel | None:
        with contextlib.suppress(Exception):
            # Do not log token hashes or previews to avoid leaking sensitive data.
            logger.debug("Looking up auth session by token hash")
        stmt = select(AuthSessionModel).where(
            AuthSessionModel.session_token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        with contextlib.suppress(Exception):
            if obj is None:
                logger.debug("Auth session lookup returned no row")
            else:
                logger.debug(
                    "Auth session lookup returned row",
                    extra={
                        "session_id": getattr(obj, "id", None),
                        "user_id": getattr(obj, "user_id", None),
                        "revoked_at": getattr(obj, "revoked_at", None),
                        "expires_at": getattr(obj, "expires_at", None),
                    },
                )
        return obj

    async def revoke(self, obj: AuthSessionModel, when: datetime | None = None) -> None:
        obj.revoked_at = when
        self.session.add(obj)
        await self.session.flush()

    async def list_for_user(self, user_id: str) -> list[AuthSessionModel]:
        stmt = select(AuthSessionModel).where(AuthSessionModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(
        self, session_id: str, user_id: str
    ) -> AuthSessionModel | None:
        stmt = (
            select(AuthSessionModel)
            .where(AuthSessionModel.id == session_id)
            .where(AuthSessionModel.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_by_id(
        self, session_id: str, user_id: str, revoked_at: datetime
    ) -> bool:
        obj = await self.get_for_user(session_id, user_id)
        if obj is None:
            return False
        if obj.revoked_at is not None:
            # already revoked
            return True
        obj.revoked_at = revoked_at
        self.session.add(obj)
        await self.session.flush()
        return True

    async def revoke_all_for_user(
        self,
        user_id: str,
        revoked_at: datetime,
        *,
        except_session_id: str | None = None,
    ) -> int:
        stmt = select(AuthSessionModel).where(AuthSessionModel.user_id == user_id)
        if except_session_id is not None:
            stmt = stmt.where(AuthSessionModel.id != except_session_id)
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        count = 0
        for r in rows:
            if r.revoked_at is None:
                r.revoked_at = revoked_at
                self.session.add(r)
                count += 1
        if count:
            await self.session.flush()
        return count
