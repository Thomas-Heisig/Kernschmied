# F:\Kernschmied\backend\app\auth\middleware.py

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.auth.models import UserContext
from app.core.settings import settings
from app.auth.authentication_service import AuthenticationService
from app.storage.database import get_session_factory

logger = logging.getLogger(__name__)


DEFAULT_ENVIRONMENT = "development"

ALLOWED_ENVIRONMENTS = {"development", "intranet", "internet"}


class AuthenticationContextMiddleware(BaseHTTPMiddleware):
    """Provide a normalized `UserContext` on each request and a canonical principal.

    This middleware keeps responsibilities small and delegates work to
    helper methods for clarity and testability.
    Canonical request.state fields set by this middleware:

    - `request.state.user` : always a `UserContext` instance
    - `request.state.principal` : original principal (DB model) or None
    - `request.state.security_context` : reserved for later (None)
    """

    def __init__(self, app: ASGIApp, *, development_fallback_enabled: bool = True) -> None:
        super().__init__(app)
        self.development_fallback_enabled = development_fallback_enabled

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        # Prepare a placeholder for security_context
        request.state.security_context = None

        environment = self._get_environment(request)

        # 1) If a principal was already set by upstream components, prefer it
        principal = self._find_existing_principal(request)
        if principal is not None:
            user = self._normalize_principal(principal=principal, request=request)
            request.state.principal = principal
            request.state.user = user

            return await call_next(request)

        # 2) Try resolving server-side session only when a session cookie exists
        token = self._extract_session_token(request)
        if token:
            session_factory = getattr(request.app.state, "session_factory", None)
            if session_factory is None:
                try:
                    session_factory = get_session_factory()
                except Exception:
                    session_factory = None

            if session_factory is not None:
                try:
                    async with session_factory() as db_session:
                        auth_svc = AuthenticationService(session=db_session)
                        resolved = await self._resolve_authenticated_user(auth_svc, token)
                        if resolved is not None:
                            # principal is the DB model; user is normalized context
                            request.state.principal = resolved
                            request.state.user = self._normalize_principal(principal=resolved, request=request)
                            return await call_next(request)
                except Exception:
                    # Do not propagate auth lookup errors to break request handling
                    logger.exception("Error while resolving session token")

        # 3) No principal and no valid session found -> apply fallback
        if environment == "development" and self.development_fallback_enabled:
            user = self._create_development_user(request)
            request.state.principal = None
            request.state.user = user
        else:
            request.state.principal = None
            request.state.user = UserContext.anonymous()

        return await call_next(request)

    # ----- helpers -------------------------------------------------

    def _extract_session_token(self, request: Request) -> Optional[str]:
        cookie_name = getattr(settings, "session_cookie_name", "kernschmied_session")
        token = request.cookies.get(cookie_name)
        return token if token else None

    async def _resolve_authenticated_user(self, auth_svc: AuthenticationService, token: str) -> Any | None:
        # Resolve session; AuthenticationService handles expiry and revocation checks
        try:
            resolved = await auth_svc.resolve_session(token)
            if resolved is None:
                logger.info("Session token did not resolve to a principal", extra={"token_hash_preview": token[:8]})
            else:
                # Log basic identity info to help debugging resolution issues
                try:
                    uid = getattr(resolved, "id", None)
                    uname = getattr(resolved, "username", None) or getattr(resolved, "display_name", None)
                except Exception:
                    uid = None
                    uname = None

                logger.info(
                    "Resolved session token to user",
                    extra={"user_id": uid, "username": uname},
                )

            return resolved
        except Exception:
            logger.exception("Error while resolving session token")
            return None

    def _get_environment(self, request: Request) -> str:
        config_service = getattr(request.app.state, "config_service", None)
        if config_service is None:
            return DEFAULT_ENVIRONMENT

        getter = getattr(config_service, "get", None)
        if not callable(getter):
            return DEFAULT_ENVIRONMENT

        try:
            raw_environment = getter("general", "environment", DEFAULT_ENVIRONMENT)
        except (KeyError, TypeError, ValueError):
            logger.exception("Environment could not be read from ConfigService")
            return DEFAULT_ENVIRONMENT

        environment = str(raw_environment).strip().lower()
        if environment not in ALLOWED_ENVIRONMENTS:
            logger.error("Unsupported environment in configuration", extra={"environment": environment})
            return DEFAULT_ENVIRONMENT

        return environment

    @staticmethod
    def _find_existing_principal(request: Request) -> Any | None:
        # Check canonical names only; keep search narrow to server-set values
        for name in ("principal", "user"):
            p = getattr(request.state, name, None)
            if p is not None:
                return p

        return None

    @staticmethod
    def _normalize_principal(*, principal: Any, request: Request) -> UserContext:
        try:
            return UserContext.from_principal(principal)
        except (TypeError, ValueError):
            logger.exception(
                "Invalid authenticated principal",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "principal_type": type(principal).__name__,
                },
            )
            return UserContext.anonymous()

    @staticmethod
    def _create_development_user(request: Request) -> UserContext:
        config_service = getattr(request.app.state, "config_service", None)
        user_id = "local-user"
        user_name = "Local Development User"
        if config_service is not None:
            getter = getattr(config_service, "get", None)
            if callable(getter):
                try:
                    user_id = str(getter("development", "local_user_id", user_id))
                    user_name = str(getter("development", "local_user_name", user_name))
                except (KeyError, TypeError, ValueError):
                    logger.exception("Development user configuration could not be read")

        return UserContext.development_admin(user_id=user_id, name=user_name)
