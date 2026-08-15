"""create user mailboxes

Revision ID: 0022_create_user_mailboxes
Revises: 0021_create_user_mentions
Create Date: 2026-08-15 19:00:00.000000
"""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0022_create_user_mailboxes"
down_revision = "0021_create_user_mentions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "user_mailboxes" not in tables:
        op.create_table(
            "user_mailboxes",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(length=36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("internal_address", sa.String(length=320), nullable=False),
            sa.Column("external_email", sa.String(length=320), nullable=True),
            sa.Column(
                "email_delivery_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            sa.Column("email_provider", sa.String(length=50), nullable=True),
            sa.Column("provider_settings", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("user_id", name="uq_user_mailboxes_user"),
            sa.UniqueConstraint(
                "internal_address",
                name="uq_user_mailboxes_internal_address",
            ),
        )

    if "mailbox_messages" not in tables:
        op.create_table(
            "mailbox_messages",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column(
                "mailbox_id",
                sa.String(length=36),
                sa.ForeignKey("user_mailboxes.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "sender_user_id",
                sa.String(length=36),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "related_mention_id",
                sa.String(length=36),
                sa.ForeignKey("user_mentions.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column("subject", sa.String(length=500), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("message_type", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("channel", sa.String(length=20), nullable=False),
            sa.Column("delivery_status", sa.String(length=30), nullable=False),
            sa.Column("email_to", sa.String(length=320), nullable=True),
            sa.Column("email_provider", sa.String(length=50), nullable=True),
            sa.Column(
                "external_message_id", sa.String(length=255), nullable=True
            ),
            sa.Column("delivery_metadata", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint(
                "related_mention_id",
                name="uq_mailbox_messages_related_mention",
            ),
        )
        op.create_index(
            "ix_mailbox_messages_mailbox_status",
            "mailbox_messages",
            ["mailbox_id", "status"],
        )
        op.create_index(
            "ix_mailbox_messages_created_at",
            "mailbox_messages",
            ["created_at"],
        )

    now = datetime.now(UTC)
    mailbox_table = sa.table(
        "user_mailboxes",
        sa.column("id", sa.String),
        sa.column("user_id", sa.String),
        sa.column("internal_address", sa.String),
        sa.column("external_email", sa.String),
        sa.column("email_delivery_enabled", sa.Boolean),
        sa.column("email_provider", sa.String),
        sa.column("provider_settings", sa.JSON),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    users = sa.table("users", sa.column("id", sa.String), sa.column("email", sa.String))
    existing_user_ids = set(bind.execute(sa.select(mailbox_table.c.user_id)).scalars())
    user_rows = bind.execute(sa.select(users.c.id, users.c.email)).all()
    for user_id, email in user_rows:
        if user_id in existing_user_ids:
            continue
        bind.execute(
            mailbox_table.insert().values(
                id=str(uuid4()),
                user_id=user_id,
                internal_address=f"{user_id}@users.kernschmied.local",
                external_email=email,
                email_delivery_enabled=False,
                email_provider=None,
                provider_settings={},
                created_at=now,
                updated_at=now,
            )
        )

    mailbox_messages = sa.table(
        "mailbox_messages",
        sa.column("id", sa.String),
        sa.column("mailbox_id", sa.String),
        sa.column("sender_user_id", sa.String),
        sa.column("related_mention_id", sa.String),
        sa.column("subject", sa.String),
        sa.column("body", sa.Text),
        sa.column("message_type", sa.String),
        sa.column("status", sa.String),
        sa.column("channel", sa.String),
        sa.column("delivery_status", sa.String),
        sa.column("email_to", sa.String),
        sa.column("email_provider", sa.String),
        sa.column("external_message_id", sa.String),
        sa.column("delivery_metadata", sa.JSON),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("read_at", sa.DateTime(timezone=True)),
        sa.column("archived_at", sa.DateTime(timezone=True)),
    )
    mentions = sa.table(
        "user_mentions",
        sa.column("id", sa.String),
        sa.column("sender_user_id", sa.String),
        sa.column("target_user_id", sa.String),
        sa.column("mention_text", sa.Text),
        sa.column("status", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("read_at", sa.DateTime(timezone=True)),
        sa.column("closed_at", sa.DateTime(timezone=True)),
    )
    mailbox_rows = bind.execute(
        sa.select(
            mailbox_table.c.user_id,
            mailbox_table.c.id,
            mailbox_table.c.external_email,
            mailbox_table.c.email_provider,
        )
    ).all()
    mailboxes_by_user = {
        user_id: (mailbox_id, external_email, email_provider)
        for user_id, mailbox_id, external_email, email_provider in mailbox_rows
    }
    existing_mentions = set(
        bind.execute(
            sa.select(mailbox_messages.c.related_mention_id).where(
                mailbox_messages.c.related_mention_id.is_not(None)
            )
        ).scalars()
    )
    for mention in bind.execute(sa.select(mentions)).mappings():
        if mention["id"] in existing_mentions:
            continue
        mailbox_data = mailboxes_by_user.get(mention["target_user_id"])
        if mailbox_data is None:
            continue
        mailbox_id, external_email, email_provider = mailbox_data
        is_archived = mention["status"] in {"answered", "closed"}
        bind.execute(
            mailbox_messages.insert().values(
                id=str(uuid4()),
                mailbox_id=mailbox_id,
                sender_user_id=mention["sender_user_id"],
                related_mention_id=mention["id"],
                subject="Neue Benutzeranfrage",
                body=mention["mention_text"],
                message_type="mention",
                status="archived" if is_archived else mention["status"],
                channel="internal",
                delivery_status="delivered",
                email_to=external_email,
                email_provider=email_provider,
                external_message_id=None,
                delivery_metadata={"email_eligible": bool(external_email)},
                created_at=mention["created_at"],
                read_at=mention["read_at"],
                archived_at=mention["closed_at"] if is_archived else None,
            )
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "mailbox_messages" in tables:
        op.drop_table("mailbox_messages")
    if "user_mailboxes" in tables:
        op.drop_table("user_mailboxes")