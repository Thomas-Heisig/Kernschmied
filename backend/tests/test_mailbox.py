from __future__ import annotations

import app.database.models
import app.services.mailbox_service as mailbox_service
import app.storage.models  # noqa: F401
import pytest
from app.database.base import Base
from app.database.models.mailbox import MailboxMessageModel, UserMailboxModel
from app.database.models.user import UserModel
from app.database.models.user_mention import UserMentionModel
from app.services.email_delivery_service import EmailDeliveryResult
from app.services.mailbox_service import (
    create_mailbox_message,
    deliver_mailbox_message_email,
    deliver_mention_to_mailbox,
    ensure_user_mailbox,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


@pytest.mark.asyncio
async def test_mention_is_delivered_to_the_recipient_mailbox() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        sender = UserModel(
            id="sender-id",
            username="sender",
            display_name="Sender",
        )
        recipient = UserModel(
            id="recipient-id",
            username="recipient",
            display_name="Recipient",
            email="recipient@example.test",
        )
        session.add_all([sender, recipient])
        await session.flush()

        mailbox = await ensure_user_mailbox(session, recipient.id)
        mention = UserMentionModel(
            id="mention-id",
            message_id="message-id",
            conversation_id="conversation-id",
            sender_user_id=sender.id,
            target_user_id=recipient.id,
            mention_text="@recipient Bitte prüfen.",
        )
        delivered = await deliver_mention_to_mailbox(session, mention)
        await session.flush()

        stored = await session.scalar(
            select(MailboxMessageModel).where(
                MailboxMessageModel.related_mention_id == mention.id
            )
        )

        assert mailbox.internal_address == "recipient-id@users.kernschmied.local"
        assert mailbox.external_email == "recipient@example.test"
        assert mailbox.email_delivery_enabled is False
        assert stored is delivered
        assert stored is not None
        assert stored.status == "unread"
        assert stored.channel == "internal"
        assert stored.delivery_status == "delivered"
        assert stored.email_to == "recipient@example.test"
        assert stored.delivery_metadata == {"email_eligible": True}

        duplicate = await ensure_user_mailbox(session, recipient.id)
        mailbox_count = len((await session.scalars(select(UserMailboxModel))).all())
        assert duplicate.id == mailbox.id
        assert mailbox_count == 1

        await ensure_user_mailbox(
            session,
            recipient.id,
            external_email=None,
            sync_external_email=True,
        )
        assert mailbox.external_email is None

    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("result", "expected_status"),
    [
        (EmailDeliveryResult(True, "smtp", "message-1"), "email_sent"),
        (
            EmailDeliveryResult(False, "smtp", error="connection refused"),
            "email_failed",
        ),
    ],
)
async def test_external_delivery_updates_the_outbox_status(
    monkeypatch: pytest.MonkeyPatch,
    result: EmailDeliveryResult,
    expected_status: str,
) -> None:
    monkeypatch.setattr(
        mailbox_service,
        "settings",
        type(
            "EmailSettings",
            (),
            {"email_delivery_enabled": True, "email_provider": "smtp"},
        )(),
    )
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    class DeliveryService:
        async def send(self, **kwargs: str) -> EmailDeliveryResult:
            assert kwargs["recipient"] == "recipient@example.test"
            return result

    async with AsyncSession(engine, expire_on_commit=False) as session:
        recipient = UserModel(
            id="recipient-id",
            username="recipient",
            display_name="Recipient",
            email="recipient@example.test",
        )
        session.add(recipient)
        await session.flush()
        mailbox = await ensure_user_mailbox(session, recipient.id)
        mailbox.email_delivery_enabled = True
        mailbox.email_provider = "smtp"
        message = await create_mailbox_message(
            session,
            recipient_user_id=recipient.id,
            sender_user_id=None,
            subject="Test",
            body="Test body",
            message_type="email_test",
        )

        await deliver_mailbox_message_email(
            session,
            message.id,
            delivery_service=DeliveryService(),  # type: ignore[arg-type]
        )

        assert message.delivery_status == expected_status
        if result.delivered:
            assert message.external_message_id == "message-1"
        else:
            assert message.delivery_metadata["email_error"] == "connection refused"

    await engine.dispose()