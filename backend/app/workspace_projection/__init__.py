"""Workspace projection package.

Provides tools to project DB entities into a filesystem representation.
This package intentionally separates path logic, low-level atomic IO
and the domain-level service that materializes users, nodes and chats.
"""

from .service import WorkspaceProjectionService

__all__ = ["WorkspaceProjectionService"]
