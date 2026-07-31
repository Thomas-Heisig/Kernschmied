# F:\Kernschmied\backend\app\auth\dependencies.py

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping
from typing import Annotated, TypeAlias

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)

from app.auth.models import UserContext
from app.auth.permissions import (
    has_all_permissions,
    has_any_permission,
    has_permission,
    has_role,
)

AuthDependency: TypeAlias = Callable[
    ...,
    Awaitable[UserContext],
]


def get_request_id(
    request: Request,
) -> str | None:
    raw_request_id: object = getattr(
        request.state,
        "request_id",
        None,
    )

    if raw_request_id is None:
        return None

    request_id = str(
        raw_request_id,
    ).strip()

    return request_id or None


def auth_error(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Mapping[str, object] | None = None,
) -> HTTPException:
    normalized_details: dict[str, object] = {}

    if details is not None:
        normalized_details = dict(
            details,
        )

    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "details": normalized_details,
            "request_id": get_request_id(
                request,
            ),
        },
    )


async def get_current_user(
    request: Request,
) -> UserContext:
    """
    Liefert den durch die AuthenticationContextMiddleware gesetzten
    Benutzerkontext.
    """

    principal: object | None = getattr(
        request.state,
        "user",
        None,
    )

    if principal is None:
        return UserContext.anonymous()

    if isinstance(
        principal,
        UserContext,
    ):
        return principal

    try:
        return UserContext.from_principal(
            principal,
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise auth_error(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INVALID_AUTH_CONTEXT",
            message=("Der serverseitige Authentifizierungskontext ist ungültig."),
        ) from exc


CurrentUser = Annotated[
    UserContext,
    Depends(get_current_user),
]


async def require_authenticated_user(
    request: Request,
    user: CurrentUser,
) -> UserContext:
    if not user.authenticated:
        raise auth_error(
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_REQUIRED",
            message=("Für diese Aktion ist eine Anmeldung erforderlich."),
        )

    if not user.active:
        raise auth_error(
            request=request,
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_INACTIVE",
            message="Das Benutzerkonto ist nicht aktiv.",
        )

    return user


AuthenticatedUser = Annotated[
    UserContext,
    Depends(require_authenticated_user),
]


def normalize_permission(
    permission: str,
) -> str:
    normalized = permission.strip().casefold()

    if not normalized:
        raise ValueError("Eine Berechtigung darf nicht leer sein.")

    return normalized


def normalize_permissions(
    permissions: Iterable[str],
) -> tuple[str, ...]:
    normalized_permissions: list[str] = []

    for permission in permissions:
        normalized = permission.strip().casefold()

        if not normalized:
            continue

        if normalized not in normalized_permissions:
            normalized_permissions.append(
                normalized,
            )

    if not normalized_permissions:
        raise ValueError("Mindestens eine Berechtigung muss angegeben werden.")

    return tuple(
        normalized_permissions,
    )


def normalize_role(
    role: str,
) -> str:
    normalized = role.strip().casefold()

    if not normalized:
        raise ValueError("Eine Rolle darf nicht leer sein.")

    return normalized


def require_permission(
    permission: str,
) -> AuthDependency:
    normalized_permission = normalize_permission(
        permission,
    )

    async def dependency(
        request: Request,
        user: AuthenticatedUser,
    ) -> UserContext:
        if not has_permission(
            user,
            normalized_permission,
        ):
            raise auth_error(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code="PERMISSION_DENIED",
                message=("Für diese Aktion fehlt die erforderliche Berechtigung."),
                details={
                    "required_permission": (normalized_permission),
                },
            )

        return user

    return dependency


def require_all_permissions(
    permissions: Iterable[str],
) -> AuthDependency:
    normalized_permissions = normalize_permissions(
        permissions,
    )

    async def dependency(
        request: Request,
        user: AuthenticatedUser,
    ) -> UserContext:
        if not has_all_permissions(
            user,
            normalized_permissions,
        ):
            raise auth_error(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code="PERMISSIONS_DENIED",
                message=("Für diese Aktion fehlen erforderliche Berechtigungen."),
                details={
                    "required_permissions": list(
                        normalized_permissions,
                    ),
                    "mode": "all",
                },
            )

        return user

    return dependency


def require_any_permission(
    permissions: Iterable[str],
) -> AuthDependency:
    normalized_permissions = normalize_permissions(
        permissions,
    )

    async def dependency(
        request: Request,
        user: AuthenticatedUser,
    ) -> UserContext:
        if not has_any_permission(
            user,
            normalized_permissions,
        ):
            raise auth_error(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code="PERMISSIONS_DENIED",
                message=(
                    "Für diese Aktion fehlt eine der erforderlichen Berechtigungen."
                ),
                details={
                    "required_permissions": list(
                        normalized_permissions,
                    ),
                    "mode": "any",
                },
            )

        return user

    return dependency


def require_role(
    role: str,
) -> AuthDependency:
    normalized_role = normalize_role(
        role,
    )

    async def dependency(
        request: Request,
        user: AuthenticatedUser,
    ) -> UserContext:
        if not has_role(
            user,
            normalized_role,
        ):
            raise auth_error(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                code="ROLE_REQUIRED",
                message=("Für diese Aktion fehlt die erforderliche Rolle."),
                details={
                    "required_role": normalized_role,
                },
            )

        return user

    return dependency
