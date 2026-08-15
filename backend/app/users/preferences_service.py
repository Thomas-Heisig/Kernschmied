from __future__ import annotations

from typing import Any, Literal, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.contracts.users import UpdateUserPreferencesRequest, UserPreferencesResponse
from app.database.models.user_role import RoleModel, UserRoleModel
from app.storage.repositories.user import UserRepository
from app.storage.repositories.user_preference import UserPreferenceRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class PreferencesError(Exception):
    pass


class PreferencesNotFound(PreferencesError):
    pass


class PreferencesInvalid(PreferencesError):
    pass


class PreferencesUpdateFailed(PreferencesError):
    pass


DEFAULTS: dict[str, Any] = {
    "language": "de",
    "timezone": "Europe/Berlin",
    "theme": "system",
    "density": "comfortable",
    "default_view": None,
    "notifications_enabled": True,
    "ai_response_on_mentions": False,
}


async def _default_ai_response_on_mentions(
    session: AsyncSession, user_id: str, is_system_admin: bool
) -> bool:
    if is_system_admin:
        return True
    result = await session.execute(
        select(RoleModel.name)
        .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
        .where(UserRoleModel.user_id == user_id)
    )
    return "admin" in set(result.scalars().all())


def _compact_mode_to_density(compact_mode: int) -> str:
    return "compact" if bool(compact_mode) else "comfortable"


def _density_to_compact_mode(density: str) -> int:
    return 1 if density == "compact" else 0


async def get_preferences(
    session: AsyncSession, user_id: str
) -> UserPreferencesResponse:
    # ensure user exists before creating preferences to avoid FK errors
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise PreferencesNotFound(
            "CURRENT_USER_NOT_FOUND: Der aktuelle Benutzer wurde nicht gefunden."
        )

    repo = UserPreferenceRepository(session)
    pref = await repo.get_by_user_id(user_id)
    if pref is None:
        # create defaults idempotently
        pref = await repo.create_default(user_id)

    # read values with defaults
    language = pref.locale or DEFAULTS["language"]
    timezone_str = pref.timezone or DEFAULTS["timezone"]
    theme = pref.theme or DEFAULTS["theme"]
    density = _compact_mode_to_density(pref.compact_mode)
    # preferences_json is typed as dict[str, Any]
    default_view = pref.preferences_json.get("default_view", DEFAULTS["default_view"])
    notifications_enabled = pref.preferences_json.get(
        "notifications_enabled", DEFAULTS["notifications_enabled"]
    )
    ai_response_on_mentions = pref.preferences_json.get("ai_response_on_mentions")
    if ai_response_on_mentions is None:
        ai_response_on_mentions = await _default_ai_response_on_mentions(
            session, user_id, bool(user.is_system_admin)
        )

    updated_at = getattr(pref, "updated_at", None)

    return UserPreferencesResponse(
        language=language,
        timezone=timezone_str,
        theme=cast(Literal["system", "light", "dark"], theme),
        density=cast(Literal["comfortable", "compact"], density),
        default_view=default_view,
        notifications_enabled=bool(notifications_enabled),
        ai_response_on_mentions=bool(ai_response_on_mentions),
        updated_at=updated_at,
    )


async def update_preferences(
    session: AsyncSession, user_id: str, request: UpdateUserPreferencesRequest
) -> UserPreferencesResponse:
    # require at least one field
    if (
        request.language is None
        and request.timezone is None
        and request.theme is None
        and request.density is None
        and request.default_view is None
        and request.notifications_enabled is None
        and request.ai_response_on_mentions is None
    ):
        raise PreferencesInvalid()

    # ensure user exists
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise PreferencesNotFound(
            "CURRENT_USER_NOT_FOUND: Der aktuelle Benutzer wurde nicht gefunden."
        )

    repo = UserPreferenceRepository(session)
    pref = await repo.get_by_user_id(user_id)
    if pref is None:
        pref = await repo.create_default(user_id)

    changes: dict[str, Any] = {}

    # language validation
    if request.language is not None:
        if request.language not in ("de", "en"):
            raise PreferencesInvalid()
        changes["locale"] = request.language

    # timezone validation
    if request.timezone is not None:
        try:
            ZoneInfo(request.timezone)
        except ZoneInfoNotFoundError:
            raise PreferencesInvalid() from None
        changes["timezone"] = request.timezone

    # theme
    if request.theme is not None:
        if request.theme not in ("system", "light", "dark"):
            raise PreferencesInvalid()
        changes["theme"] = request.theme

    # density -> compact_mode
    if request.density is not None:
        if request.density not in ("comfortable", "compact"):
            raise PreferencesInvalid()
        changes["compact_mode"] = _density_to_compact_mode(request.density)

    # default_view: accept None or short string
    if request.default_view is not None:
        if len(request.default_view) > 255:
            raise PreferencesInvalid()
        # store under preferences_json
        pref.preferences_json["default_view"] = request.default_view

    # notifications
    if request.notifications_enabled is not None:
        pref.preferences_json["notifications_enabled"] = bool(
            request.notifications_enabled
        )

    if request.ai_response_on_mentions is not None:
        pref.preferences_json["ai_response_on_mentions"] = bool(
            request.ai_response_on_mentions
        )

    if not changes and (not pref.preferences_json):
        # nothing to do
        return await get_preferences(session, user_id)

    try:
        await repo.update(pref, changes)
    except Exception:
        raise PreferencesUpdateFailed() from None

    return await get_preferences(session, user_id)
