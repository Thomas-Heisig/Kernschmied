from __future__ import annotations

from typing import ClassVar

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.authentication_service import AuthenticationService
from app.auth.dependencies import AuthenticatedUser, require_permission
from app.auth.models import UserContext
from app.contracts.auth import CurrentUserResponse
from app.contracts.users import (
    UpdateUserPreferencesRequest,
    UserCreateRequest,
    UserPreferencesResponse,
    UserRead,
)
from app.storage.database import get_session
from app.storage.repositories.user import UserRepository
from app.users.preferences_service import (
    PreferencesInvalid,
    PreferencesNotFound,
    PreferencesUpdateFailed,
    get_preferences,
    update_preferences,
)
from app.users.profile_service import (
    ProfileEmailExists,
    ProfileNotFound,
    get_current_profile,
    update_current_profile,
)

router = APIRouter()

# Module-level dependency singletons to avoid function calls in argument defaults (B008)
SESSION_DEP = Depends(get_session)
USER_CREATE_BODY = Body(...)
UPDATE_PROFILE_BODY = Body(...)
UPDATE_PREFS_BODY = Body(...)
CHANGE_PASSWORD_BODY = Body(...)
USERS_CREATE_DEP = Depends(require_permission("users.create"))
USER_PROFILE_UPDATE_DEP = Depends(require_permission("user_profile.update"))
USER_PREFS_READ_DEP = Depends(require_permission("user_preferences.read"))
USER_PREFS_UPDATE_DEP = Depends(require_permission("user_preferences.update"))


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    payload: UserCreateRequest = USER_CREATE_BODY,
    session: AsyncSession = SESSION_DEP,
    _user: UserContext = USERS_CREATE_DEP,
):
    repo = UserRepository(session)

    existing = await repo.get_by_username(payload.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="username already exists"
        )

    password_hash = None

    obj = await repo.create(
        {
            "username": payload.username,
            "display_name": payload.display_name,
            "email": payload.email,
            "password_hash": password_hash,
        }
    )

    return UserRead(
        id=obj.id,
        username=obj.username,
        display_name=obj.display_name,
        email=obj.email,
        is_active=bool(obj.is_active),
        is_system=bool(obj.is_system_admin),
        created_at=str(obj.created_at),
        updated_at=str(obj.updated_at),
    )


class UpdateOwnProfileRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(
    request: Request,
    user: AuthenticatedUser,
    session: AsyncSession = SESSION_DEP,
):
    u = await get_current_profile(session, user.id)
    return CurrentUserResponse(
        id=u.id,
        username=u.username,
        display_name=u.display_name,
        email=u.email,
        authenticated=True,
        development_session=False,
        password_login_available=bool(u.password_hash),
        tenant=None,
        created_at=u.created_at,
        last_login_at=u.last_login_at,
    )


@router.patch("/me", response_model=CurrentUserResponse)
async def patch_me(
    request: Request,
    user: UserContext = USER_PROFILE_UPDATE_DEP,
    payload: UpdateOwnProfileRequest = UPDATE_PROFILE_BODY,
    session: AsyncSession = SESSION_DEP,
):
    if payload.display_name is None and payload.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PROFILE_UPDATE_FORBIDDEN",
                "message": "Mindestens ein Feld muss gesetzt sein.",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    try:
        updated = await update_current_profile(
            session, user.id, display_name=payload.display_name, email=payload.email
        )
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    except ProfileEmailExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PROFILE_EMAIL_ALREADY_EXISTS",
                "message": "E-Mail bereits vergeben.",
                "request_id": getattr(request.state, "request_id", None),
            },
        ) from exc
    except ProfileNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CURRENT_USER_NOT_FOUND",
                "message": "Benutzer nicht gefunden.",
                "request_id": getattr(request.state, "request_id", None),
            },
        ) from exc

    return CurrentUserResponse(
        id=updated.id,
        username=updated.username,
        display_name=updated.display_name,
        email=updated.email,
        authenticated=True,
        development_session=False,
        password_login_available=bool(updated.password_hash),
        tenant=None,
        created_at=updated.created_at,
        last_login_at=updated.last_login_at,
    )


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_my_preferences(
    request: Request,
    user: UserContext = USER_PREFS_READ_DEP,
    session: AsyncSession = SESSION_DEP,
):
    try:
        prefs = await get_preferences(session, user.id)
        return prefs
    except PreferencesNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CURRENT_USER_NOT_FOUND",
                "message": "Der aktuelle Benutzer wurde nicht gefunden.",
                "request_id": getattr(request.state, "request_id", None),
            },
        ) from exc
    except Exception:
        raise


@router.patch("/me/preferences", response_model=UserPreferencesResponse)
async def patch_my_preferences(
    request: Request,
    user: UserContext = USER_PREFS_UPDATE_DEP,
    payload: UpdateUserPreferencesRequest = UPDATE_PREFS_BODY,
    session: AsyncSession = SESSION_DEP,
):
    try:
        updated = await update_preferences(session, user.id, payload)
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    except PreferencesInvalid as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "USER_PREFERENCES_INVALID",
                "message": "Ungültige Präferenzen.",
                "request_id": getattr(request.state, "request_id", None),
            },
        ) from exc
    except PreferencesNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CURRENT_USER_NOT_FOUND",
                "message": "Der aktuelle Benutzer wurde nicht gefunden.",
                "request_id": getattr(request.state, "request_id", None),
            },
        ) from exc
    except PreferencesUpdateFailed as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "USER_PREFERENCES_UPDATE_FAILED",
                "message": "Konnte Präferenzen nicht aktualisieren.",
                "request_id": getattr(request.state, "request_id", None),
            },
        ) from exc

    return updated


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/me/password", status_code=status.HTTP_200_OK)
async def change_my_password(
    request: Request,
    user: AuthenticatedUser,
    payload: ChangePasswordRequest = CHANGE_PASSWORD_BODY,
    session: AsyncSession = SESSION_DEP,
):
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user.id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CURRENT_USER_NOT_FOUND",
                "message": "Benutzer nicht gefunden.",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    svc = AuthenticationService(session=session)
    try:
        await svc.change_password(
            db_user, payload.current_password, payload.new_password
        )
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    except Exception as exc:
        msg = str(exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PASSWORD_CHANGE_FAILED",
                "message": msg,
                "request_id": getattr(request.state, "request_id", None),
            },
        ) from exc

    return {"ok": True}
