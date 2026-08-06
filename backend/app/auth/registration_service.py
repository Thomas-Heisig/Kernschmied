from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password_service import PasswordService
from app.database.models.user import UserModel
from app.database.models.user_preference import UserPreferenceModel
from app.database.models.user_role import RoleModel, UserRoleModel
from app.storage.repositories.user import UserRepository


class RegistrationError(Exception):
    pass


class RegistrationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.pwd = PasswordService()

    async def register_user(
        self,
        *,
        username: str,
        display_name: str,
        email: str | None,
        password: str,
        invitation_token: str | None = None,
        auto_login: bool = False,
    ) -> tuple[UserModel, str | None]:
        # Normalize inputs
        uname = username.strip()
        dname = display_name.strip()

        # Basic validations
        if not uname:
            raise RegistrationError("USERNAME_REQUIRED")

        # Ensure unique username
        existing = await self.user_repo.get_by_username(uname)
        if existing is not None:
            raise RegistrationError("USERNAME_EXISTS")

        if email:
            existing_email = await self.user_repo.get_by_email(email)
            if existing_email is not None:
                raise RegistrationError("EMAIL_EXISTS")

        # Validate password policy (may raise)
        self.pwd.validate_password_policy(uname, password)
        pw_hash = self.pwd.hash_password(password)

        # Create user mapping (no admin flag)
        data: dict[str, object | None] = {
            "username": uname,
            "display_name": dname,
            "email": email,
            "password_hash": pw_hash,
            "is_active": True,
            "is_system_admin": False,
        }

        user = await self.user_repo.create(data)

        # Ensure default 'user' role exists and assign
        q = select(RoleModel).where(RoleModel.name == "user")
        result = await self.session.execute(q)
        role = result.scalar_one_or_none()
        if role is None:
            role = RoleModel(name="user", display_name="User")
            self.session.add(role)
            await self.session.flush()

        # Insert mapping if it doesn't exist
        q2 = select(UserRoleModel).where(
            UserRoleModel.user_id == user.id, UserRoleModel.role_id == role.id
        )
        res2 = await self.session.execute(q2)
        mapping = res2.scalar_one_or_none()
        if mapping is None:
            ur = UserRoleModel(user_id=user.id, role_id=role.id)
            self.session.add(ur)

        # Create default preferences row
        pref = UserPreferenceModel(user_id=user.id)
        self.session.add(pref)

        # Flush so caller can commit or create session
        await self.session.flush()

        # No auto-login token handling here; caller may create session
        return user, None
