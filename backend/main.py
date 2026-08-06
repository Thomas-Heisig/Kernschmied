# F:\Kernschmied\backend\main.py

from __future__ import annotations

import inspect
import logging
import time
import uuid
from collections.abc import (
    AsyncGenerator,
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from app.api.v1.router import api_router
from app.auth import AuthenticationContextMiddleware
from app.core.bootstrap import (
    bootstrap_application,
    shutdown_application,
)
from app.core.exceptions import ApplicationError
from app.core.settings import settings
from app.status_compat import HTTP_422_UNPROCESSABLE_CONTENT
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ============================================================
# Modulkonfiguration
# ============================================================

SOURCE_FILE = "backend/main.py"
LOG_AREA = "application-runtime"

DEFAULT_API_PREFIX = "/api/v1"
DEFAULT_API_VERSION = "1.0"

REQUEST_ID_HEADER = "X-Request-ID"
CLIENT_REQUEST_ID_HEADER = "X-Client-Request-ID"

API_VERSION_HEADER = "X-API-Version"
CONFIG_REVISION_HEADER = "X-Config-Revision"

DEVELOPMENT_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)

CORS_ALLOWED_METHODS: tuple[str, ...] = (
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
)

CORS_ALLOWED_HEADERS: tuple[str, ...] = (
    "Accept",
    "Authorization",
    "Cache-Control",
    "Content-Type",
    "If-Match",
    "If-None-Match",
    "Last-Event-ID",
    CLIENT_REQUEST_ID_HEADER,
    REQUEST_ID_HEADER,
)

CORS_EXPOSED_HEADERS: tuple[str, ...] = (
    REQUEST_ID_HEADER,
    API_VERSION_HEADER,
    CONFIG_REVISION_HEADER,
    "X-Chat-Stream-ID",
    "X-Chat-Schema-Version",
    "X-Hierarchy-Schema-Version",
    "X-Model-Registry-Revision",
    "X-Model-Schema-Version",
    "X-Tool-Registry-Revision",
    "X-Tool-Schema-Version",
    "X-UI-API-Schema-Version",
    "X-UI-Schema-Version",
)

REQUEST_ID_ALLOWED_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.",
)

MAX_REQUEST_ID_LENGTH = 128


# ============================================================
# Laufzeitkonfiguration
# ============================================================


class ApplicationEnvironment(StrEnum):
    DEVELOPMENT = "development"
    INTRANET = "intranet"
    INTERNET = "internet"


@dataclass(frozen=True, slots=True)
class RuntimeApplicationConfig:
    """
    Früh verfügbare Laufzeitkonfiguration der Anwendung.

    Enthält ausschließlich Bootstrap-, Infrastruktur- und
    Sicherheitswerte. Fachliche Einstellungen werden aus dem
    ConfigService gelesen.
    """

    environment: ApplicationEnvironment
    app_name: str
    app_version: str
    api_prefix: str
    api_version: str
    cors_origins: tuple[str, ...]
    docs_enabled: bool
    development_auth_fallback_enabled: bool
    hsts_enabled: bool


def get_setting(
    name: str,
    default: object = None,
) -> object:
    """
    Liest eine Bootstrap-Einstellung defensiv.

    Fachliche Einstellungen dürfen nicht über diese Funktion
    aufgelöst werden.
    """

    return getattr(
        settings,
        name,
        default,
    )


def setting_as_string(
    name: str,
    default: str,
) -> str:
    value = get_setting(
        name,
        default,
    )

    if value is None:
        return default

    if isinstance(
        value,
        StrEnum,
    ):
        normalized = value.value.strip()
    else:
        normalized = str(
            value,
        ).strip()

    return normalized or default


def setting_as_bool(
    name: str,
    default: bool,
) -> bool:
    value = get_setting(
        name,
        default,
    )

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return value != 0

    if isinstance(
        value,
        str,
    ):
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


def coerce_non_negative_int(
    value: object,
    *,
    default: int = 0,
) -> int:
    """
    Konvertiert bekannte Werttypen in eine nicht negative Ganzzahl.
    """

    if isinstance(
        value,
        bool,
    ):
        return int(
            value,
        )

    if isinstance(
        value,
        int,
    ):
        return max(
            value,
            0,
        )

    if isinstance(
        value,
        str,
    ):
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


def normalize_api_prefix(
    value: object,
) -> str:
    if isinstance(
        value,
        StrEnum,
    ):
        raw_prefix = value.value.strip()
    else:
        raw_prefix = str(
            value or DEFAULT_API_PREFIX,
        ).strip()

    if not raw_prefix:
        return DEFAULT_API_PREFIX

    prefix = raw_prefix if raw_prefix.startswith("/") else f"/{raw_prefix}"

    prefix = prefix.rstrip("/")

    return prefix or DEFAULT_API_PREFIX


def normalize_environment_value(
    value: object,
) -> str:
    """
    Normalisiert Umgebungswerte aus Strings und Enum-Instanzen.
    """

    if isinstance(
        value,
        ApplicationEnvironment,
    ):
        return value.value

    if isinstance(
        value,
        StrEnum,
    ):
        raw_value = value.value

    else:
        enum_value = getattr(
            value,
            "value",
            None,
        )

        if isinstance(
            enum_value,
            str,
        ):
            raw_value = enum_value
        else:
            raw_value = str(
                value,
            )

    normalized = raw_value.strip().lower()

    legacy_prefixes = (
        "applicationenvironment.",
        "appenvironment.",
    )

    for prefix in legacy_prefixes:
        if not normalized.startswith(
            prefix,
        ):
            continue

        legacy_value = normalized.removeprefix(
            prefix,
        )

        _log_warning(
            "Legacy environment representation detected",
            runtime_event="legacy-environment-normalized",
            configured_environment=normalized,
            normalized_environment=legacy_value,
        )

        return legacy_value

    return normalized


def resolve_environment() -> ApplicationEnvironment:
    raw_environment = get_setting(
        "environment",
        get_setting(
            "app_environment",
            get_setting(
                "app_env",
                ApplicationEnvironment.DEVELOPMENT.value,
            ),
        ),
    )

    normalized = normalize_environment_value(
        raw_environment,
    )

    try:
        return ApplicationEnvironment(
            normalized,
        )

    except ValueError as exc:
        allowed_values = ", ".join(
            environment.value for environment in ApplicationEnvironment
        )

        raise RuntimeError(
            "Ungültige Anwendungsumgebung. "
            f"Erlaubt sind: {allowed_values}. "
            f"Konfiguriert wurde: {normalized!r}.",
        ) from exc


def normalize_origins(
    value: object,
) -> tuple[str, ...]:
    """
    Normalisiert CORS-Origins.

    Unterstützt:

    - kommaseparierte Zeichenketten,
    - Sequenzen,
    - Mengen.
    """

    raw_values: list[object]

    if value is None:
        raw_values = []

    elif isinstance(
        value,
        str,
    ):
        raw_values = list(
            value.split(","),
        )

    elif isinstance(
        value,
        Mapping,
    ):
        raw_values = []

    elif isinstance(
        value,
        Sequence,
    ):
        raw_values = list(
            cast(
                Sequence[object],
                value,
            ),
        )

    elif isinstance(
        value,
        set | frozenset,
    ):
        raw_values = list(
            cast(
                set[object] | frozenset[object],
                value,
            ),
        )

    else:
        raw_values = []

    origins: list[str] = []
    seen: set[str] = set()

    for raw_origin in raw_values:
        if raw_origin is None:
            continue

        origin = (
            str(
                raw_origin,
            )
            .strip()
            .rstrip("/")
        )

        if not origin:
            continue

        if origin == "*":
            raise RuntimeError(
                "Der CORS-Ursprung '*' ist mit allow_credentials=True nicht zulässig.",
            )

        if origin in seen:
            continue

        seen.add(
            origin,
        )

        origins.append(
            origin,
        )

    return tuple(
        origins,
    )


def resolve_cors_origins(
    environment: ApplicationEnvironment,
) -> tuple[str, ...]:
    configured_origins = normalize_origins(
        get_setting(
            "cors_origins",
            get_setting(
                "allowed_origins",
                None,
            ),
        ),
    )

    if configured_origins:
        return configured_origins

    if environment is ApplicationEnvironment.DEVELOPMENT:
        return DEVELOPMENT_CORS_ORIGINS

    return ()


def build_runtime_config() -> RuntimeApplicationConfig:
    environment = resolve_environment()

    docs_enabled_default = environment is not ApplicationEnvironment.INTERNET

    docs_enabled = setting_as_bool(
        "docs_enabled",
        docs_enabled_default,
    )

    development_auth_fallback_enabled = (
        environment is ApplicationEnvironment.DEVELOPMENT
        and setting_as_bool(
            "development_auth_fallback_enabled",
            True,
        )
    )

    hsts_enabled = environment is ApplicationEnvironment.INTERNET or setting_as_bool(
        "hsts_enabled",
        False,
    )

    return RuntimeApplicationConfig(
        environment=environment,
        app_name=setting_as_string(
            "app_name",
            "Kernschmied",
        ),
        app_version=setting_as_string(
            "app_version",
            "0.1.0",
        ),
        api_prefix=normalize_api_prefix(
            get_setting(
                "api_prefix",
                DEFAULT_API_PREFIX,
            ),
        ),
        api_version=setting_as_string(
            "api_version",
            DEFAULT_API_VERSION,
        ),
        cors_origins=resolve_cors_origins(
            environment,
        ),
        docs_enabled=docs_enabled,
        development_auth_fallback_enabled=(development_auth_fallback_enabled),
        hsts_enabled=hsts_enabled,
    )


# ============================================================
# Request-Kontext
# ============================================================


def is_valid_request_id(
    value: str,
) -> bool:
    return 1 <= len(value) <= MAX_REQUEST_ID_LENGTH and all(
        character in REQUEST_ID_ALLOWED_CHARACTERS for character in value
    )


def normalize_request_id(
    value: object,
) -> str | None:
    if not isinstance(
        value,
        str,
    ):
        return None

    normalized = value.strip()

    if not normalized:
        return None

    if not is_valid_request_id(
        normalized,
    ):
        return None

    return normalized


def get_request_id(
    request: Request,
) -> str:
    """
    Liefert die serverseitige Request-ID.

    Eine bereits durch die Middleware gesetzte ID wird bevorzugt.
    """

    state_request_id = normalize_request_id(
        getattr(
            request.state,
            "request_id",
            None,
        ),
    )

    if state_request_id is not None:
        return state_request_id

    generated_request_id = str(
        uuid.uuid4(),
    )

    request.state.request_id = generated_request_id

    return generated_request_id


def get_client_request_id(
    request: Request,
) -> str | None:
    """
    Liefert die optionale Korrelations-ID des Frontends.

    Die Client-ID bleibt getrennt von der serverseitigen Request-ID.
    """

    state_client_request_id = normalize_request_id(
        getattr(
            request.state,
            "client_request_id",
            None,
        ),
    )

    if state_client_request_id is not None:
        return state_client_request_id

    header_client_request_id = normalize_request_id(
        request.headers.get(
            CLIENT_REQUEST_ID_HEADER,
        ),
    )

    if header_client_request_id is not None:
        request.state.client_request_id = header_client_request_id

    return header_client_request_id


def get_runtime_config(
    app: FastAPI,
) -> RuntimeApplicationConfig:
    runtime_config = getattr(
        app.state,
        "runtime_config",
        None,
    )

    if isinstance(
        runtime_config,
        RuntimeApplicationConfig,
    ):
        return runtime_config

    runtime_config = build_runtime_config()

    app.state.runtime_config = runtime_config

    return runtime_config


# ============================================================
# Fehlerantworten
# ============================================================


def structured_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: object = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    request_id = get_request_id(
        request,
    )

    response_headers: dict[str, str] = {
        REQUEST_ID_HEADER: request_id,
        "Cache-Control": "no-store",
    }

    if headers is not None:
        response_headers.update(
            dict(
                headers,
            ),
        )

    # Add CORS headers for error responses when the request Origin is allowed.
    try:
        origin = request.headers.get("origin")
        if origin:
            runtime_cfg = get_runtime_config(request.app)
            # Normalize allowed origins into a set for quick membership test
            allowed = set(runtime_cfg.cors_origins or ())
            # include development defaults if present in runtime config logic
            # If origin is explicitly allowed, mirror it back as per CORSMiddleware
            if origin in allowed:
                response_headers["Access-Control-Allow-Origin"] = origin
                response_headers["Access-Control-Allow-Credentials"] = "true"
                response_headers["Access-Control-Expose-Headers"] = ", ".join(
                    CORS_EXPOSED_HEADERS
                )
                response_headers["Vary"] = "Origin"
    except Exception:
        # Best-effort: do not let CORS header logic break error handling
        pass

    content: dict[str, object] = {
        "code": code,
        "message": message,
        "details": (details if details is not None else {}),
        "request_id": request_id,
    }

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            content,
        ),
        headers=response_headers,
    )


def validation_error_details(
    exc: RequestValidationError,
) -> dict[str, object]:
    """
    Entfernt Requestwerte und interne Kontexte aus
    Validierungsfehlern.
    """

    raw_errors = cast(
        list[dict[str, object]],
        exc.errors(),
    )

    sanitized_errors: list[dict[str, object]] = []

    for raw_error in raw_errors:
        sanitized_error = {
            key: value
            for key, value in raw_error.items()
            if key
            not in {
                "input",
                "url",
                "ctx",
            }
        }

        sanitized_errors.append(
            sanitized_error,
        )

    return {
        "errors": sanitized_errors,
    }


def parse_http_exception_detail(
    detail: object,
) -> tuple[
    str,
    str,
    object,
    str | None,
]:
    if not isinstance(
        detail,
        Mapping,
    ):
        return (
            "HTTP_ERROR",
            str(
                detail,
            ),
            {},
            None,
        )

    typed_detail = cast(
        Mapping[str, object],
        detail,
    )

    raw_code = typed_detail.get(
        "code",
        "HTTP_ERROR",
    )

    raw_message = typed_detail.get(
        "message",
        "Die Anfrage konnte nicht verarbeitet werden.",
    )

    raw_details = typed_detail.get(
        "details",
        {},
    )

    request_id = normalize_request_id(
        typed_detail.get(
            "request_id",
        ),
    )

    return (
        str(
            raw_code,
        ),
        str(
            raw_message,
        ),
        raw_details,
        request_id,
    )


# ============================================================
# Lifecycle
# ============================================================


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None, None]:
    runtime_config = get_runtime_config(
        app,
    )

    app.state.bootstrap_complete = False
    app.state.bootstrap_completed = False
    app.state.bootstrap_error = None
    app.state.bootstrap_result = None
    app.state.started_at_monotonic = None
    app.state.environment = runtime_config.environment.value

    _log_info(
        "Application lifecycle startup started",
        runtime_event="lifecycle-startup-started",
        environment=runtime_config.environment.value,
        application_name=runtime_config.app_name,
        application_version=runtime_config.app_version,
        api_prefix=runtime_config.api_prefix,
    )

    try:
        bootstrap_result = await bootstrap_application(
            app,
        )

        app.state.bootstrap_result = bootstrap_result

        app.state.bootstrap_complete = True
        app.state.bootstrap_completed = True

        app.state.started_at_monotonic = time.monotonic()

        _log_info(
            "Application lifecycle startup completed",
            runtime_event="lifecycle-startup-completed",
            environment=runtime_config.environment.value,
            bootstrap_complete=True,
        )

        yield

    except Exception as exc:
        app.state.bootstrap_complete = False
        app.state.bootstrap_completed = False
        app.state.bootstrap_error = str(
            exc,
        )

        _log_exception(
            "Application lifecycle failed",
            runtime_event="lifecycle-failed",
            environment=runtime_config.environment.value,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

        raise

    finally:
        app.state.bootstrap_complete = False
        app.state.bootstrap_completed = False

        _log_info(
            "Application lifecycle shutdown started",
            runtime_event="lifecycle-shutdown-started",
            environment=runtime_config.environment.value,
        )

        try:
            await shutdown_application(
                app,
            )

        except Exception as exc:
            _log_exception(
                "Application shutdown failed",
                runtime_event="lifecycle-shutdown-failed",
                environment=runtime_config.environment.value,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

        else:
            _log_info(
                "Application lifecycle shutdown completed",
                runtime_event="lifecycle-shutdown-completed",
                environment=runtime_config.environment.value,
            )


# ============================================================
# Exception-Handler
# ============================================================


def register_exception_handlers(
    application: FastAPI,
) -> None:
    @application.exception_handler(
        ApplicationError,
    )
    async def application_error_handler(
        request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        exception_request_id = normalize_request_id(
            getattr(
                exc,
                "request_id",
                None,
            ),
        )

        if exception_request_id is not None:
            request.state.request_id = exception_request_id

        status_code_value = getattr(
            exc,
            "status_code",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        status_code_int = (
            status_code_value
            if isinstance(
                status_code_value,
                int,
            )
            else status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        code_value = getattr(
            exc,
            "code",
            "APPLICATION_ERROR",
        )

        details_value = getattr(
            exc,
            "details",
            {},
        )

        _log_warning(
            "Application error handled",
            runtime_event="application-error-handled",
            request_id=get_request_id(
                request,
            ),
            client_request_id=get_client_request_id(
                request,
            ),
            path=request.url.path,
            method=request.method,
            status_code=status_code_int,
            error_code=str(
                code_value,
            ),
            error_type=type(exc).__name__,
        )

        return structured_error_response(
            request=request,
            status_code=status_code_int,
            code=str(
                code_value,
            ),
            message=str(
                exc,
            ),
            details=details_value,
        )

    @application.exception_handler(
        RequestValidationError,
    )
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = validation_error_details(
            exc,
        )

        errors = details.get(
            "errors",
            [],
        )

        error_count = (
            len(errors)  # type: ignore
            if isinstance(
                errors,
                list,
            )
            else 0
        )

        _log_warning(
            "Request validation failed",
            runtime_event="request-validation-failed",
            request_id=get_request_id(
                request,
            ),
            client_request_id=get_client_request_id(
                request,
            ),
            path=request.url.path,
            method=request.method,
            validation_error_count=error_count,
        )

        return structured_error_response(
            request=request,
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            code="REQUEST_VALIDATION_FAILED",
            message=("Die Anfrage enthält ungültige Daten."),
            details=details,
        )

    @application.exception_handler(
        HTTPException,
    )
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        (
            code,
            message,
            details,
            exception_request_id,
        ) = parse_http_exception_detail(
            exc.detail,
        )

        if exception_request_id is not None:
            request.state.request_id = exception_request_id

        _log_warning(
            "HTTP exception handled",
            runtime_event="http-exception-handled",
            request_id=get_request_id(
                request,
            ),
            client_request_id=get_client_request_id(
                request,
            ),
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            error_code=code,
        )

        return structured_error_response(
            request=request,
            status_code=exc.status_code,
            code=code,
            message=message,
            details=details,
            headers=exc.headers,
        )

    @application.exception_handler(
        Exception,
    )
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        request_id = get_request_id(
            request,
        )

        _log_exception(
            "Unhandled application exception",
            runtime_event="unhandled-exception",
            request_id=request_id,
            client_request_id=get_client_request_id(
                request,
            ),
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

        # Include traceback in details only when explicitly enabled for development.
        include_traceback = False
        try:
            runtime_cfg = get_runtime_config(request.app)
            is_dev = runtime_cfg.environment == ApplicationEnvironment.DEVELOPMENT
            # Allow an explicit bootstrap setting to enable tracebacks in dev.
            include_traceback = is_dev and setting_as_bool(
                "include_traceback_in_error_responses", False
            )
        except Exception:
            include_traceback = False

        details: dict[str, object] | None = None
        if include_traceback:
            import traceback as _tb

            details = {"traceback": _tb.format_exc()}

        return structured_error_response(
            request=request,
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            code="INTERNAL_SERVER_ERROR",
            message=(
                "Bei der Verarbeitung der Anfrage ist ein interner Fehler aufgetreten."
            ),
            details=details,
        )


# ============================================================
# Config-Revision
# ============================================================


async def resolve_config_revision(
    app: FastAPI,
) -> int:
    config_service = getattr(
        app.state,
        "config_service",
        None,
    )

    if config_service is None:
        return 0

    getter_value = getattr(
        config_service,
        "get_revision",
        None,
    )

    if callable(
        getter_value,
    ):
        try:
            raw_result: object = getter_value()

            if inspect.isawaitable(
                raw_result,
            ):
                resolved_result: object = await cast(
                    Awaitable[object],
                    raw_result,
                )
            else:
                resolved_result = raw_result

            return coerce_non_negative_int(
                resolved_result,
            )

        except Exception as exc:
            _log_exception(
                "Config revision could not be resolved",
                runtime_event="config-revision-resolution-failed",
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

            return 0

    raw_revision = getattr(
        config_service,
        "revision",
        0,
    )

    return coerce_non_negative_int(
        raw_revision,
    )


# ============================================================
# Response- und Sicherheitsheader
# ============================================================


def add_security_headers(
    response: Response,
    *,
    runtime_config: RuntimeApplicationConfig,
    request_id: str,
) -> None:
    response.headers[REQUEST_ID_HEADER] = request_id

    response.headers[API_VERSION_HEADER] = runtime_config.api_version

    response.headers["X-Content-Type-Options"] = "nosniff"

    response.headers["X-Frame-Options"] = "DENY"

    response.headers["Referrer-Policy"] = "no-referrer"

    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    if runtime_config.hsts_enabled:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )


# ============================================================
# Middleware
# ============================================================


def register_authentication_middleware(
    application: FastAPI,
    *,
    runtime_config: RuntimeApplicationConfig,
) -> None:
    """
    Registriert die Authentifizierung.

    Diese Middleware wird vor dem Request-Kontext registriert.
    Da Starlette die zuletzt registrierte Middleware außen
    ausführt, wird der Request-Kontext danach außerhalb der
    Authentifizierung liegen.
    """

    application.add_middleware(
        AuthenticationContextMiddleware,
        development_fallback_enabled=(runtime_config.development_auth_fallback_enabled),
    )

    _log_info(
        "Authentication middleware registered",
        runtime_event="authentication-middleware-registered",
        environment=runtime_config.environment.value,
        development_fallback_enabled=(runtime_config.development_auth_fallback_enabled),
    )


def register_http_middleware(
    application: FastAPI,
) -> None:
    """
    Registriert Request-ID, Laufzeitmessung und Sicherheitsheader.
    """

    @application.middleware("http")
    async def request_context_middleware(
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:
        incoming_server_request_id = normalize_request_id(
            request.headers.get(
                REQUEST_ID_HEADER,
            ),
        )

        client_request_id = normalize_request_id(
            request.headers.get(
                CLIENT_REQUEST_ID_HEADER,
            ),
        )

        request_id = incoming_server_request_id or str(
            uuid.uuid4(),
        )

        request.state.request_id = request_id
        request.state.client_request_id = client_request_id

        started_at = time.perf_counter()

        _log_debug(
            "HTTP request started",
            runtime_event="http-request-started",
            request_id=request_id,
            client_request_id=client_request_id,
            method=request.method,
            path=request.url.path,
            origin=request.headers.get(
                "origin",
            ),
        )

        try:
            response = await call_next(
                request,
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - started_at) * 1000

            _log_exception(
                "HTTP request middleware failed",
                runtime_event="http-request-middleware-failed",
                request_id=request_id,
                client_request_id=client_request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(
                    duration_ms,
                    2,
                ),
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

            raise

        duration_ms = (time.perf_counter() - started_at) * 1000

        runtime_config = get_runtime_config(
            request.app,
        )

        add_security_headers(
            response,
            runtime_config=runtime_config,
            request_id=request_id,
        )

        _log_info(
            "HTTP request completed",
            runtime_event="http-request-completed",
            request_id=request_id,
            client_request_id=client_request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(
                duration_ms,
                2,
            ),
            origin=request.headers.get(
                "origin",
            ),
        )

        return response


def register_cors_middleware(
    application: FastAPI,
    *,
    runtime_config: RuntimeApplicationConfig,
) -> None:
    """
    Registriert CORS als äußerste Middleware.

    Dadurch werden gültige OPTIONS-Preflight-Anfragen bereits
    durch CORSMiddleware beantwortet und erreichen weder
    Authentifizierung noch API-Routen.
    """

    if not runtime_config.cors_origins:
        _log_warning(
            "No CORS origins configured",
            runtime_event="cors-without-origins",
            environment=runtime_config.environment.value,
        )

    # Ensure local development origins are permitted in development scenarios
    allowed_origins_set = set(runtime_config.cors_origins)
    for dev_origin in DEVELOPMENT_CORS_ORIGINS:
        allowed_origins_set.add(dev_origin)

    allowed_origins = list(allowed_origins_set)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=list(
            CORS_ALLOWED_METHODS,
        ),
        allow_headers=list(
            CORS_ALLOWED_HEADERS,
        ),
        expose_headers=list(
            CORS_EXPOSED_HEADERS,
        ),
        max_age=600,
    )

    _log_info(
        "CORS middleware registered",
        runtime_event="cors-middleware-registered",
        environment=runtime_config.environment.value,
        allowed_origins=allowed_origins,
        allowed_methods=list(
            CORS_ALLOWED_METHODS,
        ),
        allowed_headers=list(
            CORS_ALLOWED_HEADERS,
        ),
        exposed_headers=list(
            CORS_EXPOSED_HEADERS,
        ),
        allow_credentials=True,
        max_age=600,
    )


# ============================================================
# Routen
# ============================================================


def register_routes(
    application: FastAPI,
    *,
    runtime_config: RuntimeApplicationConfig,
) -> None:
    application.include_router(
        api_router,
        prefix=runtime_config.api_prefix,
    )

    @application.get(
        "/",
        tags=["System"],
        summary="Anwendungsstatus",
    )
    async def root(
        request: Request,
    ) -> dict[str, object]:
        config_revision = await resolve_config_revision(
            request.app,
        )

        return {
            "name": runtime_config.app_name,
            "status": "running",
            "environment": (runtime_config.environment.value),
            "application_version": (runtime_config.app_version),
            "api_version": (runtime_config.api_version),
            "api_prefix": (runtime_config.api_prefix),
            "config_revision": (config_revision),
            "request_id": get_request_id(
                request,
            ),
        }

    @application.get(
        "/debug/identity",
        include_in_schema=False,
    )
    async def debug_identity(
        request: Request,
    ) -> dict[str, object]:
        user = getattr(request.state, "user", None)
        principal = getattr(request.state, "principal", None)

        return {
            "environment": runtime_config.environment.value,
            "development_auth_fallback_enabled": (
                runtime_config.development_auth_fallback_enabled
            ),
            "user_type": type(user).__name__ if user is not None else None,
            "user_id": (
                getattr(user, "id", None)
                or getattr(user, "user_id", None)
                or getattr(user, "subject", None)
            ),
            "user": repr(user),
            "principal_type": (
                type(principal).__name__ if principal is not None else None
            ),
        }

    @application.get(
        "/health/live",
        tags=["System"],
        summary="Liveness-Prüfung",
        include_in_schema=False,
    )
    async def health_live(
        request: Request,
    ) -> dict[str, str]:
        return {
            "status": "alive",
            "request_id": get_request_id(
                request,
            ),
        }

    @application.get(
        "/health/ready",
        tags=["System"],
        summary="Readiness-Prüfung",
        include_in_schema=False,
    )
    async def health_ready(
        request: Request,
    ) -> JSONResponse:
        bootstrap_complete = bool(
            getattr(
                request.app.state,
                "bootstrap_complete",
                False,
            ),
        )

        bootstrap_completed = bool(
            getattr(
                request.app.state,
                "bootstrap_completed",
                False,
            ),
        )

        ready = bootstrap_complete and bootstrap_completed

        request_id = get_request_id(
            request,
        )

        if not ready:
            bootstrap_error = getattr(
                request.app.state,
                "bootstrap_error",
                None,
            )

            _log_warning(
                "Readiness check failed",
                runtime_event="readiness-check-failed",
                request_id=request_id,
                bootstrap_complete=bootstrap_complete,
                bootstrap_completed=bootstrap_completed,
                has_bootstrap_error=(bootstrap_error is not None),
            )

            return JSONResponse(
                status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
                content={
                    "status": "not_ready",
                    "request_id": request_id,
                },
                headers={
                    REQUEST_ID_HEADER: request_id,
                    "Cache-Control": "no-store",
                },
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "request_id": request_id,
            },
            headers={
                REQUEST_ID_HEADER: request_id,
                "Cache-Control": "no-store",
            },
        )

    _log_info(
        "Application routes registered",
        runtime_event="routes-registered",
        api_prefix=runtime_config.api_prefix,
    )


# ============================================================
# Anwendungs-Factory
# ============================================================


def create_application() -> FastAPI:
    runtime_config = build_runtime_config()

    docs_url = "/docs" if runtime_config.docs_enabled else None

    redoc_url = "/redoc" if runtime_config.docs_enabled else None

    openapi_url = "/openapi.json" if runtime_config.docs_enabled else None

    application = FastAPI(
        title=runtime_config.app_name,
        version=runtime_config.app_version,
        description=(
            "Modulare, schema-gesteuerte "
            "Chat-Anwendung mit versionierten "
            "API-Verträgen."
        ),
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    application.state.runtime_config = runtime_config

    register_exception_handlers(
        application,
    )

    # --------------------------------------------------------
    # Middleware-Reihenfolge
    # --------------------------------------------------------
    #
    # Starlette führt zuletzt registrierte Middleware außen aus.
    #
    # Ausführungsreihenfolge:
    #
    # 1. CORSMiddleware
    # 2. Request-Kontext / Request-ID
    # 3. AuthenticationContextMiddleware
    # 4. Router / Endpunkt
    #
    # Dadurch:
    #
    # - beantwortet CORS gültige OPTIONS-Preflights,
    # - erhalten Auth-Fehler Request-ID- und Sicherheitsheader,
    # - werden API-Endpunkte weiterhin authentifiziert.
    # --------------------------------------------------------

    # Ensure CORS is registered as the outermost middleware so that
    # preflight and CORS headers are handled before other middleware.
    register_cors_middleware(
        application,
        runtime_config=runtime_config,
    )

    register_authentication_middleware(
        application,
        runtime_config=runtime_config,
    )

    register_http_middleware(
        application,
    )

    register_routes(
        application,
        runtime_config=runtime_config,
    )

    _log_info(
        "FastAPI application created",
        runtime_event="application-created",
        environment=runtime_config.environment.value,
        application_name=runtime_config.app_name,
        application_version=runtime_config.app_version,
        api_prefix=runtime_config.api_prefix,
        api_version=runtime_config.api_version,
        docs_enabled=runtime_config.docs_enabled,
        cors_origins=list(
            runtime_config.cors_origins,
        ),
        development_auth_fallback_enabled=(
            runtime_config.development_auth_fallback_enabled
        ),
        hsts_enabled=runtime_config.hsts_enabled,
    )

    return application


# ============================================================
# Strukturierte Logging-Hilfsfunktionen
# ============================================================


def _log_context(
    **values: object,
) -> dict[str, object]:
    return {
        "source": SOURCE_FILE,
        "area": LOG_AREA,
        **values,
    }


def _log_debug(
    message: str,
    **context: object,
) -> None:
    logger.debug(
        message,
        extra=_log_context(
            **context,
        ),
    )


def _log_info(
    message: str,
    **context: object,
) -> None:
    logger.info(
        message,
        extra=_log_context(
            **context,
        ),
    )


def _log_warning(
    message: str,
    **context: object,
) -> None:
    logger.warning(
        message,
        extra=_log_context(
            **context,
        ),
    )


def _log_exception(
    message: str,
    **context: object,
) -> None:
    logger.exception(
        message,
        extra=_log_context(
            **context,
        ),
    )


# ============================================================
# ASGI-Anwendung
# ============================================================

app = create_application()
