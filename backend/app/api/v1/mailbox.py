from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AuthenticatedUser
from app.contracts.mailbox import (
    MailboxMessageRead,
    MailboxRead,
    UpdateMailboxMessageRequest,
)
from app.database.models.mailbox import MailboxMessageModel, UserMailboxModel
from app.database.models.user import UserModel
from app.database.models.user_mention import UserMentionModel
from app.services.mailbox_service import (
    create_mailbox_message,
    deliver_mailbox_message_email,
    ensure_user_mailbox,
)
from app.storage.database import get_session
from app.storage.models.chat import Chat

router = APIRouter()
SESSION_DEP = Depends(get_session)


def _mailbox_read(mailbox: UserMailboxModel) -> MailboxRead:
    return MailboxRead(
        id=mailbox.id,
        user_id=mailbox.user_id,
        internal_address=mailbox.internal_address,
        external_email=mailbox.external_email,
        email_delivery_enabled=mailbox.email_delivery_enabled,
        email_provider=mailbox.email_provider,
        email_ready=bool(
            mailbox.external_email
            and mailbox.email_delivery_enabled
            and mailbox.email_provider
        ),
    )


@router.get("/me", response_model=MailboxRead)
async def get_my_mailbox(
    user: AuthenticatedUser,
    session: AsyncSession = SESSION_DEP,
) -> MailboxRead:
    mailbox = await ensure_user_mailbox(session, user.id)
    await session.commit()
    return _mailbox_read(mailbox)


async def _message_rows(
    session: AsyncSession,
    mailbox_id: str,
    *,
    status_filter: str | None,
    limit: int,
) -> list[MailboxMessageRead]:
    stmt = (
        select(
            MailboxMessageModel,
            UserModel.display_name,
            Chat.node_id,
        )
        .outerjoin(UserModel, UserModel.id == MailboxMessageModel.sender_user_id)
        .outerjoin(
            UserMentionModel,
            UserMentionModel.id == MailboxMessageModel.related_mention_id,
        )
        .outerjoin(Chat, Chat.id == UserMentionModel.conversation_id)
        .where(MailboxMessageModel.mailbox_id == mailbox_id)
        .order_by(MailboxMessageModel.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(MailboxMessageModel.status == status_filter)
    rows = (await session.execute(stmt)).all()
    return [
        MailboxMessageRead(
            id=message.id,
            mailbox_id=message.mailbox_id,
            sender_user_id=message.sender_user_id,
            sender_name=sender_name,
            related_mention_id=message.related_mention_id,
            hierarchy_node_id=node_id,
            subject=message.subject,
            body=message.body,
            message_type=message.message_type,
            status=message.status,
            channel=message.channel,
            delivery_status=message.delivery_status,
            email_to=message.email_to,
            created_at=message.created_at,
            read_at=message.read_at,
            archived_at=message.archived_at,
        )
        for message, sender_name, node_id in rows
    ]


@router.get("/messages", response_model=list[MailboxMessageRead])
async def list_my_mailbox_messages(
    user: AuthenticatedUser,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=100),
    session: AsyncSession = SESSION_DEP,
) -> list[MailboxMessageRead]:
    if status_filter not in {None, "unread", "read", "archived"}:
        raise HTTPException(status_code=422, detail="invalid mailbox status")
    mailbox = await ensure_user_mailbox(session, user.id)
    return await _message_rows(
        session,
        mailbox.id,
        status_filter=status_filter,
        limit=limit,
    )


@router.post("/test-email", response_model=MailboxMessageRead)
async def send_test_email(
    user: AuthenticatedUser,
    session: AsyncSession = SESSION_DEP,
) -> MailboxMessageRead:
    mailbox = await ensure_user_mailbox(session, user.id)
    if not mailbox.external_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Für dieses Postfach ist keine externe E-Mail-Adresse hinterlegt.",
        )
    message = await create_mailbox_message(
        session,
        recipient_user_id=user.id,
        sender_user_id=None,
        subject="Kernschmied Test-E-Mail",
        body=(
            "Diese Nachricht bestätigt, dass dein Kernschmied-Postfach "
            "den konfigurierten Test-Maildienst erreicht."
        ),
        message_type="email_test",
    )
    await session.commit()
    await deliver_mailbox_message_email(session, message.id)
    await session.commit()
    rows = await _message_rows(
        session,
        mailbox.id,
        status_filter=None,
        limit=100,
    )
    return next(row for row in rows if row.id == message.id)


@router.patch("/messages/{message_id}", response_model=MailboxMessageRead)
async def update_mailbox_message(
    message_id: str,
    payload: UpdateMailboxMessageRequest,
    user: AuthenticatedUser,
    session: AsyncSession = SESSION_DEP,
) -> MailboxMessageRead:
    mailbox = await ensure_user_mailbox(session, user.id)
    message = await session.get(MailboxMessageModel, message_id)
    if message is None or message.mailbox_id != mailbox.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="mailbox message not found",
        )

    now = datetime.now(UTC)
    message.status = payload.status
    message.read_at = message.read_at or now
    if payload.status == "archived":
        message.archived_at = now
    if message.related_mention_id:
        mention = await session.get(UserMentionModel, message.related_mention_id)
        if mention is not None:
            mention.read_at = mention.read_at or now
            if payload.status == "read" and mention.status == "unread":
                mention.status = "read"
            elif payload.status == "archived":
                mention.status = "closed"
                mention.closed_at = now
    await session.commit()
    rows = await _message_rows(
        session,
        mailbox.id,
        status_filter=None,
        limit=100,
    )
    return next(row for row in rows if row.id == message_id)


@router.delete("/messages/{message_id}")
async def delete_mailbox_message(
    message_id: str,
    user: AuthenticatedUser,
    session: AsyncSession = SESSION_DEP,
) -> dict[str, bool]:
    mailbox = await ensure_user_mailbox(session, user.id)
    message = await session.get(MailboxMessageModel, message_id)
    if message is None or message.mailbox_id != mailbox.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="mailbox message not found",
        )

    if message.related_mention_id:
        mention = await session.get(UserMentionModel, message.related_mention_id)
        if mention is not None:
            now = datetime.now(UTC)
            mention.status = "closed"
            mention.read_at = mention.read_at or now
            mention.closed_at = now
    await session.delete(message)
    await session.commit()
    return {"deleted": True}