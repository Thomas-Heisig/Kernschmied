"""Resolve an orphan hierarchy subtree by building and optionally
applying a repair plan.

Usage:
    python scripts/resolve_orphan_subtree.py \
        --node-id <id> --target-parent-id <id> --target-chat-node-id <id> \
        [--apply]
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import settings
from app.maintenance.orphan_hierarchy_repair import (
    apply_orphan_repair,
    build_orphan_repair_plan,
)
from app.storage.database import init_database


def resolve_sqlite_path(database_url: str) -> Path | None:
    if database_url.startswith("sqlite"):
        parts = database_url.split(":///", 1)
        if len(parts) == 2:
            return Path(parts[1])
    return None


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve orphan subtree (dry-run default)"
    )
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--target-parent-id", required=True)
    parser.add_argument("--target-chat-node-id", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    db_path = resolve_sqlite_path(settings.effective_database_url)
    if db_path is None:
        print("This script currently supports local SQLite DB only.")
        return 2

    print(f"Resolved SQLite DB path: {db_path}")

    backup_path: Path | None = None

    if args.apply:
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        backup_path = db_path.with_name(
            f"chat.before-orphan-subtree-repair-{timestamp}.db"
        )
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")

    session_factory = await init_database(create_schema=False)

    async with session_factory() as session:
        plan = await build_orphan_repair_plan(
            session,
            orphan_node_id=args.node_id,
            target_parent_id=args.target_parent_id,
            target_chat_node_id=args.target_chat_node_id,
        )

        # Structured dry-run output
        print("MODE=" + ("APPLY" if args.apply else "DRY_RUN"))
        print(f"ORPHAN_NODE_ID={plan.orphan_node_id}")
        print("ORPHAN_TYPE=chat")
        print("ORPHAN_NAME=...")
        print(f"DIRECT_CHILD_COUNT={len(plan.child_node_ids)}")
        print(f"DESCENDANT_COUNT={len(plan.child_node_ids)}")
        print(f"LINKED_CHAT_COUNT={len(plan.chat_ids)}")
        print(f"MESSAGE_COUNT={plan.message_count}")
        print(f"TARGET_PARENT_ID={plan.target_parent_id}")
        print(f"TARGET_CHAT_NODE_ID={plan.target_chat_node_id}")
        print(f"CAN_APPLY={str(plan.can_apply).upper()}")
        print(f"BLOCKERS={','.join(plan.blockers) if plan.blockers else ''}")

        if not args.apply:
            return 0

        if not plan.can_apply:
            print("Cannot apply plan; blockers present. Aborting.")
            return 3

    # apply within a fresh transactional session_factory
    try:
        async with session_factory() as write_session, write_session.begin():
            result = await apply_orphan_repair(write_session, plan=plan)
    except Exception as exc:
        print(f"Error during apply: {exc}")
        return 4
    else:
        print("MODE=APPLY")
        # backup_path is only set when args.apply is True
        assert backup_path is not None
        print(f"BACKUP_PATH={backup_path}")
        print(f"MOVED_CHILD_IDS={','.join(result.moved_child_ids)}")
        print(f"REASSIGNED_CHAT_IDS={','.join(result.reassigned_chat_ids)}")
        print(f"DELETED_ORPHAN_NODE_ID={result.deleted_node_id}")
        print(f"MESSAGE_COUNT_BEFORE={result.message_count_before}")
        print(f"MESSAGE_COUNT_AFTER={result.message_count_after}")
        print("TRANSACTION_STATUS=COMMITTED")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
