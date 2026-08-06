from __future__ import annotations

# removed unused imports: Path, Literal
from fastapi import APIRouter, HTTPException, status

from app.contracts.documentation import (
    DocumentationNavigationResponse as DocNavContract,
)
from app.contracts.documentation import DocumentationPageResponse as DocPageContract
from app.services import documentation_service as doc_svc

router = APIRouter()


@router.get("", response_model=DocNavContract, summary="Dokumentationsübersicht laden")
async def list_documentation():
    try:
        nav = doc_svc.build_navigation()
    except FileNotFoundError as exc:
        expected = str(exc.args[0]) if exc.args else None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOCUMENTATION_MANIFEST_NOT_FOUND",
                "message": "Das Dokumentationsmanifest wurde nicht gefunden.",
                "details": {"expected_path": expected},
            },
        )
    except RuntimeError as e:
        # pass-through structured error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": (
                    "DOCUMENTATION_MANIFEST_EMPTY"
                    if str(e).startswith("DOCUMENTATION_MANIFEST_EMPTY")
                    else "DOCUMENTATION_MANIFEST_INVALID"
                ),
                "message": str(e),
                "details": {},
            },
        )

    # Map service navigation to API contract shape expected by clients
    return DocNavContract(
        documentation_version=nav.documentation_version,
        default_page_id=nav.default_page_id,
        sections=nav.sections,
    )


@router.get("/navigation", response_model=DocNavContract, summary="Navigation laden")
async def get_navigation():
    return await list_documentation()


@router.get(
    "/pages/{page_id}",
    response_model=DocPageContract,
    summary="Dokumentationsseite laden",
)
async def get_documentation_page(page_id: str):
    try:
        page = doc_svc.load_page(page_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENTATION_PAGE_NOT_FOUND",
                "message": "Die angeforderte Dokumentationsseite ist nicht registriert.",
                "details": {"page_id": page_id},
            },
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DOCUMENTATION_LOAD_FAILED",
                "message": str(e),
                "details": {"page_id": page_id},
            },
        )

    return page
