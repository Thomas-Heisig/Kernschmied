from __future__ import annotations

from typing import Any

from app.database.models.hierarchy_node import HierarchyNodeModel
from app.hierarchy.repository import HierarchyRepository


SYSTEM_ROOT_ID = "system-root"


async def ensure_system_root(repository: HierarchyRepository) -> HierarchyNodeModel:
    root = await repository.get_node(SYSTEM_ROOT_ID)

    if root is None:
        # Create a minimal system root node
        data: dict[str, Any] = {
            "node_id": SYSTEM_ROOT_ID,
            "parent_id": None,
            "type": "system",
            "name": "System Root",
            "position": 0,
            "system_prompt": None,
            "tool_policy": {},
            "config_overrides": {},
            "metadata": {},
            "is_system": True,
            "is_movable": False,
            "is_deletable": False,
            "prompt_enabled": True,
            "prompt_priority": -1000,
            "prompt_mode": "append",
        }

        # repository.create_node expects a HierarchyNodeCreate-like object
        # We'll pass a simple namespace object to satisfy the mapping
        class _D:
            pass

        d: Any = _D()
        for k, v in data.items():
            setattr(d, k if k != "node_id" else "node_id", v)

        new = await repository.create_node(d)  # type: ignore[arg-type]

        # ensure flags are correct on created node
        if not new.is_system or new.is_movable or new.is_deletable:
            new.is_system = True
            new.is_movable = False
            new.is_deletable = False

        return new

    # Repair protective flags if needed
    changed = False
    if not root.is_system:
        root.is_system = True
        changed = True
    if root.is_movable:
        root.is_movable = False
        changed = True
    if root.is_deletable:
        root.is_deletable = False
        changed = True

    if changed:
        # Persist changes directly on the repository/session
        await repository._session.flush()  # type: ignore[attr-defined]

    return root
