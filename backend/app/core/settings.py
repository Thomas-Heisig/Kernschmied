# F:\Kernschmied\backend\app\core\settings.py

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlparse

from pydantic import (
    AliasChoices,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

# ============================================================
# Projektpfade
# ============================================================


CORE_DIRECTORY: Final[Path] = Path(__file__).resolve().parent
APP_DIRECTORY: Final[Path] = CORE_DIRECTORY.parent
BACKEND_DIRECTORY: Final[Path] = APP_DIRECTORY.parent
PROJECT_DIRECTORY: Final[Path] = BACKEND_DIRECTORY.parent

DEFAULT_ENV_FILE: Final[Path] = PROJECT_DIRECTORY / ".env"
DEFAULT_DATA_DIRECTORY: Final[Path] = BACKEND_DIRECTORY / "data"
DEFAULT_CONFIG_DIRECTORY: Final[Path] = PROJECT_DIRECTORY / "config"
DEFAULT_MANIFEST_DIRECTORY: Final[Path] = PROJECT_DIRECTORY / "extensions"

DEFAULT_BOOTSTRAP_CONFIG_FILE: Final[Path] = DEFAULT_CONFIG_DIRECTORY / "bootstrap.json"

DEFAULT_SQLITE_DATABASE_FILE: Final[Path] = DEFAULT_DATA_DIRECTORY / "kernschmied.db"


# ============================================================
# Konstanten
# ============================================================


DEFAULT_API_PREFIX: Final[str] = "/api/v1"

SUPPORTED_DATABASE_SCHEMES: Final[frozenset[str]] = frozenset(
    {
        "sqlite+aiosqlite",
        "postgresql+asyncpg",
    }
)

INSECURE_SECRET_VALUES: Final[frozenset[str]] = frozenset(
    {
        "",
        "change-me",
        "change-me-too",
        "secret",
        "password",
        "development",
        "development-only",
        "development-only-change-me",
    }
)


# ============================================================
# Enums
# ============================================================


class AppEnvironment(str, Enum):
    """
    Festes Betriebsprofil.

    Dieses Profil definiert Sicherheitsuntergrenzen. Es darf nicht durch
    Datenbankkonfiguration abgeschwächt werden.
    """

    DEVELOPMENT = "development"
    INTRANET = "intranet"
    INTERNET = "internet"


class LogLevel(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class ForwardedHeaderMode(str, Enum):
    """
    Steuerung der Verarbeitung weitergeleiteter Proxy-Header.
    """

    DISABLED = "disabled"
    TRUSTED_PROXIES = "trusted_proxies"


class DatabaseMigrationMode(str, Enum):
    """
    Verhalten beim Anwendungsstart.

    Für produktive Umgebungen sollte Alembic normalerweise außerhalb des
    Webprozesses ausgeführt werden. CHECK prüft nur den Migrationsstand.
    """

    DISABLED = "disabled"
    CHECK = "check"
    UPGRADE = "upgrade"


# ============================================================
# Hilfsfunktionen
# ============================================================


def _sqlite_database_url(
    database_file: Path,
) -> str:
    resolved_path = database_file.expanduser().resolve()

    return f"sqlite+aiosqlite:///{resolved_path.as_posix()}"


def _normalize_path(
    value: Path | str,
    *,
    base_directory: Path = PROJECT_DIRECTORY,
) -> Path:
    path = Path(value).expanduser()

    if not path.is_absolute():
        path = base_directory / path

    return path.resolve()


def _normalize_string_tuple(
    values: Sequence[str] | str,
) -> tuple[str, ...]:
    if isinstance(values, str):
        values = tuple(part.strip() for part in values.split(",") if part.strip())

    normalized: list[str] = []

    for value in values:
        item = str(value).strip()

        if item and item not in normalized:
            normalized.append(item)

    return tuple(normalized)


def resolve_database_url(
    configured_url: str | None,
    *,
    backend_directory: Path,
) -> str | None:
    """Resolve SQLite relative paths in a configured database URL to absolute URLs.

    - If `configured_url` is None, returns None.
    - `sqlite+aiosqlite:///:memory:` and non-sql URLs are returned unchanged.
    - Relative sqlite paths are resolved against `backend_directory`.
    """
    if configured_url is None:
        return None

    url = str(configured_url).strip()
    if not url:
        return None

    if url.startswith("sqlite+aiosqlite://"):
        parts = url.split("sqlite+aiosqlite://", 1)
        if len(parts) == 2:
            raw_path = parts[1]
            # keep in-memory URLs untouched
            if raw_path == ":memory:" or ":memory:" in raw_path:
                return url

            stripped = raw_path.lstrip("/")
            candidate = Path(stripped)

            if not candidate.is_absolute():
                base = backend_directory
                candidate_parts = candidate.parts
                # avoid accidental duplication of 'backend' when input already started with it
                if candidate_parts and candidate_parts[0] == base.name:
                    candidate = Path(*candidate_parts[1:])

                resolved = (base / candidate).resolve()
                return f"sqlite+aiosqlite:///{resolved.as_posix()}"

    return url


# ============================================================
# Settings
# ============================================================


class Settings(BaseSettings):
    """
    Technische Bootstrap-, Infrastruktur- und Sicherheitseinstellungen.

    Diese Werte werden beim Prozessstart geladen. Fachliche Einstellungen
    gehören nicht in diese Klasse, sondern versioniert und validiert in
    die Datenbank.

    Beispiele für Datenbankkonfiguration:

    - Standardmodell
    - aktivierte Tools
    - Prompt-Vererbung
    - UI-Konfiguration
    - Chat-Parameter
    - Hierarchietypen
    - fachliche Uploadgrenzen
    """

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        env_prefix="",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        frozen=True,
    )

    # --------------------------------------------------------
    # Anwendung
    # --------------------------------------------------------

    app_name: str = Field(
        default="Kernschmied",
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices(
            "APP_NAME",
            "app_name",
        ),
    )

    app_environment: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        validation_alias=AliasChoices(
            "APP_ENVIRONMENT",
            "APP_ENV",
            "app_environment",
            "app_env",
        ),
    )

    app_version: str = Field(
        default="0.1.0",
        min_length=1,
        max_length=50,
        validation_alias=AliasChoices(
            "APP_VERSION",
            "app_version",
        ),
    )

    api_prefix: str = Field(
        default=DEFAULT_API_PREFIX,
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices(
            "API_PREFIX",
            "api_prefix",
        ),
    )

    public_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "PUBLIC_BASE_URL",
            "public_base_url",
        ),
    )

    # --------------------------------------------------------
    # Server
    # --------------------------------------------------------

    backend_host: str = Field(
        default="127.0.0.1",
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices(
            "BACKEND_HOST",
            "backend_host",
        ),
    )

    backend_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        validation_alias=AliasChoices(
            "BACKEND_PORT",
            "backend_port",
        ),
    )

    workers: int = Field(
        default=1,
        ge=1,
        le=128,
        validation_alias=AliasChoices(
            "WORKERS",
            "BACKEND_WORKERS",
            "workers",
        ),
    )

    shutdown_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=600,
        validation_alias=AliasChoices(
            "SHUTDOWN_TIMEOUT_SECONDS",
            "shutdown_timeout_seconds",
        ),
    )

    request_timeout_seconds: float = Field(
        default=120.0,
        gt=0,
        le=3600,
        validation_alias=AliasChoices(
            "REQUEST_TIMEOUT_SECONDS",
            "request_timeout_seconds",
        ),
    )

    max_request_body_bytes: int = Field(
        default=25 * 1024 * 1024,
        ge=1024,
        le=1024 * 1024 * 1024,
        validation_alias=AliasChoices(
            "MAX_REQUEST_BODY_BYTES",
            "max_request_body_bytes",
        ),
    )

    # --------------------------------------------------------
    # Datenbank
    # --------------------------------------------------------

    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "DATABASE_URL",
            "database_url",
        ),
    )

    database_echo: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "DATABASE_ECHO",
            "database_echo",
        ),
    )

    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        validation_alias=AliasChoices(
            "DATABASE_POOL_SIZE",
            "database_pool_size",
        ),
    )

    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=200,
        validation_alias=AliasChoices(
            "DATABASE_MAX_OVERFLOW",
            "database_max_overflow",
        ),
    )

    database_pool_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=300,
        validation_alias=AliasChoices(
            "DATABASE_POOL_TIMEOUT_SECONDS",
            "database_pool_timeout_seconds",
        ),
    )

    database_pool_recycle_seconds: int = Field(
        default=1800,
        ge=0,
        le=86_400,
        validation_alias=AliasChoices(
            "DATABASE_POOL_RECYCLE_SECONDS",
            "database_pool_recycle_seconds",
        ),
    )

    database_migration_mode: DatabaseMigrationMode = Field(
        default=DatabaseMigrationMode.UPGRADE,
        validation_alias=AliasChoices(
            "DATABASE_MIGRATION_MODE",
            "database_migration_mode",
        ),
    )

    # --------------------------------------------------------
    # Verzeichnisse
    # --------------------------------------------------------

    data_directory: Path = Field(
        default=DEFAULT_DATA_DIRECTORY,
        validation_alias=AliasChoices(
            "DATA_DIRECTORY",
            "data_directory",
        ),
    )

    # Workspace projection (filesystem) - infrastructure flags only
    data_projection_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "DATA_PROJECTION_ENABLED",
            "data_projection_enabled",
        ),
    )

    data_projection_path: Path = Field(
        default=Path("./data"),
        validation_alias=AliasChoices(
            "DATA_PROJECTION_PATH",
            "data_projection_path",
        ),
    )

    config_directory: Path = Field(
        default=DEFAULT_CONFIG_DIRECTORY,
        validation_alias=AliasChoices(
            "CONFIG_DIRECTORY",
            "config_directory",
        ),
    )

    bootstrap_config_file: Path = Field(
        default=DEFAULT_BOOTSTRAP_CONFIG_FILE,
        validation_alias=AliasChoices(
            "BOOTSTRAP_CONFIG_FILE",
            "bootstrap_config_file",
        ),
    )

    upload_directory: Path | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "UPLOAD_DIRECTORY",
            "upload_directory",
        ),
    )

    temporary_directory: Path | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "TEMPORARY_DIRECTORY",
            "temporary_directory",
        ),
    )

    model_manifest_directories: tuple[Path, ...] = Field(
        default_factory=lambda: (DEFAULT_MANIFEST_DIRECTORY / "models",),
        validation_alias=AliasChoices(
            "MODEL_MANIFEST_DIRECTORIES",
            "model_manifest_directories",
        ),
    )

    tool_manifest_directories: tuple[Path, ...] = Field(
        default_factory=lambda: (DEFAULT_MANIFEST_DIRECTORY / "tools",),
        validation_alias=AliasChoices(
            "TOOL_MANIFEST_DIRECTORIES",
            "tool_manifest_directories",
        ),
    )

    allowed_model_base_directories: tuple[Path, ...] = Field(
        default_factory=tuple,
        validation_alias=AliasChoices(
            "ALLOWED_MODEL_BASE_DIRECTORIES",
            "MODEL_ALLOWED_BASE_DIRS",
            "allowed_model_base_directories",
        ),
    )

    # --------------------------------------------------------
    # Secrets und Kryptografie
    # --------------------------------------------------------

    secret_key: SecretStr = Field(
        default=SecretStr(
            "development-only-change-me-123456",
        ),
        min_length=32,
        validation_alias=AliasChoices(
            "SECRET_KEY",
            "secret_key",
        ),
    )

    config_encryption_key: SecretStr = Field(
        default=SecretStr(
            "development-only-change-me-12345678901234",
        ),
        min_length=32,
        validation_alias=AliasChoices(
            "CONFIG_ENCRYPTION_KEY",
            "config_encryption_key",
        ),
    )

    bootstrap_admin_token: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices(
            "BOOTSTRAP_ADMIN_TOKEN",
            "bootstrap_admin_token",
        ),
    )

    bootstrap_admin_token_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "BOOTSTRAP_ADMIN_TOKEN_ENABLED",
            "bootstrap_admin_token_enabled",
        ),
    )

    # --------------------------------------------------------
    # TLS
    # --------------------------------------------------------

    tls_cert_file: Path | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "TLS_CERT_FILE",
            "tls_cert_file",
        ),
    )

    tls_key_file: Path | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "TLS_KEY_FILE",
            "tls_key_file",
        ),
    )

    tls_ca_file: Path | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "TLS_CA_FILE",
            "tls_ca_file",
        ),
    )

    # --------------------------------------------------------
    # Proxy und Netzwerkvertrauen
    # --------------------------------------------------------

    forwarded_header_mode: ForwardedHeaderMode = Field(
        default=ForwardedHeaderMode.DISABLED,
        validation_alias=AliasChoices(
            "FORWARDED_HEADER_MODE",
            "forwarded_header_mode",
        ),
    )

    trusted_proxies: tuple[str, ...] = Field(
        default_factory=tuple,
        validation_alias=AliasChoices(
            "TRUSTED_PROXIES",
            "trusted_proxies",
        ),
    )

    trusted_proxy_count: int = Field(
        default=0,
        ge=0,
        le=32,
        validation_alias=AliasChoices(
            "TRUSTED_PROXY_COUNT",
            "trusted_proxy_count",
        ),
    )

    cors_allowed_origins: tuple[str, ...] = Field(
        default_factory=lambda: (
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ),
        validation_alias=AliasChoices(
            "CORS_ALLOWED_ORIGINS",
            "cors_allowed_origins",
        ),
    )

    cors_allow_credentials: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "CORS_ALLOW_CREDENTIALS",
            "cors_allow_credentials",
        ),
    )

    allowed_hosts: tuple[str, ...] = Field(
        default_factory=lambda: (
            "localhost",
            "127.0.0.1",
        ),
        validation_alias=AliasChoices(
            "ALLOWED_HOSTS",
            "allowed_hosts",
        ),
    )

    # --------------------------------------------------------
    # Session und Cookies
    # --------------------------------------------------------

    session_cookie_name: str = Field(
        default="kernschmied_session",
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices(
            "SESSION_COOKIE_NAME",
            "session_cookie_name",
        ),
    )

    session_cookie_domain: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SESSION_COOKIE_DOMAIN",
            "session_cookie_domain",
        ),
    )

    session_cookie_path: str = Field(
        default="/",
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices(
            "SESSION_COOKIE_PATH",
            "session_cookie_path",
        ),
    )

    session_lifetime_seconds: int = Field(
        default=8 * 60 * 60,
        ge=300,
        le=90 * 24 * 60 * 60,
        validation_alias=AliasChoices(
            "SESSION_LIFETIME_SECONDS",
            "session_lifetime_seconds",
        ),
    )

    # --------------------------------------------------------
    # Development helpers (must be conservative and opt-in)
    # --------------------------------------------------------

    # Allow a development-only auth fallback (e.g. for local dev only).
    # Default is False to avoid accidental exposure in dev environments.
    development_auth_fallback_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "DEVELOPMENT_AUTH_FALLBACK_ENABLED",
            "development_auth_fallback_enabled",
        ),
    )

    # Enable a development administrator login endpoint (no password).
    # Only effective when `app_environment` == DEVELOPMENT.
    development_admin_login_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "DEVELOPMENT_ADMIN_LOGIN_ENABLED",
            "development_admin_login_enabled",
        ),
    )

    # Configurable identity for the development admin user created by the
    # idempotent dev-seed. These defaults are conservative and stable.
    development_admin_user_id: str = Field(
        default="local-development-admin",
        min_length=1,
        validation_alias=AliasChoices(
            "DEVELOPMENT_ADMIN_USER_ID",
            "development_admin_user_id",
        ),
    )

    development_admin_username: str = Field(
        default="admin",
        min_length=1,
        validation_alias=AliasChoices(
            "DEVELOPMENT_ADMIN_USERNAME",
            "development_admin_username",
        ),
    )

    development_admin_display_name: str = Field(
        default="Administrator",
        min_length=1,
        validation_alias=AliasChoices(
            "DEVELOPMENT_ADMIN_DISPLAY_NAME",
            "development_admin_display_name",
        ),
    )

    # Development-only plain password for the seeded admin. ONLY used in
    # development environment by the idempotent dev-seed to produce a
    # reproducible password. Do NOT weaken password policies elsewhere.
    development_admin_password: str = Field(
        default="user",
        min_length=1,
        validation_alias=AliasChoices(
            "DEVELOPMENT_ADMIN_PASSWORD",
            "development_admin_password",
        ),
    )

    # --------------------------------------------------------
    # Registration and self-service
    # --------------------------------------------------------

    # Global toggle for self-registration (affects intranet/internet profiles)
    self_registration_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "SELF_REGISTRATION_ENABLED",
            "self_registration_enabled",
        ),
    )

    # In development, allow enabling self-registration separately for convenience
    development_self_registration_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "DEVELOPMENT_SELF_REGISTRATION_ENABLED",
            "development_self_registration_enabled",
        ),
    )

    # Require a valid invitation for registration when true
    registration_requires_invitation: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "REGISTRATION_REQUIRES_INVITATION",
            "registration_requires_invitation",
        ),
    )

    # --------------------------------------------------------
    # E-Mail-Zustellung
    # --------------------------------------------------------

    email_delivery_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "EMAIL_DELIVERY_ENABLED",
            "email_delivery_enabled",
        ),
    )
    email_provider: str = Field(
        default="smtp",
        min_length=1,
        max_length=50,
        validation_alias=AliasChoices("EMAIL_PROVIDER", "email_provider"),
    )
    email_from_address: str = Field(
        default="noreply@kernschmied.local",
        min_length=3,
        max_length=320,
        validation_alias=AliasChoices(
            "EMAIL_FROM_ADDRESS",
            "email_from_address",
        ),
    )
    smtp_host: str = Field(
        default="127.0.0.1",
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("SMTP_HOST", "smtp_host"),
    )
    smtp_port: int = Field(
        default=1025,
        ge=1,
        le=65535,
        validation_alias=AliasChoices("SMTP_PORT", "smtp_port"),
    )
    smtp_starttls: bool = Field(
        default=False,
        validation_alias=AliasChoices("SMTP_STARTTLS", "smtp_starttls"),
    )
    smtp_username: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SMTP_USERNAME", "smtp_username"),
    )
    smtp_password: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices("SMTP_PASSWORD", "smtp_password"),
    )

    # --------------------------------------------------------
    # Logging und Diagnose
    # --------------------------------------------------------

    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        validation_alias=AliasChoices(
            "LOG_LEVEL",
            "log_level",
        ),
    )

    log_json: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "LOG_JSON",
            "log_json",
        ),
    )

    request_id_header: str = Field(
        default="X-Request-ID",
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices(
            "REQUEST_ID_HEADER",
            "request_id_header",
        ),
    )

    expose_api_docs: bool | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "EXPOSE_API_DOCS",
            "expose_api_docs",
        ),
    )

    expose_detailed_errors: bool | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "EXPOSE_DETAILED_ERRORS",
            "expose_detailed_errors",
        ),
    )

    # --------------------------------------------------------
    # Validierung und Normalisierung
    # --------------------------------------------------------

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized.startswith("/"):
            normalized = f"/{normalized}"

        if normalized != "/":
            normalized = normalized.rstrip("/")

        if ".." in normalized:
            raise ValueError(
                "api_prefix darf keine relativen Pfadsegmente enthalten.",
            )

        return normalized

    @field_validator("public_base_url")
    @classmethod
    def validate_public_base_url(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().rstrip("/")

        parsed = urlparse(normalized)

        if parsed.scheme not in {
            "http",
            "https",
        }:
            raise ValueError(
                "public_base_url muss eine HTTP- oder HTTPS-URL sein.",
            )

        if not parsed.netloc:
            raise ValueError(
                "public_base_url benötigt einen Hostnamen.",
            )

        return normalized

    @field_validator(
        "trusted_proxies",
        "cors_allowed_origins",
        "allowed_hosts",
        mode="before",
    )
    @classmethod
    def normalize_string_collections(
        cls,
        value: Any,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        return _normalize_string_tuple(value)

    @field_validator(
        "data_directory",
        "config_directory",
        "bootstrap_config_file",
        "upload_directory",
        "temporary_directory",
        "tls_cert_file",
        "tls_key_file",
        "tls_ca_file",
        mode="before",
    )
    @classmethod
    def normalize_optional_paths(
        cls,
        value: Any,
    ) -> Path | None:
        if value is None:
            return None

        return _normalize_path(value)

    @field_validator(
        "model_manifest_directories",
        "tool_manifest_directories",
        "allowed_model_base_directories",
        mode="before",
    )
    @classmethod
    def normalize_path_collections(
        cls,
        value: Any,
    ) -> tuple[Path, ...]:
        if value is None:
            return ()

        if isinstance(value, str):
            value = tuple(part.strip() for part in value.split(",") if part.strip())

        return tuple(_normalize_path(item) for item in value)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        scheme = normalized.split(
            "://",
            maxsplit=1,
        )[0].lower()

        if scheme not in SUPPORTED_DATABASE_SCHEMES:
            supported = ", ".join(
                sorted(SUPPORTED_DATABASE_SCHEMES),
            )

            raise ValueError(
                "Nicht unterstütztes Datenbank-Schema "
                f"'{scheme}'. Unterstützt: {supported}.",
            )

        return normalized

    @field_validator("session_cookie_path")
    @classmethod
    def validate_cookie_path(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized.startswith("/"):
            raise ValueError(
                "session_cookie_path muss mit '/' beginnen.",
            )

        return normalized

    @model_validator(mode="after")
    def validate_runtime_security(
        self,
    ) -> Settings:
        self._validate_tls_configuration()
        self._validate_proxy_configuration()
        self._validate_bootstrap_token()
        self._validate_environment_security()
        self._validate_public_url()
        self._validate_cors_configuration()

        return self

    def _validate_tls_configuration(
        self,
    ) -> None:
        cert_configured = self.tls_cert_file is not None
        key_configured = self.tls_key_file is not None

        if cert_configured != key_configured:
            raise ValueError(
                "TLS_CERT_FILE und TLS_KEY_FILE müssen gemeinsam konfiguriert werden.",
            )

    def _validate_proxy_configuration(
        self,
    ) -> None:
        if (
            self.forwarded_header_mode == ForwardedHeaderMode.TRUSTED_PROXIES
            and not self.trusted_proxies
            and self.trusted_proxy_count == 0
        ):
            raise ValueError(
                "FORWARDED_HEADER_MODE=trusted_proxies benötigt "
                "TRUSTED_PROXIES oder TRUSTED_PROXY_COUNT.",
            )

        if self.forwarded_header_mode == ForwardedHeaderMode.DISABLED and (
            self.trusted_proxies or self.trusted_proxy_count > 0
        ):
            raise ValueError(
                "TRUSTED_PROXIES und TRUSTED_PROXY_COUNT dürfen nur "
                "bei FORWARDED_HEADER_MODE=trusted_proxies gesetzt sein.",
            )

    def _validate_bootstrap_token(
        self,
    ) -> None:
        token = self.bootstrap_admin_token.get_secret_value().strip()

        if self.bootstrap_admin_token_enabled and not token:
            raise ValueError(
                "BOOTSTRAP_ADMIN_TOKEN_ENABLED=true benötigt einen "
                "BOOTSTRAP_ADMIN_TOKEN.",
            )

        if token and len(token) < 32:
            raise ValueError(
                "BOOTSTRAP_ADMIN_TOKEN muss mindestens 32 Zeichen lang sein.",
            )

    def _validate_environment_security(
        self,
    ) -> None:
        if self.app_environment == AppEnvironment.DEVELOPMENT:
            return

        secret_key = self.secret_key.get_secret_value().strip()

        encryption_key = self.config_encryption_key.get_secret_value().strip()

        if secret_key.lower() in INSECURE_SECRET_VALUES or len(secret_key) < 32:
            raise ValueError(
                "SECRET_KEY muss in Intranet- und Internetprofilen "
                "sicher gesetzt und mindestens 32 Zeichen lang sein.",
            )

        if encryption_key.lower() in INSECURE_SECRET_VALUES or len(encryption_key) < 32:
            raise ValueError(
                "CONFIG_ENCRYPTION_KEY muss in Intranet- und "
                "Internetprofilen sicher gesetzt und mindestens "
                "32 Zeichen lang sein.",
            )

        if self.database_migration_mode == DatabaseMigrationMode.UPGRADE:
            if self.app_environment == AppEnvironment.INTERNET:
                raise ValueError(
                    "DATABASE_MIGRATION_MODE=upgrade ist im "
                    "Internetprofil nicht zulässig. Migrationen müssen "
                    "kontrolliert vor dem Webprozess ausgeführt werden.",
                )

    def _validate_public_url(
        self,
    ) -> None:
        if self.public_base_url is None:
            return

        parsed = urlparse(
            self.public_base_url,
        )

        if self.app_environment == AppEnvironment.INTERNET and parsed.scheme != "https":
            raise ValueError(
                "PUBLIC_BASE_URL muss im Internetprofil HTTPS verwenden.",
            )

    def _validate_cors_configuration(
        self,
    ) -> None:
        wildcard_present = "*" in self.cors_allowed_origins

        if wildcard_present and self.cors_allow_credentials:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS='*' darf nicht mit "
                "CORS_ALLOW_CREDENTIALS=true kombiniert werden.",
            )

        if (
            self.app_environment
            in {
                AppEnvironment.INTRANET,
                AppEnvironment.INTERNET,
            }
            and wildcard_present
        ):
            raise ValueError(
                "Wildcard-CORS ist im Intranet- und Internetprofil nicht zulässig.",
            )

    # --------------------------------------------------------
    # Abgeleitete Werte
    # --------------------------------------------------------

    @property
    def app_env(self) -> str:
        """
        Rückwärtskompatibilität für bisherigen Code.

        Neue Aufrufer sollten `app_environment` verwenden.
        """

        return self.app_environment.value

    @property
    def effective_database_url(self) -> str:
        """
        Liefert die konfigurierte Datenbank-URL oder eine absolute
        SQLite-Standard-URL.
        """

        # If a URL is explicitly configured, normalize sqlite relative paths
        url = resolve_database_url(
            self.database_url, backend_directory=BACKEND_DIRECTORY
        )
        if url:
            return url

        return _sqlite_database_url(
            self.data_directory / "kernschmied.db",
        )

    @property
    def effective_upload_directory(self) -> Path:
        return self.upload_directory or self.data_directory / "uploads"

    @property
    def effective_temporary_directory(self) -> Path:
        return self.temporary_directory or self.data_directory / "tmp"

    @property
    def api_docs_enabled(self) -> bool:
        if self.expose_api_docs is not None:
            return self.expose_api_docs

        return self.app_environment != AppEnvironment.INTERNET

    @property
    def detailed_errors_enabled(self) -> bool:
        if self.expose_detailed_errors is not None:
            return self.expose_detailed_errors

        return self.app_environment == AppEnvironment.DEVELOPMENT

    @property
    def tls_configured(self) -> bool:
        return self.tls_cert_file is not None and self.tls_key_file is not None

    @property
    def is_development(self) -> bool:
        return self.app_environment == AppEnvironment.DEVELOPMENT

    @property
    def is_intranet(self) -> bool:
        return self.app_environment == AppEnvironment.INTRANET

    @property
    def is_internet(self) -> bool:
        return self.app_environment == AppEnvironment.INTERNET

    # --------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------

    def ensure_runtime_directories(self) -> None:
        """
        Erstellt ausschließlich technische Laufzeitverzeichnisse.

        Diese Methode sollte kontrolliert während des Bootstraps aufgerufen
        werden und nicht bereits beim Import der Settings.
        """

        directories = {
            self.data_directory,
            self.config_directory,
            self.effective_upload_directory,
            self.effective_temporary_directory,
        }

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    def validate_runtime_files(self) -> None:
        """
        Prüft konfigurierte Dateien, ohne sie automatisch zu erzeugen.
        """

        required_files: list[tuple[str, Path | None]] = [
            (
                "TLS_CERT_FILE",
                self.tls_cert_file,
            ),
            (
                "TLS_KEY_FILE",
                self.tls_key_file,
            ),
            (
                "TLS_CA_FILE",
                self.tls_ca_file,
            ),
        ]

        missing_files = [
            f"{name}: {path}"
            for name, path in required_files
            if path is not None and not path.is_file()
        ]

        if missing_files:
            raise RuntimeError(
                "Konfigurierte Laufzeitdateien wurden nicht gefunden: "
                + "; ".join(missing_files),
            )

    # --------------------------------------------------------
    # Sichere Diagnose
    # --------------------------------------------------------

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Liefert eine protokollierbare Übersicht ohne Secrets.
        """

        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "app_environment": self.app_environment.value,
            "api_prefix": self.api_prefix,
            "backend_host": self.backend_host,
            "backend_port": self.backend_port,
            "workers": self.workers,
            "database_scheme": self.database_scheme,
            "database_migration_mode": (self.database_migration_mode.value),
            "data_directory": str(
                self.data_directory,
            ),
            "config_directory": str(
                self.config_directory,
            ),
            "upload_directory": str(
                self.effective_upload_directory,
            ),
            "temporary_directory": str(
                self.effective_temporary_directory,
            ),
            "tls_configured": self.tls_configured,
            "forwarded_header_mode": (self.forwarded_header_mode.value),
            "trusted_proxy_count": (self.trusted_proxy_count),
            "configured_trusted_proxies": len(
                self.trusted_proxies,
            ),
            "cors_origin_count": len(
                self.cors_allowed_origins,
            ),
            "allowed_host_count": len(
                self.allowed_hosts,
            ),
            "api_docs_enabled": self.api_docs_enabled,
            "detailed_errors_enabled": (self.detailed_errors_enabled),
            "bootstrap_admin_token_enabled": (self.bootstrap_admin_token_enabled),
        }

    @property
    def database_scheme(self) -> str:
        return self.effective_database_url.split(
            "://",
            maxsplit=1,
        )[0]


# ============================================================
# Settings-Provider
# ============================================================


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Zentraler Settings-Provider.

    Die Instanz bleibt pro Prozess stabil. Dadurch können Dependencies und
    Tests denselben Vertrag verwenden, ohne veränderbare globale Settings
    zu erzeugen.
    """

    return Settings()


def reload_settings() -> Settings:
    """
    Lädt Bootstrap-Settings kontrolliert neu.

    Diese Funktion ist hauptsächlich für Tests, CLI-Befehle und
    kontrollierte Wartungsabläufe gedacht. Fachliche Laufzeitkonfiguration
    wird weiterhin über ConfigService und Config-Revision aktualisiert.
    """

    get_settings.cache_clear()

    return get_settings()


# Rückwärtskompatibilität für bestehende Imports:
#
#     from app.core.settings import settings
#
# Neue Dependencies sollten bevorzugt `get_settings()` verwenden.
settings = get_settings()
