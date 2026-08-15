from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.auth import UserSessionResponse
from app.storage.repositories.auth_session import AuthSessionRepository


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _is_active(session_model: Any) -> bool:
    now = datetime.now(UTC)
    if session_model.revoked_at is not None:
        return False
    expires_at = _as_utc(session_model.expires_at)
    if expires_at is None:
        return True
    return expires_at > now


async def list_sessions(
    session: AsyncSession, user_id: str, current_session_id: str | None
) -> list[UserSessionResponse]:
    repo = AuthSessionRepository(session)
    rows: list[Any] = await repo.list_for_user(user_id)

    mapped: list[UserSessionResponse] = []
    for r in rows:
        active = _is_active(r)
        mapped.append(
            UserSessionResponse(
                id=r.id,
                authentication_method=r.authentication_method or "",
                created_at=_as_utc(r.created_at) or datetime.fromtimestamp(0, tz=UTC),
                expires_at=_as_utc(r.expires_at) or datetime.fromtimestamp(0, tz=UTC),
                last_seen_at=_as_utc(r.last_seen_at),
                revoked_at=_as_utc(r.revoked_at),
                current=(r.id == current_session_id),
                active=active,
                ip_address=r.ip_address,
                user_agent=(r.user_agent[:512] if r.user_agent else None),
            )
        )

    # Stable two-pass sort: newest first, then current session first.
    mapped.sort(key=lambda item: item.created_at, reverse=True)
    mapped.sort(key=lambda item: not item.current)
    return mapped


async def revoke_session(session: AsyncSession, user_id: str, session_id: str) -> bool:
    repo = AuthSessionRepository(session)
    now = datetime.now(UTC)
    return await repo.revoke_by_id(session_id, user_id, now)


async def revoke_all_sessions(
    session: AsyncSession, user_id: str, *, except_session_id: str | None = None
) -> int:
    repo = AuthSessionRepository(session)
    now = datetime.now(UTC)
    return await repo.revoke_all_for_user(
        user_id, now, except_session_id=except_session_id
    )
