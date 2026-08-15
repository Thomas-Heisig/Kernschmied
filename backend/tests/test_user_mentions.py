from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest
from app.api.v1.mentions import (
    allowed_mention_target_ids,
    is_administrator_auto_answer_user,
)
from app.models.service import ModelAccessContext
from app.services.chat_service import (
    ChatEventType,
    ChatRepository,
    ChatRequest,
    ChatResponse,
    ChatService,
    ChatServiceContext,
)
from app.storage.repositories.auth_session import AuthSessionRepository
from app.users import preferences_service


class RecordingRepository:
    def __init__(self) -> None:
        self.user_messages: list[dict[str, object]] = []

    async def create_conversation(self, **kwargs: object) -> None:
        del kwargs

    async def append_user_message(self, **kwargs: object) -> None:
        self.user_messages.append(kwargs)

    async def append_assistant_message(self, **kwargs: object) -> None:
        raise AssertionError(f"assistant message must not be persisted: {kwargs}")

    async def mark_assistant_message_failed(self, **kwargs: object) -> None:
        raise AssertionError(f"assistant failure must not be persisted: {kwargs}")


class FailOnModelUse:
    async def stream(self, **kwargs: object):
        raise AssertionError(f"model must not be called: {kwargs}")
        yield


def test_only_managed_system_admin_uses_automatic_answer() -> None:
    system_admin = SimpleNamespace(is_system_user=True, is_system_admin=True)
    human_admin = SimpleNamespace(is_system_user=False, is_system_admin=True)

    assert is_administrator_auto_answer_user(system_admin)
    assert not is_administrator_auto_answer_user(human_admin)


@pytest.mark.asyncio
async def test_user_request_can_complete_without_calling_the_model() -> None:
    repository = RecordingRepository()
    service = ChatService(
        model_service=FailOnModelUse(),  # type: ignore[arg-type]
        default_model_id="model-default",
        repository=cast(ChatRepository, repository),
    )
    request = ChatRequest(
        message="@michael Bitte pruefen",
        conversation_id="conversation-1",
        respond_with_ai=False,
        metadata={"mentions": [{"user_id": "michael-id"}]},
    )
    context = ChatServiceContext(
        request_id="request-1",
        user_id="thomas-id",
        access=ModelAccessContext(user_id="thomas-id"),
    )

    events = [event async for event in service.stream(request, context=context)]

    assert [event.event for event in events] == [
        ChatEventType.START,
        ChatEventType.COMPLETE,
    ]
    assert events[-1].data["ai_response"] is False
    assert len(repository.user_messages) == 1


@pytest.mark.asyncio
async def test_session_presence_touch_is_throttled() -> None:
    session = AsyncMock()
    session.add = Mock()
    repository = AuthSessionRepository(session)
    now = datetime.now(UTC)
    recent = SimpleNamespace(last_seen_at=now - timedelta(seconds=30))

    await repository.touch(recent, now)

    session.add.assert_not_called()
    session.flush.assert_not_awaited()

    stale = SimpleNamespace(last_seen_at=now - timedelta(minutes=2))
    await repository.touch(stale, now)

    assert stale.last_seen_at == now
    session.add.assert_called_once_with(stale)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_mention_targets_are_limited_to_the_active_hierarchy_path() -> None:
    session = AsyncMock()
    chat_node = SimpleNamespace(
        id="chat-1",
        parent_id="workspace-1",
        node_metadata={"assigned_user_ids": ["michael-id"]},
    )
    workspace_node = SimpleNamespace(
        id="workspace-1",
        parent_id=None,
        node_metadata={"owner_user_id": "thomas-id"},
    )
    session.get = AsyncMock(side_effect=[chat_node, workspace_node])

    allowed = await allowed_mention_target_ids(
        session, "chat-1", is_admin=False
    )

    assert allowed == {"thomas-id", "michael-id"}
    assert await allowed_mention_target_ids(
        session, "chat-1", is_admin=True
    ) is None


@pytest.mark.asyncio
async def test_admin_ai_response_default_can_be_overridden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preference = SimpleNamespace(
        locale="de",
        timezone="Europe/Berlin",
        theme="system",
        compact_mode=0,
        preferences_json={},
        updated_at=None,
    )
    user = SimpleNamespace(id="admin-id", is_system_admin=True)
    user_repository = SimpleNamespace(get_by_id=AsyncMock(return_value=user))
    preference_repository = SimpleNamespace(
        get_by_user_id=AsyncMock(return_value=preference)
    )
    monkeypatch.setattr(
        preferences_service, "UserRepository", lambda session: user_repository
    )
    monkeypatch.setattr(
        preferences_service,
        "UserPreferenceRepository",
        lambda session: preference_repository,
    )
    session = AsyncMock()

    defaults = await preferences_service.get_preferences(session, "admin-id")
    assert defaults.ai_response_on_mentions is True

    preference.preferences_json["ai_response_on_mentions"] = False
    overridden = await preferences_service.get_preferences(session, "admin-id")
    assert overridden.ai_response_on_mentions is False


@pytest.mark.asyncio
async def test_administrator_auto_answer_is_persisted_with_admin_identity() -> None:
    class AssistantRecordingRepository(RecordingRepository):
        def __init__(self) -> None:
            super().__init__()
            self.assistant_messages: list[dict[str, object]] = []

        async def append_assistant_message(self, **kwargs: object) -> None:
            self.assistant_messages.append(kwargs)

    repository = AssistantRecordingRepository()
    service = ChatService(
        model_service=FailOnModelUse(),  # type: ignore[arg-type]
        default_model_id="model-default",
        repository=cast(ChatRepository, repository),
    )
    request = ChatRequest(
        message="@Administrator Bitte pruefen",
        metadata={
            "administrator_auto_answer": True,
            "administrator_user_id": "admin-id",
        },
    )
    response = ChatResponse(
        request_id="request-1",
        conversation_id="conversation-1",
        message_id="message-1",
        model_id="model-default",
        content="Erledigt.",
    )

    await service._persist_assistant_response(request=request, response=response)

    persisted = repository.assistant_messages[0]
    assert persisted["user_id"] == "admin-id"
    assert persisted["metadata"] == {
        "administrator_auto_answer": True,
        "assistant_display_name": "Administrator",
    }
