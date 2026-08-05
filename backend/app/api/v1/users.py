from __future__ import annotations

from fastapi import APIRouter, Body, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.users import UserCreateRequest, UserRead
from app.auth.dependencies import require_permission
from app.auth.models import UserContext
from app.storage.database import get_session
from app.storage.repositories.user import UserRepository
from app.auth.password_service import PasswordService

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    payload: UserCreateRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    _user: UserContext = Depends(require_permission("users.create")),
):
    repo = UserRepository(session)

    existing = await repo.get_by_username(payload.username)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")

    password_hash = None
    # Admin may set an initial password; if not set, account is created without password.
    # Password handling must use PasswordService to hash and validate policy if provided.
    # For MVP we accept no initial password.

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
