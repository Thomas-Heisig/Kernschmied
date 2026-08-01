from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter()

SCHEMA_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
WIKI_ROOT = PROJECT_ROOT / "wiki"
MAX_DOCUMENT_SIZE_BYTES = 2_000_000


@dataclass(frozen=True, slots=True)
class DocumentationPageDefinition:
    id: str
    title: str
    section_id: str
    section_title: str
    relative_path: str
    description: str = ""
    order: int = 0


def _scan_wiki_pages() -> list[DocumentationPageDefinition]:
    """Dynamically scan the `wiki/` folder and construct documentation page definitions.

    Rules:
    - Ignore files or directories starting with an underscore (`_`).
    - Use the first H1 in the file as the page title; fall back to filename stem.
    - Files directly under `wiki/` are grouped into the `project` section.
    - Section id/title are derived from the immediate parent folder name.
    - Page id is the relative path with slashes replaced by '-' and lowercased (without .md).
    """
    pages: list[DocumentationPageDefinition] = []

    if not WIKI_ROOT.exists():
        return pages

    for path in sorted(WIKI_ROOT.rglob("*.md")):
        try:
            rel = path.relative_to(WIKI_ROOT)
        except Exception:
            continue

        parts = rel.parts
        # ignore files or folders starting with '_'
        if any(p.startswith("_") for p in parts):
            continue

        # determine section (parent folder) and section title
        if len(parts) == 1:
            section_id = "project"
            section_title = "Projekt"
            relative_path = parts[0]
        else:
            section_id = parts[0].lower().replace(" ", "-")
            section_title = parts[0]
            relative_path = str(rel).replace("\\", "/")

        # read title from first H1 if possible
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue

        title = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                break

        if not title:
            title = path.stem

        page_id = (
            str(rel).replace("\\", "/").replace("/", "-").rsplit(".md", 1)[0].lower()
        )

        pages.append(
            DocumentationPageDefinition(
                id=page_id,
                title=title,
                section_id=section_id,
                section_title=section_title,
                relative_path=relative_path,
                description="",
                order=0,
            )
        )

    return pages


def _available_pages() -> tuple[DocumentationPageDefinition, ...]:
    return tuple(
        page
        for page in _scan_wiki_pages()
        if (WIKI_ROOT / page.relative_path).is_file()
    )


class DocumentationPageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str = ""


class DocumentationSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    pages: list[DocumentationPageSummary] = Field(
        default_factory=lambda: list[DocumentationPageSummary](),
    )


class DocumentationIndexResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    default_page_id: str | None = None
    sections: list[DocumentationSection] = Field(
        default_factory=lambda: list[DocumentationSection](),
    )


class DocumentationPageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    id: str
    title: str
    section_id: str
    section_title: str
    content: str


def _resolve_page_path(definition: DocumentationPageDefinition) -> Path:
    wiki_root = WIKI_ROOT.resolve()
    candidate = (wiki_root / definition.relative_path).resolve()

    if candidate != wiki_root and wiki_root not in candidate.parents:
        raise RuntimeError("Ungültiger Dokumentationspfad in der Registry.")

    return candidate


@router.get(
    "",
    response_model=DocumentationIndexResponse,
    summary="Dokumentationsübersicht laden",
)
async def list_documentation() -> DocumentationIndexResponse:
    pages = _available_pages()
    sections_by_id: dict[str, DocumentationSection] = {}

    for page in sorted(
        pages, key=lambda item: (item.section_title, item.order, item.title)
    ):
        section = sections_by_id.get(page.section_id)
        if section is None:
            section = DocumentationSection(id=page.section_id, title=page.section_title)
            sections_by_id[page.section_id] = section

        section.pages.append(
            DocumentationPageSummary(
                id=page.id, title=page.title, description=page.description
            ),
        )

    default_page_id = pages[0].id if pages else None

    return DocumentationIndexResponse(
        default_page_id=default_page_id, sections=list(sections_by_id.values())
    )


@router.get(
    "/pages/{page_id}",
    response_model=DocumentationPageResponse,
    summary="Dokumentationsseite laden",
)
async def get_documentation_page(page_id: str) -> DocumentationPageResponse:
    pages = {p.id: p for p in _available_pages()}
    definition = pages.get(page_id)

    if definition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENTATION_PAGE_NOT_FOUND",
                "message": "Die angeforderte Dokumentationsseite ist nicht registriert.",
                "details": {"page_id": page_id},
            },
        )

    page_path = _resolve_page_path(definition)

    if not page_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENTATION_FILE_NOT_FOUND",
                "message": "Die registrierte Dokumentationsdatei ist nicht vorhanden.",
                "details": {"page_id": page_id},
            },
        )

    file_size = page_path.stat().st_size
    if file_size > MAX_DOCUMENT_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "DOCUMENTATION_FILE_TOO_LARGE",
                "message": "Die Dokumentationsdatei überschreitet die zulässige Größe.",
                "details": {"page_id": page_id, "size": file_size},
            },
        )

    content = page_path.read_text(encoding="utf-8")

    return DocumentationPageResponse(
        id=definition.id,
        title=definition.title,
        section_id=definition.section_id,
        section_title=definition.section_title,
        content=content,
    )
