# F:\Kernschmied\backend\app\models\providers\ollama.py

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import TypeAlias, cast

import httpx

from app.contracts.model_backend import (
    BaseModelBackend,
    ChatMessage,
    GenerationRequest,
    JsonMapping,
    JsonValue,
    MessageRole,
    ModelCapability,
    ModelInfo,
    StreamEvent,
    StreamEventType,
    Usage,
)

logger = logging.getLogger(__name__)

ProviderDependencies: TypeAlias = Mapping[str, object]

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_TIMEOUT_SECONDS = 120.0


# ============================================================
# Fehler
# ============================================================


class OllamaProviderError(RuntimeError):
    pass


class OllamaConfigurationError(OllamaProviderError):
    pass


class OllamaModelNotFoundError(OllamaProviderError):
    pass


# ============================================================
# Provider
# ============================================================


class OllamaProvider(BaseModelBackend):
    def __init__(self, config: JsonMapping) -> None:
        self._base_url = (
            _read_optional_string(config, "base_url") or DEFAULT_BASE_URL
        ).rstrip("/")
        self._default_model = (
            _read_optional_string(config, "default_model") or DEFAULT_MODEL
        )
        models = _read_string_sequence(config, "models")
        self._model_ids = tuple(dict.fromkeys(models or (self._default_model,)))
        if self._default_model not in self._model_ids:
            self._model_ids = (self._default_model, *self._model_ids)
        self._timeout = _read_positive_float(
            config, "timeout_seconds", default=DEFAULT_TIMEOUT_SECONDS
        )
        self._client: httpx.AsyncClient | None = None

    @property
    def backend_name(self) -> str:
        return "ollama"

    async def is_available(self) -> bool:
        try:
            response = await self._get_client().get("/api/version")
            return response.is_success
        except httpx.HTTPError:
            return False

    async def list_models(self) -> list[ModelInfo]:
        return [self._create_model_info(model_id) for model_id in self._model_ids]

    async def get_model(self, model_id: str) -> ModelInfo:
        return self._create_model_info(self._resolve_model_id(model_id))

    def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        return self._stream_request(request)

    async def shutdown(self) -> None:
        client = self._client
        self._client = None
        if client is not None:
            await client.aclose()

    async def _stream_request(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        model_id = self._resolve_model_id(request.model)

        yield StreamEvent.create(
            type=StreamEventType.START,
            data={"backend": self.backend_name, "model": model_id},
        )

        try:
            if request.tools or request.tool_choice is not None:
                raise OllamaConfigurationError(
                    "Tool-Aufrufe sind in dieser Ollama-Provider-Version noch nicht "
                    "implementiert."
                )

            payload: dict[str, object] = {
                "model": model_id,
                "messages": _convert_messages(request.messages),
                "stream": True,
                "options": {
                    "temperature": min(max(request.temperature, 0.0), 2.0),
                    "num_predict": request.max_tokens if request.max_tokens is not None else 4096,
                },
            }

            if request.top_p is not None:
                cast_options = payload["options"]
                if isinstance(cast_options, dict):
                    cast_options["top_p"] = request.top_p

            if request.stop:
                cast_options = payload["options"]
                if isinstance(cast_options, dict):
                    cast_options["stop"] = [
                        item.strip() for item in request.stop if item.strip()
                    ]

            usage: Usage | None = None
            finish_reason: str | None = None

            async with self._get_client().stream(
                "POST", "/api/chat", json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    raw = _parse_json_object(line)
                    if raw is None:
                        continue

                    message = _read_json_object(raw, "message")
                    if message is not None:
                        content = _read_optional_string_value(message, "content")
                        if content:
                            yield StreamEvent.create(
                                type=StreamEventType.TOKEN,
                                content=content,
                            )

                    if _read_bool_value(raw, "done") is True:
                        finish_reason = (
                            _read_optional_string_value(raw, "done_reason") or "stop"
                        )

                        prompt_tokens = _read_non_negative_int_value(
                            raw, "prompt_eval_count"
                        )
                        completion_tokens = _read_non_negative_int_value(
                            raw, "eval_count"
                        )

                        if (
                            prompt_tokens is not None
                            or completion_tokens is not None
                        ):
                            resolved_prompt_tokens = prompt_tokens or 0
                            resolved_completion_tokens = completion_tokens or 0

                            usage = Usage(
                                prompt_tokens=resolved_prompt_tokens,
                                completion_tokens=resolved_completion_tokens,
                                total_tokens=(
                                    resolved_prompt_tokens + resolved_completion_tokens
                                ),
                            )

            data: dict[str, JsonValue] = {
                "backend": self.backend_name,
                "model": model_id,
            }
            if finish_reason is not None:
                data["finish_reason"] = finish_reason

            yield StreamEvent.create(
                type=StreamEventType.END,
                usage=usage,
                data=data,
            )

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=str(exc),
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": True,
                    "error_type": type(exc).__name__,
                },
            )

        except httpx.HTTPStatusError as exc:
            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=str(exc),
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": exc.response.status_code
                    in {408, 409, 429, 500, 502, 503, 504},
                    "status_code": exc.response.status_code,
                    "error_type": type(exc).__name__,
                },
            )

        except OllamaProviderError as exc:
            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=str(exc),
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": False,
                    "error_type": type(exc).__name__,
                },
            )

        except Exception as exc:
            logger.exception("Unexpected Ollama provider error")
            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content="Bei der Ollama-Anfrage ist ein unerwarteter Fehler aufgetreten.",
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": False,
                    "error_type": type(exc).__name__,
                },
            )

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout
            )
        return self._client

    def _resolve_model_id(self, requested: str) -> str:
        model_id = requested.strip() or self._default_model
        if model_id not in self._model_ids:
            raise OllamaModelNotFoundError(
                f"Das Ollama-Modell '{model_id}' ist nicht freigegeben."
            )
        return model_id

    def _create_model_info(self, model_id: str) -> ModelInfo:
        return ModelInfo.create(
            id=model_id,
            backend=self.backend_name,
            display_name=model_id,
            provider="Ollama",
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.COMPLETION,
                ModelCapability.STREAMING,
            },
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            metadata={"configured": True, "remote": False, "endpoint": self._base_url},
        )


# ============================================================
# Hilfsfunktionen für typsicheren JSON-Zugriff
# ============================================================


def _parse_json_object(
    value: str,
) -> dict[str, object] | None:
    try:
        parsed: object = json.loads(value)
    except json.JSONDecodeError as exc:
        raise OllamaProviderError(
            "Ollama lieferte eine ungültige JSON-Antwort."
        ) from exc

    if not isinstance(parsed, dict):
        return None

    parsed_mapping = cast(
        dict[object, object],
        parsed,
    )

    result: dict[str, object] = {}

    for raw_key, raw_value in parsed_mapping.items():
        if isinstance(raw_key, str):
            result[raw_key] = raw_value

    return result


def _read_json_object(
    values: Mapping[str, object],
    key: str,
) -> dict[str, object] | None:
    value = values.get(key)

    if not isinstance(value, dict):
        return None

    nested_mapping = cast(
        dict[object, object],
        value,
    )

    result: dict[str, object] = {}

    for raw_key, raw_value in nested_mapping.items():
        if isinstance(raw_key, str):
            result[raw_key] = raw_value

    return result


def _read_optional_string_value(
    values: Mapping[str, object], key: str
) -> str | None:
    value = values.get(key)
    if not isinstance(value, str):
        return None
    return value


def _read_bool_value(values: Mapping[str, object], key: str) -> bool | None:
    value = values.get(key)
    if not isinstance(value, bool):
        return None
    return value


def _read_non_negative_int_value(
    values: Mapping[str, object], key: str
) -> int | None:
    return _as_non_negative_int(values.get(key))


# ============================================================
# Konvertierungs- und Konfigurationshelfer
# ============================================================


def _convert_messages(messages: Sequence[ChatMessage]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for message in messages:
        content = message.content.strip()
        if not content:
            continue

        if message.role is MessageRole.SYSTEM:
            role = "system"
        elif message.role is MessageRole.ASSISTANT:
            role = "assistant"
        elif message.role is MessageRole.TOOL:
            role = "tool"
        else:
            role = "user"

        result.append({"role": role, "content": content})

    if not result:
        raise OllamaConfigurationError(
            "Die Ollama-Anfrage enthält keine verwendbare Nachricht."
        )
    return result


def _as_non_negative_int(value: object) -> int | None:
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
        else None
    )


def _read_optional_string(config: JsonMapping, key: str) -> str | None:
    value = config.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _read_string_sequence(config: JsonMapping, key: str) -> tuple[str, ...]:
    value = config.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(
        item.strip() for item in value if isinstance(item, str) and item.strip()
    )


def _read_positive_float(
    config: JsonMapping, key: str, *, default: float
) -> float:
    value = config.get(key)
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)) and float(value) > 0:
        return float(value)
    return default


def create_ollama_backend(
    *, provider_config: JsonMapping, dependencies: ProviderDependencies | None = None
) -> BaseModelBackend:
    del dependencies
    return OllamaProvider(provider_config)


__all__ = [
    "OllamaConfigurationError",
    "OllamaModelNotFoundError",
    "OllamaProvider",
    "OllamaProviderError",
    "create_ollama_backend",
]