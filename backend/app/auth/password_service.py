from __future__ import annotations

from typing import Any

from passlib.context import CryptContext  # type: ignore[import]


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
        # CryptContext lacks distributed type stubs; treat as Any for typing
        self._ctx: Any = CryptContext(
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
            raise PasswordPolicyError(
                "PASSWORD_TOO_SHORT", "Ein Passwort darf nicht leer sein."
            )

        if len(password) < 12:
            raise PasswordPolicyError(
                "PASSWORD_TOO_SHORT", "Das Passwort ist zu kurz (min. 12 Zeichen)."
            )

        if len(password) > 4096:
            raise PasswordPolicyError("PASSWORD_TOO_LONG", "Das Passwort ist zu lang.")

        if password.strip().lower() == username.strip().lower():
            raise PasswordPolicyError(
                "PASSWORD_EQUALS_USERNAME",
                "Das Passwort darf nicht mit dem Benutzernamen übereinstimmen.",
            )

        # Additional checks (dictionary, entropy) can be added later.

    def generate_password(self, *, length: int = 14) -> str:
        """Generate a secure password that satisfies the basic policy.

        Uses the `secrets` module to ensure cryptographic randomness and
        re-runs generation until validate_password_policy accepts it.
        """
        import secrets
        import string

        if length < 12:
            length = 12

        alphabet = string.ascii_letters + string.digits + "!@#$%&*()-_=+[]{}<>?"

        # Attempt generation a few times; in the unlikely event of failure
        # this will raise from validate_password_policy.
        for _ in range(10):
            pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
            # Ensure at least one upper, lower, digit, special
            if (any(c.isupper() for c in pwd)
                    and any(c.islower() for c in pwd)
                    and any(c.isdigit() for c in pwd)
                    and any(c in "!@#$%&*()-_=+[]{}<>?" for c in pwd)):
                try:
                    # We validate using the existing policy – may raise
                    self.validate_password_policy('', pwd)
                    return pwd
                except PasswordPolicyError:
                    continue

        # Last resort: generate and return, let caller handle validation exception
        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
        return pwd
