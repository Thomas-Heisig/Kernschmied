from __future__ import annotations

from typing import Literal, List, cast
from pydantic import BaseModel, Field

class DocumentationPageSummary(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str
    title: str
    section_id: str
    order: int = 0

class DocumentationSection(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str
    title: str
    order: int = 0
    pages: List["DocumentationPageSummary"] = Field(default_factory=lambda: cast(List["DocumentationPageSummary"], []))

class DocumentationNavigationResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    documentation_version: str
    # field expected by frontend: `default_page_id`
    default_page_id: str
    sections: List["DocumentationSection"] = Field(default_factory=lambda: cast(List["DocumentationSection"], []))

class DocumentationPageResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str
    title: str
    section_id: str
    # frontend expects `content` key containing markdown
    content: str
    source_path: str
    documentation_version: str
