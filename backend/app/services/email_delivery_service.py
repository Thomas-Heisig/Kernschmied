from __future__ import annotations

import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid

from app.core.settings import Settings, settings


@dataclass(frozen=True, slots=True)
class EmailDeliveryResult:
    delivered: bool
    provider: str
    external_message_id: str | None = None
    error: str | None = None


class EmailDeliveryService:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config

    @property
    def enabled(self) -> bool:
        return bool(
            self.config.email_delivery_enabled
            and self.config.email_provider == "smtp"
            and self.config.smtp_host
        )

    async def send(
        self,
        *,
        recipient: str,
        subject: str,
        body: str,
    ) -> EmailDeliveryResult:
        if not self.enabled:
            return EmailDeliveryResult(
                delivered=False,
                provider=self.config.email_provider,
                error="email delivery is disabled",
            )
        try:
            message_id = await asyncio.to_thread(
                self._send_smtp,
                recipient,
                subject,
                body,
            )
        except (OSError, smtplib.SMTPException) as exc:
            return EmailDeliveryResult(
                delivered=False,
                provider=self.config.email_provider,
                error=str(exc)[:500],
            )
        return EmailDeliveryResult(
            delivered=True,
            provider=self.config.email_provider,
            external_message_id=message_id,
        )

    def _send_smtp(self, recipient: str, subject: str, body: str) -> str:
        message = EmailMessage()
        message["Message-ID"] = make_msgid(domain="kernschmied.local")
        message["From"] = self.config.email_from_address
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(
            self.config.smtp_host,
            self.config.smtp_port,
            timeout=10,
        ) as client:
            if self.config.smtp_starttls:
                client.starttls()
            if self.config.smtp_username:
                client.login(
                    self.config.smtp_username,
                    self.config.smtp_password.get_secret_value(),
                )
            client.send_message(message)
        return str(message["Message-ID"])