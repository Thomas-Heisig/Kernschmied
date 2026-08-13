from __future__ import annotations

import inspect
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("", summary="Audit log (compat)")
async def get_audit(request: Request) -> Any:
    """Compatibility audit endpoint used by frontend widgets.

    If an `audit_service` is attached to `app.state`, delegate to it.
    Otherwise return an empty items list to avoid 404s in the UI.
    """
    audit_service = getattr(request.app.state, "audit_service", None)

    if audit_service is None:
        return {"items": []}

    try:
        result = audit_service.list_entries()

        if inspect.isawaitable(result):
            result = await result

        if isinstance(result, list):
            return {"items": result}

        if isinstance(result, dict) and "items" in result:
            return result

        # Fall back to converting to list
        return {"items": list(result)}
    except Exception:
        return {"items": []}
