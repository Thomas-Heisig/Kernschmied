from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.storage.repositories.user_preference import UserPreferenceRepository
from app.contracts.users import UserPreferencesResponse, UpdateUserPreferencesRequest
from sqlalchemy.ext.asyncio import AsyncSession


class PreferencesError(Exception):
    pass


class PreferencesNotFound(PreferencesError):
    pass


class PreferencesInvalid(PreferencesError):
    pass


class PreferencesUpdateFailed(PreferencesError):
    pass


DEFAULTS = {
    'language': 'de',
    'timezone': 'Europe/Berlin',
    'theme': 'system',
    'density': 'comfortable',
    'default_view': None,
    'notifications_enabled': True,
}


def _compact_mode_to_density(compact_mode: int) -> str:
    return 'compact' if bool(compact_mode) else 'comfortable'


def _density_to_compact_mode(density: str) -> int:
    return 1 if density == 'compact' else 0


async def get_preferences(session: AsyncSession, user_id: str) -> UserPreferencesResponse:
    repo = UserPreferenceRepository(session)
    pref = await repo.get_by_user_id(user_id)
    if pref is None:
        # create defaults idempotently
        pref = await repo.create_default(user_id)

    # read values with defaults
    language = pref.locale or DEFAULTS['language']
    timezone_str = pref.timezone or DEFAULTS['timezone']
    theme = pref.theme or DEFAULTS['theme']
    density = _compact_mode_to_density(pref.compact_mode)
    default_view = pref.preferences_json.get('default_view') if isinstance(pref.preferences_json, dict) else DEFAULTS['default_view']
    notifications_enabled = pref.preferences_json.get('notifications_enabled', DEFAULTS['notifications_enabled']) if isinstance(pref.preferences_json, dict) else DEFAULTS['notifications_enabled']

    updated_at = getattr(pref, 'updated_at', None)

    return UserPreferencesResponse(
        language=language,
        timezone=timezone_str,
        theme=theme,
        density=density,
        default_view=default_view,
        notifications_enabled=bool(notifications_enabled),
        updated_at=updated_at,
    )


async def update_preferences(session: AsyncSession, user_id: str, request: UpdateUserPreferencesRequest) -> UserPreferencesResponse:
    # require at least one field
    if (
        request.language is None
        and request.timezone is None
        and request.theme is None
        and request.density is None
        and request.default_view is None
        and request.notifications_enabled is None
    ):
        raise PreferencesInvalid()

    repo = UserPreferenceRepository(session)
    pref = await repo.get_by_user_id(user_id)
    if pref is None:
        pref = await repo.create_default(user_id)

    changes: dict[str, Any] = {}

    # language validation
    if request.language is not None:
        if request.language not in ('de', 'en'):
            raise PreferencesInvalid()
        changes['locale'] = request.language

    # timezone validation
    if request.timezone is not None:
        try:
            ZoneInfo(request.timezone)
        except ZoneInfoNotFoundError:
            raise PreferencesInvalid()
        changes['timezone'] = request.timezone

    # theme
    if request.theme is not None:
        if request.theme not in ('system', 'light', 'dark'):
            raise PreferencesInvalid()
        changes['theme'] = request.theme

    # density -> compact_mode
    if request.density is not None:
        if request.density not in ('comfortable', 'compact'):
            raise PreferencesInvalid()
        changes['compact_mode'] = _density_to_compact_mode(request.density)

    # default_view: accept None or short string
    if request.default_view is not None:
        if request.default_view is not None and len(request.default_view) > 255:
            raise PreferencesInvalid()
        # store under preferences_json
        if not isinstance(pref.preferences_json, dict):
            pref.preferences_json = {}
        pref.preferences_json['default_view'] = request.default_view

    # notifications
    if request.notifications_enabled is not None:
        if not isinstance(pref.preferences_json, dict):
            pref.preferences_json = {}
        pref.preferences_json['notifications_enabled'] = bool(request.notifications_enabled)

    if not changes and (not pref.preferences_json):
        # nothing to do
        return await get_preferences(session, user_id)

    try:
        updated = await repo.update(pref, changes)
    except Exception:
        raise PreferencesUpdateFailed()

    return await get_preferences(session, user_id)
