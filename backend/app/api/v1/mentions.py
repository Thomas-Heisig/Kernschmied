from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AuthenticatedUser
from app.contracts.mentions import (
    MentionCandidate,
    UpdateMentionStatusRequest,
    UserMentionRead,
)
from app.database.models.auth_session import AuthSessionModel
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.database.models.mailbox import MailboxMessageModel
from app.database.models.user import UserModel
from app.database.models.user_mention import UserMentionModel
from app.storage.database import get_session
from app.storage.models.chat import Chat

router = APIRouter()
SESSION_DEP = Depends(get_session)


def is_administrator_auto_answer_user(user: UserModel) -> bool:
    return bool(user.is_system_user and user.is_system_admin)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def _candidate_rows(
    *,
    session: AsyncSession,
    current_user_id: str,
    query: str,
    allowed_user_ids: set[str] | None,
) -> list[MentionCandidate]:
    now = datetime.now(UTC)
    online_since = now - timedelta(minutes=5)
    latest_seen = func.max(
        func.coalesce(AuthSessionModel.last_seen_at, AuthSessionModel.created_at)
    ).label("latest_seen")
    stmt = (
        select(UserModel, latest_seen)
        .outerjoin(
            AuthSessionModel,
            and_(
                AuthSessionModel.user_id == UserModel.id,
                AuthSessionModel.revoked_at.is_(None),
                AuthSessionModel.expires_at > now,
            ),
        )
        .where(UserModel.is_active.is_(True), UserModel.id != current_user_id)
        .group_by(UserModel.id)
        .order_by(UserModel.display_name, UserModel.username)
        .limit(20)
    )
    if allowed_user_ids is not None:
        if not allowed_user_ids:
            stmt = stmt.where(UserModel.is_system_admin.is_(True))
        else:
            stmt = stmt.where(
                or_(
                    UserModel.id.in_(allowed_user_ids),
                    UserModel.is_system_admin.is_(True),
                )
            )
    normalized_query = query.strip().lower()
    if normalized_query:
        pattern = f"%{normalized_query}%"
        stmt = stmt.where(
            or_(
                func.lower(UserModel.username).like(pattern),
                func.lower(UserModel.display_name).like(pattern),
            )
        )
    rows = (await session.execute(stmt)).all()
    result: list[MentionCandidate] = []
    for db_user, latest in rows:
        seen = _as_utc(latest)
        result.append(
            MentionCandidate(
                user_id=db_user.id,
                username=db_user.username,
                display_name=db_user.display_name,
                online=seen is not None and seen >= online_since,
                is_administrator=is_administrator_auto_answer_user(db_user),
            )
        )
    return result


async def allowed_mention_target_ids(
    session: AsyncSession,
    hierarchy_node_id: str | None,
    *,
    is_admin: bool,
) -> set[str] | None:
    if is_admin:
        return None
    if not hierarchy_node_id:
        return set()

    allowed: set[str] = set()
    node = await session.get(HierarchyNodeModel, hierarchy_node_id)
    visited: set[str] = set()
    while node is not None and node.id not in visited:
        visited.add(node.id)
        metadata = dict(node.node_metadata or {})
        owner_user_id = str(metadata.get("owner_user_id") or "").strip()
        if owner_user_id:
            allowed.add(owner_user_id)
        for key in ("assigned_user_ids", "member_user_ids", "user_ids"):
            values = metadata.get(key)
            if isinstance(values, list):
                allowed.update(str(value) for value in values if str(value).strip())
        node = (
            await session.get(HierarchyNodeModel, node.parent_id)
            if node.parent_id
            else None
        )
    return allowed


@router.get("/candidates", response_model=list[MentionCandidate])
async def list_mention_candidates(
    user: AuthenticatedUser,
    q: str = Query(default="", max_length=100),
    hierarchy_node_id: str | None = Query(default=None),
    session: AsyncSession = SESSION_DEP,
) -> list[MentionCandidate]:
    allowed_ids = await allowed_mention_target_ids(
        session,
        hierarchy_node_id,
        is_admin=user.is_system_admin or "admin" in user.roles,
    )
    return await _candidate_rows(
        session=session,
        current_user_id=user.id,
        query=q,
        allowed_user_ids=allowed_ids,
    )


@router.get("/online", response_model=list[MentionCandidate])
async def list_online_users(
    user: AuthenticatedUser,
    hierarchy_node_id: str | None = Query(default=None),
    session: AsyncSession = SESSION_DEP,
) -> list[MentionCandidate]:
    allowed_ids = await allowed_mention_target_ids(
        session,
        hierarchy_node_id,
        is_admin=user.is_system_admin or "admin" in user.roles,
    )
    candidates = await _candidate_rows(
        session=session,
        current_user_id=user.id,
        query="",
        allowed_user_ids=allowed_ids,
    )
    return [candidate for candidate in candidates if candidate.online]


@router.get("/me", response_model=list[UserMentionRead])
async def list_my_mentions(
    user: AuthenticatedUser,
    status_filter: str | None = Query(default=None, alias="status"),
    session: AsyncSession = SESSION_DEP,
) -> list[UserMentionRead]:
    stmt = (
        select(UserMentionModel, UserModel.display_name, Chat.node_id)
        .join(UserModel, UserModel.id == UserMentionModel.sender_user_id)
        .join(Chat, Chat.id == UserMentionModel.conversation_id)
        .where(UserMentionModel.target_user_id == user.id)
        .order_by(UserMentionModel.created_at.desc())
        .limit(100)
    )
    if status_filter:
        if status_filter not in {"unread", "read", "answered", "closed"}:
            raise HTTPException(status_code=422, detail="invalid mention status")
        stmt = stmt.where(UserMentionModel.status == status_filter)
    rows = (await session.execute(stmt)).all()
    return [
        UserMentionRead(
            id=mention.id,
            message_id=mention.message_id,
            conversation_id=mention.conversation_id,
            hierarchy_node_id=node_id,
            sender_user_id=mention.sender_user_id,
            sender_name=sender_name,
            target_user_id=mention.target_user_id,
            mention_text=mention.mention_text,
            status=mention.status,
            created_at=mention.created_at,
            read_at=mention.read_at,
            answered_at=mention.answered_at,
            closed_at=mention.closed_at,
        )
        for mention, sender_name, node_id in rows
    ]


@router.patch("/{mention_id}", response_model=UserMentionRead)
async def update_mention_status(
    mention_id: str,
    payload: UpdateMentionStatusRequest,
    user: AuthenticatedUser,
    session: AsyncSession = SESSION_DEP,
) -> UserMentionRead:
    mention = await session.get(UserMentionModel, mention_id)
    if mention is None or mention.target_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="mention not found"
        )
    now = datetime.now(UTC)
    mention.status = payload.status
    if payload.status == "read":
        mention.read_at = mention.read_at or now
    elif payload.status == "answered":
        mention.read_at = mention.read_at or now
        mention.answered_at = now
    else:
        mention.read_at = mention.read_at or now
        mention.closed_at = now
    mailbox_message = await session.scalar(
        select(MailboxMessageModel).where(
            MailboxMessageModel.related_mention_id == mention.id
        )
    )
    if mailbox_message is not None:
        if payload.status == "read":
            mailbox_message.status = "read"
            mailbox_message.read_at = mailbox_message.read_at or now
        elif payload.status in {"answered", "closed"}:
            mailbox_message.status = "archived"
            mailbox_message.read_at = mailbox_message.read_at or now
            mailbox_message.archived_at = now
    await session.commit()
    refreshed = await list_my_mentions(user=user, status_filter=None, session=session)
    return next(item for item in refreshed if item.id == mention_id)