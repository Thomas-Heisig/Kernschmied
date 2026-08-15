from __future__ import annotations

from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.hierarchy import build_actor_from_request, structured_http_error
from app.auth.dependencies import require_authenticated_user
from app.auth.models import UserContext
from app.contracts.chat_memory import ChatHistoryResponse, ChatMessageRead
from app.hierarchy.permissions import HierarchyPermissionService
from app.storage.database import get_session
from app.storage.repositories import ChatRepository, HierarchyRepository

router = APIRouter()


@router.get("/{conversation_id}/messages", response_model=ChatHistoryResponse)
async def list_chat_messages(
    request: Request,
    conversation_id: str,
    after: int | None = Query(
        default=None, description="Return messages with sequence_number > after"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: UserContext = Depends(require_authenticated_user),
) -> ChatHistoryResponse:
    """Listet persistente Chat-Nachrichten zu einer Unterhaltung auf.

    Serverseitige Autorisierung: aktuell ist ein authentifizierter Benutzer
    erforderlich. Feinere Berechtigungsprüfungen können später ergänzt werden.
    """

    # load conversation and check existence
    repo = ChatRepository(session)
    conversation = await repo.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Build services for hierarchy lookup and permissions
    hierarchy = HierarchyRepository(session)
    perms = HierarchyPermissionService()

    # authorization: verify the user can read the node this conversation belongs to
    node = await hierarchy.get(conversation.node_id)
    if node is None:
        # if node is missing treat as forbidden
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # authorize via permission service using actor built from request
    actor = build_actor_from_request(request)
    if not perms.can(actor, "read", node):
        raise structured_http_error(
            request=request,
            status_code=403,
            code="PERMISSION_DENIED",
            message="Not authorized to read this conversation",
        )

    # authorize: build hierarchy actor and ask permission service
    actor = build_actor_from_request(request)
    perm = HierarchyPermissionService()
    if not perm.can(actor, "read", None):
        raise structured_http_error(
            request=request,
            status_code=403,
            code="PERMISSION_DENIED",
            message="Not authorized to read this conversation",
        )

    try:
        # load one extra row to determine has_more
        rows = await repo.list_messages(
            conversation_id, limit=limit + 1, after_sequence=after
        )
    except Exception as exc:
        raise structured_http_error(
            request=request,
            status_code=500,
            code="CHAT_HISTORY_UNAVAILABLE",
            message="Could not load chat history",
            details={"error": str(exc)},
        )

    visible = rows[:limit]
    has_more = len(rows) > limit
    items: list[ChatMessageRead] = []
    for m in visible:
        items.append(
            ChatMessageRead(
                id=m.id,
                conversation_id=m.conversation_id,
                hierarchy_node_id=conversation.node_id,
                user_id=m.user_id,
                parent_message_id=m.parent_message_id,
                role=cast(Literal["user", "assistant", "system", "tool"], m.role),
                content=m.content,
                message_type=cast(
                    Literal["text", "tool_call", "tool_result", "reasoning", "summary"],
                    m.message_type,
                ),
                ui_context=getattr(m, "ui_context", None),
                sequence_number=m.sequence_number,
                status=cast(
                    Literal["pending", "complete", "failed", "cancelled"], m.status
                ),
                request_id=m.request_id,
                created_at=m.created_at,
                completed_at=m.completed_at,
                schema_version=m.schema_version,
            )
        )

    next_cursor = items[-1].sequence_number if has_more and items else None

    return ChatHistoryResponse(
        schema_version="1.0",
        conversation_id=conversation_id,
        items=items,
        has_more=has_more,
        next_cursor=next_cursor,
    )
