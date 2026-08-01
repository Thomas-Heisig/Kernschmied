# F:\Kernschmied\backend\app\api\v1\settings_catalog.py

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.settings_catalog import SettingsCatalogResponse
from app.services.settings_catalog import build_settings_catalog

router = APIRouter(prefix="/settings", tags=["Administration / Settings"])


@router.get(
    "/catalog",
    response_model=SettingsCatalogResponse,
    summary="Settings-Katalog laden",
    description=(
        "Liefert die versionierte Navigations- und Metadatenstruktur der "
        "Kernschmied-Einstellungen. Der Katalog enthält keine Secrets und "
        "ersetzt keine serverseitige Autorisierung."
    ),
)
async def get_settings_catalog(request: Request) -> SettingsCatalogResponse:
    request_id = getattr(request.state, "request_id", None)
    return build_settings_catalog().model_copy(update={"request_id": request_id})
