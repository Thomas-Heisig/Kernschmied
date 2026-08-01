# backend/app/auth/development_identity.py

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class DevelopmentIdentityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool,
        user_id: str = "development-user",
    ) -> None:
        super().__init__(app)
        self._enabled = enabled
        self._user_id = user_id

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if self._enabled and not hasattr(request.state, "principal"):
            request.state.principal = {
                "id": self._user_id,
                "authentication_method": "development",
            }

        return await call_next(request)
