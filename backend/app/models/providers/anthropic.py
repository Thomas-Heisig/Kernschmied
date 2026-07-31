# F:\Kernschmied\backend\app\models\providers\anthropic.py

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Sequence
from typing import TypeAlias

from anthropic import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncAnthropic,
)
from anthropic.types import MessageParam

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


AnthropicMessageList: TypeAlias = list[MessageParam]


DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 2


class AnthropicProviderError(RuntimeError):
    """
    Basisklasse für kontrollierte Fehler des Anthropic-Providers.
    """


class AnthropicConfigurationError(AnthropicProviderError):
    """
    Die Provider-Konfiguration ist unvollständig oder ungültig.
    """


class AnthropicModelNotFoundError(AnthropicProviderError):
    """
    Das angeforderte Modell ist für diesen Provider nicht freigegeben.
    """


class AnthropicRequestError(AnthropicProviderError):
    """
    Eine Anfrage an die Anthropic-API ist fehlgeschlagen.
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
            f"Anthropic-Anfrage für Modell '{model_id}' fehlgeschlagen: {reason}",
        )


class AnthropicProvider(BaseModelBackend):
    """
    Modell-Backend für die Anthropic Messages API.

    Unterstützte Konfigurationswerte:

    - api_key:
      Anthropic-API-Key.

    - default_model:
      Standardmodell des Providers.

    - models:
      Explizite Liste der freigegebenen Modell-IDs.

    - base_url:
      Optionale alternative API-Basisadresse.

    - timeout_seconds:
      Anfrage-Timeout in Sekunden.

    - max_retries:
      Anzahl automatischer Wiederholungen des SDK.

    Die Freigabe eines Modells erfolgt ausschließlich über die
    Provider-Konfiguration. Eine entfernte Modellerkennung führt
    nicht automatisch zu einer Freigabe.
    """

    def __init__(
        self,
        config: JsonMapping,
    ) -> None:
        self._api_key = _read_optional_string(
            config,
            "api_key",
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
            self._model_ids = (self._default_model,)

        if self._default_model not in self._model_ids:
            self._model_ids = (
                self._default_model,
                *self._model_ids,
            )

        self._base_url = _read_optional_string(
            config,
            "base_url",
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

        self._client: AsyncAnthropic | None = None

    @property
    def backend_name(self) -> str:
        return "anthropic"

    async def is_available(self) -> bool:
        """
        Prüft, ob die erforderliche lokale Konfiguration vorhanden ist.

        Es wird bewusst keine externe Testanfrage ausgeführt.
        """

        return self._api_key is not None

    async def list_models(
        self,
    ) -> list[ModelInfo]:
        """
        Liefert alle explizit konfigurierten Anthropic-Modelle.
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

        normalized_model_id = model_id.strip()

        if not normalized_model_id:
            raise AnthropicModelNotFoundError(
                "Die Modell-ID darf nicht leer sein.",
            )

        if normalized_model_id not in self._model_ids:
            raise AnthropicModelNotFoundError(
                f"Das Anthropic-Modell '{normalized_model_id}' "
                "ist für diesen Provider nicht freigegeben.",
            )

        return self._create_model_info(
            normalized_model_id,
        )

    def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        """
        Liefert unmittelbar einen AsyncIterator für die Modellantwort.
        """

        return self._stream_request(
            request,
        )

    async def shutdown(self) -> None:
        """
        Schließt den wiederverwendeten Anthropic-HTTP-Client.
        """

        client = self._client

        if client is None:
            return

        self._client = None

        try:
            await client.close()

        except Exception:
            logger.exception(
                "Der Anthropic-Client konnte nicht sauber geschlossen werden.",
                extra={
                    "backend": self.backend_name,
                },
            )

    async def _stream_request(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        """
        Führt den eigentlichen Anthropic-Modellaufruf aus.
        """

        model_id = self._resolve_model_id(
            request.model,
        )

        system_prompt, messages = _convert_messages(
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

            client = self._get_client()

            if top_p is not None and stop_sequences is not None:
                stream_manager = client.messages.stream(
                    model=model_id,
                    messages=messages,
                    system=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop_sequences=stop_sequences,
                )

            elif top_p is not None:
                stream_manager = client.messages.stream(
                    model=model_id,
                    messages=messages,
                    system=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                )

            elif stop_sequences is not None:
                stream_manager = client.messages.stream(
                    model=model_id,
                    messages=messages,
                    system=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop_sequences=stop_sequences,
                )

            else:
                stream_manager = client.messages.stream(
                    model=model_id,
                    messages=messages,
                    system=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            async with stream_manager as response_stream:
                async for text in response_stream.text_stream:
                    if not text:
                        continue

                    yield StreamEvent.create(
                        type=StreamEventType.TOKEN,
                        content=text,
                    )

                final_message = await response_stream.get_final_message()

            usage = _create_usage(
                input_tokens=final_message.usage.input_tokens,
                output_tokens=final_message.usage.output_tokens,
            )

            end_data: dict[str, JsonValue] = {
                "backend": self.backend_name,
                "model": model_id,
            }

            if final_message.stop_reason is not None:
                end_data["stop_reason"] = final_message.stop_reason

            if final_message.stop_sequence is not None:
                end_data["stop_sequence"] = final_message.stop_sequence

            # Korrektur: StreamEventType.END existiert nicht, verwende COMPLETE
            yield StreamEvent.create(
                type=StreamEventType.COMPLETE,
                usage=usage,
                data=end_data,
            )

        except APIStatusError as exc:
            status_code: int = exc.status_code

            retryable = _is_retryable_status_code(
                status_code,
            )

            error = AnthropicRequestError(
                model_id=model_id,
                reason=str(
                    exc,
                ),
                retryable=retryable,
                status_code=status_code,
            )

            logger.exception(
                "Anthropic API returned an error status",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "status_code": status_code,
                    "retryable": retryable,
                },
            )

            yield _create_error_event(
                error,
            )

        except APITimeoutError as exc:
            error = AnthropicRequestError(
                model_id=model_id,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "Anthropic request timed out",
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
            error = AnthropicRequestError(
                model_id=model_id,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "Anthropic connection failed",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "retryable": True,
                },
            )

            yield _create_error_event(
                error,
            )

        except AnthropicProviderError as exc:
            logger.exception(
                "Anthropic provider rejected the request",
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
                "Unexpected Anthropic provider error",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "error_type": type(exc).__name__,
                },
            )

            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=(
                    "Bei der Anthropic-Anfrage ist ein unerwarteter Fehler aufgetreten."
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
        Validiert Funktionen, die dieser Provider noch nicht abbildet.

        Tools werden nicht stillschweigend ignoriert. Das verhindert,
        dass ein Modellaufruf scheinbar erfolgreich ausgeführt wird,
        obwohl die angeforderten Tool-Verträge nicht übertragen wurden.
        """

        if request.tools:
            raise AnthropicConfigurationError(
                "Anthropic-Tool-Aufrufe sind in dieser "
                "Provider-Version noch nicht implementiert.",
            )

        if request.tool_choice is not None:
            raise AnthropicConfigurationError(
                "Anthropic tool_choice wird in dieser "
                "Provider-Version noch nicht unterstützt.",
            )

    def _get_client(self) -> AsyncAnthropic:
        """
        Erstellt den Anthropic-Client bei der ersten Verwendung.
        """

        if self._api_key is None:
            raise AnthropicConfigurationError(
                "Der Anthropic-API-Key fehlt.",
            )

        if self._client is not None:
            return self._client

        if self._base_url is not None:
            client = AsyncAnthropic(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                max_retries=self._max_retries,
            )

        else:
            client = AsyncAnthropic(
                api_key=self._api_key,
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
        Löst die angeforderte Modell-ID gegen die Freigabeliste auf.
        """

        normalized_model_id = requested_model_id.strip()

        model_id = normalized_model_id if normalized_model_id else self._default_model

        if model_id not in self._model_ids:
            raise AnthropicModelNotFoundError(
                f"Das Anthropic-Modell '{model_id}' ist nicht freigegeben.",
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
            provider="Anthropic",
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
) -> tuple[str, AnthropicMessageList]:
    """
    Konvertiert den internen Nachrichtenvertrag für Anthropic.

    Anthropic erwartet Systemanweisungen getrennt vom normalen
    Nachrichtenarray. Im Array sind nur die Rollen `user` und
    `assistant` zulässig.

    Tool-Ergebnisse werden in dieser Provider-Version als eindeutig
    markierter Benutzertext übertragen. Native Tool-Definitionen und
    Tool-Aufrufe werden dagegen nicht unterstützt.
    """

    system_parts: list[str] = []
    converted_messages: AnthropicMessageList = []

    for message in messages:
        content = message.content.strip()

        if not content:
            continue

        if message.role is MessageRole.SYSTEM:
            system_parts.append(
                content,
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
            converted_messages.append(
                {
                    "role": "user",
                    "content": _format_tool_result(
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
        raise AnthropicConfigurationError(
            "Die Anthropic-Anfrage enthält keine "
            "verwendbare Benutzer- oder Assistentennachricht.",
        )

    system_prompt = "\n\n".join(
        system_parts,
    )

    return system_prompt, converted_messages


def _format_tool_result(
    message: ChatMessage,
    content: str,
) -> str:
    """
    Formatiert ein bereits vorhandenes Tool-Ergebnis als Text.
    """

    identifiers: list[str] = []

    if message.name is not None and message.name.strip():
        identifiers.append(
            f"Name: {message.name.strip()}",
        )

    if message.tool_call_id is not None and message.tool_call_id.strip():
        identifiers.append(
            f"Aufruf-ID: {message.tool_call_id.strip()}",
        )

    if identifiers:
        header = ", ".join(
            identifiers,
        )

        return f"Tool-Ergebnis ({header}):\n{content}"

    return f"Tool-Ergebnis:\n{content}"


def _create_usage(
    *,
    input_tokens: int,
    output_tokens: int,
) -> Usage:
    """
    Übersetzt Anthropic-Nutzungsdaten in den Backendvertrag.
    """

    # Korrektur: Verwende korrekte Feldnamen
    return Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        metadata={},  # Anthropic liefert keine zusätzlichen Metadaten
    )


def _create_error_event(
    error: AnthropicRequestError,
) -> StreamEvent:
    """
    Erstellt ein strukturiertes Fehlerereignis.
    """

    data: dict[str, JsonValue] = {
        "backend": "anthropic",
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
    Validiert die maximale Anzahl auszugebender Tokens.
    """

    if value is None:
        return DEFAULT_MAX_TOKENS

    if value <= 0:
        raise AnthropicConfigurationError(
            "max_tokens muss größer als null sein.",
        )

    return value


def _normalize_temperature(
    value: float,
) -> float:
    """
    Begrenzt die Temperatur auf den Anthropic-Wertebereich.
    """

    if value < 0.0:
        return 0.0

    if value > 1.0:
        return 1.0

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
        raise AnthropicConfigurationError(
            "top_p muss größer als null sein.",
        )

    if value > 1.0:
        raise AnthropicConfigurationError(
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
        stripped_item = item.strip()

        if stripped_item:
            normalized.append(
                stripped_item,
            )

    if not normalized:
        return None

    return normalized


def _is_retryable_status_code(
    status_code: int,
) -> bool:
    """
    Kennzeichnet vorübergehende HTTP-Fehler.
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

    if (
        isinstance(
            value,
            int,
        )
        and value >= 0
    ):
        return value

    return default
