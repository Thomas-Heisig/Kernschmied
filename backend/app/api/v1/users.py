from __future__ import annotations

from typing import ClassVar, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.auth.authentication_service import AuthenticationService
from app.auth.dependencies import AuthenticatedUser, require_permission
from app.auth.models import UserContext
from app.contracts.auth import CurrentUserResponse
from app.contracts.users import (
    UpdateUserPreferencesRequest,
    UserCreateRequest,
    UserPreferencesResponse,
    UserRead,
    UserCreateResponse,
    GeneratedCredentials,
)
from app.storage.database import get_session
from app.storage.repositories.user import UserRepository
from app.auth.registration_service import RegistrationService, RegistrationError
from app.auth.password_service import PasswordService, PasswordPolicyError
from app.auth.session_management_service import revoke_all_sessions
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
USERS_READ_DEP = Depends(require_permission("users.read"))
USERS_UPDATE_DEP = Depends(require_permission("users.update"))
USERS_DELETE_DEP = Depends(require_permission("users.delete"))


@router.post("/", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    payload: UserCreateRequest = USER_CREATE_BODY,
    session: AsyncSession = SESSION_DEP,
    _user: UserContext = USERS_CREATE_DEP,
):
    # Use RegistrationService to ensure user, role, preferences and hierarchy
    # node are created within the same DB session/transaction. The router
    # performs the final commit/rollback.
    reg = RegistrationService(session=session)
    try:
        user, generated = await reg.register_user(
            username=payload.username,
            display_name=payload.display_name,
            email=payload.email,
            password=payload.password,
            generate_password=payload.generate_password,
            require_password_change=payload.require_password_change,
            roles=payload.roles,
            preferences=payload.preferences,
            create_default_workspace=payload.create_default_workspace,
            default_workspace_name=payload.default_workspace_name,
            invitation_token=None,
            auto_login=False,
        )

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        # Post-commit: attempt to project user to filesystem (best-effort)
        try:
            post = getattr(request.app.state, "post_commit_projection", None)
            if post is not None:
                await post.project_user(user.id)
        except Exception:
            # Do not surface projection errors to client
            logger = __import__("logging").getLogger(__name__)
            logger.exception("Workspace projection failed after user commit", extra={"user_id": user.id})

    except RegistrationError as re:
        code = str(re)
        if code == "USERNAME_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="username already exists",
            ) from re
        if code == "EMAIL_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="email already exists",
            ) from re
        if code == "PASSWORD_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="password required",
            ) from re
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(re)) from re

    generated_credentials = None
    if generated is not None:
        generated_credentials = GeneratedCredentials(temporary_password=generated)

    return UserCreateResponse(
        user=UserRead(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            is_active=bool(user.is_active),
            is_system=bool(user.is_system_admin),
            created_at=str(user.created_at),
            updated_at=str(user.updated_at),
        ),
        generated_credentials=generated_credentials,
    )


@router.get("/", response_model=list[UserRead])
async def list_users(
    request: Request,
    _perm: UserContext = USERS_READ_DEP,
    session: AsyncSession = SESSION_DEP,
):
    # no repo variable needed for this projection
    res = await session.execute(
        text(
            "SELECT id, username, display_name, email, is_active, is_system_admin, is_system_user, created_at, updated_at FROM users ORDER BY username"
        )
    )
    # Use mapping results to get named access and clearer typing for static checkers
    rows: list[dict[str, Any]] = [dict(r) for r in res.mappings().all()]
    result: list[UserRead] = []
    for r in rows:
        result.append(
            UserRead(
                id=str(r.get("id")),
                username=str(r.get("username")),
                display_name=str(r.get("display_name")),
                email=str(r.get("email")),
                is_active=bool(r.get("is_active")),
                is_system=bool(r.get("is_system_admin")),
                created_at=str(r.get("created_at")),
                updated_at=str(r.get("updated_at")),
            )
        )
    return result


class PasswordSuggestionRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class PasswordSuggestionResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")
    password: str


@router.post("/password-suggestion", response_model=PasswordSuggestionResponse)
async def suggest_password(
    request: Request,
    _perm: UserContext = USERS_CREATE_DEP,
):
    # Generate a secure password; never log or persist it.
    pwd = PasswordService()
    suggested = pwd.generate_password()
    return PasswordSuggestionResponse(password=suggested)


class PasswordResetRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    generate_password: bool = False
    password: str | None = None
    require_password_change: bool = True
    revoke_sessions: bool = True


class PasswordResetResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")
    temporary_password: str | None = None


@router.post("/{user_id}/password-reset", response_model=PasswordResetResponse)
async def reset_user_password(
    request: Request,
    user_id: str,
    payload: PasswordResetRequest = CHANGE_PASSWORD_BODY,
    _perm: UserContext = USERS_UPDATE_DEP,
    session: AsyncSession = SESSION_DEP,
):
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    from app.core.settings import settings

    if getattr(db_user, "is_system_user", False) or db_user.id == settings.development_admin_user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
            "code": "SYSTEM_USER_PROTECTED",
            "message": "Der Systembenutzer kann nicht auf diese Weise geändert werden.",
            "request_id": getattr(request.state, "request_id", None),
        })

    pwdsvc = PasswordService()
    temporary_password: str | None = None

    try:
        if payload.generate_password:
            temporary_password = pwdsvc.generate_password()
            pwdsvc.validate_password_policy(db_user.username, temporary_password)
            new_hash = pwdsvc.hash_password(temporary_password)
        else:
            if not payload.password:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={
                    "code": "PASSWORD_REQUIRED",
                    "message": "Kein Passwort angegeben.",
                })
            pwdsvc.validate_password_policy(db_user.username, payload.password)
            new_hash = pwdsvc.hash_password(payload.password)
    except PasswordPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={
            "code": getattr(exc, 'code', 'PASSWORD_POLICY_VIOLATION'),
            "message": str(exc),
        }) from exc

    try:
        await repo.update(
            db_user,
            {
                "password_hash": new_hash,
                "must_change_password": bool(payload.require_password_change),
            },
        )
        if payload.revoke_sessions:
            await revoke_all_sessions(session, db_user.id)
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return PasswordResetResponse(temporary_password=temporary_password)


@router.patch("/{user_id}", response_model=UserRead)
async def patch_user(
    request: Request,
    user_id: str,
    payload: UserPreferencesResponse | UserCreateRequest = USER_CREATE_BODY,
    _perm: UserContext = USERS_UPDATE_DEP,
    session: AsyncSession = SESSION_DEP,
):
    # Limited patch: allow display_name, email, is_active, roles
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    # Protect system users
    from app.core.settings import settings

    if getattr(db_user, "is_system_user", False) or db_user.id == settings.development_admin_user_id:
        # Reject attempts to deactivate or remove admin role
        changes = {}
        # Parse payload generically
        data = payload.model_dump() if hasattr(payload, "model_dump") else {}
        if "is_active" in data and data.get("is_active") is False:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "code": "SYSTEM_USER_PROTECTED",
                "message": "Der Systembenutzer kann nicht deaktiviert werden.",
                "request_id": getattr(request.state, "request_id", None),
            })
        if "roles" in data:
            # Deny role changes that would remove administrator
            # For simplicity, deny any role change for system users
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "code": "SYSTEM_USER_PROTECTED",
                "message": "Die Rollen des Systembenutzers können nicht geändert werden.",
                "request_id": getattr(request.state, "request_id", None),
            })

    changes: dict[str, object] = {}
    if hasattr(payload, "model_dump"):
        data = payload.model_dump(exclude_unset=True)
        if "display_name" in data:
            changes["display_name"] = data["display_name"]
        if "email" in data:
            changes["email"] = data["email"]
        if "is_active" in data:
            changes["is_active"] = data["is_active"]

    try:
        updated = await repo.update(db_user, changes)
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return UserRead(
        id=updated.id,
        username=updated.username,
        display_name=updated.display_name,
        email=updated.email,
        is_active=bool(updated.is_active),
        is_system=bool(updated.is_system_admin),
        created_at=str(updated.created_at),
        updated_at=str(updated.updated_at),
    )


@router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: str,
    _perm: UserContext = USERS_DELETE_DEP,
    session: AsyncSession = SESSION_DEP,
):
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    from app.core.settings import settings

    if getattr(db_user, "is_system_user", False) or db_user.id == settings.development_admin_user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
            "code": "SYSTEM_USER_PROTECTED",
            "message": "Der Systembenutzer kann nicht gelöscht werden.",
            "request_id": getattr(request.state, "request_id", None),
        })

    # Soft-delete for MVP
    try:
        await repo.update(db_user, {"is_active": False})
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return {"ok": True}


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
