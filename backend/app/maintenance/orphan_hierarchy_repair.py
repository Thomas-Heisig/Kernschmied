from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from app.storage.models.base import utc_now
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.hierarchy_node import HierarchyNodeModel
from app.storage.models.chat import Chat as ChatModel
from app.storage.models.chat import Message as MessageModel


@dataclass(frozen=True, slots=True)
class OrphanRepairPlan:
    orphan_node_id: str
    target_parent_id: str
    target_chat_node_id: str
    child_node_ids: tuple[str, ...]
    chat_ids: tuple[str, ...]
    message_count: int
    can_apply: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OrphanRepairResult:
    orphan_node_id: str
    moved_child_ids: tuple[str, ...]
    reassigned_chat_ids: tuple[str, ...]
    deleted_node_id: str | None
    message_count_before: int
    message_count_after: int
    applied_at: datetime


async def build_orphan_repair_plan(
    session: AsyncSession,
    *,
    orphan_node_id: str,
    target_parent_id: str,
    target_chat_node_id: str,
) -> OrphanRepairPlan:
    # Validate orphan existence and properties
    orphan = await session.get(HierarchyNodeModel, orphan_node_id)
    blockers: list[str] = []
    if orphan is None:
        blockers.append("orphan_not_found")
        return OrphanRepairPlan(
            orphan_node_id=orphan_node_id,
            target_parent_id=target_parent_id,
            target_chat_node_id=target_chat_node_id,
            child_node_ids=(),
            chat_ids=(),
            message_count=0,
            can_apply=False,
            blockers=tuple(blockers),
        )

    if orphan.type != "chat":
        blockers.append("orphan_not_chat_type")

    if orphan.parent_id is not None:
        blockers.append("orphan_not_root")

    if orphan.id == "system-root":
        blockers.append("orphan_is_system_root")

    if not (isinstance(orphan.name, str) and orphan.name.startswith("Conversation conversation_")):
        blockers.append("orphan_name_unexpected")

    # target parent
    target_parent = await session.get(HierarchyNodeModel, target_parent_id)
    if target_parent is None:
        blockers.append("target_parent_not_found")

    # target chat node
    target_chat = await session.get(HierarchyNodeModel, target_chat_node_id)
    if target_chat is None:
        blockers.append("target_chat_not_found")
    else:
        if target_chat.type != "chat":
            blockers.append("target_chat_not_type_chat")

    # detect descendant relationship: ensure target_parent is not a descendant of orphan
    if target_parent is not None:
        # simple recursive check
        q = select(HierarchyNodeModel).where(HierarchyNodeModel.parent_id == orphan.id)
        rows = (await session.execute(q)).scalars().all()
        descendant_ids = {r.id for r in rows}
        # BFS to collect all descendants
        queue = list(rows)
        while queue:
            cur = queue.pop(0)
            q2 = select(HierarchyNodeModel).where(HierarchyNodeModel.parent_id == cur.id)
            more = (await session.execute(q2)).scalars().all()
            for m in more:
                if m.id not in descendant_ids:
                    descendant_ids.add(m.id)
                    queue.append(m)

        if target_parent.id in descendant_ids:
            blockers.append("target_parent_is_descendant")

    # collect children and linked chats/messages
    q_children = select(HierarchyNodeModel).where(HierarchyNodeModel.parent_id == orphan.id)
    children = (await session.execute(q_children)).scalars().all()
    child_ids = tuple(c.id for c in children)

    q_chats = select(ChatModel).where(ChatModel.node_id == orphan.id)
    chats = (await session.execute(q_chats)).scalars().all()
    chat_ids = tuple(c.id for c in chats)

    message_count = 0
    for c in chats:
        cnt_q = select(func.count()).select_from(MessageModel).where(MessageModel.conversation_id == c.id)
        cnt = (await session.execute(cnt_q)).scalar_one()
        message_count += int(cnt or 0)

    # If there are children, do not apply automatically unless they are zero
    if child_ids:
        blockers.append("orphan_has_children")

    can_apply = len(blockers) == 0

    return OrphanRepairPlan(
        orphan_node_id=orphan_node_id,
        target_parent_id=target_parent_id,
        target_chat_node_id=target_chat_node_id,
        child_node_ids=child_ids,
        chat_ids=chat_ids,
        message_count=message_count,
        can_apply=can_apply,
        blockers=tuple(blockers),
    )


async def apply_orphan_repair(
    session: AsyncSession,
    *,
    plan: OrphanRepairPlan,
) -> OrphanRepairResult:
    if not plan.can_apply:
        raise RuntimeError("Plan cannot be applied; blockers present: %s" % (plan.blockers,))

    # Re-load and validate inside transaction
    orphan = await session.get(HierarchyNodeModel, plan.orphan_node_id)
    if orphan is None:
        raise LookupError("Orphan disappeared")

    target_parent = await session.get(HierarchyNodeModel, plan.target_parent_id)
    if target_parent is None:
        raise LookupError("Target parent disappeared")

    target_chat = await session.get(HierarchyNodeModel, plan.target_chat_node_id)
    if target_chat is None:
        raise LookupError("Target chat disappeared")

    # move children
    moved = []
    for child_id in plan.child_node_ids:
        child = await session.get(HierarchyNodeModel, child_id)
        if child is None:
            continue
        child.parent_id = target_parent.id
        session.add(child)
        moved.append(child.id)

    # reassign chats
    reassigned = []
    for chat_id in plan.chat_ids:
        chat = await session.get(ChatModel, chat_id)
        if chat is None:
            continue
        chat.node_id = target_chat.id
        session.add(chat)
        reassigned.append(chat.id)

    # ensure messages preserved: count before/after
    before = plan.message_count
    # flush so counts are stable
    await session.flush()

    after = 0
    for chat_id in plan.chat_ids:
        mq = select(func.count()).select_from(MessageModel).where(MessageModel.conversation_id == chat_id)
        cnt = (await session.execute(mq)).scalar_one()
        after += int(cnt or 0)

    deleted = None
    # delete orphan only if it has no children and no chats referencing it
    q_children2 = select(HierarchyNodeModel).where(HierarchyNodeModel.parent_id == orphan.id)
    remaining_children = (await session.execute(q_children2)).scalars().all()
    q_chatrefs = select(ChatModel).where(ChatModel.node_id == orphan.id)
    remaining_chats = (await session.execute(q_chatrefs)).scalars().all()

    if not remaining_children and not remaining_chats:
        await session.delete(orphan)
        deleted = orphan.id

    await session.flush()

    return OrphanRepairResult(
        orphan_node_id=plan.orphan_node_id,
        moved_child_ids=tuple(moved),
        reassigned_chat_ids=tuple(reassigned),
        deleted_node_id=deleted,
        message_count_before=before,
        message_count_after=after,
        applied_at=utc_now(),
    )
