"""
Inspect an orphan subtree and linked chats/messages (read-only).

Usage:
  python scripts/inspect_orphan_subtree.py --node-id <id>

Prints node details recursively and lists chats/messages summary for chats
whose node_id is the orphan or any descendant.
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any, List

from sqlalchemy import select

from app.database.models.hierarchy_node import HierarchyNodeModel
from app.storage.models.chat import Chat as ChatModel
from app.storage.models.chat import Message as MessageModel
from app.storage.database import init_database
from app.core.settings import settings


def resolve_sqlite_path(database_url: str) -> Path | None:
    if database_url.startswith("sqlite"):
        parts = database_url.split(":///", 1)
        if len(parts) == 2:
            return Path(parts[1])
    return None


async def gather_subtree(session, root_id: str) -> List[HierarchyNodeModel]:
    # simple BFS
    nodes_by_id: dict[str, HierarchyNodeModel] = {}
    q = select(HierarchyNodeModel).where(HierarchyNodeModel.id == root_id)
    r = await session.execute(q)
    root = r.scalars().first()
    if root is None:
        return []

    queue = [root]
    nodes_by_id[root.id] = root
    while queue:
        current = queue.pop(0)
        q2 = select(HierarchyNodeModel).where(HierarchyNodeModel.parent_id == current.id)
        rows = (await session.execute(q2)).scalars().all()
        for child in rows:
            if child.id not in nodes_by_id:
                nodes_by_id[child.id] = child
                queue.append(child)
    return list(nodes_by_id.values())


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect orphan subtree and linked chats/messages")
    parser.add_argument("--node-id", required=True)
    args = parser.parse_args(argv)

    db_path = resolve_sqlite_path(settings.effective_database_url)
    if db_path is None:
        print("This script currently supports the local SQLite DB only.")
        return 2

    print(f"Resolved SQLite DB path: {db_path}")

    session_factory = await init_database(create_schema=False)
    async with session_factory() as session:
        root_id = args.node_id
        print(f"Inspecting subtree for node: {root_id}\n")

        nodes = await gather_subtree(session, root_id)
        if not nodes:
            print("No node found with that id.")
            return 1

        # Print nodes sorted by parent_id then position
        nodes_sorted = sorted(nodes, key=lambda n: (n.parent_id or "", n.position or 0, n.id))

        print("Nodes in subtree:")
        for n in nodes_sorted:
            print(f"- id={n.id} parent_id={n.parent_id} type={n.type} name={n.name} position={n.position} is_system={n.is_system} is_active={n.is_active} prompt_enabled={n.prompt_enabled} prompt_priority={n.prompt_priority} prompt_mode={n.prompt_mode} created_at={n.created_at} updated_at={n.updated_at} metadata={n.node_metadata}")

        descendant_ids = [n.id for n in nodes]

        # find chats linked to these nodes
        q = select(ChatModel).where(ChatModel.node_id.in_(descendant_ids))
        chats = (await session.execute(q)).scalars().all()
        print(f"\nFound {len(chats)} chat(s) referencing the subtree nodes")
        for c in chats:
            # count messages
            mq = select(MessageModel).where(MessageModel.conversation_id == c.id)
            msgs = (await session.execute(mq)).scalars().all()
            print(f"- chat id={c.id} node_id={c.node_id} user_id={c.user_id} title={c.title} created_at={c.created_at} updated_at={c.updated_at} messages={len(msgs)}")
            for m in msgs:
                print(f"    message seq={m.sequence_number} role={m.role} type={m.message_type} status={m.status} length={len(m.content) if m.content is not None else 0} created_at={m.created_at}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
