# F:\Kernschmied\backend\app\core\security_profile.py

from __future__ import annotations

from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict

from app.core.settings import settings


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    INTRANET = "intranet"
    INTERNET = "internet"


class AuthMode(str, Enum):
    NONE = "none"
    API_KEY = "api_key"
    SESSION = "session"


class SecurityProfile(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    environment: AppEnvironment

    auth_required: bool

    allowed_auth_modes: frozenset[AuthMode]

    https_required: bool

    audit_log_enabled: bool

    rate_limits_enabled: bool

    csrf_required: bool

    secure_cookies: bool

    hsts_enabled: bool

    cors_locked: bool


_DEVELOPMENT: Final = SecurityProfile(
    environment=AppEnvironment.DEVELOPMENT,
    auth_required=False,
    allowed_auth_modes=frozenset(
        {
            AuthMode.NONE,
            AuthMode.API_KEY,
        }
    ),
    https_required=False,
    audit_log_enabled=False,
    rate_limits_enabled=False,
    csrf_required=False,
    secure_cookies=False,
    hsts_enabled=False,
    cors_locked=False,
)

_INTRANET: Final = SecurityProfile(
    environment=AppEnvironment.INTRANET,
    auth_required=True,
    allowed_auth_modes=frozenset(
        {
            AuthMode.API_KEY,
            AuthMode.SESSION,
        }
    ),
    https_required=False,
    audit_log_enabled=True,
    rate_limits_enabled=False,
    csrf_required=True,
    secure_cookies=False,
    hsts_enabled=False,
    cors_locked=True,
)

_INTERNET: Final = SecurityProfile(
    environment=AppEnvironment.INTERNET,
    auth_required=True,
    allowed_auth_modes=frozenset(
        {
            AuthMode.SESSION,
        }
    ),
    https_required=True,
    audit_log_enabled=True,
    rate_limits_enabled=True,
    csrf_required=True,
    secure_cookies=True,
    hsts_enabled=True,
    cors_locked=True,
)


_PROFILES: Final = {
    AppEnvironment.DEVELOPMENT: _DEVELOPMENT,
    AppEnvironment.INTRANET: _INTRANET,
    AppEnvironment.INTERNET: _INTERNET,
}


def get_security_profile() -> SecurityProfile:
    """
    Liefert das unveränderliche Mindest-Sicherheitsprofil der aktuellen
    Betriebsumgebung.

    Dieses Profil bildet die Untergrenze der Sicherheit. Fachliche
    Konfigurationen aus der Datenbank dürfen zusätzliche Einschränkungen
    aktivieren, diese Mindestanforderungen jedoch niemals unterschreiten.
    """

    environment = AppEnvironment(settings.app_env)

    return _PROFILES[environment]
