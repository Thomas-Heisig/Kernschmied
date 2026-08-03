from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import json
from pydantic import BaseModel, ValidationError
from app.contracts import documentation as contracts
import re


def resolve_default_documentation_root() -> Path:
    """
    Ermittelt den kanonischen Dokumentationsordner unabhängig davon,
    aus welchem Arbeitsverzeichnis Uvicorn oder Pytest gestartet wurde.
    """
    repository_root = Path(__file__).resolve().parents[3]
    documentation_root = repository_root / "documentation"
    return documentation_root.resolve()


ROOT = Path(__file__).resolve().parents[3]


class DocumentationManifestError(RuntimeError):
    pass


class ManifestSchema(BaseModel):
    schema_version: str
    documentation_version: Optional[str] = "0.1.0"
    home_page: Optional[str]
    sections: List[Dict]


def _safe_id_from_file(file_path: str) -> str:
    # create an id from file path: remove extension, replace non-alnum with '-', lower
    name = Path(file_path).stem
    safe = re.sub(r"[^A-Za-z0-9_-]", "-", name).strip("-_ ").lower()
    return safe or name.lower()


class DocumentationService:
    def __init__(self, documentation_root: Path | None = None) -> None:
        self._root = (
            documentation_root.resolve()
            if documentation_root is not None
            else resolve_default_documentation_root()
        )
        self._manifest_path = self._root / "manifest.json"
        self._manifest: Optional[ManifestSchema] = None
        # mapping page id -> relative file path from root
        self._page_map: Dict[str, str] = {}

    @property
    def root(self) -> Path:
        return self._root

    def load_manifest(self) -> ManifestSchema:
        if not self._manifest_path.is_file():
            raise FileNotFoundError(str(self._manifest_path))

        try:
            raw = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise DocumentationManifestError(
                f"Dokumentationsmanifest konnte nicht gelesen werden: {exc}"
            ) from exc

        if isinstance(raw, dict) and "sections" in raw and isinstance(raw["sections"], list):
            try:
                m = ManifestSchema(**{
                    "schema_version": raw.get("schema_version", "1.0"),
                    "documentation_version": raw.get("documentation_version", raw.get("version", "0.1.0")),
                    "home_page": raw.get("home_page") or raw.get("default_page_id") or None,
                    "sections": raw["sections"],
                })
            except ValidationError as e:
                raise DocumentationManifestError(f"manifest validation failed: {e}")
        else:
            raise DocumentationManifestError("Unsupported manifest format")

        # build page map for safe resolution
        page_map: Dict[str, str] = {}
        for sec in m.sections:
            for p in sec.get("pages", []):
                file = p.get("file") or p.get("path") or p.get("href")
                if not file:
                    continue
                pid = p.get("id") or _safe_id_from_file(file)
                page_map[pid] = file

        self._manifest = m
        self._page_map = page_map
        return m

    def build_navigation(self) -> contracts.DocumentationNavigationResponse:
        manifest = self._manifest or self.load_manifest()
        if not manifest.sections:
            raise DocumentationManifestError("DOCUMENTATION_MANIFEST_EMPTY")

        sections_out: List[contracts.DocumentationSection] = []
        home_page_id = manifest.home_page or ""

        for sec in manifest.sections:
            title = sec.get("title") or sec.get("name") or str(sec.get("id", "section"))
            pages = []
            for p in sec.get("pages", []):
                file = p.get("file") or p.get("path") or p.get("href")
                if not file:
                    continue
                pid = p.get("id") or _safe_id_from_file(file)
                pages.append(
                    contracts.DocumentationPageSummary(
                        id=pid,
                        title=p.get("title") or Path(file).stem,
                        section_id=title.lower().replace(" ", "-"),
                        order=int(p.get("order") or 0),
                    )
                )
                if (manifest.home_page is None) and (home_page_id == ""):
                    home_page_id = pid
            section_obj = contracts.DocumentationSection(
                id=title.lower().replace(" ", "-"), title=title, pages=pages
            )
            if pages:
                sections_out.append(section_obj)

        if not home_page_id and sections_out and sections_out[0].pages:
            home_page_id = sections_out[0].pages[0].id

        nav = contracts.DocumentationNavigationResponse(
            documentation_version=manifest.documentation_version or "0.1.0",
            default_page_id=home_page_id,
            sections=sections_out,
        )

        return nav

    def resolve_page_path(self, page_id: str) -> Path:
        # Only allow files declared in the manifest
        if not self._page_map:
            if not self._manifest:
                self.load_manifest()

        rel = self._page_map.get(page_id)
        if not rel:
            raise FileNotFoundError(f"page id not found: {page_id}")

        candidate = (self._root / rel).resolve()

        try:
            candidate.relative_to(self._root)
        except Exception as exc:
            raise DocumentationManifestError("Die Dokumentationsseite liegt außerhalb des Dokumentationsroots.") from exc

        if not candidate.is_file():
            raise FileNotFoundError(str(candidate))

        if candidate.suffix.lower() not in {".md", ".markdown"}:
            raise DocumentationManifestError(f"Nicht unterstützter Dokumentationstyp: {candidate.suffix}")

        return candidate

    def load_page(self, page_id: str) -> contracts.DocumentationPageResponse:
        path = self.resolve_page_path(page_id)
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            content = path.read_text(encoding="latin-1", errors="ignore")

        title = None
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        if not title:
            title = path.stem

        return contracts.DocumentationPageResponse(
            id=page_id,
            title=title,
            section_id=path.parent.name,
            content=content,
            source_path=str(path.relative_to(ROOT)),
            documentation_version=self._manifest.documentation_version if self._manifest else "0.1.0",
        )


# module-level default service for backwards compatibility
service = DocumentationService()


def build_navigation() -> contracts.DocumentationNavigationResponse:
    return service.build_navigation()


def load_page(page_id: str) -> contracts.DocumentationPageResponse:
    return service.load_page(page_id)
