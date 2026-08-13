from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password_service import PasswordService
from app.auth.session_service import SessionService
from app.core.settings import Settings
from app.database.models.user import UserModel
from app.storage.repositories.auth_session import AuthSessionRepository
from app.storage.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    pass


class AuthenticationService:
    def __init__(
        self, *, session: AsyncSession, settings: Settings | None = None
    ) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.session_repo = AuthSessionRepository(session)
        self.pwd = PasswordService()
        self.session_svc = SessionService()

    async def authenticate(self, username: str, password: str) -> UserModel:
        user = await self.user_repo.get_by_username(username)
        if user is None or user.password_hash is None:
            raise AuthenticationError("INVALID_CREDENTIALS")

        if not self.pwd.verify_password(password, user.password_hash):
            raise AuthenticationError("INVALID_CREDENTIALS")

        if not user.is_active:
            raise AuthenticationError("USER_DISABLED")

        # update last_login_at (use timezone-aware UTC)
        user.last_login_at = datetime.now(tz=UTC)
        changes: dict[str, object] = {}
        await self.user_repo.update(user, changes)

        return user

    async def create_session(
        self,
        user: UserModel,
        *,
        request_meta: dict[str, object] | None = None,
        authentication_method: str | None = None,
    ) -> str:
        token = self.session_svc.generate_token()
        token_hash = self.session_svc.hash_token(token)
        expires_at = self.session_svc.token_expiry()

        data: dict[str, object | None] = {
            "user_id": user.id,
            "session_token_hash": token_hash,
            "expires_at": expires_at,
            # request_meta values are untyped; cast to expected
            # string types when present
            "ip_address": cast(
                str | None, request_meta.get("ip") if request_meta else None
            ),
            "user_agent": cast(
                str | None, request_meta.get("ua") if request_meta else None
            ),
            "authentication_method": authentication_method,
        }

        await self.session_repo.create(data)
        # Persist the new session so subsequent requests can resolve it.
        try:
            await self.session.commit()
        except Exception:
            # If commit fails, attempt rollback and re-raise to surface the error.
            await self.session.rollback()
            raise

        return token

    async def resolve_session(self, token: str) -> object | None:
        token_hash = self.session_svc.hash_token(token)
        # Avoid logging token hashes or previews to prevent leaking sensitive data.
        logger.debug("Resolving session token")
        auth = await self.session_repo.get_by_token_hash(token_hash)
        if auth is None:
            logger.debug("No auth session row found for token hash")
        else:
            logger.debug(
                "Auth session row found",
                extra={
                    "session_id": getattr(auth, "id", None),
                    "user_id": getattr(auth, "user_id", None),
                    "revoked_at": getattr(auth, "revoked_at", None),
                    "expires_at": getattr(auth, "expires_at", None),
                },
            )
        if auth is None:
            return None

        if auth.revoked_at is not None:
            return None

        now = datetime.now(tz=UTC)
        # Normalize expires_at to timezone-aware UTC if DB returned a naive datetime
        expires_at = getattr(auth, "expires_at", None)
        if expires_at is not None and expires_at.tzinfo is None:
            try:
                expires_at = expires_at.replace(tzinfo=UTC)
            except Exception:
                # Fall back to treating as not expired if normalization fails
                expires_at = None

        if expires_at is not None and expires_at <= now:
            return None

        user = await self.user_repo.get_by_id(auth.user_id)
        if user is None:
            return None

        # Use the canonical principal mapper to produce the same shape
        # as the middleware-resolved principal. This ensures consistency
        # between session-based auth and ORM-resolved principals.

        # Return the resolved DB user model here. The middleware expects
        # a model-like object so it can build a canonical principal itself.
        # Returning the user model keeps responsibility for principal
        # construction in the middleware layer and avoids double-mapping.
        return user

    async def logout(self, token: str) -> None:
        token_hash = self.session_svc.hash_token(token)
        auth = await self.session_repo.get_by_token_hash(token_hash)
        if auth is None:
            return
        await self.session_repo.revoke(auth, when=datetime.now(tz=UTC))
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def change_password(
        self, user: UserModel, current_password: str, new_password: str
    ) -> None:
        if not self.pwd.verify_password(current_password, user.password_hash or ""):
            raise AuthenticationError("INVALID_CREDENTIALS")

        self.pwd.validate_password_policy(user.username, new_password)
        new_hash = self.pwd.hash_password(new_password)
        changes: dict[str, str] = {"password_hash": new_hash}
        await self.user_repo.update(user, changes)

    async def authenticate_development_admin(self) -> UserModel:
        """Return or create the configured development admin user.

        This method enforces that it is only usable in a development
        environment and that the corresponding setting is enabled.
        """
        from app.core.settings import settings

        if (
            getattr(settings, "app_environment", None) is None
            or settings.app_environment.name.lower() != "development"
        ):
            raise AuthenticationError("NOT_ALLOWED")

        if not getattr(settings, "development_admin_login_enabled", False):
            raise AuthenticationError("NOT_ALLOWED")

        # Try to find existing admin by configured id or username
        user = await self.user_repo.get_by_id(settings.development_admin_user_id)
        if user is None:
            user = await self.user_repo.get_by_username(
                settings.development_admin_username
            )

        if user is None:
            data: dict[str, object | None] = {
                "id": settings.development_admin_user_id,
                "username": settings.development_admin_username,
                "display_name": settings.development_admin_display_name,
                "email": None,
                "password_hash": None,
                "is_active": True,
                "is_system_admin": True,
                "is_system_user": True,
            }
            user = await self.user_repo.create(data)
        else:
            # Ensure flags are set on existing admin user
            updated = False
            if not getattr(user, "is_system_admin", False):
                user.is_system_admin = True
                updated = True
            if not getattr(user, "is_system_user", False):
                user.is_system_user = True
                updated = True
            if updated:
                await self.user_repo.update(user, {})

        return user
