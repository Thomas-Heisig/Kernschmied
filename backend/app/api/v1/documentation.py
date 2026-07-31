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


DOCUMENTATION_PAGES: tuple[DocumentationPageDefinition, ...] = (
    DocumentationPageDefinition(
        id="user-manual-overview",
        title="Benutzerhandbuch",
        section_id="user-manual",
        section_title="Benutzerhandbuch",
        relative_path="User-Manual/Overview.md",
        description="Überblick über Bedienung und zentrale Funktionen.",
        order=10,
    ),
    DocumentationPageDefinition(
        id="user-manual-chat",
        title="Chat verwenden",
        section_id="user-manual",
        section_title="Benutzerhandbuch",
        relative_path="User-Manual/Chat.md",
        description="Nachrichten senden, Modelle wählen und Antworten verstehen.",
        order=20,
    ),
    DocumentationPageDefinition(
        id="user-manual-hierarchy",
        title="Hierarchie und Arbeitsbereiche",
        section_id="user-manual",
        section_title="Benutzerhandbuch",
        relative_path="User-Manual/Hierarchy.md",
        description="Arbeitsbereiche, Projekte und Chats organisieren.",
        order=30,
    ),
    DocumentationPageDefinition(
        id="user-manual-settings",
        title="Einstellungen",
        section_id="user-manual",
        section_title="Benutzerhandbuch",
        relative_path="User-Manual/Settings.md",
        description="System- und Benutzereinstellungen sicher verwalten.",
        order=40,
    ),
    DocumentationPageDefinition(
        id="user-manual-troubleshooting",
        title="Fehlerbehebung",
        section_id="user-manual",
        section_title="Benutzerhandbuch",
        relative_path="User-Manual/Troubleshooting.md",
        description="Häufige Probleme erkennen und beheben.",
        order=50,
    ),
    DocumentationPageDefinition(
        id="home",
        title="Projektübersicht",
        section_id="project",
        section_title="Projekt",
        relative_path="Home.md",
        description="Ziele, Aufbau und aktueller Stand von Kernschmied.",
        order=10,
    ),
    DocumentationPageDefinition(
        id="getting-started",
        title="Erste Schritte",
        section_id="project",
        section_title="Projekt",
        relative_path="Getting-Started.md",
        description="Installation und erster Start.",
        order=20,
    ),
    DocumentationPageDefinition(
        id="installation",
        title="Installation",
        section_id="project",
        section_title="Projekt",
        relative_path="Installation.md",
        description="Technische Installationsanleitung.",
        order=30,
    ),
    DocumentationPageDefinition(
        id="faq",
        title="FAQ",
        section_id="project",
        section_title="Projekt",
        relative_path="FAQ.md",
        description="Häufig gestellte Fragen.",
        order=40,
    ),
    DocumentationPageDefinition(
        id="architecture-overview",
        title="Architekturübersicht",
        section_id="architecture",
        section_title="Architektur",
        relative_path="Architecture/Overview.md",
        description="Gesamtarchitektur und Leitprinzipien.",
        order=10,
    ),
    DocumentationPageDefinition(
        id="dynamic-ui",
        title="Dynamische UI",
        section_id="concepts",
        section_title="Konzepte",
        relative_path="Concepts/Dynamic-UI.md",
        description="Schema-gesteuerte Benutzeroberfläche.",
        order=10,
    ),
    DocumentationPageDefinition(
        id="runtime-configuration",
        title="Runtime-Konfiguration",
        section_id="concepts",
        section_title="Konzepte",
        relative_path="Concepts/Runtime-Configuration.md",
        description="Versionierte Fachkonfiguration zur Laufzeit.",
        order=20,
    ),
    DocumentationPageDefinition(
        id="schema-versioning",
        title="Schema-Versionierung",
        section_id="concepts",
        section_title="Konzepte",
        relative_path="Concepts/Schema-Versioning.md",
        description="Stabile und versionierte Verträge.",
        order=30,
    ),
    DocumentationPageDefinition(
        id="backend-security",
        title="Backend-Sicherheit",
        section_id="backend",
        section_title="Backend",
        relative_path="Backend/Security.md",
        description="Sicherheitsgrenzen und Autorisierung.",
        order=10,
    ),
    DocumentationPageDefinition(
        id="tool-registry",
        title="Tool-Registry",
        section_id="backend",
        section_title="Backend",
        relative_path="Backend/Tool-Registry.md",
        description="Registrierung und Freigabe von Tools.",
        order=20,
    ),
    DocumentationPageDefinition(
        id="development-testing",
        title="Tests",
        section_id="development",
        section_title="Entwicklung",
        relative_path="Development/Testing.md",
        description="Testsuite und Qualitätsprüfungen.",
        order=10,
    ),
    DocumentationPageDefinition(
        id="coding-guidelines",
        title="Coding-Guidelines",
        section_id="development",
        section_title="Entwicklung",
        relative_path="Development/Coding-Guidelines.md",
        description="Verbindliche Entwicklungsregeln.",
        order=20,
    ),
)

DOCUMENTATION_PAGE_MAP = {page.id: page for page in DOCUMENTATION_PAGES}


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


def _available_pages() -> tuple[DocumentationPageDefinition, ...]:
    return tuple(
        page
        for page in DOCUMENTATION_PAGES
        if _resolve_page_path(page).is_file()
    )


@router.get(
    "",
    response_model=DocumentationIndexResponse,
    summary="Dokumentationsübersicht laden",
)
async def list_documentation() -> DocumentationIndexResponse:
    pages = _available_pages()
    sections_by_id: dict[str, DocumentationSection] = {}

    for page in sorted(pages, key=lambda item: (item.section_title, item.order, item.title)):
        section = sections_by_id.get(page.section_id)
        if section is None:
            section = DocumentationSection(
                id=page.section_id,
                title=page.section_title,
            )
            sections_by_id[page.section_id] = section

        section.pages.append(
            DocumentationPageSummary(
                id=page.id,
                title=page.title,
                description=page.description,
            ),
        )

    default_page_id = pages[0].id if pages else None

    return DocumentationIndexResponse(
        default_page_id=default_page_id,
        sections=list(sections_by_id.values()),
    )


@router.get(
    "/pages/{page_id}",
    response_model=DocumentationPageResponse,
    summary="Dokumentationsseite laden",
)
async def get_documentation_page(page_id: str) -> DocumentationPageResponse:
    definition = DOCUMENTATION_PAGE_MAP.get(page_id)

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
