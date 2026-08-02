"""Storage compatibility shim for the canonical hierarchy model.

This module intentionally does not define a new ORM mapping. Instead it
re-exports the canonical `HierarchyNodeModel` from
`app.database.models.hierarchy_node` under the historical name
`HierarchyNode` so existing imports continue to work while avoiding a
duplicate table mapping.
"""

from __future__ import annotations

from app.database.models.hierarchy_node import HierarchyNodeModel as HierarchyNode

__all__ = ["HierarchyNode"]
