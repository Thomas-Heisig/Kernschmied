from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta


class SessionService:
    def __init__(self, *, lifetime_seconds: int = 8 * 60 * 60) -> None:
        self.lifetime_seconds = int(lifetime_seconds)

    def generate_token(self, length: int = 48) -> str:
        return secrets.token_urlsafe(length)

    def hash_token(self, token: str) -> str:
        # Use SHA-256 for server-side token hashing (token never stored in plaintext)
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def token_expiry(self) -> datetime:
        return datetime.now(UTC) + timedelta(seconds=self.lifetime_seconds)

    def is_expired(self, expires_at: datetime | None) -> bool:
        if expires_at is None:
            return False
        return expires_at <= datetime.now(UTC)
