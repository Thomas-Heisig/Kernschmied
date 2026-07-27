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
from typing import TypeAlias, cast

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

from app.api.v1.router import api_router
from app.auth import AuthenticationContextMiddleware
from app.core.bootstrap import bootstrap_application
from app.core.exceptions import ApplicationError
from app.core.settings import settings


logger = logging.getLogger(__name__)


# ============================================================
# Konstanten
# ============================================================


DEFAULT_API_PREFIX = "/api/v1"
DEFAULT_API_VERSION = "1.0"

REQUEST_ID_HEADER = "X-Request-ID"
API_VERSION_HEADER = "X-API-Version"
CONFIG_REVISION_HEADER = "X-Config-Revision"

DEVELOPMENT_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)

REQUEST_ID_ALLOWED_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "-_.",
)

ShutdownCallback: TypeAlias = Callable[
    [],
    None | Awaitable[None],
]


# ============================================================
# Laufzeitkonfiguration
# ============================================================


class ApplicationEnvironment(StrEnum):
    DEVELOPMENT = "development"
    INTRANET = "intranet"
    INTERNET = "internet"


@dataclass(frozen=True, slots=True)
class RuntimeApplicationConfig:
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

    Diese Funktion ist nur für Infrastruktur-, Bootstrap- und
    Sicherheitswerte gedacht. Fachliche Konfiguration wird nicht aus
    `settings`, sondern aus dem ConfigService gelesen.
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

    if isinstance(value, StrEnum):
        normalized = value.value.strip()
    else:
        normalized = str(value).strip()

    return normalized or default


def setting_as_bool(
    name: str,
    default: bool,
) -> bool:
    value = get_setting(
        name,
        default,
    )

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


def coerce_non_negative_int(
    value: object,
    *,
    default: int = 0,
) -> int:
    """
    Konvertiert bekannte Werttypen in eine nicht negative Ganzzahl.

    Unbekannte Objekte werden bewusst nicht direkt an int() übergeben.
    """

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


def normalize_api_prefix(
    value: object,
) -> str:
    if isinstance(value, StrEnum):
        raw_prefix = value.value.strip()
    else:
        raw_prefix = str(
            value or DEFAULT_API_PREFIX,
        ).strip()

    if not raw_prefix:
        return DEFAULT_API_PREFIX

    prefix = (
        raw_prefix
        if raw_prefix.startswith("/")
        else f"/{raw_prefix}"
    )

    prefix = prefix.rstrip("/")

    if not prefix:
        return DEFAULT_API_PREFIX

    return prefix


def normalize_environment_value(
    value: object,
) -> str:
    """
    Normalisiert Umgebungswerte aus Strings und Enum-Instanzen.

    Dadurch werden sowohl

    - "development"
    - ApplicationEnvironment.DEVELOPMENT
    - ältere Darstellungen wie "AppEnvironment.DEVELOPMENT"

    sicher behandelt.
    """

    if isinstance(
        value,
        ApplicationEnvironment,
    ):
        return value.value

    if isinstance(value, StrEnum):
        raw_value = value.value
    else:
        enum_value = getattr(
            value,
            "value",
            None,
        )

        if isinstance(enum_value, str):
            raw_value = enum_value
        else:
            raw_value = str(value)

    normalized = raw_value.strip().lower()

    legacy_prefixes = (
        "applicationenvironment.",
        "appenvironment.",
    )

    for prefix in legacy_prefixes:
        if normalized.startswith(prefix):
            legacy_value = normalized.removeprefix(
                prefix,
            )

            logger.warning(
                "Legacy environment representation detected",
                extra={
                    "configured_environment": normalized,
                    "normalized_environment": legacy_value,
                },
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
            environment.value
            for environment in ApplicationEnvironment
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

    Unterstützt werden:

    - kommaseparierte Zeichenketten
    - Sequenzen aus Zeichenketten
    - Mengen aus Zeichenketten
    """

    raw_values: list[object]

    if value is None:
        raw_values = []

    elif isinstance(value, str):
        raw_values = list(
            value.split(","),
        )

    elif isinstance(value, Mapping):
        raw_values = []

    elif isinstance(value, Sequence):
        raw_values = list(
            cast(
                Sequence[object],
                value,
            ),
        )

    elif isinstance(
        value,
        (
            set,
            frozenset,
        ),
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

        origin = str(
            raw_origin,
        ).strip().rstrip("/")

        if not origin:
            continue

        if origin == "*":
            raise RuntimeError(
                "Der CORS-Ursprung '*' ist mit "
                "allow_credentials=True nicht zulässig.",
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

    docs_enabled_default = (
        environment
        is not ApplicationEnvironment.INTERNET
    )

    docs_enabled = setting_as_bool(
        "docs_enabled",
        docs_enabled_default,
    )

    development_auth_fallback_enabled = (
        environment
        is ApplicationEnvironment.DEVELOPMENT
        and setting_as_bool(
            "development_auth_fallback_enabled",
            True,
        )
    )

    hsts_enabled = (
        environment
        is ApplicationEnvironment.INTERNET
        or setting_as_bool(
            "hsts_enabled",
            False,
        )
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
        development_auth_fallback_enabled=(
            development_auth_fallback_enabled
        ),
        hsts_enabled=hsts_enabled,
    )


# ============================================================
# Request-Kontext
# ============================================================


def is_valid_request_id(
    value: str,
) -> bool:
    return (
        1 <= len(value) <= 128
        and all(
            character in REQUEST_ID_ALLOWED_CHARACTERS
            for character in value
        )
    )


def get_request_id(
    request: Request,
) -> str:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    if isinstance(request_id, str):
        normalized = request_id.strip()

        if (
            normalized
            and is_valid_request_id(
                normalized,
            )
        ):
            return normalized

    generated_request_id = str(
        uuid.uuid4(),
    )

    request.state.request_id = (
        generated_request_id
    )

    return generated_request_id


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

    app.state.runtime_config = (
        runtime_config
    )

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
            dict(headers),
        )

    content: dict[str, object] = {
        "code": code,
        "message": message,
        "details": (
            details
            if details is not None
            else {}
        ),
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
    Entfernt Eingabewerte und Kontexte aus Validierungsfehlern.

    Dadurch werden keine Passwörter, Tokens oder sonstigen sensitiven
    Request-Daten in Fehlerantworten zurückgegeben.
    """

    raw_errors = cast(
        list[dict[str, object]],
        exc.errors(),
    )

    sanitized_errors: list[
        dict[str, object]
    ] = []

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
            str(detail),
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

    raw_request_id = typed_detail.get(
        "request_id",
    )

    request_id = (
        str(raw_request_id).strip()
        if raw_request_id is not None
        else None
    )

    if request_id == "":
        request_id = None

    return (
        str(raw_code),
        str(raw_message),
        raw_details,
        request_id,
    )


# ============================================================
# Shutdown-Verwaltung
# ============================================================


def register_shutdown_callback(
    app: FastAPI,
    callback: ShutdownCallback,
) -> None:
    """
    Registriert eine geordnete Shutdown-Funktion.

    Bootstrap-Komponenten sollten diese Schnittstelle verwenden, statt
    von `main.py` über Attributnamen erkannt zu werden.
    """

    callbacks_value: object = getattr(
        app.state,
        "shutdown_callbacks",
        None,
    )

    if callbacks_value is None:
        callbacks: list[ShutdownCallback] = []
        app.state.shutdown_callbacks = callbacks

    elif isinstance(
        callbacks_value,
        list,
    ):
        callbacks = cast(
            list[ShutdownCallback],
            callbacks_value,
        )

    else:
        raise RuntimeError(
            "app.state.shutdown_callbacks besitzt "
            "einen ungültigen Typ.",
        )

    callbacks.append(
        callback,
    )

    owner = getattr(
        callback,
        "__self__",
        None,
    )

    if owner is None:
        return

    managed_ids_value: object = getattr(
        app.state,
        "shutdown_managed_object_ids",
        None,
    )

    if managed_ids_value is None:
        managed_ids: set[int] = set()
        app.state.shutdown_managed_object_ids = (
            managed_ids
        )

    elif isinstance(
        managed_ids_value,
        set,
    ):
        managed_ids = cast(
            set[int],
            managed_ids_value,
        )

    else:
        raise RuntimeError(
            "app.state.shutdown_managed_object_ids "
            "besitzt einen ungültigen Typ.",
        )

    managed_ids.add(
        id(owner),
    )

async def invoke_shutdown_callback(
    callback: ShutdownCallback,
    *,
    callback_name: str,
) -> None:
    try:
        result = callback()

        if inspect.isawaitable(
            result,
        ):
            await result

    except Exception:
        logger.exception(
            "Shutdown callback failed",
            extra={
                "callback": callback_name,
            },
        )


async def run_registered_shutdown_callbacks(
    app: FastAPI,
) -> None:
    callbacks_value = getattr(
        app.state,
        "shutdown_callbacks",
        None,
    )

    if not isinstance(
        callbacks_value,
        list,
    ):
        return

    callbacks = cast(
        list[ShutdownCallback],
        callbacks_value,
    )

    for callback in reversed(
        callbacks.copy(),
    ):
        callback_name = getattr(
            callback,
            "__qualname__",
            getattr(
                callback,
                "__name__",
                callback.__class__.__name__,
            ),
        )

        await invoke_shutdown_callback(
            callback,
            callback_name=str(
                callback_name,
            ),
        )

    callbacks.clear()


async def shutdown_legacy_state_services(
    app: FastAPI,
) -> None:
    """
    Übergangskompatibilität für Services ohne registrierten
    Shutdown-Callback.
    """

    state_attribute_names: tuple[str, ...] = (
        "chat_service",
        "model_service",
        "model_lifecycle",
        "tool_registry",
        "model_registry",
        "config_service",
        "database",
        "database_manager",
        "db_engine",
    )

    managed_ids_value: object = getattr(
        app.state,
        "shutdown_managed_object_ids",
        None,
    )

    if managed_ids_value is None:
        managed_object_ids: set[int] = set()

    elif isinstance(
        managed_ids_value,
        set,
    ):
        managed_object_ids = cast(
            set[int],
            managed_ids_value,
        )

    else:
        logger.warning(
            "Invalid shutdown_managed_object_ids state",
            extra={
                "actual_type": (
                    managed_ids_value
                    .__class__
                    .__name__
                ),
            },
        )

        managed_object_ids = set()

    closed_objects: set[int] = set()

    for attribute_name in state_attribute_names:
        service = getattr(
            app.state,
            attribute_name,
            None,
        )

        if service is None:
            continue

        object_id = id(
            service,
        )

        if object_id in managed_object_ids:
            continue

        if object_id in closed_objects:
            continue

        closed_objects.add(
            object_id,
        )

        for method_name in (
            "shutdown",
            "close",
            "dispose",
        ):
            method_value = getattr(
                service,
                method_name,
                None,
            )

            if not callable(
                method_value,
            ):
                continue

            callback = cast(
                ShutdownCallback,
                method_value,
            )

            await invoke_shutdown_callback(
                callback,
                callback_name=(
                    f"{attribute_name}."
                    f"{method_name}"
                ),
            )

            break

async def shutdown_application(
    app: FastAPI,
) -> None:
    await run_registered_shutdown_callbacks(
        app,
    )

    await shutdown_legacy_state_services(
        app,
    )

    managed_ids_value: object = getattr(
        app.state,
        "shutdown_managed_object_ids",
        None,
    )

    if isinstance(
        managed_ids_value,
        set,
    ):
        managed_ids_value.clear()


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

    app.state.shutdown_callbacks = []
    app.state.shutdown_managed_object_ids = set()
    app.state.bootstrap_completed = False
    app.state.bootstrap_result = None

    logger.info(
        "Application bootstrap started",
        extra={
            "environment": (
                runtime_config.environment.value
            ),
        },
    )

    try:
        bootstrap_result = await bootstrap_application(
            app,
        )

        app.state.bootstrap_result = (
            bootstrap_result
        )

        app.state.bootstrap_completed = True

        app.state.started_at_monotonic = (
            time.monotonic()
        )

        app.state.environment = (
            runtime_config.environment.value
        )

        logger.info(
            "Application bootstrap completed",
            extra={
                "environment": (
                    runtime_config.environment.value
                ),
            },
        )

        yield

    except Exception:
        logger.exception(
            "Application lifecycle failed",
            extra={
                "environment": (
                    runtime_config.environment.value
                ),
            },
        )
        raise

    finally:
        app.state.bootstrap_completed = False

        logger.info(
            "Application shutdown started",
        )

        await shutdown_application(
            app,
        )

        logger.info(
            "Application shutdown completed",
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
        exception_request_id = getattr(
            exc,
            "request_id",
            None,
        )

        if (
            isinstance(
                exception_request_id,
                str,
            )
            and is_valid_request_id(
                exception_request_id,
            )
        ):
            request.state.request_id = (
                exception_request_id
            )

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
        return structured_error_response(
            request=request,
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            code="REQUEST_VALIDATION_FAILED",
            message=(
                "Die Anfrage enthält ungültige Daten."
            ),
            details=validation_error_details(
                exc,
            ),
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

        if (
            exception_request_id is not None
            and is_valid_request_id(
                exception_request_id,
            )
        ):
            request.state.request_id = (
                exception_request_id
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

        logger.exception(
            "Unhandled application exception",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "exception_type": (
                    exc.__class__.__name__
                ),
            },
        )

        return structured_error_response(
            request=request,
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            code="INTERNAL_SERVER_ERROR",
            message=(
                "Bei der Verarbeitung der Anfrage "
                "ist ein interner Fehler aufgetreten."
            ),
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

        except Exception:
            logger.exception(
                "Config revision could not be resolved",
            )
            return 0

    raw_revision: object = getattr(
        config_service,
        "revision",
        0,
    )

    return coerce_non_negative_int(
        raw_revision,
    )


# ============================================================
# Middleware
# ============================================================


def add_security_headers(
    response: Response,
    *,
    runtime_config: RuntimeApplicationConfig,
    request_id: str,
) -> None:
    response.headers[
        REQUEST_ID_HEADER
    ] = request_id

    response.headers[
        API_VERSION_HEADER
    ] = runtime_config.api_version

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    response.headers[
        "Referrer-Policy"
    ] = "no-referrer"

    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), microphone=(), "
        "geolocation=()"
    )

    if runtime_config.hsts_enabled:
        response.headers[
            "Strict-Transport-Security"
        ] = (
            "max-age=31536000; "
            "includeSubDomains"
        )


def register_http_middleware(
    application: FastAPI,
) -> None:
    @application.middleware("http")
    async def request_context_middleware(
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:
        incoming_request_id = request.headers.get(
            REQUEST_ID_HEADER,
        )

        normalized_incoming_request_id = (
            incoming_request_id.strip()
            if incoming_request_id is not None
            else None
        )

        request_id = (
            normalized_incoming_request_id
            if (
                normalized_incoming_request_id is not None
                and is_valid_request_id(
                    normalized_incoming_request_id,
                )
            )
            else str(
                uuid.uuid4(),
            )
        )

        request.state.request_id = (
            request_id
        )

        started_at = time.perf_counter()

        response = await call_next(
            request,
        )

        duration_ms = (
            time.perf_counter() - started_at
        ) * 1000

        runtime_config = get_runtime_config(
            request.app,
        )

        add_security_headers(
            response,
            runtime_config=runtime_config,
            request_id=request_id,
        )

        logger.info(
            "HTTP request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": (
                    response.status_code
                ),
                "duration_ms": round(
                    duration_ms,
                    2,
                ),
            },
        )

        return response


def register_authentication_middleware(
    application: FastAPI,
    *,
    runtime_config: RuntimeApplicationConfig,
) -> None:
    application.add_middleware(
        AuthenticationContextMiddleware,
        development_fallback_enabled=(
            runtime_config
            .development_auth_fallback_enabled
        ),
    )


def register_cors_middleware(
    application: FastAPI,
    *,
    runtime_config: RuntimeApplicationConfig,
) -> None:
    if (
        runtime_config.environment
        in {
            ApplicationEnvironment.INTRANET,
            ApplicationEnvironment.INTERNET,
        }
        and not runtime_config.cors_origins
    ):
        logger.info(
            "Cross-origin requests are disabled",
            extra={
                "environment": (
                    runtime_config.environment.value
                ),
            },
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(
            runtime_config.cors_origins,
        ),
        allow_credentials=True,
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
        allow_headers=[
            "Accept",
            "Authorization",
            "Content-Type",
            "If-Match",
            "If-None-Match",
            "Last-Event-ID",
            REQUEST_ID_HEADER,
        ],
        expose_headers=[
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
        ],
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
            "environment": (
                runtime_config.environment.value
            ),
            "application_version": (
                runtime_config.app_version
            ),
            "api_version": (
                runtime_config.api_version
            ),
            "api_prefix": (
                runtime_config.api_prefix
            ),
            "config_revision": (
                config_revision
            ),
            "request_id": get_request_id(
                request,
            ),
        }

    @application.get(
        "/health/live",
        tags=["System"],
        summary="Liveness-Prüfung",
        include_in_schema=False,
    )
    async def health_live() -> dict[str, str]:
        return {
            "status": "alive",
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
        bootstrap_completed = bool(
            getattr(
                request.app.state,
                "bootstrap_completed",
                False,
            ),
        )

        request_id = get_request_id(
            request,
        )

        if not bootstrap_completed:
            return JSONResponse(
                status_code=(
                    status.HTTP_503_SERVICE_UNAVAILABLE
                ),
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


# ============================================================
# Anwendungs-Factory
# ============================================================


def create_application() -> FastAPI:
    runtime_config = build_runtime_config()

    docs_url = (
        "/docs"
        if runtime_config.docs_enabled
        else None
    )

    redoc_url = (
        "/redoc"
        if runtime_config.docs_enabled
        else None
    )

    openapi_url = (
        "/openapi.json"
        if runtime_config.docs_enabled
        else None
    )

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

    application.state.runtime_config = (
        runtime_config
    )

    register_exception_handlers(
        application,
    )

    register_http_middleware(
        application,
    )

    register_authentication_middleware(
        application,
        runtime_config=runtime_config,
    )

    # Starlette führt die zuletzt registrierte Middleware außen aus.
    # CORS bleibt deshalb außen, damit auch Antworten der
    # Authentifizierungs-Middleware CORS-Header erhalten.
    register_cors_middleware(
        application,
        runtime_config=runtime_config,
    )

    register_routes(
        application,
        runtime_config=runtime_config,
    )

    logger.info(
        "FastAPI application created",
        extra={
            "environment": (
                runtime_config.environment.value
            ),
            "api_prefix": (
                runtime_config.api_prefix
            ),
            "docs_enabled": (
                runtime_config.docs_enabled
            ),
            "cors_origins": list(
                runtime_config.cors_origins,
            ),
        },
    )

    return application


app = create_application()