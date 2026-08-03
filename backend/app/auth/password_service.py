from __future__ import annotations

from passlib.context import CryptContext
from typing import Tuple


class PasswordPolicyError(ValueError):
    code: str

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class PasswordService:
    """Encapsulates password hashing and policy validation.

    Uses Argon2id via passlib CryptContext.
    """

    def __init__(self) -> None:
        self._ctx = CryptContext(
            schemes=["argon2"],
            deprecated="auto",
            # Defaults are safe for MVP; tuning can be done in configuration
        )

    def hash_password(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify_password(self, password: str, hash_: str) -> bool:
        return self._ctx.verify(password, hash_)

    def needs_rehash(self, hash_: str) -> bool:
        return self._ctx.needs_update(hash_)

    def validate_password_policy(self, username: str, password: str) -> None:
        if not password:
            raise PasswordPolicyError("PASSWORD_TOO_SHORT", "Ein Passwort darf nicht leer sein.")

        if len(password) < 12:
            raise PasswordPolicyError("PASSWORD_TOO_SHORT", "Das Passwort ist zu kurz (min. 12 Zeichen).")

        if len(password) > 4096:
            raise PasswordPolicyError("PASSWORD_TOO_LONG", "Das Passwort ist zu lang.")

        if password.strip().lower() == username.strip().lower():
            raise PasswordPolicyError("PASSWORD_EQUALS_USERNAME", "Das Passwort darf nicht mit dem Benutzernamen übereinstimmen.")

        # Additional checks (dictionary, entropy) can be added later.
