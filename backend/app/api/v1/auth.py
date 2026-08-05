from __future__ import annotations


from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, ConfigDict
from app.contracts.auth import CurrentUserResponse, TenantSummary
from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast, ClassVar

from app.auth.authentication_service import AuthenticationService, AuthenticationError
from app.auth.registration_service import RegistrationService, RegistrationError
from app.core.settings import settings
from app.database.models.user import UserModel
from app.storage.database import get_session
# dependencies
from app.auth.dependencies import AuthenticatedUser
# from app.auth.password_service import PasswordService
from app.auth.session_management_service import list_sessions, revoke_session, revoke_all_sessions
from app.contracts.auth import UserSessionResponse

router = APIRouter()


# -----------------------------
# Pydantic DTOs
# -----------------------------


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(CurrentUserResponse):
    # Keep backward-compatible alias for inline usage
    pass


class RegisterRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    username: str
    display_name: str
    email: EmailStr | None = None
    password: str
    password_confirmation: str
    invitation_token: str | None = None


class RegisterResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    user: UserOut
    login_required: bool
    schema_version: str = "1.0"


def _user_to_out(u: object) -> UserOut:
    # Support both DB model (`UserModel`) and request-level `UserContext`.
    # Prefer DB attributes when available, otherwise fall back to normalized context.
    # continue to generic mapping for both DB model and UserContext-like principals

    # Generic mapping for UserContext or mapping-like principals
    user_id = getattr(u, "id", None)
    username = getattr(u, "username", None) or getattr(u, "name", None) or str(user_id)
    display_name = getattr(u, "display_name", None) or getattr(u, "name", None) or username

    email: str | None = None
    if hasattr(u, "email"):
        email = getattr(u, "email")
    else:
        # Narrow metadata typing so static checkers know the mapping signature
        metadata = cast(dict[str, object] | None, getattr(u, "metadata", None))
        if metadata is not None:
            # metadata values are untyped; cast the email entry to expected type
            email = cast(str | None, metadata.get("email"))

    # `is_active` not used here; presence kept in DB models but not needed in DTO mapping
    # Determine development_session flag and password login availability
    development_session = False
    password_login_available = False

    # If DB model, inspect known attributes
    if isinstance(u, UserModel):
        password_login_available = bool(getattr(u, 'password_hash', None))
        # Development session if this is the configured development admin
        try:
            from app.core.settings import settings as _settings

            dev_id = getattr(_settings, 'development_admin_user_id', None)
            dev_username = getattr(_settings, 'development_admin_username', None)
            env = getattr(_settings, 'app_environment', None)
            if (dev_id and u.id == dev_id) or (dev_username and u.username == dev_username):
                # Only treat as development when running in development env and admin login enabled
                if getattr(_settings, 'development_admin_login_enabled', False) and getattr(env, 'name', str(env)).lower() == 'development':
                    development_session = True
        except Exception:
            development_session = False

    else:
        # Generic mapping for UserContext or mapping-like principals
        development_session = bool(
            getattr(u, 'development_session', None)
            or (isinstance(getattr(u, 'authentication_method', None), str) and 'development' in getattr(u, 'authentication_method', ''))
            or getattr(u, 'auth_method', None) == 'development'
        )

        if hasattr(u, 'password_login_available'):
            password_login_available = bool(getattr(u, 'password_login_available'))
        else:
            # try to infer from metadata or password_hash
            if hasattr(u, 'password_hash'):
                password_login_available = bool(getattr(u, 'password_hash'))

    tenant_obj: TenantSummary | None = None
    if hasattr(u, 'tenant') and getattr(u, 'tenant') is not None:
        tenant = getattr(u, 'tenant')
        try:
            tenant_obj = TenantSummary(
                id=str(tenant.get('id')),
                display_name=str(tenant.get('display_name') or tenant.get('name') or ''),
            )
        except Exception:
            tenant_obj = None
    else:
        # fallbacks
        tenant_id = getattr(u, 'tenant_id', None) or getattr(u, 'organization_id', None)
        tenant_name = None
        if hasattr(u, 'tenant_display_name'):
            tenant_name = getattr(u, 'tenant_display_name')
        elif hasattr(u, 'organization_name'):
            tenant_name = getattr(u, 'organization_name')

        if tenant_id is not None:
            tenant_obj = TenantSummary(id=str(tenant_id), display_name=str(tenant_name or ''))

    return UserOut(
        id=str(user_id),
        username=username,
        display_name=display_name,
        email=email,
        authenticated=True,
        development_session=development_session,
        password_login_available=password_login_available,
        tenant=tenant_obj,
    )



@router.post("/login", response_model=UserOut)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest = Body(...),
    session: AsyncSession = Depends(get_session),
):
    svc = AuthenticationService(session=session)
    try:
        user = await svc.authenticate(payload.username, payload.password)
    except AuthenticationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    request_meta: dict[str, object] = {
        "ip": request.client.host if request.client is not None else None,
        "ua": request.headers.get("user-agent"),
    }

    token = await svc.create_session(user, request_meta=request_meta, authentication_method="password")


    cookie_name = settings.session_cookie_name
    response.set_cookie(
        key=cookie_name,
        value=token,
        httponly=True,
        secure=(settings.app_environment != "development"),
        samesite="lax",
        path=settings.session_cookie_path,
        max_age=settings.session_lifetime_seconds,
    )

    # Convert to canonical contract
    out = _user_to_out(user)
    # Map fields to CurrentUserResponse shape where possible
    return CurrentUserResponse(
        id=out.id,
        username=out.username,
        display_name=out.display_name,
        email=out.email,
        authenticated=True,
        development_session=out.development_session,
        password_login_available=out.password_login_available,
        tenant=out.tenant,
        created_at=getattr(user, 'created_at', None),
        last_login_at=getattr(user, 'last_login_at', None),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    cookie_name = settings.session_cookie_name
    token = request.cookies.get(cookie_name)
    if not token:
        response.delete_cookie(cookie_name, path=settings.session_cookie_path)
        return None

    svc = AuthenticationService(session=session)
    await svc.logout(token)

    response.delete_cookie(cookie_name, path=settings.session_cookie_path)
    return None


@router.get("/me", response_model=UserOut | None)
async def me(request: Request):
    user = getattr(request.state, "user", None)
    if user is None or (hasattr(user, "authenticated") and not getattr(user, "authenticated")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    out = _user_to_out(user)
    return CurrentUserResponse(
        id=out.id,
        username=out.username,
        display_name=out.display_name,
        email=out.email,
        authenticated=True,
        development_session=out.development_session,
        password_login_available=out.password_login_available,
        tenant=out.tenant,
        created_at=getattr(user, 'created_at', None),
        last_login_at=getattr(user, 'last_login_at', None),
    )


@router.post("/development-login", response_model=UserOut)
async def development_login(request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    # Only available in development when explicitly enabled by settings
    if settings.app_environment.name.lower() != "development" or not getattr(settings, "development_admin_login_enabled", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    svc = AuthenticationService(session=session)
    try:
        user = await svc.authenticate_development_admin()
    except AuthenticationError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    request_meta: dict[str, object] = {
        "ip": request.client.host if request.client is not None else None,
        "ua": request.headers.get("user-agent"),
    }

    token = await svc.create_session(user, request_meta=request_meta, authentication_method="development_admin")

    cookie_name = settings.session_cookie_name
    response.set_cookie(
        key=cookie_name,
        value=token,
        httponly=True,
        secure=(settings.app_environment != "development"),
        samesite="lax",
        path=settings.session_cookie_path,
        max_age=settings.session_lifetime_seconds,
    )

    out = _user_to_out(user)
    return CurrentUserResponse(
        id=out.id,
        username=out.username,
        display_name=out.display_name,
        email=out.email,
        authenticated=True,
        development_session=out.development_session,
        password_login_available=out.password_login_available,
        tenant=out.tenant,
        created_at=getattr(user, 'created_at', None),
        last_login_at=getattr(user, 'last_login_at', None),
    )


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: Request,
    response: Response,
    payload: RegisterRequest = Body(...),
    session: AsyncSession = Depends(get_session),
):
    # Determine effective registration allowance
    app_env = str(getattr(settings, "app_environment", "development")).lower()
    if app_env == "development":
        registration_allowed = bool(getattr(settings, "development_self_registration_enabled", False))
    else:
        registration_allowed = bool(getattr(settings, "self_registration_enabled", False))

    if not registration_allowed:
        # Not exposed in this environment
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # If invitations required, ensure token present
    requires_invite = bool(getattr(settings, "registration_requires_invitation", False))
    if requires_invite and not payload.invitation_token:
        request_id = getattr(request.state, "request_id", None)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "REGISTRATION_INVITATION_NOT_IMPLEMENTED",
                "message": "Die Registrierung mit Einladung ist noch nicht verfügbar.",
                "details": {},
                "request_id": request_id,
            },
        )

    svc = AuthenticationService(session=session)
    reg_svc = RegistrationService(session=session)

    # Simple payload validation
    if payload.password != payload.password_confirmation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    try:
        user, _ = await reg_svc.register_user(
            username=payload.username,
            display_name=payload.display_name,
            email=payload.email,
            password=payload.password,
            invitation_token=payload.invitation_token,
            auto_login=False,
        )

        # Persist transaction
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    except RegistrationError as re:
        code = str(re)
        if code == "USERNAME_EXISTS":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        if code == "EMAIL_EXISTS":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(re))

    # Auto-login behavior: in development, or when registration does not require invitation,
    # create session immediately. Otherwise require explicit login.
    login_required = True
    if app_env == "development" or (not requires_invite):
        request_meta: dict[str, object] = {
            "ip": request.client.host if request.client is not None else None,
            "ua": request.headers.get("user-agent"),
        }
        token = await svc.create_session(user, request_meta=request_meta, authentication_method="password")

        cookie_name = settings.session_cookie_name
        response.set_cookie(
            key=cookie_name,
            value=token,
            httponly=True,
            secure=(settings.app_environment != "development"),
            samesite="lax",
            path=settings.session_cookie_path,
            max_age=settings.session_lifetime_seconds,
        )
        login_required = False

    return RegisterResponse(user=_user_to_out(user), login_required=login_required)


@router.get("/sessions", response_model=list[UserSessionResponse])
async def list_auth_sessions(request: Request, user: AuthenticatedUser, session: AsyncSession = Depends(get_session)):
    current_session_id = getattr(user, 'session_id', None)
    rows = await list_sessions(session, getattr(user, 'id'), current_session_id)
    return rows


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_auth_session(session_id: str, request: Request, response: Response, user: AuthenticatedUser, session: AsyncSession = Depends(get_session)):
    try:
        revoked = await revoke_session(session, getattr(user, 'id'), session_id)
        if not revoked:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "SESSION_NOT_FOUND", "message": "Session nicht gefunden.", "request_id": getattr(request.state, 'request_id', None)})

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    finally:
        # If user revoked the current session, clear cookie
        if session_id == getattr(user, 'session_id', None):
            cookie_name = settings.session_cookie_name
            response.delete_cookie(cookie_name, path=settings.session_cookie_path)

    return None


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all(request: Request, response: Response, user: AuthenticatedUser, session: AsyncSession = Depends(get_session)):
    try:
        count = await revoke_all_sessions(session, getattr(user, 'id'))
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"code": "LOGOUT_ALL_FAILED", "message": "Konnte alle Sessions nicht abmelden.", "request_id": getattr(request.state, 'request_id', None)})

    # Clear cookie for current session
    cookie_name = settings.session_cookie_name
    response.delete_cookie(cookie_name, path=settings.session_cookie_path)
    return {"revoked": count}
