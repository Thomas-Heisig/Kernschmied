# F:\Kernschmied\backend\app\models\providers\openai.py

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


class OpenAIProviderError(RuntimeError):
    """
    Basisklasse für kontrollierte Fehler des OpenAI-Providers.
    """


class OpenAIConfigurationError(
    OpenAIProviderError,
):
    """
    Die Provider-Konfiguration oder Anfrage ist ungültig.
    """


class OpenAIModelNotFoundError(
    OpenAIProviderError,
):
    """
    Das angeforderte OpenAI-Modell ist nicht freigegeben.
    """


class OpenAIRequestError(
    OpenAIProviderError,
):
    """
    Eine Anfrage an OpenAI ist fehlgeschlagen.
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
            f"OpenAI-Anfrage für Modell "
            f"'{model_id}' fehlgeschlagen: {reason}",
        )


class OpenAIProvider(
    BaseModelBackend,
):
    """
    Backend für die OpenAI Chat-Completions-Schnittstelle.

    Unterstützte Konfigurationswerte:

    - api_key:
      API-Schlüssel für OpenAI.

    - organization:
      Optionale OpenAI-Organisations-ID.

    - project:
      Optionale OpenAI-Projekt-ID.

    - base_url:
      Optionaler alternativer API-Endpunkt.

    - default_model:
      Standardmäßig zu verwendendes Modell.

    - models:
      Explizite Liste freigegebener Modell-IDs.

    - timeout_seconds:
      Anfrage-Timeout in Sekunden.

    - max_retries:
      Anzahl automatischer SDK-Wiederholungen.

    Modelle werden niemals automatisch freigegeben. Jede Modell-ID muss
    über ``default_model`` oder ``models`` explizit konfiguriert sein.
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
        return "openai"

    async def is_available(
        self,
    ) -> bool:
        """
        Prüft ausschließlich die lokale Konfiguration.

        Es wird bewusst keine Netzwerk- oder Testanfrage ausgeführt.
        """

        return self._api_key is not None

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
        Liefert unmittelbar einen AsyncIterator der Modellantwort.
        """

        return self._stream_request(
            request,
        )

    async def shutdown(
        self,
    ) -> None:
        """
        Schließt den wiederverwendeten OpenAI-Client.
        """

        client = self._client

        if client is None:
            return

        self._client = None

        try:
            await client.close()

        except Exception:
            logger.exception(
                "Der OpenAI-Client konnte nicht sauber "
                "geschlossen werden.",
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
            self._validate_request(
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

            # Die Aufrufe werden absichtlich explizit getrennt.
            #
            # Ein dynamisches ``dict[str, object]`` mit ``**kwargs``
            # verhindert, dass Pylance den Overload mit ``stream=True``
            # erkennt. Das Ergebnis würde dadurch als Unknown behandelt.
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
                    usage = _create_usage(
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

            error = OpenAIRequestError(
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
                "OpenAI returned an error status",
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
            error = OpenAIRequestError(
                model_id=model_id,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "OpenAI request timed out",
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
            error = OpenAIRequestError(
                model_id=model_id,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "OpenAI connection failed",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": True,
                },
            )

            yield _create_error_event(
                error,
            )

        except OpenAIProviderError as exc:
            logger.exception(
                "OpenAI provider rejected the request",
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
                "Unexpected OpenAI provider error",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "error_type": type(exc).__name__,
                },
            )

            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=(
                    "Bei der OpenAI-Anfrage ist ein "
                    "unerwarteter Fehler aufgetreten."
                ),
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": False,
                    "error_type": type(exc).__name__,
                },
            )

    def _validate_request(
        self,
        request: GenerationRequest,
    ) -> None:
        """
        Lehnt noch nicht übersetzte Vertragsfunktionen sichtbar ab.

        Tools dürfen nicht stillschweigend ignoriert werden.
        """

        if request.tools:
            raise OpenAIConfigurationError(
                "OpenAI-Tool-Aufrufe sind in dieser "
                "Provider-Version noch nicht implementiert.",
            )

        if request.tool_choice is not None:
            raise OpenAIConfigurationError(
                "OpenAI tool_choice wird in dieser "
                "Provider-Version noch nicht unterstützt.",
            )

    def _get_client(
        self,
    ) -> AsyncOpenAI:
        """
        Erstellt den Client bei der ersten tatsächlichen Verwendung.

        Die optionalen Parameter werden explizit übergeben. Dadurch
        bleibt der Konstruktoraufruf vollständig typisiert und benötigt
        weder ``dict[str, object]`` noch ``type: ignore``.
        """

        if self._api_key is None:
            raise OpenAIConfigurationError(
                "Der OpenAI-API-Key fehlt.",
            )

        if self._client is not None:
            return self._client

        client = AsyncOpenAI(
            api_key=self._api_key,
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
        """
        Löst die Modell-ID gegen die freigegebenen Modelle auf.
        """

        normalized_model_id = requested_model_id.strip()

        model_id = (
            normalized_model_id
            if normalized_model_id
            else self._default_model
        )

        if model_id not in self._model_ids:
            raise OpenAIModelNotFoundError(
                f"Das OpenAI-Modell '{model_id}' "
                "ist nicht freigegeben.",
            )

        return model_id

    def _create_model_info(
        self,
        model_id: str,
    ) -> ModelInfo:
        """
        Erstellt die öffentliche Modellbeschreibung.
        """

        capabilities: set[ModelCapability] = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.STREAMING,
        }

        return ModelInfo.create(
            id=model_id,
            backend=self.backend_name,
            display_name=model_id,
            provider="OpenAI",
            capabilities=capabilities,
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            metadata={
                "configured": True,
                "remote": True,
            },
        )


def _convert_messages(
    messages: Sequence[ChatMessage],
) -> OpenAIMessageList:
    """
    Übersetzt interne Chatnachrichten in OpenAI-Nachrichten.

    Leere Nachrichten werden nicht übertragen. Tool-Ergebnisse ohne
    gültige Tool-Aufruf-ID werden sichtbar als Benutzertext dargestellt,
    statt stillschweigend als ungültige Tool-Nachricht versendet zu
    werden.
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
        raise OpenAIConfigurationError(
            "Die OpenAI-Anfrage enthält keine "
            "verwendbare Nachricht.",
        )

    return converted_messages


def _format_tool_result_as_text(
    message: ChatMessage,
    content: str,
) -> str:
    """
    Stellt ein Tool-Ergebnis ohne gültige Aufruf-ID als Text dar.
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


def _create_usage(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> Usage:
    """
    Übersetzt OpenAI-Nutzungsdaten in den Backendvertrag.
    """

    return Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def _create_error_event(
    error: OpenAIRequestError,
) -> StreamEvent:
    """
    Erstellt ein einheitliches Fehlerereignis.
    """

    data: dict[str, JsonValue] = {
        "backend": "openai",
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
    """
    Validiert die maximale Ausgabelänge.
    """

    if value is None:
        return DEFAULT_MAX_TOKENS

    if value <= 0:
        raise OpenAIConfigurationError(
            "max_tokens muss größer als null sein.",
        )

    return value


def _normalize_temperature(
    value: float,
) -> float:
    """
    Begrenzt die Temperatur auf den unterstützten Wertebereich.
    """

    if value < 0.0:
        return 0.0

    if value > 2.0:
        return 2.0

    return value


def _normalize_optional_top_p(
    value: float | None,
) -> float | None:
    """
    Validiert den optionalen Top-p-Wert.
    """

    if value is None:
        return None

    if value <= 0.0:
        raise OpenAIConfigurationError(
            "top_p muss größer als null sein.",
        )

    if value > 1.0:
        raise OpenAIConfigurationError(
            "top_p darf nicht größer als 1 sein.",
        )

    return value


def _normalize_stop_sequences(
    value: list[str] | None,
) -> list[str] | None:
    """
    Bereinigt optionale Stop-Sequenzen.
    """

    if value is None:
        return None

    normalized: list[str] = []

    for item in value:
        normalized_item = item.strip()

        if normalized_item:
            normalized.append(
                normalized_item,
            )

    if not normalized:
        return None

    return normalized


def _is_retryable_status_code(
    status_code: int,
) -> bool:
    """
    Kennzeichnet typischerweise vorübergehende HTTP-Fehler.
    """

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
    """
    Liest einen optionalen nichtleeren String.
    """

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
    """
    Liest eine JSON-Liste nichtleerer Strings.
    """

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
    """
    Liest eine positive Fließkommazahl.
    """

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
    """
    Liest eine nichtnegative Ganzzahl.
    """

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


def create_openai_backend(
    *,
    provider_config: JsonMapping,
    dependencies: ProviderDependencies | None = None,
) -> BaseModelBackend:
    """
    Factory für die feste Modell-Provider-Registry.

    Noch nicht benötigte Abhängigkeiten werden ausdrücklich verworfen.
    Die Signatur bleibt mit dem gemeinsamen Registry-Vertrag kompatibel.
    """

    del dependencies

    return OpenAIProvider(
        provider_config,
    )


__all__ = [
    "OpenAIConfigurationError",
    "OpenAIModelNotFoundError",
    "OpenAIProvider",
    "OpenAIProviderError",
    "OpenAIRequestError",
    "create_openai_backend",
]