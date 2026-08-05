from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from app.storage.repositories.auth_session import AuthSessionRepository
from app.contracts.auth import UserSessionResponse
from sqlalchemy.ext.asyncio import AsyncSession


def _is_active(session_model) -> bool:
    now = datetime.now(timezone.utc)
    if session_model.revoked_at is not None:
        return False
    if session_model.expires_at is None:
        return True
    return session_model.expires_at > now


async def list_sessions(session: AsyncSession, user_id: str, current_session_id: str | None) -> List[UserSessionResponse]:
    repo = AuthSessionRepository(session)
    rows = await repo.list_for_user(user_id)

    mapped = []
    for r in rows:
        active = _is_active(r)
        mapped.append(
            UserSessionResponse(
                id=r.id,
                authentication_method=r.authentication_method or "",
                created_at=r.created_at,
                expires_at=r.expires_at or datetime.fromtimestamp(0, tz=timezone.utc),
                last_seen_at=r.last_seen_at,
                revoked_at=r.revoked_at,
                current=(r.id == current_session_id),
                active=active,
                ip_address=r.ip_address,
                user_agent=(r.user_agent[:512] if r.user_agent else None),
            )
        )

    # sort: current first, then created_at desc
    mapped.sort(key=lambda x: (not x.current, getattr(x, 'created_at', datetime.min)), reverse=True)
    return mapped


async def revoke_session(session: AsyncSession, user_id: str, session_id: str) -> bool:
    repo = AuthSessionRepository(session)
    now = datetime.now(timezone.utc)
    return await repo.revoke_by_id(session_id, user_id, now)


async def revoke_all_sessions(session: AsyncSession, user_id: str, *, except_session_id: str | None = None) -> int:
    repo = AuthSessionRepository(session)
    now = datetime.now(timezone.utc)
    return await repo.revoke_all_for_user(user_id, now, except_session_id=except_session_id)
