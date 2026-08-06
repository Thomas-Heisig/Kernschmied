"""
Repair orphan conversation hierarchy nodes.

Dry-run by default. Use --apply to perform changes. Always creates a backup
of the SQLite file before any write.

This script looks for hierarchy_nodes with:
    type = 'chat'
    parent_id IS NULL
    id != 'system-root'
    name LIKE 'Conversation conversation_%'

And attempts a conservative repair according to project rules.
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.settings import settings
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.storage.database import init_database
from app.storage.models.chat import Chat as ChatModel
from app.storage.models.chat import Message as MessageModel
from sqlalchemy import func, select


def resolve_sqlite_path(database_url: str) -> Path | None:
    if database_url.startswith("sqlite"):
        parts = database_url.split(":///", 1)
        if len(parts) == 2:
            return Path(parts[1])
    return None


async def gather_orphans(session: Any) -> list[HierarchyNodeModel]:
    q = select(HierarchyNodeModel).where(
        HierarchyNodeModel.type == "chat",
        HierarchyNodeModel.parent_id.is_(None),
        HierarchyNodeModel.id != "system-root",
        HierarchyNodeModel.name.like("Conversation conversation_%"),
    )
    rows = await session.execute(q)
    return rows.scalars().all()


async def inspect_orphan(session: Any, node: HierarchyNodeModel) -> dict[str, Any]:
    # gather chats referencing this node
    chats_q = select(ChatModel).where(ChatModel.node_id == node.id)
    chats = (await session.execute(chats_q)).scalars().all()

    messages_count = 0
    for c in chats:
        cnt_q = (
            select(func.count())
            .select_from(MessageModel)
            .where(MessageModel.conversation_id == c.id)
        )
        cnt = (await session.execute(cnt_q)).scalar_one()
        messages_count += int(cnt or 0)

    # check for child nodes referencing this node as parent
    child_q = select(HierarchyNodeModel).where(HierarchyNodeModel.parent_id == node.id)
    child_rows = (await session.execute(child_q)).scalars().all()
    child_count = len(child_rows)

    return {
        "node": node,
        "chats": chats,
        "messages_count": messages_count,
        "child_count": int(child_count or 0),
        "child_rows": child_rows,
    }


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Repair orphan conversation hierarchy nodes"
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    args = parser.parse_args(argv)

    db_path = resolve_sqlite_path(settings.effective_database_url)
    if db_path is None:
        print("This script currently supports the local SQLite DB only.")
        return 2

    print(f"Resolved SQLite DB path: {db_path}")

    if args.apply:
        # create backup
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        backup_path = db_path.with_name(f"chat.before-hierarchy-repair-{timestamp}.db")
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")

    # initialize DB session factory (do not create schema)
    session_factory = await init_database(create_schema=False)

    async with session_factory() as session:
        orphans = await gather_orphans(session)

        if not orphans:
            print("No orphan conversation hierarchy nodes found.")
            return 0

        print("DRY RUN: Found orphan conversation hierarchy nodes:")
        proposals: list[dict[str, Any]] = []
        for n in orphans:
            info = await inspect_orphan(session, n)
            node = info["node"]
            chats = info["chats"]
            messages = info["messages_count"]

            print(
                f"- node.id={node.id} name={node.name} chats={len(chats)} messages={messages} children={info.get('child_count', 0)}"
            )
            if info.get("child_count", 0) > 0:
                for cnode in info.get("child_rows", []):
                    print(
                        f"    child -> id={cnode.id} type={cnode.type} name={cnode.name}"
                    )

            # If node has children, we cannot safely delete it.
            if info.get("child_count", 0) > 0:
                proposals.append(
                    {
                        "action": "unresolved",
                        "node_id": node.id,
                        "reason": "node has child nodes",
                    }
                )
            elif len(chats) == 0:
                proposals.append(
                    {
                        "action": "delete_node",
                        "node_id": node.id,
                        "reason": "no linked chats",
                    }
                )
            elif len(chats) >= 1:
                # Conservative strategy: only auto-assign to canonical 'chat-1' if present
                canonical = (
                    (
                        await session.execute(
                            select(HierarchyNodeModel).where(
                                HierarchyNodeModel.id == "chat-1"
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if canonical is not None:
                    proposals.append(
                        {
                            "action": "reassign_and_delete",
                            "node_id": node.id,
                            "target_node_id": "chat-1",
                            "chats": [c.id for c in chats],
                            "reason": "assign to canonical development chat-1",
                        }
                    )
                else:
                    proposals.append(
                        {
                            "action": "unresolved",
                            "node_id": node.id,
                            "chats": [c.id for c in chats],
                        }
                    )

        # print summary
        print("\nProposed actions:")
        unresolved = [p for p in proposals if p["action"] == "unresolved"]
        for p in proposals:
            print(f"- {p}")

        if unresolved:
            print(
                "\nFound unresolved items; no changes will be applied. Resolve manually."
            )
            return 3

        if not args.apply:
            print(
                "\nDry run complete. Re-run with --apply to execute the proposed changes."
            )
            return 0

        # APPLY changes in a single transaction using a fresh session
        try:
            async with session_factory() as write_session:
                async with write_session.begin():
                    for p in proposals:
                        if p["action"] == "delete_node":
                            node = await write_session.get(
                                HierarchyNodeModel, p["node_id"]
                            )
                            if node is not None:
                                await write_session.delete(node)
                        elif p["action"] == "reassign_and_delete":
                            target_id = p["target_node_id"]
                            for chat_id in p["chats"]:
                                chat = await write_session.get(ChatModel, chat_id)
                                if chat is None:
                                    continue
                                print(
                                    f"Reassigning chat {chat.id} node_id {chat.node_id} -> {target_id}"
                                )
                                chat.node_id = target_id
                                write_session.add(chat)
                            node = await write_session.get(
                                HierarchyNodeModel, p["node_id"]
                            )
                            if node is not None:
                                await write_session.delete(node)
            print("Apply complete.")
            return 0
        except Exception as e:
            print(f"Error during apply: {e}")
            return 4


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
