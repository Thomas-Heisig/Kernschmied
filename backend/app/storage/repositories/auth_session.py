from __future__ import annotations

from datetime import datetime
from typing import Optional, Mapping
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.auth_session import AuthSessionModel
import logging

logger = logging.getLogger(__name__)


class AuthSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: Mapping[str, object | None]) -> AuthSessionModel:
        obj = AuthSessionModel(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        try:
            # Avoid logging sensitive token hashes. Keep only non-sensitive identifiers.
            logger.debug(
                "Created auth session",
                extra={
                    "session_id": getattr(obj, "id", None),
                    "user_id": getattr(obj, "user_id", None),
                },
            )
        except Exception:
            # Logging must never raise in production flows
            pass
        return obj

    async def get_by_token_hash(self, token_hash: str) -> Optional[AuthSessionModel]:
        try:
            # Do not log token hashes or previews to avoid leaking sensitive data.
            logger.debug("Looking up auth session by token hash")
        except Exception:
            pass
        stmt = select(AuthSessionModel).where(AuthSessionModel.session_token_hash == token_hash)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        try:
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
        except Exception:
            pass
        return obj

    async def revoke(self, obj: AuthSessionModel, when: datetime | None = None) -> None:
        obj.revoked_at = when
        self.session.add(obj)
        await self.session.flush()
