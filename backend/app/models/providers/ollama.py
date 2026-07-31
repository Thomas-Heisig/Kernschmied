# F:\Kernschmied\backend\app\models\providers\ollama.py

"""
Ollama-Modell-Provider für Kernschmied.

Der Provider übersetzt den stabilen, providerunabhängigen
ModelBackend-Vertrag in die lokale Ollama-Chat-API.

Unterstützte Funktionen:

- Chat-Streaming
- Textgenerierung
- Reasoning-/Thinking-Ausgabe
- Tool Calling
- Structured Output
- Token-Nutzungsdaten
- kontrollierter HTTP-Client-Lebenszyklus

Architekturregeln:

- Logische Kernschmied-Modell-ID und Ollama-Modellname bleiben getrennt.
- Der Provider autorisiert keine Benutzer.
- Der Provider lädt keine beliebigen Python-Module.
- Fehler werden in kontrollierte StreamEvents übersetzt.
- asyncio.CancelledError wird niemals verschluckt.
- Injizierte HTTP-Clients werden nicht vom Provider geschlossen.
"""

from __future__ import annotations

import asyncio
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
    JsonObject,
    JsonValue,
    MessageRole,
    ModelCapability,
    ModelInfo,
    ResponseFormat,
    StreamEvent,
    StreamEventType,
    ToolDefinition,
    Usage,
)

logger = logging.getLogger(__name__)


ProviderDependencies: TypeAlias = Mapping[
    str,
    object,
]


DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_MAX_TOKENS = 4096

SUPPORTED_TOOL_CHOICES = frozenset(
    {
        "auto",
    },
)


# ============================================================
# Fehler
# ============================================================


class OllamaProviderError(RuntimeError):
    """
    Basisklasse für kontrollierte Ollama-Providerfehler.
    """


class OllamaConfigurationError(OllamaProviderError):
    """
    Die Provider- oder Request-Konfiguration ist ungültig.
    """


class OllamaModelNotFoundError(OllamaProviderError):
    """
    Die angeforderte logische Modell-ID gehört nicht zu diesem Provider.
    """


class OllamaResponseError(OllamaProviderError):
    """
    Ollama lieferte eine syntaktisch oder semantisch ungültige Antwort.
    """


# ============================================================
# Provider
# ============================================================


class OllamaProvider(BaseModelBackend):
    """
    Backend für genau ein logisch registriertes Ollama-Modell.

    Eine Provider-Instanz gehört immer zu einem ModelRegistry-Eintrag.
    Sie stellt daher nicht den gesamten Ollama-Server als globale
    Modellquelle dar.
    """

    def __init__(
        self,
        config: JsonMapping,
        *,
        dependencies: ProviderDependencies | None = None,
    ) -> None:
        self._base_url = (
            _read_optional_string(
                config,
                "base_url",
            )
            or DEFAULT_BASE_URL
        ).rstrip("/")

        self._ollama_model_name = (
            _read_optional_string(
                config,
                "model",
            )
            or _read_optional_string(
                config,
                "default_model",
            )
            or DEFAULT_MODEL
        )

        self._logical_model_id = (
            _read_optional_string(
                config,
                "logical_model_id",
            )
            or self._ollama_model_name
        )

        self._display_name = (
            _read_optional_string(
                config,
                "display_name",
            )
            or self._ollama_model_name
        )

        self._timeout_seconds = _read_positive_float(
            config,
            "timeout_seconds",
            default=DEFAULT_TIMEOUT_SECONDS,
        )

        self._default_max_tokens = _read_positive_int(
            config,
            "max_tokens",
            default=DEFAULT_MAX_TOKENS,
        )

        self._keep_alive = _read_optional_string(
            config,
            "keep_alive",
        )

        self._thinking = _read_optional_bool_or_string(
            config,
            "think",
        )

        self._supports_tools = _read_bool(
            config,
            "supports_tools",
            default=False,
        )

        self._supports_thinking = _read_bool(
            config,
            "supports_thinking",
            default=False,
        )

        self._supports_structured_output = _read_bool(
            config,
            "supports_structured_output",
            default=False,
        )

        self._supports_vision = _read_bool(
            config,
            "supports_vision",
            default=False,
        )

        self._supports_embeddings = _read_bool(
            config,
            "supports_embeddings",
            default=False,
        )

        self._client: httpx.AsyncClient | None = None
        self._owns_client = True
        self._client_lock = asyncio.Lock()

        self._configure_dependencies(
            dependencies,
        )

    # ========================================================
    # Öffentlicher Backend-Vertrag (BaseModelBackend)
    # ========================================================

    @property
    def backend_name(self) -> str:
        return "ollama"

    def get_model_info(self) -> ModelInfo:
        """
        Implementiert die abstrakte Methode aus BaseModelBackend.
        """
        return self._create_model_info(self._logical_model_id)

    async def is_available(self) -> bool:
        try:
            client = await self._get_client()

            response = await client.get(
                "/api/version",
            )

            return response.is_success

        except asyncio.CancelledError:
            raise

        except httpx.HTTPError:
            return False

    async def list_models(
        self,
    ) -> list[ModelInfo]:
        """
        Liefert das dieser Provider-Instanz zugeordnete logische Modell.

        Die Methode fragt absichtlich nicht alle Modelle des Ollama-Servers
        ab. Discovery und Freigabe erfolgen ausschließlich über model.json.
        """

        return [
            self._create_model_info(
                self._logical_model_id,
            ),
        ]

    async def get_model(
        self,
        model_id: str,
    ) -> ModelInfo:
        resolved_id = self._resolve_logical_model_id(
            model_id,
        )

        return self._create_model_info(
            resolved_id,
        )

    def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        return self._stream_request(
            request,
        )

    async def shutdown(self) -> None:
        async with self._client_lock:
            client = self._client
            owns_client = self._owns_client

            self._client = None

        if client is not None and owns_client:
            await client.aclose()

    # ========================================================
    # Streaming
    # ========================================================

    async def _stream_request(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        ollama_model_name = self._get_ollama_model_name(
            request,
        )

        yield StreamEvent.create(
            type=StreamEventType.START,
            data={
                "backend": self.backend_name,
                "model": ollama_model_name,
                "logical_model_id": (self._logical_model_id),
            },
        )

        try:
            payload = self._create_chat_payload(
                request,
            )

            usage: Usage | None = None
            finish_reason: str | None = None

            client = await self._get_client()

            async with client.stream(
                "POST",
                "/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    raw = _parse_json_object(
                        line,
                    )

                    await self._raise_for_ollama_error(
                        raw,
                    )

                    message = _read_json_object(
                        raw,
                        "message",
                    )

                    if message is not None:
                        thinking = _read_optional_string_value(
                            message,
                            "thinking",
                        )

                        if thinking:
                            yield StreamEvent.create(
                                type=(StreamEventType.REASONING),
                                content=thinking,
                                data={
                                    "backend": (self.backend_name),
                                    "model": (ollama_model_name),
                                },
                            )

                        content = _read_optional_string_value(
                            message,
                            "content",
                        )

                        if content:
                            yield StreamEvent.create(
                                type=StreamEventType.TOKEN,
                                content=content,
                                data={
                                    "backend": (self.backend_name),
                                    "model": (ollama_model_name),
                                },
                            )

                        tool_calls = _read_json_array(
                            message,
                            "tool_calls",
                        )

                        if tool_calls:
                            for event in _convert_tool_call_events(
                                tool_calls,
                                backend_name=(self.backend_name),
                                model_name=(ollama_model_name),
                            ):
                                yield event

                    if (
                        _read_bool_value(
                            raw,
                            "done",
                        )
                        is True
                    ):
                        finish_reason = (
                            _read_optional_string_value(
                                raw,
                                "done_reason",
                            )
                            or "stop"
                        )

                        usage = _create_usage(
                            raw,
                        )

            if usage is not None:
                yield StreamEvent.create(
                    type=StreamEventType.USAGE,
                    usage=usage,
                    data={
                        "backend": self.backend_name,
                        "model": ollama_model_name,
                    },
                )

            complete_data: dict[
                str,
                JsonValue,
            ] = {
                "backend": self.backend_name,
                "model": ollama_model_name,
                "logical_model_id": (self._logical_model_id),
            }

            if finish_reason is not None:
                complete_data["finish_reason"] = finish_reason

            yield StreamEvent.create(
                type=StreamEventType.COMPLETE,
                data=complete_data,
            )

        except asyncio.CancelledError:
            raise

        except (
            httpx.TimeoutException,
            httpx.ConnectError,
        ) as exc:
            yield self._create_error_event(
                message=(
                    "Ollama ist nicht erreichbar oder "
                    "die Anfrage hat das Zeitlimit "
                    "überschritten."
                ),
                ollama_model_name=ollama_model_name,
                retryable=True,
                error=exc,
            )

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            error_message = _read_http_error_message(
                exc.response,
            ) or str(exc)

            yield self._create_error_event(
                message=error_message,
                ollama_model_name=ollama_model_name,
                retryable=(
                    status_code
                    in {
                        408,
                        409,
                        429,
                        500,
                        502,
                        503,
                        504,
                    }
                ),
                error=exc,
                status_code=status_code,
            )

        except OllamaProviderError as exc:
            yield self._create_error_event(
                message=str(
                    exc,
                ),
                ollama_model_name=ollama_model_name,
                retryable=False,
                error=exc,
            )

        except Exception as exc:
            logger.exception(
                "Unexpected Ollama provider error",
                extra={
                    "backend": self.backend_name,
                    "model": ollama_model_name,
                    "logical_model_id": (self._logical_model_id),
                },
            )

            yield self._create_error_event(
                message=(
                    "Bei der Ollama-Anfrage ist ein unerwarteter Fehler aufgetreten."
                ),
                ollama_model_name=ollama_model_name,
                retryable=False,
                error=exc,
            )

    # ========================================================
    # Payload
    # ========================================================

    def _create_chat_payload(
        self,
        request: GenerationRequest,
    ) -> dict[str, object]:
        self._validate_request_capabilities(
            request,
        )

        options: dict[str, object] = {
            "temperature": request.temperature,
            "num_predict": (
                request.max_tokens
                if request.max_tokens is not None
                else self._default_max_tokens
            ),
        }

        if request.top_p is not None:
            options["top_p"] = request.top_p

        if request.stop:
            options["stop"] = list(
                request.stop,
            )

        payload: dict[str, object] = {
            "model": self._ollama_model_name,
            "messages": _convert_messages(
                request.messages,
            ),
            "stream": True,
            "options": options,
        }

        if self._keep_alive is not None:
            payload["keep_alive"] = self._keep_alive

        if self._thinking is not None:
            payload["think"] = self._thinking

        if request.tools:
            payload["tools"] = _convert_tools(
                request.tools,
            )

        response_format = request.response_format

        if response_format is not None:
            format_value = _convert_response_format(
                response_format,
            )

            if format_value is not None:
                payload["format"] = format_value

        return payload

    def _validate_request_capabilities(
        self,
        request: GenerationRequest,
    ) -> None:
        if request.tools:
            if not self._supports_tools:
                raise OllamaConfigurationError(
                    "Das konfigurierte Ollama-Modell "
                    "ist nicht für Tool Calling freigegeben.",
                )

        if request.tool_choice is not None:
            normalized_tool_choice = request.tool_choice.strip().lower()

            if normalized_tool_choice not in SUPPORTED_TOOL_CHOICES:
                raise OllamaConfigurationError(
                    "Ollama unterstützt in diesem "
                    "Providervertrag nur tool_choice='auto'.",
                )

            if not request.tools:
                raise OllamaConfigurationError(
                    "tool_choice darf nur zusammen mit "
                    "mindestens einem Tool verwendet werden.",
                )

        if (
            request.response_format is not None
            and request.response_format.type != "text"
            and not self._supports_structured_output
        ):
            raise OllamaConfigurationError(
                "Das konfigurierte Ollama-Modell ist "
                "nicht für Structured Output freigegeben.",
            )

        if self._thinking is not None and not self._supports_thinking:
            raise OllamaConfigurationError(
                "Für dieses Ollama-Modell ist Thinking "
                "konfiguriert, aber nicht freigegeben.",
            )

    # ========================================================
    # Client
    # ========================================================

    def _configure_dependencies(
        self,
        dependencies: ProviderDependencies | None,
    ) -> None:
        if dependencies is None:
            return

        injected_client = dependencies.get(
            "http_client",
        )

        if injected_client is None:
            return

        if not isinstance(
            injected_client,
            httpx.AsyncClient,
        ):
            raise OllamaConfigurationError(
                "dependencies['http_client'] muss ein httpx.AsyncClient sein.",
            )

        self._client = injected_client
        self._owns_client = False

    async def _get_client(
        self,
    ) -> httpx.AsyncClient:
        client = self._client

        if client is not None:
            return client

        async with self._client_lock:
            client = self._client

            if client is not None:
                return client

            client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(
                    self._timeout_seconds,
                ),
            )

            self._client = client
            self._owns_client = True

            return client

    # ========================================================
    # Modellauflösung
    # ========================================================

    def _get_ollama_model_name(
        self,
        request: GenerationRequest,
    ) -> str:
        requested = request.model.strip()

        if requested != self._logical_model_id:
            raise OllamaModelNotFoundError(
                "Die angeforderte logische Modell-ID "
                f"'{requested}' gehört nicht zu diesem "
                "Provider. Erwartet wurde "
                f"'{self._logical_model_id}'.",
            )

        return self._ollama_model_name

    def _resolve_logical_model_id(
        self,
        requested: str,
    ) -> str:
        model_id = requested.strip()

        if model_id != self._logical_model_id:
            raise OllamaModelNotFoundError(
                f"Das angeforderte Modell '{model_id}' "
                "ist in dieser Provider-Instanz nicht "
                "konfiguriert.",
            )

        return model_id

    # ========================================================
    # Diagnose
    # ========================================================

    def _create_model_info(
        self,
        model_id: str,
    ) -> ModelInfo:
        capabilities: set[ModelCapability] = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.STREAMING,
        }

        if self._supports_tools:
            capabilities.add(
                ModelCapability.TOOLS,
            )

        if self._supports_vision:
            capabilities.add(
                ModelCapability.VISION,
            )

        if self._supports_embeddings:
            capabilities.add(
                ModelCapability.EMBEDDINGS,
            )

        if self._supports_structured_output:
            capabilities.add(
                ModelCapability.STRUCTURED_OUTPUT,
            )

        return ModelInfo.create(
            id=model_id,
            backend=self.backend_name,
            display_name=self._display_name,
            provider=self.backend_name,
            capabilities=capabilities,
            supports_streaming=True,
            supports_tools=self._supports_tools,
            supports_vision=self._supports_vision,
            supports_embeddings=(self._supports_embeddings),
            supports_structured_output=(self._supports_structured_output),
            metadata={
                "configured": True,
                "remote": False,
                "endpoint": self._base_url,
                "ollama_model": (self._ollama_model_name),
                "supports_thinking": (self._supports_thinking),
            },
        )

    def _create_error_event(
        self,
        *,
        message: str,
        ollama_model_name: str,
        retryable: bool,
        error: BaseException,
        status_code: int | None = None,
    ) -> StreamEvent:
        data: dict[str, JsonValue] = {
            "backend": self.backend_name,
            "model": ollama_model_name,
            "logical_model_id": (self._logical_model_id),
            "retryable": retryable,
            "error_type": (error.__class__.__name__),
        }

        if status_code is not None:
            data["status_code"] = status_code

        return StreamEvent.create(
            type=StreamEventType.ERROR,
            content=message,
            data=data,
        )

    @staticmethod
    async def _raise_for_ollama_error(
        raw: Mapping[str, object],
    ) -> None:
        error_value = raw.get(
            "error",
        )

        if error_value is None:
            return

        if isinstance(
            error_value,
            str,
        ):
            message = error_value.strip()

            if message:
                raise OllamaResponseError(
                    message,
                )

        raise OllamaResponseError(
            "Ollama meldete einen unbekannten Fehler.",
        )


# ============================================================
# Nachrichtenkonvertierung
# ============================================================


def _convert_messages(
    messages: Sequence[ChatMessage],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []

    for message in messages:
        if not message.content.strip():
            continue

        converted_message: dict[str, object] = {
            "role": _convert_message_role(
                message.role,
            ),
            "content": message.content,
        }

        if message.role is MessageRole.TOOL and message.name is not None:
            converted_message["tool_name"] = message.name

        result.append(
            converted_message,
        )

    if not result:
        raise OllamaConfigurationError(
            "Die Ollama-Anfrage enthält keine verwendbare Nachricht.",
        )

    return result


def _convert_message_role(
    role: MessageRole,
) -> str:
    if role is MessageRole.SYSTEM:
        return "system"

    if role is MessageRole.ASSISTANT:
        return "assistant"

    if role is MessageRole.TOOL:
        return "tool"

    return "user"


# ============================================================
# Tool Calling
# ============================================================


def _convert_tools(
    tools: Sequence[ToolDefinition],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []

    known_names: set[str] = set()

    for tool in tools:
        tool_name = tool.name.strip()

        if not tool_name:
            raise OllamaConfigurationError(
                "Ein Tool besitzt keinen gültigen Namen.",
            )

        if tool_name in known_names:
            raise OllamaConfigurationError(
                f"Der Toolname '{tool_name}' wurde mehrfach übergeben.",
            )

        known_names.add(
            tool_name,
        )

        result.append(
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": (tool.description),
                    "parameters": dict(
                        tool.schema,
                    ),
                },
            },
        )

    return result


def _convert_tool_call_events(
    tool_calls: Sequence[object],
    *,
    backend_name: str,
    model_name: str,
) -> list[StreamEvent]:
    events: list[StreamEvent] = []

    for index, raw_tool_call in enumerate(
        tool_calls,
    ):
        if not isinstance(
            raw_tool_call,
            dict,
        ):
            continue

        # Typ-Cast, um Pylance zufrieden zu stellen
        tool_call = _string_key_mapping(cast(dict[object, object], raw_tool_call))

        function = _read_json_object(
            tool_call,
            "function",
        )

        if function is None:
            continue

        name = _read_optional_string_value(
            function,
            "name",
        )

        if not name:
            continue

        raw_arguments = function.get(
            "arguments",
            {},
        )

        # Auch hier casten wir den Typ
        if isinstance(raw_arguments, dict):
            arguments = _normalize_json_object(
                _string_key_mapping(cast(dict[object, object], raw_arguments))
            )
        else:
            arguments = _normalize_json_object(raw_arguments)

        tool_call_id = (
            _read_optional_string_value(
                tool_call,
                "id",
            )
            or f"ollama-tool-call-{index + 1}"
        )

        events.append(
            StreamEvent.create(
                type=StreamEventType.TOOL_CALL,
                data={
                    "id": tool_call_id,
                    "name": name,
                    "arguments": arguments,
                    "backend": backend_name,
                    "model": model_name,
                },
            ),
        )

    return events


# ============================================================
# Structured Output
# ============================================================


def _convert_response_format(
    response_format: ResponseFormat,
) -> object | None:
    if response_format.type == "text":
        return None

    if response_format.type == "json_object":
        return "json"

    if response_format.type == "json_schema":
        if response_format.schema is None:
            raise OllamaConfigurationError(
                "Für response_format.type='json_schema' fehlt das JSON-Schema.",
            )

        return dict(
            response_format.schema,
        )

    raise OllamaConfigurationError(
        f"Nicht unterstütztes response_format.type: '{response_format.type}'.",
    )


# ============================================================
# Usage
# ============================================================


def _create_usage(
    raw: Mapping[str, object],
) -> Usage | None:
    prompt_tokens = _read_non_negative_int_value(
        raw,
        "prompt_eval_count",
    )

    completion_tokens = _read_non_negative_int_value(
        raw,
        "eval_count",
    )

    if prompt_tokens is None and completion_tokens is None:
        return None

    resolved_prompt_tokens = prompt_tokens or 0
    resolved_completion_tokens = completion_tokens or 0

    metadata: JsonObject = {}

    duration_fields = {
        "total_duration": "total_duration_ns",
        "load_duration": "load_duration_ns",
        "prompt_eval_duration": "prompt_eval_duration_ns",
        "eval_duration": "eval_duration_ns",
    }

    for source_key, target_key in duration_fields.items():
        duration = _read_non_negative_int_value(
            raw,
            source_key,
        )

        if duration is not None:
            metadata[target_key] = duration

    return Usage(
        input_tokens=resolved_prompt_tokens,
        output_tokens=resolved_completion_tokens,
        total_tokens=(resolved_prompt_tokens + resolved_completion_tokens),
        metadata=metadata,
    )


# ============================================================
# JSON-Helfer
# ============================================================


def _parse_json_object(
    value: str,
) -> dict[str, object]:
    try:
        parsed: object = json.loads(
            value,
        )

    except json.JSONDecodeError as exc:
        raise OllamaResponseError(
            "Ollama lieferte eine ungültige JSON-Antwort.",
        ) from exc

    if not isinstance(
        parsed,
        dict,
    ):
        raise OllamaResponseError(
            "Ollama lieferte kein JSON-Objekt.",
        )

    return _string_key_mapping(cast(dict[object, object], parsed))


def _string_key_mapping(
    value: Mapping[object, object],
) -> dict[str, object]:
    result: dict[str, object] = {}

    for raw_key, raw_value in value.items():
        if isinstance(
            raw_key,
            str,
        ):
            result[raw_key] = raw_value

    return result


def _read_json_object(
    values: Mapping[str, object],
    key: str,
) -> dict[str, object] | None:
    value = values.get(
        key,
    )

    if not isinstance(
        value,
        dict,
    ):
        return None

    return _string_key_mapping(cast(dict[object, object], value))


def _read_json_array(
    values: Mapping[str, object],
    key: str,
) -> list[object] | None:
    value = values.get(
        key,
    )

    if not isinstance(
        value,
        list,
    ):
        return None

    return list(
        cast(
            list[object],
            value,
        ),
    )


def _read_optional_string_value(
    values: Mapping[str, object],
    key: str,
) -> str | None:
    value = values.get(
        key,
    )

    if not isinstance(
        value,
        str,
    ):
        return None

    return value


def _read_bool_value(
    values: Mapping[str, object],
    key: str,
) -> bool | None:
    value = values.get(
        key,
    )

    if not isinstance(
        value,
        bool,
    ):
        return None

    return value


def _read_non_negative_int_value(
    values: Mapping[str, object],
    key: str,
) -> int | None:
    return _as_non_negative_int(
        values.get(
            key,
        ),
    )


def _normalize_json_object(
    value: object,
) -> JsonObject:
    if isinstance(
        value,
        dict,
    ):
        raw_mapping = _string_key_mapping(cast(dict[object, object], value))

        return cast(
            JsonObject,
            raw_mapping,
        )

    if isinstance(
        value,
        str,
    ):
        try:
            parsed: object = json.loads(
                value,
            )

        except json.JSONDecodeError:
            return {
                "value": value,
            }

        if isinstance(
            parsed,
            dict,
        ):
            return cast(
                JsonObject,
                _string_key_mapping(cast(dict[object, object], parsed)),
            )

        return {
            "value": cast(
                JsonValue,
                parsed,
            ),
        }

    if value is None:
        return {}

    return {
        "value": cast(
            JsonValue,
            value,
        ),
    }


# ============================================================
# Konfigurationshelfer
# ============================================================


def _as_non_negative_int(
    value: object,
) -> int | None:
    if (
        isinstance(
            value,
            int,
        )
        and not isinstance(
            value,
            bool,
        )
        and value >= 0
    ):
        return value

    return None


def _read_optional_string(
    config: JsonMapping,
    key: str,
) -> str | None:
    value = config.get(
        key,
    )

    if not isinstance(
        value,
        str,
    ):
        return None

    normalized = value.strip()

    return normalized or None


def _read_positive_float(
    config: JsonMapping,
    key: str,
    *,
    default: float,
) -> float:
    value = config.get(
        key,
    )

    if isinstance(
        value,
        bool,
    ):
        return default

    if isinstance(
        value,
        int | float,
    ):
        normalized = float(
            value,
        )

        if normalized > 0:
            return normalized

    return default


def _read_positive_int(
    config: JsonMapping,
    key: str,
    *,
    default: int,
) -> int:
    value = config.get(
        key,
    )

    if (
        isinstance(
            value,
            int,
        )
        and not isinstance(
            value,
            bool,
        )
        and value > 0
    ):
        return value

    return default


def _read_bool(
    config: JsonMapping,
    key: str,
    *,
    default: bool,
) -> bool:
    value = config.get(
        key,
    )

    if isinstance(
        value,
        bool,
    ):
        return value

    return default


def _read_optional_bool_or_string(
    config: JsonMapping,
    key: str,
) -> bool | str | None:
    value = config.get(
        key,
    )

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        normalized = value.strip().lower()

        if normalized:
            return normalized

    return None


def _read_http_error_message(
    response: httpx.Response,
) -> str | None:
    try:
        payload: object = response.json()

    except (
        json.JSONDecodeError,
        ValueError,
    ):
        return None

    if not isinstance(
        payload,
        dict,
    ):
        return None

    values = _string_key_mapping(cast(dict[object, object], payload))

    error = values.get(
        "error",
    )

    if not isinstance(
        error,
        str,
    ):
        return None

    normalized = error.strip()

    return normalized or None


# ============================================================
# Factory
# ============================================================


def create_ollama_backend(
    *,
    provider_config: JsonMapping,
    dependencies: ProviderDependencies | None = None,
) -> BaseModelBackend:
    """
    Erstellt ein Ollama-Backend.

    Die Factory bleibt synchron. Netzwerkverbindungen werden erst beim
    ersten tatsächlichen API-Aufruf aufgebaut.
    """

    return OllamaProvider(
        provider_config,
        dependencies=dependencies,
    )


__all__ = [
    "OllamaConfigurationError",
    "OllamaModelNotFoundError",
    "OllamaProvider",
    "OllamaProviderError",
    "OllamaResponseError",
    "create_ollama_backend",
]
