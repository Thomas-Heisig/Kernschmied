from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password_service import PasswordService
from app.contracts.hierarchy import HierarchyNodeCreate
from app.database.models.user import UserModel
from app.database.models.user_preference import UserPreferenceModel
from app.database.models.user_role import RoleModel, UserRoleModel
from app.hierarchy.repository import HierarchyRepository
from app.services.mailbox_service import ensure_user_mailbox, queue_welcome_email
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
        password: str | None = None,
        generate_password: bool = False,
        require_password_change: bool = True,
        roles: list[str] | None = None,
        preferences: dict[str, object] | None = None,
        create_default_workspace: bool = False,
        default_workspace_name: str | None = None,
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

        # Password handling: either provided or generated
        generated_password: str | None = None
        if password is None and generate_password:
            generated_password = self.pwd.generate_password()
            password_to_use = generated_password
        elif password is not None:
            password_to_use = password
        else:
            raise RegistrationError("PASSWORD_REQUIRED")

        # Validate password policy (may raise)
        self.pwd.validate_password_policy(uname, password_to_use)
        pw_hash = self.pwd.hash_password(password_to_use)

        # Create user mapping (no admin flag)
        data: dict[str, object | None] = {
            "username": uname,
            "display_name": dname,
            "email": email,
            "password_hash": pw_hash,
            "is_active": True,
            "is_system_admin": False,
            "must_change_password": bool(require_password_change),
        }

        user = await self.user_repo.create(data)

        # Roles: validate requested roles and assign atomically
        requested_roles = roles or ["guest"]
        q = select(RoleModel).where(RoleModel.name.in_(requested_roles))
        res = await self.session.execute(q)
        found_roles = {r.name: r for r in res.scalars().all()}

        built_in_roles = {
            "guest": ("Gast", "Zugriff auf eigene und öffentliche Bereiche"),
            "user": ("Intern", "Zugriff auf eigene, öffentliche und interne Bereiche"),
        }
        for role_name in requested_roles:
            if role_name in found_roles or role_name not in built_in_roles:
                continue
            display_name, description = built_in_roles[role_name]
            role = RoleModel(
                name=role_name,
                display_name=display_name,
                description=description,
            )
            self.session.add(role)
            await self.session.flush()
            found_roles[role_name] = role

        # Validate requested role names exist and are assignable
        for rname in requested_roles:
            if rname not in found_roles:
                raise RegistrationError(f"ROLE_NOT_FOUND:{rname}")
            role_obj = found_roles[rname]
            if not getattr(role_obj, "assignable", True):
                raise RegistrationError(f"ROLE_NOT_ASSIGNABLE:{rname}")

        # Insert mappings
        for r in found_roles.values():
            q2 = select(UserRoleModel).where(
                UserRoleModel.user_id == user.id, UserRoleModel.role_id == r.id
            )
            res2 = await self.session.execute(q2)
            mapping = res2.scalar_one_or_none()
            if mapping is None:
                ur = UserRoleModel(user_id=user.id, role_id=r.id)
                self.session.add(ur)

        # Create preferences row, applying provided keys with sensible defaults
        pref_data = {}
        if preferences:
            pref_data["locale"] = preferences.get("locale")
            pref_data["timezone"] = preferences.get("timezone")
            pref_data["theme"] = preferences.get("theme")
            pref_data["compact_mode"] = preferences.get("compact_mode")

        pref = UserPreferenceModel(user_id=user.id, **pref_data)
        self.session.add(pref)
        await ensure_user_mailbox(
            self.session,
            user.id,
            external_email=user.email,
            sync_external_email=True,
        )
        await queue_welcome_email(
            self.session,
            user_id=user.id,
            display_name=user.display_name,
        )

        # Create a corresponding hierarchy node under users-root if missing.
        try:
            hrepo = HierarchyRepository(self.session)
            node_id = f"user-{user.id}"
            existing = await hrepo.get_node(node_id)
            if existing is None:
                await hrepo.create_node(
                    HierarchyNodeCreate(
                        node_id=node_id,
                        type="user",
                        name=user.display_name or user.username,
                        parent_id="users-root",
                        system_prompt=None,
                        tool_policy={},
                        config_overrides={},
                        metadata={
                            "entity_type": "user",
                            "entity_id": user.id,
                            "display_name": user.display_name,
                        },
                    )
                )

                # Optionally create a default workspace under the user
                if create_default_workspace:
                    ws_node_id = f"workspace-{user.id}-default"
                    try:
                        existing_ws = await hrepo.get_node(ws_node_id)
                        if existing_ws is None:
                            await hrepo.create_node(
                                HierarchyNodeCreate(
                                    node_id=ws_node_id,
                                    type="workspace",
                                    name=default_workspace_name or "Workspace",
                                    parent_id=node_id,
                                    system_prompt=None,
                                    tool_policy={},
                                    config_overrides={},
                                    metadata={"entity_type": "workspace", "entity_id": ws_node_id},
                                )
                            )
                    except Exception:
                        raise RegistrationError("WORKSPACE_CREATE_FAILED")
        except Exception:
            # Let caller handle rollback; surface a domain error
            raise RegistrationError("HIERARCHY_NODE_CREATE_FAILED")

        # Flush so caller can commit or create session
        await self.session.flush()
        await self.user_repo.load_authorization(user)

        # No auto-login token handling here; caller may create session
        return user, generated_password
