# F:\Kernschmied\backend\app\models\providers\azure_openai.py

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import TypeAlias

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncAzureOpenAI,
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


AzureMessageList: TypeAlias = list[ChatCompletionMessageParam]
ProviderDependencies: TypeAlias = Mapping[str, object]


DEFAULT_API_VERSION = "2024-10-21"
DEFAULT_DEPLOYMENT = "gpt-4o-mini"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 2


class AzureOpenAIProviderError(RuntimeError):
    """
    Basisklasse für kontrollierte Fehler des Azure-OpenAI-Providers.
    """


class AzureOpenAIConfigurationError(
    AzureOpenAIProviderError,
):
    """
    Die Provider-Konfiguration oder Anfrage ist ungültig.
    """


class AzureOpenAIModelNotFoundError(
    AzureOpenAIProviderError,
):
    """
    Das angeforderte Azure-Deployment ist nicht freigegeben.
    """


class AzureOpenAIRequestError(
    AzureOpenAIProviderError,
):
    """
    Eine Anfrage an Azure OpenAI ist fehlgeschlagen.
    """

    def __init__(
        self,
        *,
        deployment_id: str,
        reason: str,
        retryable: bool,
        status_code: int | None = None,
    ) -> None:
        self.deployment_id = deployment_id
        self.reason = reason
        self.retryable = retryable
        self.status_code = status_code

        super().__init__(
            f"Azure-OpenAI-Anfrage für Deployment "
            f"'{deployment_id}' fehlgeschlagen: {reason}",
        )


class AzureOpenAIProvider(BaseModelBackend):
    """
    Backend für Azure OpenAI Chat Completions.

    Unterstützte Konfigurationswerte:

    - endpoint:
      Azure-OpenAI-Endpunkt, beispielsweise
      `https://example.openai.azure.com`.

    - api_key:
      API-Key der Azure-OpenAI-Ressource.

    - api_version:
      Zu verwendende Azure-API-Version.

    - default_model:
      Standard-Deployment-Name.

    - models:
      Explizite Liste freigegebener Deployment-Namen.

    - timeout_seconds:
      Anfrage-Timeout in Sekunden.

    - max_retries:
      Anzahl automatischer SDK-Wiederholungen.

    Wichtig:

    Der Wert `model` im Modellvertrag bezeichnet für Azure OpenAI
    grundsätzlich den Deployment-Namen. Der technische Basismodellname
    kann davon abweichen.
    """

    def __init__(
        self,
        config: JsonMapping,
    ) -> None:
        self._endpoint = _read_optional_string(
            config,
            "endpoint",
        )

        self._api_key = _read_optional_string(
            config,
            "api_key",
        )

        self._api_version = (
            _read_optional_string(
                config,
                "api_version",
            )
            or DEFAULT_API_VERSION
        )

        self._default_deployment = (
            _read_optional_string(
                config,
                "default_model",
            )
            or DEFAULT_DEPLOYMENT
        )

        configured_deployments = _read_string_sequence(
            config,
            "models",
        )

        if configured_deployments:
            self._deployment_ids = tuple(
                dict.fromkeys(
                    configured_deployments,
                ),
            )
        else:
            self._deployment_ids = (self._default_deployment,)

        if self._default_deployment not in self._deployment_ids:
            self._deployment_ids = (
                self._default_deployment,
                *self._deployment_ids,
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

        self._client: AsyncAzureOpenAI | None = None

    @property
    def backend_name(self) -> str:
        return "azure_openai"

    # ========================================================
    # Implementierung der abstrakten Methode get_model_info
    # ========================================================

    def get_model_info(self) -> ModelInfo:
        """
        Gibt die Modellinformationen des Backends zurück.
        Für Azure OpenAI verwenden wir das Standard-Deployment.
        """
        return self._create_model_info(self._default_deployment)

    async def is_available(self) -> bool:
        """
        Prüft ausschließlich die erforderliche lokale Konfiguration.

        Es wird bewusst keine Netzwerk- oder Testanfrage ausgeführt.
        """

        return self._endpoint is not None and self._api_key is not None

    async def list_models(
        self,
    ) -> list[ModelInfo]:
        """
        Liefert die explizit freigegebenen Azure-Deployments.
        """

        return [
            self._create_model_info(
                deployment_id,
            )
            for deployment_id in self._deployment_ids
        ]

    async def get_model(
        self,
        model_id: str,
    ) -> ModelInfo:
        """
        Liefert Informationen zu einem freigegebenen Deployment.
        """

        deployment_id = model_id.strip()

        if not deployment_id:
            raise AzureOpenAIModelNotFoundError(
                "Der Azure-Deployment-Name darf nicht leer sein.",
            )

        if deployment_id not in self._deployment_ids:
            raise AzureOpenAIModelNotFoundError(
                f"Das Azure-OpenAI-Deployment '{deployment_id}' ist nicht freigegeben.",
            )

        return self._create_model_info(
            deployment_id,
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

    async def shutdown(self) -> None:
        """
        Schließt den wiederverwendeten Azure-OpenAI-Client.
        """

        client = self._client

        if client is None:
            return

        self._client = None

        try:
            await client.close()

        except Exception:
            logger.exception(
                "Der Azure-OpenAI-Client konnte nicht sauber geschlossen werden.",
                extra={
                    "backend": self.backend_name,
                },
            )

    async def _stream_request(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        deployment_id = self._resolve_deployment_id(
            request.model,
        )

        yield StreamEvent.create(
            type=StreamEventType.START,
            data={
                "backend": self.backend_name,
                "model": deployment_id,
                "deployment": deployment_id,
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

            if top_p is not None and stop_sequences is not None:
                response_stream = await client.chat.completions.create(
                    model=deployment_id,
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

            elif top_p is not None:
                response_stream = await client.chat.completions.create(
                    model=deployment_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stream=True,
                    stream_options={
                        "include_usage": True,
                    },
                )

            elif stop_sequences is not None:
                response_stream = await client.chat.completions.create(
                    model=deployment_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop_sequences,
                    stream=True,
                    stream_options={
                        "include_usage": True,
                    },
                )

            else:
                response_stream = await client.chat.completions.create(
                    model=deployment_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                    stream_options={
                        "include_usage": True,
                    },
                )

            usage: Usage | None = None
            finish_reason: str | None = None
            response_id: str | None = None

            async for chunk in response_stream:
                if response_id is None and chunk.id:
                    response_id = chunk.id

                if chunk.usage is not None:
                    usage = _create_usage(
                        input_tokens=chunk.usage.prompt_tokens,
                        output_tokens=chunk.usage.completion_tokens,
                        total_tokens=chunk.usage.total_tokens,
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
                "model": deployment_id,
                "deployment": deployment_id,
            }

            if response_id is not None:
                end_data["response_id"] = response_id

            if finish_reason is not None:
                end_data["finish_reason"] = finish_reason

            # Korrektur: StreamEventType.END durch COMPLETE ersetzen
            yield StreamEvent.create(
                type=StreamEventType.COMPLETE,
                usage=usage,
                data=end_data,
            )

        except APIStatusError as exc:
            status_code: int = exc.status_code

            error = AzureOpenAIRequestError(
                deployment_id=deployment_id,
                reason=str(
                    exc,
                ),
                retryable=_is_retryable_status_code(
                    status_code,
                ),
                status_code=status_code,
            )

            logger.exception(
                "Azure OpenAI returned an error status",
                extra={
                    "backend": self.backend_name,
                    "model": deployment_id,
                    "status_code": status_code,
                    "retryable": error.retryable,
                },
            )

            yield _create_error_event(
                error,
            )

        except APITimeoutError as exc:
            error = AzureOpenAIRequestError(
                deployment_id=deployment_id,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "Azure OpenAI request timed out",
                extra={
                    "backend": self.backend_name,
                    "model": deployment_id,
                    "retryable": True,
                },
            )

            yield _create_error_event(
                error,
            )

        except APIConnectionError as exc:
            error = AzureOpenAIRequestError(
                deployment_id=deployment_id,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "Azure OpenAI connection failed",
                extra={
                    "backend": self.backend_name,
                    "model": deployment_id,
                    "retryable": True,
                },
            )

            yield _create_error_event(
                error,
            )

        except AzureOpenAIProviderError as exc:
            logger.exception(
                "Azure OpenAI provider rejected the request",
                extra={
                    "backend": self.backend_name,
                    "model": deployment_id,
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
                    "model": deployment_id,
                    "retryable": False,
                    "error_type": type(exc).__name__,
                },
            )

        except Exception as exc:
            logger.exception(
                "Unexpected Azure OpenAI provider error",
                extra={
                    "backend": self.backend_name,
                    "model": deployment_id,
                    "error_type": type(exc).__name__,
                },
            )

            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=(
                    "Bei der Azure-OpenAI-Anfrage ist ein "
                    "unerwarteter Fehler aufgetreten."
                ),
                data={
                    "backend": self.backend_name,
                    "model": deployment_id,
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
            raise AzureOpenAIConfigurationError(
                "Azure-OpenAI-Tool-Aufrufe sind in dieser "
                "Provider-Version noch nicht implementiert.",
            )

        if request.tool_choice is not None:
            raise AzureOpenAIConfigurationError(
                "Azure OpenAI tool_choice wird in dieser "
                "Provider-Version noch nicht unterstützt.",
            )

    def _get_client(self) -> AsyncAzureOpenAI:
        """
        Erstellt den Client bei der ersten tatsächlichen Verwendung.
        """

        if self._endpoint is None:
            raise AzureOpenAIConfigurationError(
                "Der Azure-OpenAI-Endpunkt fehlt.",
            )

        if self._api_key is None:
            raise AzureOpenAIConfigurationError(
                "Der Azure-OpenAI-API-Key fehlt.",
            )

        if self._client is not None:
            return self._client

        client = AsyncAzureOpenAI(
            azure_endpoint=self._endpoint,
            api_key=self._api_key,
            api_version=self._api_version,
            timeout=self._timeout_seconds,
            max_retries=self._max_retries,
        )

        self._client = client

        return client

    def _resolve_deployment_id(
        self,
        requested_model_id: str,
    ) -> str:
        """
        Löst die Modell-ID gegen die freigegebenen Deployments auf.
        """

        normalized_model_id = requested_model_id.strip()

        deployment_id = (
            normalized_model_id if normalized_model_id else self._default_deployment
        )

        if deployment_id not in self._deployment_ids:
            raise AzureOpenAIModelNotFoundError(
                f"Das Azure-OpenAI-Deployment '{deployment_id}' ist nicht freigegeben.",
            )

        return deployment_id

    def _create_model_info(
        self,
        deployment_id: str,
    ) -> ModelInfo:
        """
        Erstellt die öffentliche Deployment-Beschreibung.
        """

        capabilities: set[ModelCapability] = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.STREAMING,
        }

        return ModelInfo.create(
            id=deployment_id,
            backend=self.backend_name,
            display_name=deployment_id,
            provider="Azure OpenAI",
            capabilities=capabilities,
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            metadata={
                "configured": True,
                "remote": True,
                "deployment": deployment_id,
                "api_version": self._api_version,
            },
        )


def _convert_messages(
    messages: Sequence[ChatMessage],
) -> AzureMessageList:
    """
    Übersetzt interne Chatnachrichten in OpenAI-Nachrichten.

    Leere Nachrichten werden nicht übertragen. Bereits vorhandene
    Tool-Ergebnisse können als Tool-Nachricht übertragen werden, sofern
    eine Aufruf-ID vorhanden ist. Ohne Aufruf-ID werden sie sichtbar als
    Benutzertext dargestellt.
    """

    converted_messages: AzureMessageList = []

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
                message.tool_call_id.strip() if message.tool_call_id is not None else ""
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
        raise AzureOpenAIConfigurationError(
            "Die Azure-OpenAI-Anfrage enthält keine verwendbare Nachricht.",
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

    return f"Tool-Ergebnis von '{normalized_name}':\n{content}"


def _create_usage(
    *,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
) -> Usage:
    """
    Übersetzt OpenAI-Nutzungsdaten in den Backendvertrag.

    Korrigierte Feldnamen: input_tokens, output_tokens, total_tokens.
    """
    return Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        metadata={},  # OpenAI liefert keine zusätzlichen Metadaten
    )


def _create_error_event(
    error: AzureOpenAIRequestError,
) -> StreamEvent:
    """
    Erstellt ein einheitliches Fehlerereignis.
    """

    data: dict[str, JsonValue] = {
        "backend": "azure_openai",
        "model": error.deployment_id,
        "deployment": error.deployment_id,
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
        raise AzureOpenAIConfigurationError(
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
        raise AzureOpenAIConfigurationError(
            "top_p muss größer als null sein.",
        )

    if value > 1.0:
        raise AzureOpenAIConfigurationError(
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

    if (
        isinstance(
            value,
            int,
        )
        and value >= 0
    ):
        return value

    return default


def create_azure_openai_backend(
    *,
    provider_config: JsonMapping,
    dependencies: ProviderDependencies | None = None,
) -> BaseModelBackend:
    """
    Factory für die feste Modell-Provider-Registry.

    Noch nicht benötigte Abhängigkeiten werden ausdrücklich verworfen.
    Die Signatur bleibt dennoch mit dem gemeinsamen Registry-Vertrag
    kompatibel.
    """

    del dependencies

    return AzureOpenAIProvider(
        provider_config,
    )


__all__ = [
    "AzureOpenAIConfigurationError",
    "AzureOpenAIModelNotFoundError",
    "AzureOpenAIProvider",
    "AzureOpenAIProviderError",
    "AzureOpenAIRequestError",
    "create_azure_openai_backend",
]
