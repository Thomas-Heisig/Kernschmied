# F:\Kernschmied\backend\app\auth\middleware.py

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.auth.models import UserContext

logger = logging.getLogger(__name__)


DEFAULT_ENVIRONMENT = "development"

ALLOWED_ENVIRONMENTS = {
    "development",
    "intranet",
    "internet",
}


class AuthenticationContextMiddleware(BaseHTTPMiddleware):
    """
    Stellt für jeden Request einen einheitlichen UserContext bereit.

    Diese Middleware führt noch keine Session-, OIDC- oder Passwortprüfung
    durch. Sie normalisiert einen bereits von einer vorgeschalteten
    Authentifizierung gesetzten Principal.

    Verhalten:

    development:
        Ohne vorhandenen Principal wird ein lokaler Entwicklungsbenutzer
        erzeugt.

    intranet/internet:
        Ohne vorhandenen Principal wird ein anonymer Benutzer gesetzt.

    Spätere Authentifizierungsmiddleware kann vor dieser Middleware
    beispielsweise `request.state.authenticated_principal` setzen.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        development_fallback_enabled: bool = True,
    ) -> None:
        super().__init__(app)

        self.development_fallback_enabled = development_fallback_enabled

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        environment = self._get_environment(request)

        principal = self._find_existing_principal(request)

        if principal is not None:
            user = self._normalize_principal(
                principal=principal,
                request=request,
            )
        elif environment == "development" and self.development_fallback_enabled:
            user = self._create_development_user(request)
        else:
            user = UserContext.anonymous()

        request.state.user = user
        request.state.principal = user

        response = await call_next(request)

        return response

    def _get_environment(
        self,
        request: Request,
    ) -> str:
        config_service = getattr(
            request.app.state,
            "config_service",
            None,
        )

        if config_service is None:
            return DEFAULT_ENVIRONMENT

        getter = getattr(
            config_service,
            "get",
            None,
        )

        if not callable(getter):
            return DEFAULT_ENVIRONMENT

        try:
            raw_environment = getter(
                "general",
                "environment",
                DEFAULT_ENVIRONMENT,
            )
        except (KeyError, TypeError, ValueError):
            logger.exception(
                "Environment could not be read from ConfigService",
            )
            return DEFAULT_ENVIRONMENT

        environment = str(raw_environment).strip().lower()

        if environment not in ALLOWED_ENVIRONMENTS:
            logger.error(
                "Unsupported environment in configuration",
                extra={
                    "environment": environment,
                },
            )
            return DEFAULT_ENVIRONMENT

        return environment

    @staticmethod
    def _find_existing_principal(
        request: Request,
    ) -> Any | None:
        """
        Prüft bewusst nur serverseitig gesetzte Request-State-Werte.

        Beliebige Client-Header wie X-User-ID oder X-Admin dürfen nicht
        ohne vertrauenswürdige Reverse-Proxy-Validierung verwendet werden.
        """

        candidates = (
            "authenticated_principal",
            "authenticated_user",
            "session_user",
        )

        for attribute_name in candidates:
            principal = getattr(
                request.state,
                attribute_name,
                None,
            )

            if principal is not None:
                return principal

        return None

    @staticmethod
    def _normalize_principal(
        *,
        principal: Any,
        request: Request,
    ) -> UserContext:
        try:
            return UserContext.from_principal(principal)
        except (TypeError, ValueError):
            logger.exception(
                "Invalid authenticated principal",
                extra={
                    "request_id": getattr(
                        request.state,
                        "request_id",
                        None,
                    ),
                    "principal_type": type(principal).__name__,
                },
            )

            return UserContext.anonymous()

    @staticmethod
    def _create_development_user(
        request: Request,
    ) -> UserContext:
        config_service = getattr(
            request.app.state,
            "config_service",
            None,
        )

        user_id = "local-user"
        user_name = "Lokaler Benutzer"

        if config_service is not None:
            getter = getattr(
                config_service,
                "get",
                None,
            )

            if callable(getter):
                try:
                    user_id = str(
                        getter(
                            "development",
                            "local_user_id",
                            user_id,
                        ),
                    )

                    user_name = str(
                        getter(
                            "development",
                            "local_user_name",
                            user_name,
                        ),
                    )
                except (KeyError, TypeError, ValueError):
                    logger.exception(
                        "Development user configuration could not be read",
                    )

        return UserContext.development_admin(
            user_id=user_id,
            name=user_name,
        )
