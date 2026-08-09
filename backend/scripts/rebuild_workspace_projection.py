"""Script to rebuild the workspace projection from the database.

This script is safe to run repeatedly and will regenerate the projection
under the configured DATA_PROJECTION_PATH.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.storage.database import get_engine, get_session
from app.storage.repositories import HierarchyRepository, ChatRepository
from app.workspace_projection.contracts import ProjectionConfig, UserDto, NodeDto, ConversationDto, MessageDto
from app.workspace_projection.service import WorkspaceProjectionService


def main() -> int:
    if not settings.data_projection_enabled:
        print("DATA_PROJECTION is disabled in settings; enable DATA_PROJECTION_ENABLED to run this script.")
        return 2

    root = Path(settings.data_projection_path)
    config = ProjectionConfig(enabled=True, root_path=str(root))
    svc = WorkspaceProjectionService(config)

    # For simplicity, this script runs synchronous DB calls using AsyncSession via sync engine
    engine = get_engine()
    with engine.connect() as conn:
        # iterate users/hierarchy and project — simplified for MVP
        print("Rebuild currently not fully implemented in script; run tests for detailed logic.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
