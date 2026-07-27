from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import TypeAlias

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
)
from openai.types.chat import ChatCompletionMessageParam

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


OpenAIMessageList: TypeAlias = list[ChatCompletionMessageParam]
ProviderDependencies: TypeAlias = Mapping[str, object]


DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_API_KEY = "not-required"


class OpenAICompatibleProviderError(RuntimeError):
    """
    Basisklasse für kontrollierte Fehler des
    OpenAI-kompatiblen Providers.
    """


class OpenAICompatibleConfigurationError(
    OpenAICompatibleProviderError,
):
    """
    Die Providerkonfiguration oder Anfrage ist ungültig.
    """


class OpenAICompatibleModelNotFoundError(
    OpenAICompatibleProviderError,
):
    """
    Das angeforderte Modell ist nicht freigegeben.
    """


class OpenAICompatibleRequestError(
    OpenAICompatibleProviderError,
):
    """
    Eine Anfrage an den OpenAI-kompatiblen Endpunkt ist fehlgeschlagen.
    """

    def __init__(
        self,
        *,
        model_id: str,
        reason: str,
        retryable: bool,
        status_code: int | None = None,
    ) -> None:
        self.model_id = model_id
        self.reason = reason
        self.retryable = retryable
        self.status_code = status_code

        super().__init__(
            "OpenAI-kompatible Anfrage für Modell "
            f"'{model_id}' fehlgeschlagen: {reason}",
        )


class OpenAICompatibleProvider(
    BaseModelBackend,
):
    """
    Provider für OpenAI-kompatible Chat-Completions-Endpunkte.

    Typische Einsatzfälle sind lokale oder selbst gehostete Systeme wie:

    - Ollama mit OpenAI-Endpunkt
    - LM Studio
    - vLLM
    - LocalAI
    - llama.cpp Server
    - andere kompatible Gateways

    Modelle werden ausschließlich über die Konfiguration freigegeben.
    """

    def __init__(
        self,
        config: JsonMapping,
    ) -> None:
        self._api_key = _read_optional_string(
            config,
            "api_key",
        )

        self._organization = _read_optional_string(
            config,
            "organization",
        )

        self._project = _read_optional_string(
            config,
            "project",
        )

        self._base_url = _read_optional_string(
            config,
            "base_url",
        )

        self._default_model = (
            _read_optional_string(
                config,
                "default_model",
            )
            or DEFAULT_MODEL
        )

        configured_models = _read_string_sequence(
            config,
            "models",
        )

        if configured_models:
            self._model_ids = tuple(
                dict.fromkeys(
                    configured_models,
                ),
            )
        else:
            self._model_ids = (
                self._default_model,
            )

        if self._default_model not in self._model_ids:
            self._model_ids = (
                self._default_model,
                *self._model_ids,
            )

        self._timeout_seconds = _read_positive_float(
            config,
            "timeout_seconds",
            default=DEFAULT_TIMEOUT_SECONDS,
        )

        self._max_retries = _read_non_negative_int(
            config,
            "max_retries",
            default=DEFAULT_MAX_RETRIES,
        )

        self._client: AsyncOpenAI | None = None

    @property
    def backend_name(
        self,
    ) -> str:
        return "openai_compatible"

    async def is_available(
        self,
    ) -> bool:
        """
        Prüft nur, ob ein Endpunkt konfiguriert ist.

        Eine Netzwerkverbindung wird dabei nicht aufgebaut.
        """

        return self._base_url is not None

    async def list_models(
        self,
    ) -> list[ModelInfo]:
        """
        Liefert ausschließlich die explizit freigegebenen Modelle.
        """

        return [
            self._create_model_info(
                model_id,
            )
            for model_id in self._model_ids
        ]

    async def get_model(
        self,
        model_id: str,
    ) -> ModelInfo:
        """
        Liefert die Beschreibung eines freigegebenen Modells.
        """

        resolved_model_id = self._resolve_model_id(
            model_id,
        )

        return self._create_model_info(
            resolved_model_id,
        )

    def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        """
        Liefert unmittelbar einen asynchronen Antwortstream.
        """

        return self._stream_request(
            request,
        )

    async def shutdown(
        self,
    ) -> None:
        """
        Schließt den wiederverwendeten API-Client.
        """

        client = self._client

        if client is None:
            return

        self._client = None

        try:
            await client.close()

        except Exception:
            logger.exception(
                "Der OpenAI-kompatible Client konnte nicht "
                "sauber geschlossen werden.",
                extra={
                    "backend": self.backend_name,
                },
            )

    async def _stream_request(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        model_id = self._resolve_model_id(
            request.model,
        )

        yield StreamEvent.create(
            type=StreamEventType.START,
            data={
                "backend": self.backend_name,
                "model": model_id,
            },
        )

        try:
            _validate_request(
                request,
            )

            messages = _convert_messages(
                request.messages,
            )

            max_tokens = _resolve_max_tokens(
                request.max_tokens,
            )

            temperature = _normalize_temperature(
                request.temperature,
            )

            top_p = _normalize_optional_top_p(
                request.top_p,
            )

            stop_sequences = _normalize_stop_sequences(
                request.stop,
            )

            client = self._get_client()

            # Die vier expliziten Aufrufe sind bewusst getrennt.
            # Dadurch erkennt Pylance den OpenAI-SDK-Overload mit
            # stream=True und leitet einen typisierten Stream ab.
            if (
                top_p is not None
                and stop_sequences is not None
            ):
                response_stream = (
                    await client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        stop=stop_sequences,
                        stream=True,
                        stream_options={
                            "include_usage": True,
                        },
                    )
                )

            elif top_p is not None:
                response_stream = (
                    await client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        stream=True,
                        stream_options={
                            "include_usage": True,
                        },
                    )
                )

            elif stop_sequences is not None:
                response_stream = (
                    await client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stop=stop_sequences,
                        stream=True,
                        stream_options={
                            "include_usage": True,
                        },
                    )
                )

            else:
                response_stream = (
                    await client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=True,
                        stream_options={
                            "include_usage": True,
                        },
                    )
                )

            usage: Usage | None = None
            finish_reason: str | None = None
            response_id: str | None = None

            async for chunk in response_stream:
                if response_id is None and chunk.id:
                    response_id = chunk.id

                if chunk.usage is not None:
                    usage = Usage(
                        prompt_tokens=(
                            chunk.usage.prompt_tokens
                        ),
                        completion_tokens=(
                            chunk.usage.completion_tokens
                        ),
                        total_tokens=(
                            chunk.usage.total_tokens
                        ),
                    )

                if not chunk.choices:
                    continue

                choice = chunk.choices[0]

                if choice.finish_reason is not None:
                    finish_reason = choice.finish_reason

                content = choice.delta.content

                if content is None or not content:
                    continue

                yield StreamEvent.create(
                    type=StreamEventType.TOKEN,
                    content=content,
                )

            end_data: dict[str, JsonValue] = {
                "backend": self.backend_name,
                "model": model_id,
            }

            if response_id is not None:
                end_data["response_id"] = response_id

            if finish_reason is not None:
                end_data["finish_reason"] = finish_reason

            yield StreamEvent.create(
                type=StreamEventType.END,
                usage=usage,
                data=end_data,
            )

        except APIStatusError as exc:
            status_code: int = exc.status_code

            error = OpenAICompatibleRequestError(
                model_id=model_id,
                reason=str(
                    exc,
                ),
                retryable=_is_retryable_status_code(
                    status_code,
                ),
                status_code=status_code,
            )

            logger.exception(
                "OpenAI-compatible endpoint returned an error status",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "status_code": status_code,
                    "retryable": error.retryable,
                },
            )

            yield _create_error_event(
                error,
            )

        except APITimeoutError as exc:
            error = OpenAICompatibleRequestError(
                model_id=model_id,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "OpenAI-compatible request timed out",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": True,
                },
            )

            yield _create_error_event(
                error,
            )

        except APIConnectionError as exc:
            error = OpenAICompatibleRequestError(
                model_id=model_id,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "OpenAI-compatible connection failed",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": True,
                },
            )

            yield _create_error_event(
                error,
            )

        except OpenAICompatibleProviderError as exc:
            logger.exception(
                "OpenAI-compatible provider rejected the request",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "error_type": type(exc).__name__,
                },
            )

            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=str(
                    exc,
                ),
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": False,
                    "error_type": type(exc).__name__,
                },
            )

        except Exception as exc:
            logger.exception(
                "Unexpected OpenAI-compatible provider error",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "error_type": type(exc).__name__,
                },
            )

            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=(
                    "Bei der OpenAI-kompatiblen Anfrage ist ein "
                    "unerwarteter Fehler aufgetreten."
                ),
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": False,
                    "error_type": type(exc).__name__,
                },
            )

    def _get_client(
        self,
    ) -> AsyncOpenAI:
        """
        Erstellt den Client bei der ersten tatsächlichen Verwendung.

        Der Konstruktor wird explizit aufgerufen, damit keine
        Typinformationen durch ein dynamisches kwargs-Dictionary
        verloren gehen.
        """

        if self._base_url is None:
            raise OpenAICompatibleConfigurationError(
                "Die base_url des OpenAI-kompatiblen "
                "Endpunkts fehlt.",
            )

        if self._client is not None:
            return self._client

        client = AsyncOpenAI(
            api_key=(
                self._api_key
                or DEFAULT_API_KEY
            ),
            organization=self._organization,
            project=self._project,
            base_url=self._base_url,
            timeout=self._timeout_seconds,
            max_retries=self._max_retries,
        )

        self._client = client

        return client

    def _resolve_model_id(
        self,
        requested_model_id: str,
    ) -> str:
        normalized_model_id = requested_model_id.strip()

        model_id = (
            normalized_model_id
            if normalized_model_id
            else self._default_model
        )

        if model_id not in self._model_ids:
            raise OpenAICompatibleModelNotFoundError(
                f"Das OpenAI-kompatible Modell '{model_id}' "
                "ist nicht freigegeben.",
            )

        return model_id

    def _create_model_info(
        self,
        model_id: str,
    ) -> ModelInfo:
        capabilities: set[ModelCapability] = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.STREAMING,
        }

        metadata: dict[str, JsonValue] = {
            "configured": self._base_url is not None,
            "remote": True,
        }

        if self._base_url is not None:
            metadata["base_url"] = self._base_url

        return ModelInfo.create(
            id=model_id,
            backend=self.backend_name,
            display_name=model_id,
            provider="OpenAI-kompatibel",
            capabilities=capabilities,
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            metadata=metadata,
        )


def _validate_request(
    request: GenerationRequest,
) -> None:
    """
    Lehnt noch nicht implementierte Vertragsfunktionen sichtbar ab.
    """

    if request.tools:
        raise OpenAICompatibleConfigurationError(
            "Tool-Aufrufe sind in dieser OpenAI-kompatiblen "
            "Provider-Version noch nicht implementiert.",
        )

    if request.tool_choice is not None:
        raise OpenAICompatibleConfigurationError(
            "tool_choice wird in dieser OpenAI-kompatiblen "
            "Provider-Version noch nicht unterstützt.",
        )


def _convert_messages(
    messages: Sequence[ChatMessage],
) -> OpenAIMessageList:
    """
    Übersetzt interne Nachrichten in das OpenAI-Nachrichtenformat.
    """

    converted_messages: OpenAIMessageList = []

    for message in messages:
        content = message.content.strip()

        if not content:
            continue

        if message.role is MessageRole.SYSTEM:
            converted_messages.append(
                {
                    "role": "system",
                    "content": content,
                },
            )
            continue

        if message.role is MessageRole.ASSISTANT:
            converted_messages.append(
                {
                    "role": "assistant",
                    "content": content,
                },
            )
            continue

        if message.role is MessageRole.TOOL:
            tool_call_id = (
                message.tool_call_id.strip()
                if message.tool_call_id is not None
                else ""
            )

            if tool_call_id:
                converted_messages.append(
                    {
                        "role": "tool",
                        "content": content,
                        "tool_call_id": tool_call_id,
                    },
                )
            else:
                converted_messages.append(
                    {
                        "role": "user",
                        "content": _format_tool_result_as_text(
                            message,
                            content,
                        ),
                    },
                )

            continue

        converted_messages.append(
            {
                "role": "user",
                "content": content,
            },
        )

    if not converted_messages:
        raise OpenAICompatibleConfigurationError(
            "Die OpenAI-kompatible Anfrage enthält keine "
            "verwendbare Nachricht.",
        )

    return converted_messages


def _format_tool_result_as_text(
    message: ChatMessage,
    content: str,
) -> str:
    """
    Stellt Tool-Ergebnisse ohne gültige Tool-ID als Benutzertext dar.
    """

    if message.name is None:
        return f"Tool-Ergebnis:\n{content}"

    normalized_name = message.name.strip()

    if not normalized_name:
        return f"Tool-Ergebnis:\n{content}"

    return (
        f"Tool-Ergebnis von '{normalized_name}':\n"
        f"{content}"
    )


def _create_error_event(
    error: OpenAICompatibleRequestError,
) -> StreamEvent:
    data: dict[str, JsonValue] = {
        "backend": "openai_compatible",
        "model": error.model_id,
        "retryable": error.retryable,
        "error_type": type(error).__name__,
    }

    if error.status_code is not None:
        data["status_code"] = error.status_code

    return StreamEvent.create(
        type=StreamEventType.ERROR,
        content=str(
            error,
        ),
        data=data,
    )


def _resolve_max_tokens(
    value: int | None,
) -> int:
    if value is None:
        return DEFAULT_MAX_TOKENS

    if value <= 0:
        raise OpenAICompatibleConfigurationError(
            "max_tokens muss größer als null sein.",
        )

    return value


def _normalize_temperature(
    value: float,
) -> float:
    if value < 0.0:
        return 0.0

    if value > 2.0:
        return 2.0

    return value


def _normalize_optional_top_p(
    value: float | None,
) -> float | None:
    if value is None:
        return None

    if value <= 0.0:
        raise OpenAICompatibleConfigurationError(
            "top_p muss größer als null sein.",
        )

    if value > 1.0:
        raise OpenAICompatibleConfigurationError(
            "top_p darf nicht größer als 1 sein.",
        )

    return value


def _normalize_stop_sequences(
    value: list[str] | None,
) -> list[str] | None:
    if value is None:
        return None

    normalized: list[str] = []

    for item in value:
        normalized_item = item.strip()

        if normalized_item:
            normalized.append(
                normalized_item,
            )

    return normalized or None


def _is_retryable_status_code(
    status_code: int,
) -> bool:
    return status_code in {
        408,
        409,
        429,
        500,
        502,
        503,
        504,
    }


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


def _read_string_sequence(
    config: JsonMapping,
    key: str,
) -> tuple[str, ...]:
    value = config.get(
        key,
    )

    if not isinstance(
        value,
        list,
    ):
        return ()

    result: list[str] = []

    for item in value:
        if not isinstance(
            item,
            str,
        ):
            continue

        normalized = item.strip()

        if normalized:
            result.append(
                normalized,
            )

    return tuple(
        result,
    )


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
        converted = float(
            value,
        )

        if converted > 0.0:
            return converted

    return default


def _read_non_negative_int(
    config: JsonMapping,
    key: str,
    *,
    default: int,
) -> int:
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
        int,
    ) and value >= 0:
        return value

    return default


def create_openai_compatible_backend(
    *,
    provider_config: JsonMapping,
    dependencies: ProviderDependencies | None = None,
) -> BaseModelBackend:
    """
    Factory für die feste Modell-Provider-Registry.
    """

    del dependencies

    return OpenAICompatibleProvider(
        provider_config,
    )


__all__ = [
    "OpenAICompatibleConfigurationError",
    "OpenAICompatibleModelNotFoundError",
    "OpenAICompatibleProvider",
    "OpenAICompatibleProviderError",
    "OpenAICompatibleRequestError",
    "create_openai_compatible_backend",
]