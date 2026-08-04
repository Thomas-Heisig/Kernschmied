from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password_service import PasswordService, PasswordPolicyError
from app.auth.session_service import SessionService
from app.core.settings import settings
from app.database.models.auth_session import AuthSessionModel
from app.database.models.user import UserModel
from app.storage.database import get_session

router = APIRouter()


# -----------------------------
# Pydantic DTOs
# -----------------------------


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    email: EmailStr | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    display_name: str
    email: EmailStr | None = None
    is_active: bool


def _user_to_out(u: UserModel) -> UserOut:
    return UserOut(
        id=u.id,
        username=u.username,
        display_name=u.display_name,
        email=u.email,
        is_active=bool(u.is_active),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest = Body(...),
    session: AsyncSession = Depends(get_session),
):
    # basic uniqueness checks
    stmt = select(UserModel).where(sa.or_(UserModel.username == payload.username, UserModel.email == payload.email))
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with that username or email already exists")

    password_service = PasswordService()
    try:
        password_service.validate_password_policy(payload.username, payload.password)
    except PasswordPolicyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    password_hash = password_service.hash_password(payload.password)

    user = UserModel(
        username=payload.username,
        display_name=payload.display_name or payload.username,
        email=payload.email,
        password_hash=password_hash,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return _user_to_out(user)


@router.post("/login", response_model=UserOut)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest = Body(...),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(UserModel).where(UserModel.username == payload.username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or user.password_hash is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    password_service = PasswordService()
    if not password_service.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # create session
    session_service = SessionService(lifetime_seconds=settings.session_lifetime_seconds)
    token = session_service.generate_token()
    token_hash = session_service.hash_token(token)
    expires_at = session_service.token_expiry()

    auth_obj = AuthSessionModel(
        user_id=user.id,
        session_token_hash=token_hash,
        expires_at=expires_at,
        ip_address=(request.client.host if request.client is not None else None),
        user_agent=request.headers.get("user-agent"),
    )

    session.add(auth_obj)
    await session.commit()

    # set cookie
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

    return _user_to_out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    cookie_name = settings.session_cookie_name
    token = request.cookies.get(cookie_name)
    if not token:
        # idempotent
        response.delete_cookie(cookie_name, path=settings.session_cookie_path)
        return None

    session_service = SessionService()
    token_hash = session_service.hash_token(token)

    stmt = select(AuthSessionModel).where(AuthSessionModel.session_token_hash == token_hash)
    result = await session.execute(stmt)
    auth_record = result.scalar_one_or_none()
    if auth_record is not None:
        try:
            auth_record.revoked_at = datetime.utcnow()
            session.add(auth_record)
            await session.commit()
        except Exception:
            pass

    response.delete_cookie(cookie_name, path=settings.session_cookie_path)
    return None


@router.get("/me", response_model=UserOut | None)
async def me(request: Request):
    user = getattr(request.state, "user", None)
    if user is None:
        return None

    return _user_to_out(user)
