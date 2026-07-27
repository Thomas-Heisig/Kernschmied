# F:\Kernschmied\backend\app\models\providers\http_generic.py

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Final, TypeAlias, cast

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
    StreamEvent,
    StreamEventType,
    Usage,
)


logger = logging.getLogger(__name__)


# ============================================================
# Typen
# ============================================================


HTTPMessage: TypeAlias = JsonObject
HTTPMessageList: TypeAlias = list[JsonValue]
HTTPHeaders: TypeAlias = dict[str, str]
ProviderDependencies: TypeAlias = Mapping[str, object]
PlaceholderValues: TypeAlias = Mapping[str, JsonValue]


# ============================================================
# Standardwerte
# ============================================================


DEFAULT_TIMEOUT_SECONDS: Final[float] = 60.0
DEFAULT_MAX_RETRIES: Final[int] = 2
DEFAULT_MAX_TOKENS: Final[int] = 4096

DEFAULT_MODEL_ID: Final[str] = "http-generic"
DEFAULT_DISPLAY_NAME: Final[str] = "HTTP Generic"

DEFAULT_RESPONSE_PATH: Final[str] = (
    "choices.0.message.content"
)
DEFAULT_STREAM_RESPONSE_PATH: Final[str] = (
    "choices.0.delta.content"
)
DEFAULT_STREAM_FINISH_REASON_PATH: Final[str] = (
    "choices.0.finish_reason"
)
DEFAULT_STREAM_USAGE_PATH: Final[str] = "usage"

SUPPORTED_STREAM_MODES: Final[frozenset[str]] = frozenset(
    {
        "json",
        "sse",
        "jsonl",
        "raw",
    },
)

SUPPORTED_METHODS: Final[frozenset[str]] = frozenset(
    {
        "DELETE",
        "GET",
        "PATCH",
        "POST",
        "PUT",
    },
)


def _default_request_template() -> JsonObject:
    """
    Erstellt eine OpenAI-kompatible Standardvorlage.

    Eigene REST-Endpunkte können diese Vorlage vollständig über
    `request_template` ersetzen.
    """

    return {
        "model": "{{model}}",
        "messages": "{{messages}}",
        "temperature": "{{temperature}}",
        "max_tokens": "{{max_tokens}}",
        "top_p": "{{top_p}}",
        "stop": "{{stop}}",
        "stream": "{{stream}}",
    }


# ============================================================
# Fehler
# ============================================================


class HTTPGenericProviderError(RuntimeError):
    """
    Basisklasse für kontrollierte Fehler des HTTP-Generic-Providers.
    """


class HTTPGenericConfigurationError(
    HTTPGenericProviderError,
):
    """
    Die Provider-Konfiguration oder Anfrage ist ungültig.
    """


class HTTPGenericModelNotFoundError(
    HTTPGenericProviderError,
):
    """
    Die angeforderte Modell-ID ist nicht freigegeben.
    """


class HTTPGenericRequestError(
    HTTPGenericProviderError,
):
    """
    Die HTTP-Anfrage an den externen Dienst ist fehlgeschlagen.
    """

    def __init__(
        self,
        *,
        url: str,
        reason: str,
        retryable: bool,
        status_code: int | None = None,
    ) -> None:
        self.url = url
        self.reason = reason
        self.retryable = retryable
        self.status_code = status_code

        super().__init__(
            f"HTTP-Anfrage an '{url}' fehlgeschlagen: {reason}",
        )


class HTTPGenericResponseError(
    HTTPGenericProviderError,
):
    """
    Die Antwort des externen Dienstes konnte nicht verarbeitet werden.
    """

    def __init__(
        self,
        *,
        url: str,
        reason: str,
    ) -> None:
        self.url = url
        self.reason = reason

        super().__init__(
            f"Antwort von '{url}' konnte nicht verarbeitet werden: "
            f"{reason}",
        )


# ============================================================
# Interner Streamzustand
# ============================================================


@dataclass(slots=True)
class HTTPStreamMetadata:
    """
    Während eines Streams gesammelte Metadaten.

    Die Instanz wird ausschließlich innerhalb eines einzelnen
    GenerationRequest verwendet und ist deshalb nebenläufigkeitssicher.
    """

    usage: Usage | None = None
    finish_reason: str | None = None


# ============================================================
# Provider
# ============================================================


class HTTPGenericProvider(BaseModelBackend):
    """
    Universeller HTTP-Provider für kontrolliert konfigurierte REST-APIs.

    Unterstützte Konfigurationswerte:

    - url:
      Erforderliche Ziel-URL.

    - method:
      HTTP-Methode. Erlaubt sind GET, POST, PUT, PATCH und DELETE.
      Standard: POST.

    - headers:
      Zusätzliche HTTP-Header als Objekt mit Stringwerten.

    - request_template:
      Rekursiv aufgelöste JSON-Vorlage für den Request-Body.

    - model_id:
      Öffentliche Modell-ID dieses Endpunkts.

    - display_name:
      Anzeigename des Endpunkts.

    - response_path:
      JSON-Pfad für eine nicht gestreamte JSON-Antwort.

    - stream_response_path:
      JSON-Pfad für Textfragmente innerhalb von SSE- oder JSONL-Daten.

    - stream_finish_reason_path:
      Optionaler JSON-Pfad zum Beendigungsgrund.

    - stream_usage_path:
      Optionaler JSON-Pfad zu Token-Nutzungsdaten.

    - stream_mode:
      `json`, `sse`, `jsonl` oder `raw`.

    - timeout:
      Anfrage-Timeout in Sekunden.

    - max_retries:
      Anzahl der Verbindungswiederholungen des HTTP-Transports.

    Platzhalter in `request_template`:

    - {{messages}}
    - {{model}}
    - {{max_tokens}}
    - {{temperature}}
    - {{top_p}}
    - {{stop}}
    - {{stream}}

    Ein Platzhalter, der den vollständigen Stringwert bildet, wird als
    strukturierter JSON-Wert eingesetzt. Dadurch bleibt beispielsweise
    `{{messages}}` eine Liste und wird nicht zu einem JSON-String.
    """

    def __init__(
        self,
        config: JsonMapping,
    ) -> None:
        self._url = _read_required_string(
            config,
            "url",
        )

        self._method = _read_http_method(
            config,
            "method",
            default="POST",
        )

        self._headers = _read_string_mapping(
            config,
            "headers",
        )

        configured_template = _read_optional_json_object(
            config,
            "request_template",
        )

        self._request_template = (
            configured_template
            if configured_template is not None
            else _default_request_template()
        )

        self._model_id = (
            _read_optional_string(
                config,
                "model_id",
            )
            or DEFAULT_MODEL_ID
        )

        self._display_name = (
            _read_optional_string(
                config,
                "display_name",
            )
            or DEFAULT_DISPLAY_NAME
        )

        self._response_path = (
            _read_optional_string(
                config,
                "response_path",
            )
            or DEFAULT_RESPONSE_PATH
        )

        self._stream_response_path = (
            _read_optional_string(
                config,
                "stream_response_path",
            )
            or DEFAULT_STREAM_RESPONSE_PATH
        )

        self._stream_finish_reason_path = (
            _read_optional_string(
                config,
                "stream_finish_reason_path",
            )
            or DEFAULT_STREAM_FINISH_REASON_PATH
        )

        self._stream_usage_path = (
            _read_optional_string(
                config,
                "stream_usage_path",
            )
            or DEFAULT_STREAM_USAGE_PATH
        )

        self._stream_mode = _read_stream_mode(
            config,
            "stream_mode",
            default="sse",
        )

        self._timeout_seconds = _read_positive_float(
            config,
            "timeout",
            default=DEFAULT_TIMEOUT_SECONDS,
        )

        self._max_retries = _read_non_negative_int(
            config,
            "max_retries",
            default=DEFAULT_MAX_RETRIES,
        )

        self._client: httpx.AsyncClient | None = None

    @property
    def backend_name(self) -> str:
        return "http_generic"

    async def is_available(self) -> bool:
        """
        Prüft ausschließlich die lokale Provider-Konfiguration.

        Es wird keine Netzwerkverbindung aufgebaut.
        """

        return bool(
            self._url,
        )

    async def list_models(
        self,
    ) -> list[ModelInfo]:
        """
        Liefert das kontrolliert konfigurierte HTTP-Modell.
        """

        return [
            self._create_model_info(),
        ]

    async def get_model(
        self,
        model_id: str,
    ) -> ModelInfo:
        """
        Liefert die Modellbeschreibung bei passender Modell-ID.
        """

        normalized_model_id = model_id.strip()

        if normalized_model_id != self._model_id:
            raise HTTPGenericModelNotFoundError(
                f"Dieser HTTP-Provider unterstützt nur das Modell "
                f"'{self._model_id}'. Angefragt wurde "
                f"'{normalized_model_id}'.",
            )

        return self._create_model_info()

    def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        """
        Liefert unmittelbar einen AsyncIterator.
        """

        return self._stream_request(
            request,
        )

    async def shutdown(self) -> None:
        """
        Schließt den wiederverwendeten HTTP-Client.
        """

        client = self._client

        if client is None:
            return

        self._client = None

        try:
            await client.aclose()

        except Exception:
            logger.exception(
                "HTTP-Client konnte nicht sauber geschlossen werden.",
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

        metadata = HTTPStreamMetadata()

        yield StreamEvent.create(
            type=StreamEventType.START,
            data={
                "backend": self.backend_name,
                "model": model_id,
                "url": self._url,
                "stream_mode": self._stream_mode,
            },
        )

        try:
            self._validate_request(
                request,
            )

            messages = _convert_messages(
                request.messages,
            )

            payload = self._build_payload(
                messages=messages,
                model=model_id,
                max_tokens=_resolve_max_tokens(
                    request.max_tokens,
                ),
                temperature=_normalize_temperature(
                    request.temperature,
                ),
                top_p=_normalize_optional_top_p(
                    request.top_p,
                ),
                stop=_normalize_stop_sequences(
                    request.stop,
                ),
                stream=self._stream_mode != "json",
            )

            client = self._get_client()

            if self._stream_mode == "json":
                async for event in self._request_json(
                    client=client,
                    payload=payload,
                    metadata=metadata,
                ):
                    yield event

            elif self._stream_mode == "sse":
                async for event in self._stream_sse(
                    client=client,
                    payload=payload,
                    metadata=metadata,
                ):
                    yield event

            elif self._stream_mode == "jsonl":
                async for event in self._stream_jsonl(
                    client=client,
                    payload=payload,
                    metadata=metadata,
                ):
                    yield event

            elif self._stream_mode == "raw":
                async for event in self._stream_raw(
                    client=client,
                    payload=payload,
                ):
                    yield event

            end_data: JsonObject = {
                "backend": self.backend_name,
                "model": model_id,
                "url": self._url,
                "stream_mode": self._stream_mode,
            }

            if metadata.finish_reason is not None:
                end_data["finish_reason"] = (
                    metadata.finish_reason
                )

            yield StreamEvent.create(
                type=StreamEventType.END,
                usage=metadata.usage,
                data=end_data,
            )

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            error = HTTPGenericRequestError(
                url=self._url,
                reason=_create_http_status_reason(
                    exc.response,
                ),
                retryable=_is_retryable_status_code(
                    status_code,
                ),
                status_code=status_code,
            )

            logger.exception(
                "HTTP-Generic-Endpunkt lieferte einen Statusfehler.",
                extra={
                    "backend": self.backend_name,
                    "url": self._url,
                    "status_code": status_code,
                    "retryable": error.retryable,
                },
            )

            yield _create_error_event(
                error,
            )

        except httpx.TimeoutException as exc:
            error = HTTPGenericRequestError(
                url=self._url,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "Zeitüberschreitung beim HTTP-Generic-Endpunkt.",
                extra={
                    "backend": self.backend_name,
                    "url": self._url,
                    "retryable": True,
                },
            )

            yield _create_error_event(
                error,
            )

        except httpx.RequestError as exc:
            error = HTTPGenericRequestError(
                url=self._url,
                reason=str(
                    exc,
                ),
                retryable=True,
            )

            logger.exception(
                "Verbindungsfehler beim HTTP-Generic-Endpunkt.",
                extra={
                    "backend": self.backend_name,
                    "url": self._url,
                    "retryable": True,
                },
            )

            yield _create_error_event(
                error,
            )

        except HTTPGenericProviderError as exc:
            logger.exception(
                "HTTP-Generic-Provider hat die Anfrage abgelehnt.",
                extra={
                    "backend": self.backend_name,
                    "url": self._url,
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
                    "url": self._url,
                    "retryable": False,
                    "error_type": type(exc).__name__,
                },
            )

        except Exception as exc:
            logger.exception(
                "Unerwarteter Fehler im HTTP-Generic-Provider.",
                extra={
                    "backend": self.backend_name,
                    "url": self._url,
                    "error_type": type(exc).__name__,
                },
            )

            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=(
                    "Bei der Anfrage an den generischen HTTP-Endpunkt "
                    "ist ein unerwarteter Fehler aufgetreten."
                ),
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "url": self._url,
                    "retryable": False,
                    "error_type": type(exc).__name__,
                },
            )

    def _validate_request(
        self,
        request: GenerationRequest,
    ) -> None:
        """
        Lehnt noch nicht unterstützte Funktionen sichtbar ab.
        """

        if request.tools:
            raise HTTPGenericConfigurationError(
                "Tool-Aufrufe werden vom HTTP-Generic-Provider "
                "noch nicht unterstützt.",
            )

        if request.tool_choice is not None:
            raise HTTPGenericConfigurationError(
                "tool_choice wird vom HTTP-Generic-Provider "
                "noch nicht unterstützt.",
            )

    def _resolve_model_id(
        self,
        requested_model_id: str,
    ) -> str:
        """
        Prüft die angeforderte Modell-ID gegen die Freigabe.
        """

        normalized_model_id = requested_model_id.strip()

        model_id = (
            normalized_model_id
            if normalized_model_id
            else self._model_id
        )

        if model_id != self._model_id:
            raise HTTPGenericModelNotFoundError(
                f"Das HTTP-Modell '{model_id}' ist nicht freigegeben. "
                f"Erlaubt ist ausschließlich '{self._model_id}'.",
            )

        return model_id

    def _build_payload(
        self,
        *,
        messages: HTTPMessageList,
        model: str,
        max_tokens: int,
        temperature: float,
        top_p: float | None,
        stop: list[str] | None,
        stream: bool,
    ) -> JsonObject:
        """
        Löst Platzhalter rekursiv und typsicher auf.
        """

        stop_value: JsonValue = (
            _string_sequence_to_json_list(stop)
            if stop is not None
            else None
        )

        placeholders: dict[str, JsonValue] = {
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop": stop_value,
            "stream": stream,
        }

        resolved = _resolve_template_value(
            deepcopy(
                self._request_template,
            ),
            placeholders,
        )

        if not isinstance(
            resolved,
            dict,
        ):
            raise HTTPGenericConfigurationError(
                "request_template muss nach der Platzhalterauflösung "
                "ein JSON-Objekt ergeben.",
            )

        return resolved

    async def _request_json(
        self,
        *,
        client: httpx.AsyncClient,
        payload: JsonObject,
        metadata: HTTPStreamMetadata,
    ) -> AsyncIterator[StreamEvent]:
        """
        Verarbeitet eine einzelne nicht gestreamte JSON-Antwort.
        """

        response = await client.request(
            method=self._method,
            url=self._url,
            headers=self._headers,
            json=payload,
        )

        response.raise_for_status()

        data = _parse_json_response(
            response,
            url=self._url,
        )

        text_value = _extract_by_path(
            data,
            self._response_path,
        )

        text = _coerce_text_value(
            text_value,
        )

        if text:
            yield StreamEvent.create(
                type=StreamEventType.TOKEN,
                content=text,
            )

        self._update_stream_metadata(
            data=data,
            metadata=metadata,
        )

    async def _stream_sse(
        self,
        *,
        client: httpx.AsyncClient,
        payload: JsonObject,
        metadata: HTTPStreamMetadata,
    ) -> AsyncIterator[StreamEvent]:
        """
        Verarbeitet Server-Sent Events.

        Mehrere aufeinanderfolgende `data:`-Zeilen eines SSE-Ereignisses
        werden gemäß SSE-Struktur zusammengeführt.
        """

        async with client.stream(
            method=self._method,
            url=self._url,
            headers=self._headers,
            json=payload,
        ) as response:
            response.raise_for_status()

            data_lines: list[str] = []

            async for line in response.aiter_lines():
                if line == "":
                    if data_lines:
                        data_text = "\n".join(
                            data_lines,
                        )

                        data_lines.clear()

                        async for event in self._process_stream_data(
                            data_text=data_text,
                            metadata=metadata,
                            source="sse",
                        ):
                            yield event

                    continue

                if line.startswith(
                    ":",
                ):
                    continue

                if line.startswith(
                    "data:",
                ):
                    data_lines.append(
                        line[5:].lstrip(),
                    )

            if data_lines:
                data_text = "\n".join(
                    data_lines,
                )

                async for event in self._process_stream_data(
                    data_text=data_text,
                    metadata=metadata,
                    source="sse",
                ):
                    yield event

    async def _stream_jsonl(
        self,
        *,
        client: httpx.AsyncClient,
        payload: JsonObject,
        metadata: HTTPStreamMetadata,
    ) -> AsyncIterator[StreamEvent]:
        """
        Verarbeitet JSON-Lines-Antworten.
        """

        async with client.stream(
            method=self._method,
            url=self._url,
            headers=self._headers,
            json=payload,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                normalized_line = line.strip()

                if not normalized_line:
                    continue

                async for event in self._process_stream_data(
                    data_text=normalized_line,
                    metadata=metadata,
                    source="jsonl",
                ):
                    yield event

    async def _stream_raw(
        self,
        *,
        client: httpx.AsyncClient,
        payload: JsonObject,
    ) -> AsyncIterator[StreamEvent]:
        """
        Gibt dekodierte Textfragmente unverändert als Tokens aus.

        `aiter_text()` übernimmt die korrekte Dekodierung auch dann,
        wenn Mehrbytezeichen über mehrere Netzwerkpakete verteilt sind.
        """

        async with client.stream(
            method=self._method,
            url=self._url,
            headers=self._headers,
            json=payload,
        ) as response:
            response.raise_for_status()

            async for text in response.aiter_text():
                if not text:
                    continue

                yield StreamEvent.create(
                    type=StreamEventType.TOKEN,
                    content=text,
                )

    async def _process_stream_data(
        self,
        *,
        data_text: str,
        metadata: HTTPStreamMetadata,
        source: str,
    ) -> AsyncIterator[StreamEvent]:
        """
        Verarbeitet ein vollständiges SSE- oder JSONL-Datenelement.
        """

        if data_text == "[DONE]":
            return

        try:
            raw_data: object = json.loads(
                data_text,
            )

            data = _validate_json_value(
                raw_data,
            )

        except (
            json.JSONDecodeError,
            HTTPGenericResponseError,
        ) as exc:
            logger.warning(
                "Ungültige %s-Daten vom HTTP-Generic-Endpunkt: %s",
                source,
                exc,
                extra={
                    "backend": self.backend_name,
                    "url": self._url,
                },
            )

            return

        token_value = _extract_by_path(
            data,
            self._stream_response_path,
        )

        token = _coerce_text_value(
            token_value,
        )

        if token:
            yield StreamEvent.create(
                type=StreamEventType.TOKEN,
                content=token,
            )

        self._update_stream_metadata(
            data=data,
            metadata=metadata,
        )

    def _update_stream_metadata(
        self,
        *,
        data: JsonValue,
        metadata: HTTPStreamMetadata,
    ) -> None:
        """
        Extrahiert Finish-Reason und Usage aus einem Antwortobjekt.
        """

        finish_reason_value = _extract_by_path(
            data,
            self._stream_finish_reason_path,
        )

        finish_reason = _coerce_text_value(
            finish_reason_value,
        )

        if finish_reason:
            metadata.finish_reason = finish_reason

        usage_value = _extract_by_path(
            data,
            self._stream_usage_path,
        )

        if isinstance(
            usage_value,
            dict,
        ):
            usage = _create_usage_from_mapping(
                usage_value,
            )

            if usage is not None:
                metadata.usage = usage

    def _get_client(self) -> httpx.AsyncClient:
        """
        Erstellt den HTTP-Client erst bei tatsächlicher Verwendung.
        """

        if self._client is not None:
            return self._client

        transport = httpx.AsyncHTTPTransport(
            retries=self._max_retries,
        )

        client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                self._timeout_seconds,
            ),
            transport=transport,
            follow_redirects=True,
            max_redirects=5,
        )

        self._client = client

        return client

    def _create_model_info(
        self,
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
            id=self._model_id,
            backend=self.backend_name,
            display_name=self._display_name,
            provider="HTTP Generic",
            capabilities=capabilities,
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            metadata={
                "url": self._url,
                "method": self._method,
                "stream_mode": self._stream_mode,
                "configured": True,
                "remote": True,
            },
        )


# ============================================================
# Nachrichtenkonvertierung
# ============================================================


def _convert_messages(
    messages: Sequence[ChatMessage],
) -> HTTPMessageList:
    """
    Konvertiert interne Chatnachrichten in ein generisches JSON-Format.

    Die Rückgabe ist unmittelbar als JSON-Liste typisiert. Dadurch kann
    sie ohne unsicheren Cast als Wert eines JsonObject verwendet werden.
    """

    converted: HTTPMessageList = []

    for message in messages:
        content = message.content.strip()

        if not content:
            continue

        role = _convert_message_role(
            message.role,
        )

        converted_message: JsonObject = {
            "role": role,
            "content": content,
        }

        if message.name is not None:
            normalized_name = message.name.strip()

            if normalized_name:
                converted_message["name"] = normalized_name

        if message.tool_call_id is not None:
            normalized_tool_call_id = (
                message.tool_call_id.strip()
            )

            if normalized_tool_call_id:
                converted_message["tool_call_id"] = (
                    normalized_tool_call_id
                )

        if message.metadata:
            converted_message["metadata"] = deepcopy(
                message.metadata,
            )

        converted.append(
            converted_message,
        )

    if not converted:
        raise HTTPGenericConfigurationError(
            "Die Anfrage enthält keine verwendbaren Nachrichten.",
        )

    return converted
def _convert_message_role(
    role: MessageRole,
) -> str:
    """
    Übersetzt die interne Rolle ohne stillschweigenden Rollenverlust.
    """

    if role is MessageRole.SYSTEM:
        return "system"

    if role is MessageRole.ASSISTANT:
        return "assistant"

    if role is MessageRole.TOOL:
        return "tool"

    return "user"


# ============================================================
# Vorlagenauflösung
# ============================================================


def _resolve_template_value(
    value: JsonValue,
    placeholders: PlaceholderValues,
) -> JsonValue:
    """
    Löst Platzhalter rekursiv innerhalb eines JSON-Wertes auf.
    """

    if isinstance(
        value,
        dict,
    ):
        return {
            key: _resolve_template_value(
                child_value,
                placeholders,
            )
            for key, child_value in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            _resolve_template_value(
                child_value,
                placeholders,
            )
            for child_value in value
        ]

    if not isinstance(
        value,
        str,
    ):
        return value

    exact_placeholder = _extract_exact_placeholder(
        value,
    )

    if exact_placeholder is not None:
        if exact_placeholder not in placeholders:
            raise HTTPGenericConfigurationError(
                f"Unbekannter Platzhalter "
                f"'{{{{{exact_placeholder}}}}}' "
                "in request_template.",
            )

        return deepcopy(
            placeholders[
                exact_placeholder
            ],
        )

    resolved = value

    for name, replacement in placeholders.items():
        placeholder = f"{{{{{name}}}}}"

        if placeholder not in resolved:
            continue

        resolved = resolved.replace(
            placeholder,
            _json_value_to_inline_text(
                replacement,
            ),
        )

    if "{{" in resolved or "}}" in resolved:
        raise HTTPGenericConfigurationError(
            f"Nicht aufgelöster oder ungültiger Platzhalter "
            f"in request_template: '{resolved}'.",
        )

    return resolved


def _extract_exact_placeholder(
    value: str,
) -> str | None:
    """
    Erkennt einen String, der nur aus einem Platzhalter besteht.
    """

    if not value.startswith(
        "{{",
    ):
        return None

    if not value.endswith(
        "}}",
    ):
        return None

    name = value[2:-2].strip()

    return name or None


def _json_value_to_inline_text(
    value: JsonValue,
) -> str:
    """
    Übersetzt JSON-Werte für Platzhalter innerhalb längerer Strings.
    """

    if value is None:
        return "null"

    if isinstance(
        value,
        bool,
    ):
        return "true" if value else "false"

    if isinstance(
        value,
        str,
    ):
        return value

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    )


# ============================================================
# JSON-Verarbeitung
# ============================================================

def _normalize_stop_sequences(
    value: list[str] | None,
) -> list[str] | None:
    """
    Bereinigt optionale Stop-Sequenzen.

    Leere Einträge und reine Leerzeichen werden entfernt.
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

    return normalized or None

def _parse_json_response(
    response: httpx.Response,
    *,
    url: str,
) -> JsonValue:
    """
    Liest und validiert eine JSON-Antwort.
    """

    try:
        raw_data: object = response.json()

    except json.JSONDecodeError as exc:
        raise HTTPGenericResponseError(
            url=url,
            reason=(
                "Der Antwortinhalt ist kein gültiges JSON."
            ),
        ) from exc

    return _validate_json_value(
        raw_data,
    )


def _validate_json_value(
    value: object,
) -> JsonValue:
    """
    Validiert einen unbekannten Laufzeitwert als JSON-Wert.
    """

    if value is None:
        return None

    if isinstance(
        value,
        str | bool | int | float,
    ):
        return value

    if isinstance(
        value,
        list,
    ):
        object_list = cast(
            list[object],
            value,
        )

        return [
            _validate_json_value(
                item,
            )
            for item in object_list
        ]

    if isinstance(
        value,
        dict,
    ):
        object_mapping = cast(
            Mapping[object, object],
            value,
        )

        result: JsonObject = {}

        for key, child_value in object_mapping.items():
            if not isinstance(
                key,
                str,
            ):
                raise HTTPGenericResponseError(
                    url="<response>",
                    reason=(
                        "Ein JSON-Objekt enthält einen Schlüssel, "
                        "der keine Zeichenkette ist."
                    ),
                )

            result[key] = _validate_json_value(
                child_value,
            )

        return result

    raise HTTPGenericResponseError(
        url="<response>",
        reason=(
            f"Nicht unterstützter JSON-Wert vom Typ "
            f"'{type(value).__name__}'."
        ),
    )


def _extract_by_path(
    data: JsonValue,
    path: str,
) -> JsonValue | None:
    """
    Extrahiert einen Wert anhand eines Punktpfades.

    Beispiele:

    - choices.0.message.content
    - candidates.0.content.parts.0.text

    Bei Listen muss das Pfadsegment eine numerische Position sein.
    """

    normalized_path = path.strip()

    if not normalized_path:
        return None

    current: JsonValue = data

    for segment in normalized_path.split(
        ".",
    ):
        if isinstance(
            current,
            dict,
        ):
            if segment not in current:
                return None

            current = current[segment]
            continue

        if isinstance(
            current,
            list,
        ):
            try:
                index = int(
                    segment,
                )

            except ValueError:
                return None

            if index < 0 or index >= len(
                current,
            ):
                return None

            current = current[index]
            continue

        return None

    return current


def _coerce_text_value(
    value: JsonValue | None,
) -> str | None:
    """
    Übersetzt einen skalaren Antwortwert in Text.

    Objekte und Listen werden nicht automatisch als Modelltext
    serialisiert.
    """

    if value is None:
        return None

    if isinstance(
        value,
        str,
    ):
        return value

    if isinstance(
        value,
        bool,
    ):
        return "true" if value else "false"

    if isinstance(
        value,
        int | float,
    ):
        return str(
            value,
        )

    return None


# ============================================================
# Usage
# ============================================================


def _create_usage_from_mapping(
    data: JsonMapping,
) -> Usage | None:
    """
    Erkennt verbreitete Tokenfeldnamen verschiedener APIs.
    """

    prompt_tokens = _read_first_non_negative_integer(
        data,
        (
            "prompt_tokens",
            "promptTokenCount",
            "input_tokens",
            "inputTokens",
        ),
    )

    completion_tokens = _read_first_non_negative_integer(
        data,
        (
            "completion_tokens",
            "completionTokenCount",
            "candidatesTokenCount",
            "output_tokens",
            "outputTokens",
        ),
    )

    total_tokens = _read_first_non_negative_integer(
        data,
        (
            "total_tokens",
            "totalTokenCount",
            "totalTokens",
        ),
    )

    if prompt_tokens is None and completion_tokens is None:
        return None

    normalized_prompt_tokens = prompt_tokens or 0
    normalized_completion_tokens = completion_tokens or 0

    normalized_total_tokens = (
        total_tokens
        if total_tokens is not None
        else (
            normalized_prompt_tokens
            + normalized_completion_tokens
        )
    )

    return Usage(
        prompt_tokens=normalized_prompt_tokens,
        completion_tokens=normalized_completion_tokens,
        total_tokens=normalized_total_tokens,
    )


def _read_first_non_negative_integer(
    data: JsonMapping,
    keys: Sequence[str],
) -> int | None:
    """
    Liest den ersten gültigen nichtnegativen Ganzzahlwert.
    """

    for key in keys:
        value = data.get(
            key,
        )

        converted = _coerce_non_negative_integer(
            value,
        )

        if converted is not None:
            return converted

    return None


def _coerce_non_negative_integer(
    value: JsonValue | None,
) -> int | None:
    """
    Wandelt einen JSON-Skalar kontrolliert in eine Ganzzahl um.
    """

    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        int,
    ):
        return value if value >= 0 else None

    if isinstance(
        value,
        float,
    ):
        if value < 0 or not value.is_integer():
            return None

        return int(
            value,
        )

    if isinstance(
        value,
        str,
    ):
        try:
            converted = int(
                value.strip(),
            )

        except ValueError:
            return None

        return converted if converted >= 0 else None

    return None


# ============================================================
# Konfigurationsleser
# ============================================================


def _read_required_string(
    config: JsonMapping,
    key: str,
) -> str:
    """
    Liest einen erforderlichen nichtleeren String.
    """

    value = _read_optional_string(
        config,
        key,
    )

    if value is None:
        raise HTTPGenericConfigurationError(
            f"Konfigurationswert '{key}' ist erforderlich.",
        )

    return value


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


def _read_http_method(
    config: JsonMapping,
    key: str,
    *,
    default: str,
) -> str:
    """
    Liest und validiert die HTTP-Methode.
    """

    method = (
        _read_optional_string(
            config,
            key,
        )
        or default
    ).upper()

    if method not in SUPPORTED_METHODS:
        raise HTTPGenericConfigurationError(
            f"Nicht unterstützte HTTP-Methode '{method}'. "
            f"Erlaubt sind: "
            f"{', '.join(sorted(SUPPORTED_METHODS))}.",
        )

    return method


def _read_stream_mode(
    config: JsonMapping,
    key: str,
    *,
    default: str,
) -> str:
    """
    Liest und validiert den Antwortmodus.
    """

    stream_mode = (
        _read_optional_string(
            config,
            key,
        )
        or default
    ).lower()

    if stream_mode not in SUPPORTED_STREAM_MODES:
        raise HTTPGenericConfigurationError(
            f"Unbekannter stream_mode '{stream_mode}'. "
            f"Erlaubt sind: "
            f"{', '.join(sorted(SUPPORTED_STREAM_MODES))}.",
        )

    return stream_mode


def _read_string_mapping(
    config: JsonMapping,
    key: str,
) -> HTTPHeaders:
    """
    Liest ein JSON-Objekt mit ausschließlich Stringwerten.
    """

    value = config.get(
        key,
    )

    if value is None:
        return {}

    if not isinstance(
        value,
        dict,
    ):
        raise HTTPGenericConfigurationError(
            f"Konfigurationswert '{key}' muss ein Objekt sein.",
        )

    result: HTTPHeaders = {}

    for header_name, header_value in value.items():
        if not isinstance(
            header_value,
            str,
        ):
            raise HTTPGenericConfigurationError(
                f"Header '{header_name}' muss eine Zeichenkette sein.",
            )

        normalized_name = header_name.strip()
        normalized_value = header_value.strip()

        if not normalized_name:
            raise HTTPGenericConfigurationError(
                "Headernamen dürfen nicht leer sein.",
            )

        result[normalized_name] = normalized_value

    return result


def _read_optional_json_object(
    config: JsonMapping,
    key: str,
) -> JsonObject | None:
    """
    Liest eine veränderbare Kopie eines JSON-Objekts.
    """

    value = config.get(
        key,
    )

    if value is None:
        return None

    if not isinstance(
        value,
        dict,
    ):
        raise HTTPGenericConfigurationError(
            f"Konfigurationswert '{key}' muss ein JSON-Objekt sein.",
        )

    return deepcopy(
        value,
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


# ============================================================
# Generierungsparameter
# ============================================================


def _resolve_max_tokens(
    value: int | None,
) -> int:
    """
    Validiert die maximale Anzahl auszugebender Tokens.
    """

    if value is None:
        return DEFAULT_MAX_TOKENS

    if value <= 0:
        raise HTTPGenericConfigurationError(
            "max_tokens muss größer als null sein.",
        )

    return value


def _normalize_temperature(
    value: float,
) -> float:
    """
    Begrenzt die Temperatur auf einen generischen Wertebereich.
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

    if value <= 0.0 or value > 1.0:
        raise HTTPGenericConfigurationError(
            "top_p muss größer als null und höchstens 1 sein.",
        )

    return value


def _string_sequence_to_json_list(
    values: Sequence[str],
) -> list[JsonValue]:
    """
    Übersetzt eine Stringsequenz explizit in eine JSON-Liste.

    Die explizite Elementtypisierung ist notwendig, weil `list` invariant
    ist und `list[str]` deshalb statisch nicht als `list[JsonValue]`
    behandelt wird.
    """

    result: list[JsonValue] = []

    for value in values:
        result.append(
            value,
        )

    return result


# ============================================================
# HTTP-Fehler
# ============================================================


def _is_retryable_status_code(
    status_code: int,
) -> bool:
    """
    Kennzeichnet typischerweise vorübergehende HTTP-Fehler.
    """

    return status_code in {
        408,
        409,
        425,
        429,
        500,
        502,
        503,
        504,
    }


def _create_http_status_reason(
    response: httpx.Response,
) -> str:
    """
    Erstellt eine begrenzte, aussagekräftige Fehlermeldung.
    """

    body = response.text.strip()

    if len(
        body,
    ) > 1000:
        body = f"{body[:1000]}…"

    if body:
        return (
            f"HTTP {response.status_code}: {body}"
        )

    return (
        f"HTTP {response.status_code}: "
        f"{response.reason_phrase}"
    )


def _create_error_event(
    error: HTTPGenericRequestError,
) -> StreamEvent:
    """
    Erstellt ein strukturiertes Fehlerereignis.
    """

    data: JsonObject = {
        "backend": "http_generic",
        "url": error.url,
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


# ============================================================
# Registry-Factory
# ============================================================


def create_http_generic_backend(
    *,
    provider_config: JsonMapping,
    dependencies: ProviderDependencies | None = None,
) -> BaseModelBackend:
    """
    Factory für die feste Modell-Provider-Registry.
    """

    del dependencies

    return HTTPGenericProvider(
        provider_config,
    )


__all__ = [
    "HTTPGenericConfigurationError",
    "HTTPGenericModelNotFoundError",
    "HTTPGenericProvider",
    "HTTPGenericProviderError",
    "HTTPGenericRequestError",
    "HTTPGenericResponseError",
    "create_http_generic_backend",
]