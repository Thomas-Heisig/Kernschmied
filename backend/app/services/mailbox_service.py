from __future__ import annotations

from pydantic import JsonValue
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.database.models.mailbox import MailboxMessageModel, UserMailboxModel
from app.database.models.user import UserModel
from app.database.models.user_mention import UserMentionModel
from app.services.email_delivery_service import EmailDeliveryService


def internal_mailbox_address(user_id: str) -> str:
    return f"{user_id}@users.kernschmied.local"


async def ensure_user_mailbox(
    session: AsyncSession,
    user_id: str,
    *,
    external_email: str | None = None,
    sync_external_email: bool = False,
) -> UserMailboxModel:
    result = await session.execute(
        select(UserMailboxModel).where(UserMailboxModel.user_id == user_id)
    )
    mailbox = result.scalar_one_or_none()
    if mailbox is not None:
        if sync_external_email and mailbox.external_email != external_email:
            mailbox.external_email = external_email
            session.add(mailbox)
        _configure_email_delivery(mailbox)
        return mailbox

    if external_email is None:
        external_email = await session.scalar(
            select(UserModel.email).where(UserModel.id == user_id)
        )
    mailbox = UserMailboxModel(
        user_id=user_id,
        internal_address=internal_mailbox_address(user_id),
        external_email=external_email,
    )
    _configure_email_delivery(mailbox)
    session.add(mailbox)
    await session.flush()
    return mailbox


def _configure_email_delivery(mailbox: UserMailboxModel) -> None:
    mailbox.email_delivery_enabled = bool(
        settings.email_delivery_enabled and mailbox.external_email
    )
    mailbox.email_provider = (
        settings.email_provider if mailbox.email_delivery_enabled else None
    )


async def create_mailbox_message(
    session: AsyncSession,
    *,
    recipient_user_id: str,
    sender_user_id: str | None,
    subject: str,
    body: str,
    message_type: str,
    related_mention_id: str | None = None,
    delivery_metadata: dict[str, JsonValue] | None = None,
) -> MailboxMessageModel:
    mailbox = await ensure_user_mailbox(session, recipient_user_id)
    email_pending = bool(
        mailbox.email_delivery_enabled
        and mailbox.external_email
        and mailbox.email_provider
    )
    message = MailboxMessageModel(
        mailbox_id=mailbox.id,
        sender_user_id=sender_user_id,
        related_mention_id=related_mention_id,
        subject=subject,
        body=body,
        message_type=message_type,
        status="unread",
        channel="internal",
        delivery_status="email_pending" if email_pending else "delivered",
        email_to=mailbox.external_email,
        email_provider=mailbox.email_provider,
        delivery_metadata={
            "email_eligible": bool(mailbox.external_email),
            **(delivery_metadata or {}),
        },
    )
    session.add(message)
    await session.flush()
    return message


async def queue_welcome_email(
    session: AsyncSession,
    *,
    user_id: str,
    display_name: str,
) -> MailboxMessageModel:
    return await create_mailbox_message(
        session,
        recipient_user_id=user_id,
        sender_user_id=None,
        subject="Willkommen bei Kernschmied",
        body=(
            f"Hallo {display_name},\n\n"
            "dein Kernschmied-Benutzerkonto und dein persönliches Postfach "
            "wurden erfolgreich eingerichtet."
        ),
        message_type="welcome",
    )


async def deliver_mailbox_message_email(
    session: AsyncSession,
    message_id: str,
    *,
    delivery_service: EmailDeliveryService | None = None,
) -> MailboxMessageModel | None:
    message = await session.get(MailboxMessageModel, message_id)
    if message is None or message.delivery_status != "email_pending":
        return message
    if not message.email_to:
        message.delivery_status = "internal_only"
        return message

    result = await (delivery_service or EmailDeliveryService()).send(
        recipient=message.email_to,
        subject=message.subject,
        body=message.body,
    )
    metadata = dict(message.delivery_metadata or {})
    metadata["email_provider"] = result.provider
    if result.delivered:
        message.delivery_status = "email_sent"
        message.external_message_id = result.external_message_id
        metadata.pop("email_error", None)
    else:
        message.delivery_status = "email_failed"
        metadata["email_error"] = result.error or "unknown delivery error"
    message.delivery_metadata = metadata
    session.add(message)
    return message


async def deliver_pending_email_for_user(
    session: AsyncSession,
    user_id: str,
) -> None:
    mailbox = await ensure_user_mailbox(session, user_id)
    message_ids = list(
        (
            await session.scalars(
                select(MailboxMessageModel.id).where(
                    MailboxMessageModel.mailbox_id == mailbox.id,
                    MailboxMessageModel.delivery_status == "email_pending",
                )
            )
        ).all()
    )
    for message_id in message_ids:
        await deliver_mailbox_message_email(session, message_id)


async def safely_deliver_pending_email_for_user(
    session: AsyncSession,
    user_id: str,
) -> None:
    try:
        await deliver_pending_email_for_user(session, user_id)
        await session.commit()
    except Exception:
        await session.rollback()


async def deliver_mention_to_mailbox(
    session: AsyncSession,
    mention: UserMentionModel,
) -> MailboxMessageModel:
    return await create_mailbox_message(
        session,
        recipient_user_id=mention.target_user_id,
        sender_user_id=mention.sender_user_id,
        related_mention_id=mention.id,
        subject="Neue Benutzeranfrage",
        body=mention.mention_text,
        message_type="mention",
    )