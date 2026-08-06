# F:\Kernschmied\backend\app\api\v1\bootstrap.py

from __future__ import annotations

import inspect
from collections.abc import (
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from enum import StrEnum
from typing import Literal, TypeAlias, cast

from fastapi import (
    APIRouter,
    Request,
    Response,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.core.security_profile import SecurityProfile, get_security_profile
from app.core.settings import settings

router = APIRouter()


BOOTSTRAP_SCHEMA_VERSION = "1.1"
UI_SCHEMA_VERSION = "1.0"
HIERARCHY_SCHEMA_VERSION = "1.0"
CHAT_SCHEMA_VERSION = "1.0"
MODEL_SCHEMA_VERSION = "1.0"
TOOL_SCHEMA_VERSION = "1.0"
API_VERSION = "v1"

DEFAULT_ENVIRONMENT = "development"
DEFAULT_CONFIG_REVISION = 0

EnvironmentLiteral: TypeAlias = Literal[
    "development",
    "intranet",
    "internet",
]

AsyncOrSyncCallable: TypeAlias = Callable[..., object]


class ApplicationEnvironment(StrEnum):
    DEVELOPMENT = "development"
    INTRANET = "intranet"
    INTERNET = "internet"


class BootstrapUser(BaseModel):
    """
    Minimale, frontendfähige Darstellung des aktuellen Benutzers.

    Es werden keine Session-Tokens, Passwortdaten oder internen
    Authentifizierungsinformationen ausgegeben.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    name: str
    roles: list[str] = Field(
        default_factory=list,
    )
    permissions: list[str] = Field(
        default_factory=list,
    )
    authenticated: bool = False


class BootstrapApplication(BaseModel):
    """
    Grundinformationen über die laufende Anwendung.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    name: str
    version: str
    environment: EnvironmentLiteral
    api_prefix: str


class BootstrapVersions(BaseModel):
    """
    Versionen der stabilen Backend- und Frontend-Verträge.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    bootstrap_schema: str = BOOTSTRAP_SCHEMA_VERSION
    ui_schema: str = UI_SCHEMA_VERSION
    hierarchy_schema: str = HIERARCHY_SCHEMA_VERSION
    chat_schema: str = CHAT_SCHEMA_VERSION
    model_schema: str = MODEL_SCHEMA_VERSION
    tool_schema: str = TOOL_SCHEMA_VERSION
    api: str = API_VERSION


class BootstrapEndpoints(BaseModel):
    """
    Zentrale API-Einstiegspunkte für das Frontend.

    Die Pfade werden aus dem tatsächlich konfigurierten API-Prefix
    erzeugt und nicht mehrfach im Frontend fest verdrahtet.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    bootstrap: str
    ui_schema: str
    hierarchy: str
    chat_stream: str
    chats: str
    configuration: str
    models: str
    tools: str
    auth_login: str | None = None
    auth_logout: str | None = None
    auth_me: str | None = None
    auth_development_login: str | None = None
    auth_register: str | None = None
    user_profile: str | None = None
    user_preferences: str | None = None
    auth_sessions: str | None = None
    auth_logout_all: str | None = None
    health_live: str
    health_ready: str


class BootstrapCapabilities(BaseModel):
    """
    Technische Verfügbarkeit von Modulen.

    Diese Werte sind keine Berechtigungsentscheidung. Jeder aufgerufene
    Endpunkt muss die jeweilige Benutzeraktion erneut serverseitig
    autorisieren.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    hierarchy: bool = False
    ui_schema: bool = False
    chat_streaming: bool = False
    chat_persistence: bool = False
    model_registry: bool = False
    model_service: bool = False
    tool_registry: bool = False
    configuration: bool = False
    configuration_admin: bool = False
    file_upload: bool = False
    audit_log: bool = False
    development_login: bool = False


class BootstrapFeatures(BaseModel):
    """
    Für das Frontend sichtbare technische Betriebsmerkmale.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    schema_driven_ui: bool = True
    recursive_hierarchy: bool = True
    server_side_authorization: bool = True
    streaming_transport: Literal["sse"] = "sse"
    dynamic_models: bool = False
    dynamic_tools: bool = False
    runtime_configuration: bool = False
    # Runtime-visible feature flags
    development_admin_login: bool = False
    self_registration: bool = False
    registration_requires_invitation: bool = False


class BootstrapRevisions(BaseModel):
    """
    Revisionsstände für Cache-Invalidierung und Diagnose.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    configuration: int = Field(
        default=0,
        ge=0,
    )
    model_registry: int = Field(
        default=0,
        ge=0,
    )
    tool_registry: int = Field(
        default=0,
        ge=0,
    )


class BootstrapResponse(BaseModel):
    """
    Stabiler und versionierter Bootstrap-Vertrag.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: str = BOOTSTRAP_SCHEMA_VERSION  # <-- NEU
    api_version: str = API_VERSION  # <-- NEU

    application: BootstrapApplication
    environment: EnvironmentLiteral
    user: BootstrapUser
    security_profile: dict[str, object]
    capabilities: BootstrapCapabilities
    features: BootstrapFeatures
    versions: BootstrapVersions
    endpoints: BootstrapEndpoints
    revisions: BootstrapRevisions
    config_revision: int = Field(
        ge=0,
    )
    request_id: str | None = None

    # Optionale Felder für Frontend-Kompatibilität
    minimum_client_version: str | None = Field(
        default=None,
        description="Erforderliche Mindestversion des Frontends.",
    )
    feature_flags: dict[str, bool] | None = Field(
        default=None,
        description="Feature-Flags für das Frontend.",
    )


def _get_request_id(
    request: Request,
) -> str | None:
    request_id: object = getattr(
        request.state,
        "request_id",
        None,
    )

    if request_id is None:
        return None

    normalized = str(
        request_id,
    ).strip()

    return normalized or None


def _normalize_api_prefix(
    value: object,
) -> str:
    raw_prefix = str(
        value or "/api/v1",
    ).strip()

    if not raw_prefix:
        return "/api/v1"

    normalized = raw_prefix if raw_prefix.startswith("/") else f"/{raw_prefix}"

    if normalized != "/":
        normalized = normalized.rstrip("/")

    return normalized or "/api/v1"


def _get_api_prefix(
    request: Request,
) -> str:
    runtime_config: object = getattr(
        request.app.state,
        "runtime_config",
        None,
    )

    if runtime_config is not None:
        runtime_prefix: object = getattr(
            runtime_config,
            "api_prefix",
            None,
        )

        if runtime_prefix is not None:
            return _normalize_api_prefix(
                runtime_prefix,
            )

    return _normalize_api_prefix(
        getattr(
            settings,
            "api_prefix",
            "/api/v1",
        ),
    )


def _get_config_service(
    request: Request,
) -> object:
    config_service: object = getattr(
        request.app.state,
        "config_service",
        None,
    )

    # If no config service is registered in the ASGI app state, do not
    # treat this as a hard failure for the bootstrap endpoint. The
    # frontend needs a minimal, public bootstrap to render the login UI
    # and feature flags. Downstream callers should defensively handle a
    # missing config_service where appropriate.
    return config_service


async def _resolve_maybe_awaitable(
    value: object,
) -> object:
    if inspect.isawaitable(value):
        return await cast(
            Awaitable[object],
            value,
        )

    return value


async def _read_config_value(
    config_service: object,
    section: str,
    key: str,
    default: object,
) -> object:
    """
    Liest einen Konfigurationswert aus unterschiedlichen
    ConfigService-Implementierungen.

    Unterstützt werden synchrone und asynchrone `get()`-Methoden.
    """

    getter_value: object = getattr(
        config_service,
        "get",
        None,
    )

    if not callable(getter_value):
        return default

    getter = getter_value

    try:
        raw_result = getter(
            section,
            key,
            default,
        )

        resolved_result = await _resolve_maybe_awaitable(
            raw_result,
        )

        return default if resolved_result is None else resolved_result

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        return default


def _normalize_environment(
    value: object,
) -> EnvironmentLiteral:
    normalized = (
        str(
            value,
        )
        .strip()
        .lower()
    )

    if normalized == ApplicationEnvironment.INTRANET.value:
        return "intranet"

    if normalized == ApplicationEnvironment.INTERNET.value:
        return "internet"

    return "development"


def _normalize_string_list(
    value: object,
) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        values: list[object] = [
            value,
        ]

    elif isinstance(value, Mapping):
        return []

    elif isinstance(value, Sequence):
        values = list(
            cast(
                Sequence[object],
                value,
            ),
        )

    elif isinstance(
        value,
        set | frozenset,
    ):
        values = list(
            cast(
                set[object] | frozenset[object],
                value,
            ),
        )

    else:
        return []

    result: list[str] = []
    seen: set[str] = set()

    for item in values:
        if item is None:
            continue

        normalized = str(
            item,
        ).strip()

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(
            normalized,
        )
        result.append(
            normalized,
        )

    return result


def _read_mapping_or_attribute(
    source: object,
    key: str,
    default: object = None,
) -> object:
    if isinstance(source, Mapping):
        typed_mapping = cast(
            Mapping[object, object],
            source,
        )

        return typed_mapping.get(
            key,
            default,
        )

    return getattr(
        source,
        key,
        default,
    )


def _coerce_bool(
    value: object,
    *,
    default: bool = False,
) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value != 0

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {
            "1",
            "true",
            "yes",
            "on",
            "enabled",
        }:
            return True

        if normalized in {
            "0",
            "false",
            "no",
            "off",
            "disabled",
        }:
            return False

    return default


def _coerce_non_negative_int(
    value: object,
    *,
    default: int = 0,
) -> int:
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return max(
            value,
            0,
        )

    if isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            return default

        try:
            return max(
                int(normalized),
                0,
            )
        except ValueError:
            return default

    return default


def _resolve_authenticated_user(
    request: Request,
) -> BootstrapUser | None:
    """
    Erwartet einen von der Authentifizierungs-Middleware bereitgestellten
    Principal unter `request.state.user` oder `request.state.principal`.
    """

    principal: object = getattr(
        request.state,
        "user",
        None,
    )

    if principal is None:
        principal = getattr(
            request.state,
            "principal",
            None,
        )

    if principal is None:
        return None

    user_id = _read_mapping_or_attribute(
        principal,
        "id",
    )

    if user_id is None:
        user_id = _read_mapping_or_attribute(
            principal,
            "user_id",
        )

    if user_id is None:
        user_id = _read_mapping_or_attribute(
            principal,
            "subject",
        )

    if user_id is None:
        return None

    name = _read_mapping_or_attribute(
        principal,
        "name",
    )

    if name is None:
        name = _read_mapping_or_attribute(
            principal,
            "display_name",
        )

    if name is None:
        name = _read_mapping_or_attribute(
            principal,
            "username",
        )

    if name is None:
        name = str(
            user_id,
        )

    authenticated_value = _read_mapping_or_attribute(
        principal,
        "authenticated",
        True,
    )

    return BootstrapUser(
        id=str(
            user_id,
        ),
        name=str(
            name,
        ),
        roles=_normalize_string_list(
            _read_mapping_or_attribute(
                principal,
                "roles",
                [],
            ),
        ),
        permissions=_normalize_string_list(
            _read_mapping_or_attribute(
                principal,
                "permissions",
                [],
            ),
        ),
        authenticated=_coerce_bool(
            authenticated_value,
            default=True,
        ),
    )


async def _development_user(
    config_service: object,
) -> BootstrapUser:
    """
    Lokaler Benutzer ausschließlich für das Development-Profil.

    Der Fallback wird niemals für Intranet oder Internet verwendet.
    """

    user_id = await _read_config_value(
        config_service,
        "development",
        "local_user_id",
        "local-user",
    )

    user_name = await _read_config_value(
        config_service,
        "development",
        "local_user_name",
        "Lokaler Benutzer",
    )

    roles = await _read_config_value(
        config_service,
        "development",
        "local_user_roles",
        ["admin"],
    )

    permissions = await _read_config_value(
        config_service,
        "development",
        "local_user_permissions",
        ["*"],
    )

    return BootstrapUser(
        id=str(
            user_id,
        ),
        name=str(
            user_name,
        ),
        roles=_normalize_string_list(
            roles,
        ),
        permissions=_normalize_string_list(
            permissions,
        ),
        authenticated=True,
    )


def _anonymous_user() -> BootstrapUser:
    return BootstrapUser(
        id="anonymous",
        name="Nicht angemeldet",
        roles=[],
        permissions=[],
        authenticated=False,
    )


async def _resolve_user(
    request: Request,
    config_service: object,
    environment: EnvironmentLiteral,
) -> BootstrapUser:
    authenticated_user = _resolve_authenticated_user(
        request,
    )

    if authenticated_user is not None:
        return authenticated_user

    # Only provide the development fallback when the runtime configuration
    # actually enables the authentication fallback. This keeps the bootstrap
    # response consistent with the AuthenticationContextMiddleware which may
    # refuse to inject a development principal.
    if environment == "development":
        runtime_cfg = getattr(request.app.state, "runtime_config", None)
        fallback_enabled = False
        if runtime_cfg is not None:
            fallback_enabled = bool(
                getattr(runtime_cfg, "development_auth_fallback_enabled", False)
            )

        if fallback_enabled:
            return await _development_user(
                config_service,
            )

    return _anonymous_user()


async def _read_revision_from_service(
    service: object,
    *,
    default: int = 0,
) -> int:
    getter_value: object = getattr(
        service,
        "get_revision",
        None,
    )

    if callable(getter_value):
        getter = cast(
            Callable[[], object],
            getter_value,
        )

        try:
            raw_result = getter()

            resolved_result = await _resolve_maybe_awaitable(
                raw_result,
            )

            return _coerce_non_negative_int(
                resolved_result,
                default=default,
            )

        except (
            TypeError,
            ValueError,
            RuntimeError,
        ):
            return default

    revision_value: object = getattr(
        service,
        "revision",
        default,
    )

    return _coerce_non_negative_int(
        revision_value,
        default=default,
    )


async def _get_config_revision(
    config_service: object,
) -> int:
    return await _read_revision_from_service(
        config_service,
        default=DEFAULT_CONFIG_REVISION,
    )


def _get_service(
    request: Request,
    *service_names: str,
) -> object | None:
    for service_name in service_names:
        service: object = getattr(
            request.app.state,
            service_name,
            None,
        )

        if service is not None:
            return service

    return None


def _service_available(
    request: Request,
    *service_names: str,
) -> bool:
    return (
        _get_service(
            request,
            *service_names,
        )
        is not None
    )


def _has_any_permission(
    user: BootstrapUser,
    *,
    permissions: set[str],
    roles: set[str] | None = None,
) -> bool:
    user_permissions = set(
        user.permissions,
    )

    if "*" in user_permissions:
        return True

    if user_permissions.intersection(
        permissions,
    ):
        return True

    if roles is not None:
        user_roles = set(
            user.roles,
        )

        if user_roles.intersection(
            roles,
        ):
            return True

    return False


def _resolve_capabilities(
    request: Request,
    user: BootstrapUser,
) -> BootstrapCapabilities:
    hierarchy_available = _service_available(
        request,
        "hierarchy_service",
        "hierarchy_repository",
    )

    ui_schema_available = _service_available(
        request,
        "ui_schema_service",
        "ui_service",
    )

    chat_service_available = _service_available(
        request,
        "chat_service",
    )

    chat_repository_available = _service_available(
        request,
        "chat_repository",
        "database",
        "database_manager",
    )

    model_registry_available = _service_available(
        request,
        "model_registry",
    )

    model_service_available = _service_available(
        request,
        "model_service",
        "model_lifecycle",
    )

    tool_registry_available = _service_available(
        request,
        "tool_registry",
    )

    config_service_available = _service_available(
        request,
        "config_service",
    )

    audit_log_available = _service_available(
        request,
        "audit_service",
        "audit_log",
        "audit_repository",
    )

    file_upload_available = _service_available(
        request,
        "file_service",
        "upload_service",
        "storage_service",
    )

    configuration_admin = _has_any_permission(
        user,
        permissions={
            "config:read",
            "config:write",
            "config:admin",
        },
        roles={
            "admin",
            "administrator",
        },
    )

    development_login_enabled = str(
        getattr(settings, "app_environment", "development")
    ).lower() == "development" and bool(
        getattr(settings, "development_admin_login_enabled", False)
    )

    return BootstrapCapabilities(
        hierarchy=hierarchy_available,
        ui_schema=ui_schema_available,
        chat_streaming=chat_service_available,
        chat_persistence=chat_repository_available,
        model_registry=model_registry_available,
        model_service=model_service_available,
        tool_registry=tool_registry_available,
        configuration=config_service_available,
        configuration_admin=configuration_admin,
        file_upload=file_upload_available,
        audit_log=audit_log_available,
        development_login=development_login_enabled,
    )


def _resolve_features(
    capabilities: BootstrapCapabilities,
) -> BootstrapFeatures:
    # Determine registration and development-login features based on settings
    app_env = str(getattr(settings, "app_environment", "development")).lower()
    development_admin_login = app_env == "development" and bool(
        getattr(settings, "development_admin_login_enabled", False)
    )

    if app_env == "development":
        self_registration = bool(
            getattr(settings, "development_self_registration_enabled", False)
        )
    else:
        self_registration = bool(getattr(settings, "self_registration_enabled", False))

    registration_requires_invitation = bool(
        getattr(settings, "registration_requires_invitation", False)
    )

    return BootstrapFeatures(
        schema_driven_ui=True,
        recursive_hierarchy=capabilities.hierarchy,
        server_side_authorization=True,
        streaming_transport="sse",
        dynamic_models=(capabilities.model_registry or capabilities.model_service),
        dynamic_tools=capabilities.tool_registry,
        runtime_configuration=(capabilities.configuration),
        # extend with runtime-visible flags
        **{
            "development_admin_login": development_admin_login,
            "self_registration": self_registration,
            "registration_requires_invitation": registration_requires_invitation,
        },
    )


def _build_endpoints(
    api_prefix: str,
) -> BootstrapEndpoints:
    return BootstrapEndpoints(
        bootstrap=f"{api_prefix}/bootstrap",
        ui_schema=f"{api_prefix}/ui/schema",
        hierarchy=f"{api_prefix}/hierarchy",
        chat_stream=f"{api_prefix}/chat/stream",
        chats=f"{api_prefix}/chats",
        configuration=f"{api_prefix}/config",
        models=f"{api_prefix}/models",
        tools=f"{api_prefix}/tools",
        auth_login=f"{api_prefix}/auth/login",
        auth_logout=f"{api_prefix}/auth/logout",
        auth_me=f"{api_prefix}/auth/me",
        auth_development_login=f"{api_prefix}/auth/development-login",
        auth_register=f"{api_prefix}/auth/register",
        user_profile=f"{api_prefix}/users/me",
        user_preferences=f"{api_prefix}/users/me/preferences",
        auth_sessions=f"{api_prefix}/auth/sessions",
        auth_logout_all=f"{api_prefix}/auth/logout-all",
        health_live="/health/live",
        health_ready="/health/ready",
    )


def _build_application_info(
    *,
    environment: EnvironmentLiteral,
    api_prefix: str,
) -> BootstrapApplication:
    app_name = str(
        getattr(
            settings,
            "app_name",
            "Kernschmied",
        ),
    )

    app_version = str(
        getattr(
            settings,
            "app_version",
            "0.1.0",
        ),
    )

    return BootstrapApplication(
        name=app_name,
        version=app_version,
        environment=environment,
        api_prefix=api_prefix,
    )


async def _resolve_revisions(
    request: Request,
    config_service: object,
) -> BootstrapRevisions:
    model_registry = _get_service(
        request,
        "model_registry",
        "model_service",
    )

    tool_registry = _get_service(
        request,
        "tool_registry",
    )

    configuration_revision = await _get_config_revision(
        config_service,
    )

    model_registry_revision = (
        await _read_revision_from_service(
            model_registry,
        )
        if model_registry is not None
        else 0
    )

    tool_registry_revision = (
        await _read_revision_from_service(
            tool_registry,
        )
        if tool_registry is not None
        else 0
    )

    return BootstrapRevisions(
        configuration=configuration_revision,
        model_registry=model_registry_revision,
        tool_registry=tool_registry_revision,
    )


def _serialize_security_profile(
    security_profile: SecurityProfile | None = None,
) -> dict[str, object]:
    if security_profile is None:
        security_profile = get_security_profile()

    raw_security = security_profile.model_dump(
        mode="json",
    )

    return cast(dict[str, object], raw_security)


def _enhanced_security_profile() -> dict[str, object]:
    """Return a serializable security profile extended with runtime
    information about available login methods and development identity.
    """
    security_profile = get_security_profile()

    raw_security = _serialize_security_profile(security_profile)

    result: dict[str, object] = dict(raw_security)

    # Canonical profile name
    result["profile"] = str(getattr(settings, "app_environment", "development")).lower()

    result["authentication_required"] = bool(
        getattr(security_profile, "auth_required", True)
    )

    # Development identity active only in development when explicitly enabled
    app_env = str(getattr(settings, "app_environment", "development")).lower()
    result["development_identity_active"] = app_env == "development" and bool(
        getattr(settings, "development_admin_login_enabled", False)
    )

    # Compute available login methods conservatively from security profile and settings
    methods: list[str] = []
    allowed_auth_modes: set[object] = getattr(
        security_profile, "allowed_auth_modes", set()
    )
    # session -> password-based login
    from app.core.security_profile import AuthMode

    if AuthMode.SESSION in allowed_auth_modes:
        methods.append("password")

    if AuthMode.API_KEY in allowed_auth_modes:
        methods.append("api_key")

    # development-admin only in development and when enabled
    if app_env == "development" and bool(
        getattr(settings, "development_admin_login_enabled", False)
    ):
        methods.append("development_admin")

    # registration availability
    registration_allowed = False
    if app_env == "development":
        registration_allowed = bool(
            getattr(settings, "development_self_registration_enabled", False)
        )
    else:
        registration_allowed = bool(
            getattr(settings, "self_registration_enabled", False)
        )

    if registration_allowed:
        methods.append("registration")

    result["available_login_methods"] = methods

    # Explicit runtime flags for authentication/settings UI
    result["development_fallback_enabled"] = app_env == "development" and bool(
        getattr(settings, "development_auth_fallback_enabled", False)
    )
    result["development_admin_login_enabled"] = bool(
        getattr(settings, "development_admin_login_enabled", False)
    )
    result["self_registration"] = registration_allowed
    result["development_self_registration"] = bool(
        getattr(settings, "development_self_registration_enabled", False)
    )
    result["registration_requires_invitation"] = bool(
        getattr(settings, "registration_requires_invitation", False)
    )

    return result


@router.get(
    "",
    response_model=BootstrapResponse,
    response_model_exclude_none=True,
    summary="Frontend-Bootstrap laden",
    description=(
        "Liefert die initialen, nicht sensiblen Laufzeitinformationen "
        "für das schema-gesteuerte Frontend. Der Bootstrap ersetzt "
        "keine serverseitige Autorisierung."
    ),
)
async def bootstrap(
    request: Request,
    response: Response,
) -> BootstrapResponse:
    """
    Initialer Einstiegspunkt für das Frontend.

    Der Endpunkt liefert:

    - Anwendung und Betriebsprofil
    - aktuellen Benutzerkontext
    - festes Sicherheitsprofil
    - technische Fähigkeiten
    - aktivierte Feature-Gruppen
    - Vertragsversionen
    - dynamisch erzeugte API-Einstiegspunkte
    - Config-, Modell- und Tool-Revisionen
    """

    config_service = _get_config_service(
        request,
    )

    # Das Sicherheitsprofil ist Bootstrap-/Infrastrukturkonfiguration.
    # Die Datenbank darf es nicht auf ein schwächeres Profil umstellen.
    configured_environment: object = getattr(
        settings,
        "app_environment",
        DEFAULT_ENVIRONMENT,
    )

    environment = _normalize_environment(
        getattr(
            configured_environment,
            "value",
            configured_environment,
        ),
    )

    user = await _resolve_user(
        request=request,
        config_service=config_service,
        environment=environment,
    )

    capabilities = _resolve_capabilities(
        request=request,
        user=user,
    )

    revisions = await _resolve_revisions(
        request=request,
        config_service=config_service,
    )

    api_prefix = _get_api_prefix(
        request,
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    response.headers["X-Config-Revision"] = str(
        revisions.configuration,
    )
    response.headers["X-Model-Registry-Revision"] = str(
        revisions.model_registry,
    )
    response.headers["X-Tool-Registry-Revision"] = str(
        revisions.tool_registry,
    )
    response.headers["X-Bootstrap-Schema-Version"] = BOOTSTRAP_SCHEMA_VERSION

    return BootstrapResponse(
        schema_version=BOOTSTRAP_SCHEMA_VERSION,
        api_version=API_VERSION,
        application=_build_application_info(
            environment=environment,
            api_prefix=api_prefix,
        ),
        environment=environment,
        user=user,
        security_profile=_enhanced_security_profile(),
        capabilities=capabilities,
        features=_resolve_features(
            capabilities,
        ),
        versions=BootstrapVersions(),
        endpoints=_build_endpoints(
            api_prefix,
        ),
        revisions=revisions,
        config_revision=revisions.configuration,
        request_id=_get_request_id(
            request,
        ),
        minimum_client_version="1.0.0",
        feature_flags={
            "experimental_ui": False,
            "new_tool_selector": True,
        },
    )
