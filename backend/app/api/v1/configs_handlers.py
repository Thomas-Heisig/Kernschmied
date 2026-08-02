from __future__ import annotations

from fastapi import Request, Response, status

from .configs import (
    router,
    require_config_permission,
    validate_config_name,
    is_reserved_group,
    is_sensitive_key,
    validate_catalog_config_value,
    get_request_id,
    build_config_groups,
)

from .configs_service import (
    get_config_service,
    get_service_revision,
    read_config_entries,
    call_config_set,
)

from .configs_schema import (
    BulkConfigUpdateRequest,
    ConfigChangeItem,
    ConfigUpdateRequest,
    ConfigUpdateResponse,
)

from app.schemas.configuration import ConfigListResponse, ConfigEntryResponse


@router.get(
    "",
    response_model=ConfigListResponse,
    response_model_exclude_none=False,
    summary="Konfiguration auflisten",
    description=(
        "Liefert die sichtbare Fachkonfiguration und die aktuelle "
        "Revision. Sensible Werte werden nicht ausgegeben."
    ),
)
async def list_config(request: Request, response: Response) -> ConfigListResponse:
    require_config_permission(request, "config:read")

    service = get_config_service(request)

    revision = await get_service_revision(service)

    entries = await read_config_entries(service, request)

    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Config-Revision"] = str(revision)
    response.headers["X-Config-Schema-Version"] = "2.0"

    # Cast entries to the annotated ConfigEntries type for static checkers
    from .configs import ConfigEntries

    typed_entries: ConfigEntries = {  # type: ignore[arg-type]
        (g, k): v for (g, k), v in entries.items()
    }

    groups = build_config_groups(typed_entries)

    # Build an index of entries by their full_key for convenient client
    # consumption (keys look like 'group.key').
    entries_by_full_key: dict[str, ConfigEntryResponse] = {}
    for g in groups:
        for entry in g.entries:
            entries_by_full_key[entry.full_key] = entry

    return ConfigListResponse(
        revision=revision,
        groups=groups,
        entriesByFullKey=entries_by_full_key,
        request_id=get_request_id(request),
    )



@router.put(
    "",
    summary="Mehrere Konfigurationswerte ändern (Bulk)",
    description=(
        "Nimmt ein gruppiertes `values`-Objekt entgegen und speichert alle enthaltenen Werte in einer Transaktion."
    ),
)
async def bulk_update_config(payload: BulkConfigUpdateRequest, request: Request, response: Response) -> dict[str, object]:
    require_config_permission(request, "config:write")

    service = get_config_service(request)

    updates: dict[tuple[str, str], object] = {}

    changes_list: list[ConfigChangeItem] = payload.changes
    if changes_list:
            for change in changes_list:
                g = change.group
                k = change.key
                updates[(g.strip().lower(), k.strip().lower())] = change.value
    else:
        for raw_group, raw_group_value in payload.values.items():
            normalized_group = str(raw_group).strip().lower()
            for raw_key, raw_value in raw_group_value.items():
                updates[(normalized_group, str(raw_key).strip().lower())] = raw_value

    try:
        await service.set_many(updates, expected_revision=payload.expected_revision)
    except Exception as exc:
        # forward known service-level exceptions as structured HTTP errors
        from app.config.service import (
            ConfigValidationError,
            ConfigPersistenceError,
            ConfigServiceError,
        )

        from .configs import structured_http_error

        if isinstance(exc, ConfigValidationError):
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=exc.code,
                message=exc.message,
                details={},
            ) from exc

        if isinstance(exc, ConfigPersistenceError):
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="CONFIG_PERSISTENCE_ERROR",
                message=(exc.reason if hasattr(exc, "reason") else str(exc)),
                details={},
            ) from exc

        if isinstance(exc, ConfigServiceError):
            raise structured_http_error(
                request=request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="CONFIG_SERVICE_ERROR",
                message=str(exc),
                details={},
            ) from exc

        # Unknown exception: re-raise to surface as 500 with traceback
        raise

    revision = await get_service_revision(service)
    entries = await read_config_entries(service, request)

    grouped: dict[str, dict[str, object]] = {}
    for (group, key), value in entries.items():
        grouped.setdefault(group, {})[key] = value

    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Config-Revision"] = str(revision)
    response.headers["X-Config-Schema-Version"] = "2.0"

    return {"values": grouped, "revision": revision}



@router.put(
    "/{group}/{key}",
    response_model=ConfigUpdateResponse,
    summary="Konfigurationswert ändern",
    description=(
        "Ändert einen registrierten, runtime-editierbaren "
        "Konfigurationswert. Die Änderung wird anhand des "
        "Settings-Katalogs validiert, versioniert und protokolliert."
    ),
)
async def update_config(group: str, key: str, payload: ConfigUpdateRequest, request: Request, response: Response) -> ConfigUpdateResponse:
    require_config_permission(request, "config:write")

    normalized_group = validate_config_name(group, field_name="group", request=request)
    normalized_key = validate_config_name(key, field_name="key", request=request)

    if is_reserved_group(normalized_group):
        from .configs import structured_http_error

        raise structured_http_error(request=request, status_code=status.HTTP_403_FORBIDDEN, code="CONFIG_GROUP_NOT_RUNTIME_EDITABLE", message=("Diese Konfigurationsgruppe darf nicht zur Laufzeit bearbeitet werden."), details={"group": normalized_group, "key": normalized_key})

    if is_sensitive_key(normalized_group, normalized_key):
        from .configs import structured_http_error

        raise structured_http_error(request=request, status_code=status.HTTP_403_FORBIDDEN, code="SENSITIVE_CONFIG_NOT_ALLOWED", message=("Sensible Werte dürfen nicht über die Fachkonfiguration gespeichert werden."), details={"group": normalized_group, "key": normalized_key})

    descriptor, validated_value = validate_catalog_config_value(group=normalized_group, key=normalized_key, payload=payload, request=request)

    service = get_config_service(request)

    current_revision = await get_service_revision(service)

    if payload.expected_revision is not None and (payload.expected_revision != current_revision):
        from .configs import structured_http_error

        raise structured_http_error(request=request, status_code=status.HTTP_409_CONFLICT, code="CONFIG_REVISION_CONFLICT", message=("Die Konfiguration wurde zwischenzeitlich geändert. Bitte laden Sie die aktuellen Werte erneut."), details={"group": normalized_group, "key": normalized_key, "expected_revision": (payload.expected_revision), "current_revision": current_revision})

    await call_config_set(service=service, group=normalized_group, key=normalized_key, value=validated_value, payload=payload, request=request)

    new_revision = await get_service_revision(service, default=(current_revision + 1))
    if new_revision <= current_revision:
        new_revision = current_revision + 1

    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Config-Revision"] = str(new_revision)
    response.headers["X-Config-Schema-Version"] = "2.0"

    # log update
    from .configs import logger, get_actor_id

    logger.info(
        "Configuration value updated",
        extra={
            "group": normalized_group,
            "key": normalized_key,
            "field_id": descriptor.id,
            "control": descriptor.control.value,
            "revision": new_revision,
            "actor_id": get_actor_id(request),
            "request_id": get_request_id(request),
            "reason": payload.reason,
        },
    )

    return ConfigUpdateResponse(group=normalized_group, key=normalized_key, revision=new_revision, request_id=get_request_id(request))
