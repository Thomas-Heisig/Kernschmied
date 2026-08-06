# F:\Kernschmied\backend\app\models\providers\google_gemini.py

from __future__ import annotations

import logging
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Mapping,
    Sequence,
)
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, cast

if TYPE_CHECKING:
    # Provide names for static type checkers without requiring installed stubs
    from google import genai  # type: ignore
    from google.genai import errors, types  # type: ignore
else:
    try:
        from google import genai  # type: ignore
        from google.genai import errors, types  # type: ignore
    except Exception:
        genai = cast(Any, None)
        errors = cast(Any, None)
        types = cast(Any, None)

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

# Local fallbacks for external SDK types to keep static checkers happy
ContentType: TypeAlias = Any
GenerateContentConfigType: TypeAlias = Any
GenerateContentResponseType: TypeAlias = Any

GeminiContentList: TypeAlias = list[ContentType]
ProviderDependencies: TypeAlias = Mapping[str, object]


class GeminiAsyncModelsProtocol(Protocol):
    """
    Enger Typvertrag für den verwendeten asynchronen Gemini-Aufruf.

    Das Google-SDK veröffentlicht für `generate_content_stream`
    teilweise unbekannte Union-Typen. Dieses Protocol beschreibt nur
    den von Kernschmied tatsächlich verwendeten, kontrollierten
    Aufrufpfad.
    """

    def generate_content_stream(
        self,
        *,
        model: str,
        contents: GeminiContentList,
        config: GenerateContentConfigType,
    ) -> Awaitable[AsyncIterator[GenerateContentResponseType]]: ...


class GeminiAioClientProtocol(Protocol):
    """Subset of the SDK's asynchronous client used by this provider."""

    models: GeminiAsyncModelsProtocol

    async def aclose(self) -> None: ...


class GeminiClientProtocol(Protocol):
    """Subset of the SDK's synchronous client used by this provider."""

    aio: GeminiAioClientProtocol

    def close(self) -> None: ...


# Prefer the explicit protocol when possible; fall back to Any if needed.
ClientType: TypeAlias = GeminiClientProtocol | Any


DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_API_VERSION = "v1beta"


class GoogleGeminiProviderError(RuntimeError):
    """
    Basisklasse für kontrollierte Fehler des Gemini-Providers.
    """


class GoogleGeminiConfigurationError(
    GoogleGeminiProviderError,
):
    """
    Die Provider-Konfiguration oder Anfrage ist ungültig.
    """


class GoogleGeminiModelNotFoundError(
    GoogleGeminiProviderError,
):
    """
    Das angeforderte Gemini-Modell ist nicht freigegeben.
    """


class GoogleGeminiRequestError(
    GoogleGeminiProviderError,
):
    """
    Eine Anfrage an die Gemini API ist fehlgeschlagen.
    """

    def __init__(
        self,
        *,
        model_id: str,
        reason: str,
        retryable: bool,
    ) -> None:
        self.model_id = model_id
        self.reason = reason
        self.retryable = retryable

        super().__init__(
            f"Gemini-Anfrage für Modell '{model_id}' fehlgeschlagen: {reason}",
        )


class GoogleGeminiProvider(BaseModelBackend):
    """
    Modell-Backend für die Google Gemini Developer API.

    Unterstützte Konfigurationswerte:

    - api_key:
      API-Key für die Gemini Developer API.

    - default_model:
      Standardmäßig verwendete Modell-ID.

    - models:
      Explizite Liste freigegebener Modell-IDs.

    - api_version:
      Zu verwendende API-Version. Standard ist `v1beta`.

    Das Backend erkennt keine entfernten Modelle automatisch als
    freigegeben. Ausschließlich die konfigurierten Modell-IDs werden
    über `list_models()` veröffentlicht.
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

        self._api_version = (
            _read_optional_string(
                config,
                "api_version",
            )
            or DEFAULT_API_VERSION
        )

        self._client: ClientType | None = None

    @property
    def backend_name(self) -> str:
        return "google_gemini"

    # ========================================================
    # Implementierung der abstrakten Methode get_model_info
    # ========================================================

    def get_model_info(self) -> ModelInfo:
        """
        Gibt die Modellinformationen des Backends zurück.
        Für Gemini verwenden wir das Standardmodell.
        """
        return self._create_model_info(self._default_model)

    async def is_available(self) -> bool:
        """
        Prüft ausschließlich die erforderliche lokale Konfiguration.

        Es wird bewusst keine Netzwerk- oder Testanfrage ausgeführt.
        """

        return self._api_key is not None

    async def list_models(
        self,
    ) -> list[ModelInfo]:
        """
        Liefert alle explizit freigegebenen Gemini-Modelle.
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
        Liefert Informationen zu einem freigegebenen Modell.
        """

        normalized_model_id = model_id.strip()

        if not normalized_model_id:
            raise GoogleGeminiModelNotFoundError(
                "Die Gemini-Modell-ID darf nicht leer sein.",
            )

        if normalized_model_id not in self._model_ids:
            raise GoogleGeminiModelNotFoundError(
                f"Das Gemini-Modell '{normalized_model_id}' ist nicht freigegeben.",
            )

        return self._create_model_info(
            normalized_model_id,
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
        Schließt die vom Google-SDK verwendeten HTTP-Clients.
        """

        client = self._client

        if client is None:
            return

        self._client = None

        try:
            await client.aio.aclose()

        except Exception:
            logger.exception(
                "Der asynchrone Gemini-Client konnte nicht sauber geschlossen werden.",
                extra={
                    "backend": self.backend_name,
                },
            )

        try:
            client.close()

        except Exception:
            logger.exception(
                "Der synchrone Gemini-Client konnte nicht sauber geschlossen werden.",
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

            system_instruction, contents = _convert_messages(
                request.messages,
            )

            generation_config = _create_generation_config(
                system_instruction=system_instruction,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stop=request.stop,
            )

            client = self._get_client()

            async_models = cast(
                GeminiAsyncModelsProtocol,
                client.aio.models,
            )

            response_stream = await async_models.generate_content_stream(
                model=model_id,
                contents=contents,
                config=generation_config,
            )

            usage: Usage | None = None
            finish_reason: str | None = None
            response_id: str | None = None

            async for chunk in response_stream:
                if response_id is None and chunk.response_id is not None:
                    response_id = chunk.response_id

                if chunk.usage_metadata is not None:
                    usage = _create_usage(
                        input_tokens=_normalize_token_count(
                            chunk.usage_metadata.prompt_token_count,
                        ),
                        output_tokens=_normalize_token_count(
                            chunk.usage_metadata.candidates_token_count,
                        ),
                        total_tokens=_normalize_token_count(
                            chunk.usage_metadata.total_token_count,
                        ),
                    )

                chunk_finish_reason = _read_finish_reason(
                    chunk,
                )

                if chunk_finish_reason is not None:
                    finish_reason = chunk_finish_reason

                text = chunk.text

                if text is None or not text:
                    continue

                yield StreamEvent.create(
                    type=StreamEventType.TOKEN,
                    content=text,
                )

            end_data: dict[str, JsonValue] = {
                "backend": self.backend_name,
                "model": model_id,
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

        except GoogleGeminiProviderError as exc:
            # Provider-specific, expected domain errors
            logger.exception(
                "Gemini provider rejected the request",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "error_type": type(exc).__name__,
                },
            )

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
            # Handle SDK APIError specially when possible, otherwise unexpected
            APIErrorClass = getattr(cast(object, errors), "APIError", None)

            if APIErrorClass is not None and isinstance(exc, APIErrorClass):
                retryable = _is_retryable_api_error(exc)

                error = GoogleGeminiRequestError(
                    model_id=model_id,
                    reason=str(exc),
                    retryable=retryable,
                )

                logger.exception(
                    "Gemini API returned an error",
                    extra={
                        "backend": self.backend_name,
                        "model": model_id,
                        "retryable": error.retryable,
                    },
                )

                yield _create_error_event(error)
            else:
                logger.exception(
                    "Unexpected Gemini provider error",
                    extra={
                        "backend": self.backend_name,
                        "model": model_id,
                        "error_type": type(exc).__name__,
                    },
                )

                yield StreamEvent.create(
                    type=StreamEventType.ERROR,
                    content=(
                        "Bei der Gemini-Anfrage ist ein unerwarteter Fehler aufgetreten."
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
        Lehnt noch nicht implementierte Vertragsfunktionen sichtbar ab.

        Tool-Definitionen dürfen nicht stillschweigend ignoriert werden.
        """

        if request.tools:
            raise GoogleGeminiConfigurationError(
                "Gemini-Tool-Aufrufe sind in dieser "
                "Provider-Version noch nicht implementiert.",
            )

        if request.tool_choice is not None:
            raise GoogleGeminiConfigurationError(
                "Gemini tool_choice wird in dieser "
                "Provider-Version noch nicht unterstützt.",
            )

    def _get_client(self) -> ClientType:
        """
        Erstellt den Gemini-Client erst bei tatsächlicher Verwendung.
        """

        if self._api_key is None:
            raise GoogleGeminiConfigurationError(
                "Der Gemini-API-Key fehlt.",
            )

        if self._client is not None:
            return self._client

        # Build http_options only if available in the SDK. Use getattr guards
        # to avoid static references to unknown SDK members.
        http_options: object | None = None
        types_obj = cast(object, types)
        HttpOptions = getattr(types_obj, "HttpOptions", None)
        if HttpOptions is not None:
            try:
                http_options = HttpOptions(api_version=self._api_version)
            except Exception:
                http_options = None

        genai_obj = cast(object, genai)
        ClientConstructor = getattr(genai_obj, "Client", None)
        if ClientConstructor is None:
            raise GoogleGeminiConfigurationError(
                "Die Gemini-Client-Klasse ist nicht verfügbar (google.genai fehlt).",
            )

        if http_options is not None:
            client = cast(
                ClientType,
                ClientConstructor(api_key=self._api_key, http_options=http_options),
            )
        else:
            client = cast(ClientType, ClientConstructor(api_key=self._api_key))

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
            raise GoogleGeminiModelNotFoundError(
                f"Das Gemini-Modell '{model_id}' ist nicht freigegeben.",
            )

        return model_id

    def _create_model_info(
        self,
        model_id: str,
    ) -> ModelInfo:
        """
        Erstellt die öffentliche Beschreibung eines Gemini-Modells.
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
            provider="Google Gemini",
            capabilities=capabilities,
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            metadata={
                "configured": True,
                "remote": True,
                "api_version": self._api_version,
            },
        )


def _convert_messages(
    messages: Sequence[ChatMessage],
) -> tuple[str | None, GeminiContentList]:
    """
    Übersetzt interne Chatnachrichten in den Gemini-Inhaltsvertrag.

    Gemini verwendet:

    - `user` für Benutzernachrichten,
    - `model` für Assistentenantworten,
    - `system_instruction` für Systemanweisungen.

    Bereits vorhandene Tool-Ergebnisse werden vorerst sichtbar als
    Benutzertext übertragen. Native Tool-Aufrufe werden erst aktiviert,
    sobald der gemeinsame Kernschmied-Vertrag vollständig abgebildet ist.
    """

    system_parts: list[str] = []
    contents: GeminiContentList = []

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
            parts = [
                _make_part_from_text(
                    content,
                ),
            ]

            contents.append(
                _make_content(
                    role="model",
                    parts=parts,
                ),
            )
            continue

        if message.role is MessageRole.TOOL:
            parts = [
                _make_part_from_text(
                    _format_tool_result(
                        message,
                        content,
                    ),
                ),
            ]

            contents.append(
                _make_content(
                    role="user",
                    parts=parts,
                ),
            )
            continue

        parts = [
            _make_part_from_text(
                content,
            ),
        ]

        contents.append(
            _make_content(
                role="user",
                parts=parts,
            ),
        )

    if not contents:
        raise GoogleGeminiConfigurationError(
            "Die Gemini-Anfrage enthält keine "
            "verwendbare Benutzer- oder Assistentennachricht.",
        )

    system_instruction = (
        "\n\n".join(
            system_parts,
        )
        if system_parts
        else None
    )

    return system_instruction, contents


def _make_part_from_text(text: str) -> Any:
    """Erzeugt eine `Part`-Instanz über das SDK, oder eine einfache Struktur als Fallback."""
    types_obj = cast(object, types)
    PartType = getattr(types_obj, "Part", None)
    from_text = getattr(PartType, "from_text", None)
    if PartType is not None and callable(from_text):
        return from_text(text=text)

    return {"type": "text", "text": text}


def _make_content(role: str, parts: list[Any]) -> ContentType:
    """Erzeugt eine `Content`-Instanz über das SDK, oder eine einfache Struktur als Fallback."""
    types_obj = cast(object, types)
    ContentConstructor = getattr(types_obj, "Content", None)
    if ContentConstructor is not None:
        return ContentConstructor(role=role, parts=parts)

    return {"role": role, "parts": parts}


def _format_tool_result(
    message: ChatMessage,
    content: str,
) -> str:
    """
    Formatiert ein vorhandenes Tool-Ergebnis als Benutzertext.
    """

    identifiers: list[str] = []

    if message.name is not None:
        normalized_name = message.name.strip()

        if normalized_name:
            identifiers.append(
                f"Name: {normalized_name}",
            )

    if message.tool_call_id is not None:
        normalized_call_id = message.tool_call_id.strip()

        if normalized_call_id:
            identifiers.append(
                f"Aufruf-ID: {normalized_call_id}",
            )

    if identifiers:
        header = ", ".join(
            identifiers,
        )

        return f"Tool-Ergebnis ({header}):\n{content}"

    return f"Tool-Ergebnis:\n{content}"


def _create_generation_config(
    *,
    system_instruction: str | None,
    temperature: float,
    max_tokens: int | None,
    top_p: float | None,
    stop: list[str] | None,
) -> GenerateContentConfigType:
    """
    Erstellt eine vollständig typisierte Gemini-Generierungskonfiguration.
    """

    normalized_temperature = _normalize_temperature(
        temperature,
    )

    normalized_max_tokens = _resolve_max_tokens(
        max_tokens,
    )

    normalized_top_p = _normalize_optional_top_p(
        top_p,
    )

    stop_sequences = _normalize_stop_sequences(
        stop,
    )

    types_obj = cast(object, types)
    GenConfig = getattr(types_obj, "GenerateContentConfig", None)
    if GenConfig is not None:
        return GenConfig(
            system_instruction=system_instruction,
            temperature=normalized_temperature,
            max_output_tokens=normalized_max_tokens,
            top_p=normalized_top_p,
            stop_sequences=stop_sequences,
        )

    return {
        "system_instruction": system_instruction,
        "temperature": normalized_temperature,
        "max_output_tokens": normalized_max_tokens,
        "top_p": normalized_top_p,
        "stop_sequences": stop_sequences,
    }


def _read_finish_reason(
    response: GenerateContentResponseType,
) -> str | None:
    """
    Liest den Beendigungsgrund aus dem ersten Kandidaten.
    """

    candidates = response.candidates

    if candidates is None or not candidates:
        return None

    finish_reason = candidates[0].finish_reason

    if finish_reason is None:
        return None

    return finish_reason.value


def _create_usage(
    *,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
) -> Usage:
    """
    Übersetzt Gemini-Nutzungsdaten in den Backendvertrag.

    Korrigierte Feldnamen: input_tokens, output_tokens, total_tokens.
    """
    calculated_total = total_tokens

    if calculated_total == 0:
        calculated_total = input_tokens + output_tokens

    return Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=calculated_total,
        metadata={},  # Gemini liefert keine zusätzlichen Metadaten
    )


def _normalize_token_count(
    value: int | None,
) -> int:
    """
    Normalisiert optionale Tokenwerte des Gemini-SDK.
    """

    if value is None or value < 0:
        return 0

    return value


def _create_error_event(
    error: GoogleGeminiRequestError,
) -> StreamEvent:
    """
    Erstellt ein strukturiertes Fehlerereignis.
    """

    data: dict[str, JsonValue] = {
        "backend": "google_gemini",
        "model": error.model_id,
        "retryable": error.retryable,
        "error_type": type(error).__name__,
    }

    return StreamEvent.create(
        type=StreamEventType.ERROR,
        content=str(
            error,
        ),
        data=data,
    )


def _is_retryable_api_error(
    error: object,
) -> bool:
    """
    Erkennt vorübergehende Fehler anhand des Fehlertexts.

    Der konkrete Fehlercode unterscheidet sich abhängig von Transport
    und API-Auswahl. Die Providergrenze bleibt deshalb unabhängig von
    internen Transporttypen des Google-SDK.
    """

    normalized_message = str(error).lower()

    retryable_markers = (
        "408",
        "409",
        "429",
        "500",
        "502",
        "503",
        "504",
        "deadline exceeded",
        "resource exhausted",
        "rate limit",
        "temporarily unavailable",
        "timeout",
        "timed out",
    )

    return any(marker in normalized_message for marker in retryable_markers)


def _resolve_max_tokens(
    value: int | None,
) -> int:
    """
    Validiert die maximale Anzahl auszugebender Tokens.
    """

    if value is None:
        return DEFAULT_MAX_TOKENS

    if value <= 0:
        raise GoogleGeminiConfigurationError(
            "max_tokens muss größer als null sein.",
        )

    return value


def _normalize_temperature(
    value: float,
) -> float:
    """
    Begrenzt die Temperatur auf einen sicheren Wertebereich.
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
        raise GoogleGeminiConfigurationError(
            "top_p muss größer als null sein.",
        )

    if value > 1.0:
        raise GoogleGeminiConfigurationError(
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


def create_google_gemini_backend(
    *,
    provider_config: JsonMapping,
    dependencies: ProviderDependencies | None = None,
) -> BaseModelBackend:
    """
    Factory für die feste Modell-Provider-Registry.
    """

    del dependencies

    return GoogleGeminiProvider(
        provider_config,
    )


__all__ = [
    "GoogleGeminiConfigurationError",
    "GoogleGeminiModelNotFoundError",
    "GoogleGeminiProvider",
    "GoogleGeminiProviderError",
    "GoogleGeminiRequestError",
    "create_google_gemini_backend",
]
