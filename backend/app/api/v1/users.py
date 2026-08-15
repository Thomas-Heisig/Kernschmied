from __future__ import annotations

from typing import Any, ClassVar, cast

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.authentication_service import AuthenticationService
from app.auth.dependencies import AuthenticatedUser, require_permission
from app.auth.models import UserContext
from app.auth.password_service import PasswordPolicyError, PasswordService
from app.auth.registration_service import RegistrationError, RegistrationService
from app.auth.session_management_service import revoke_all_sessions
from app.contracts.auth import CurrentUserResponse
from app.contracts.users import (
    AccessLevel,
    GeneratedCredentials,
    UpdateUserPreferencesRequest,
    UserCreateRequest,
    UserCreateResponse,
    UserPreferencesResponse,
    UserRead,
    UserUpdateRequest,
)
from app.database.models.auth_session import AuthSessionModel
from app.database.models.user import UserModel
from app.database.models.user_preference import UserPreferenceModel
from app.database.models.user_role import RoleModel, UserRoleModel
from app.hierarchy.repository import HierarchyRepository
from app.services.mailbox_service import (
    ensure_user_mailbox,
    safely_deliver_pending_email_for_user,
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
USERS_READ_DEP = Depends(require_permission("users.read"))
USERS_UPDATE_DEP = Depends(require_permission("users.update"))
USERS_DELETE_DEP = Depends(require_permission("users.delete"))

ACCESS_LEVEL_ROLES: dict[AccessLevel, str] = {
    "guest": "guest",
    "internal": "user",
    "admin": "admin",
}


class UpdateOwnProfileRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None


def _access_level_from_roles(roles: list[str] | str | None) -> AccessLevel:
    if isinstance(roles, str):
        role_names = {role.strip() for role in roles.split(",") if role.strip()}
    else:
        role_names = set(roles or [])
    if "admin" in role_names:
        return "admin"
    if role_names.intersection({"user", "internal", "intern"}):
        return "internal"
    return "guest"


async def _assign_access_level(
    session: AsyncSession,
    user_id: str,
    access_level: AccessLevel,
) -> None:
    role_name = ACCESS_LEVEL_ROLES[access_level]
    result = await session.execute(select(RoleModel).where(RoleModel.name == role_name))
    role = result.scalar_one_or_none()
    if role is None and role_name in {"guest", "user"}:
        role = RoleModel(
            name=role_name,
            display_name="Gast" if role_name == "guest" else "Intern",
        )
        session.add(role)
        await session.flush()
    if role is None or not role.assignable:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="access level is not assignable",
        )

    await session.execute(delete(UserRoleModel).where(UserRoleModel.user_id == user_id))
    session.add(UserRoleModel(user_id=user_id, role_id=role.id))


async def _get_access_level(session: AsyncSession, user_id: str) -> AccessLevel:
    result = await session.execute(
        select(RoleModel.name)
        .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
        .where(UserRoleModel.user_id == user_id)
    )
    return _access_level_from_roles(list(result.scalars().all()))


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
            roles=payload.roles or [ACCESS_LEVEL_ROLES[payload.access_level]],
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
        await safely_deliver_pending_email_for_user(session, user.id)
        # Post-commit: attempt to project user to filesystem (best-effort)
        try:
            post = getattr(request.app.state, "post_commit_projection", None)
            if post is not None:
                await post.project_user(user.id)
        except Exception:
            # Do not surface projection errors to client
            logger = __import__("logging").getLogger(__name__)
            logger.exception("Workspace projection failed after user commit", extra={"user_id": user.id})

    except PasswordPolicyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except RegistrationError as re:
        await session.rollback()
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
            access_level=(
                _access_level_from_roles(payload.roles)
                if payload.roles
                else payload.access_level
            ),
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
                 """
                 SELECT users.id, users.username, users.display_name, users.email,
                     users.is_active, users.is_system_admin, users.is_system_user,
                     users.created_at, users.updated_at,
                     GROUP_CONCAT(roles.name) AS roles
                 FROM users
                 LEFT JOIN user_roles ON user_roles.user_id = users.id
                 LEFT JOIN roles ON roles.id = user_roles.role_id
                 GROUP BY users.id
                 ORDER BY users.username
                 """
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
                email=str(r["email"]) if r.get("email") is not None else None,
                is_active=bool(r.get("is_active")),
                is_system=bool(
                    r.get("is_system_admin") or r.get("is_system_user")
                ),
                access_level=_access_level_from_roles(r.get("roles")),
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


@router.patch("/me", response_model=CurrentUserResponse)
async def patch_me(
    request: Request,
    user: AuthenticatedUser,
    payload: UpdateOwnProfileRequest = UPDATE_PROFILE_BODY,
    session: AsyncSession = SESSION_DEP,
):
    return await _patch_me_impl(request, user, payload, session)


@router.patch("/{user_id}", response_model=UserRead)
async def patch_user(
    request: Request,
    user_id: str,
    payload: UserUpdateRequest = USER_CREATE_BODY,
    _perm: UserContext = USERS_UPDATE_DEP,
    session: AsyncSession = SESSION_DEP,
):
    # Limited patch: allow display_name, email, is_active, roles
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    data = payload.model_dump(exclude_unset=True)

    # Protect system users
    from app.core.settings import settings

    if getattr(db_user, "is_system_user", False) or db_user.id == settings.development_admin_user_id:
        # Reject attempts to deactivate or remove admin role
        changes = {}
        if "is_active" in data and data.get("is_active") is False:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "code": "SYSTEM_USER_PROTECTED",
                "message": "Der Systembenutzer kann nicht deaktiviert werden.",
                "request_id": getattr(request.state, "request_id", None),
            })
        if "roles" in data or "access_level" in data:
            # Deny role changes that would remove administrator
            # For simplicity, deny any role change for system users
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "code": "SYSTEM_USER_PROTECTED",
                "message": "Die Rollen des Systembenutzers können nicht geändert werden.",
                "request_id": getattr(request.state, "request_id", None),
            })

    changes: dict[str, object] = {}
    current_access_level = await _get_access_level(session, db_user.id)
    if "display_name" in data:
        changes["display_name"] = data["display_name"]
    if "email" in data:
        changes["email"] = data["email"]
    if "is_active" in data:
        changes["is_active"] = data["is_active"]
    requested_access_level = cast(AccessLevel | None, data.get("access_level"))

    try:
        if requested_access_level is not None:
            await _assign_access_level(session, db_user.id, requested_access_level)
        updated = await repo.update(db_user, changes)
        await ensure_user_mailbox(
            session,
            updated.id,
            external_email=updated.email,
            sync_external_email=True,
        )
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
        access_level=requested_access_level or current_access_level,
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

    try:
        hierarchy = HierarchyRepository(session)
        pending_node_ids = [f"user-{db_user.id}"]
        hierarchy_node_ids: list[str] = []
        while pending_node_ids:
            current_node_id = pending_node_ids.pop()
            current_node = await hierarchy.get_node(current_node_id)
            if current_node is None:
                continue
            hierarchy_node_ids.append(current_node_id)
            pending_node_ids.extend(
                child.id for child in await hierarchy.list_children(current_node_id)
            )

        for hierarchy_node_id in reversed(hierarchy_node_ids):
            await hierarchy.delete_node(hierarchy_node_id)

        await session.execute(
            delete(AuthSessionModel).where(AuthSessionModel.user_id == db_user.id)
        )
        await session.execute(
            delete(UserPreferenceModel).where(
                UserPreferenceModel.user_id == db_user.id
            )
        )
        await session.execute(
            delete(UserRoleModel).where(UserRoleModel.user_id == db_user.id)
        )
        await session.execute(delete(UserModel).where(UserModel.id == db_user.id))
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return {"ok": True}


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
        roles=list(user.roles),
        permissions=list(user.permissions),
        tenant=None,
        created_at=u.created_at,
        last_login_at=u.last_login_at,
    )


async def _patch_me_impl(
    request: Request,
    user: UserContext,
    payload: UpdateOwnProfileRequest,
    session: AsyncSession,
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
        await ensure_user_mailbox(
            session,
            updated.id,
            external_email=updated.email,
            sync_external_email=True,
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
        roles=list(user.roles),
        permissions=list(user.permissions),
        tenant=None,
        created_at=updated.created_at,
        last_login_at=updated.last_login_at,
    )


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_my_preferences(
    request: Request,
    user: AuthenticatedUser,
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
    user: AuthenticatedUser,
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
