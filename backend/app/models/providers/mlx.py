from __future__ import annotations

import asyncio
import importlib
import logging
import platform
from collections.abc import (
    AsyncIterator,
    Iterator,
    Mapping,
    Sequence,
)
from pathlib import Path
from types import ModuleType
from typing import Protocol, TypeAlias, cast, runtime_checkable

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
)


logger = logging.getLogger(__name__)


ProviderDependencies: TypeAlias = Mapping[str, object]
ConvertedMessage: TypeAlias = dict[str, str]
ConvertedMessages: TypeAlias = list[ConvertedMessage]

DEFAULT_MODEL_ID = "mlx"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 1.0


class MLXProviderError(RuntimeError):
    """
    Basisklasse für kontrollierte Fehler des MLX-Providers.
    """


class MLXConfigurationError(
    MLXProviderError,
):
    """
    Die MLX-Konfiguration oder Anfrage ist ungültig.
    """


class MLXModelNotFoundError(
    MLXProviderError,
):
    """
    Das angeforderte MLX-Modell ist nicht freigegeben.
    """


@runtime_checkable
class MLXTokenizerProtocol(Protocol):
    """
    Minimaler Vertrag eines MLX-kompatiblen Tokenizers.
    """

    def apply_chat_template(
        self,
        conversation: Sequence[Mapping[str, str]],
        *,
        tokenize: bool,
        add_generation_prompt: bool,
    ) -> object:
        ...


@runtime_checkable
class MLXGenerationResponseProtocol(Protocol):
    """
    Minimaler Vertrag eines Stream-Generation-Ergebnisses.
    """

    @property
    def text(
        self,
    ) -> str:
        ...


class MLXLoadProtocol(Protocol):
    """
    Vertrag für mlx_lm.load().
    """

    def __call__(
        self,
        model_path: str,
    ) -> tuple[object, object]:
        ...


class MLXStreamGenerateProtocol(Protocol):
    """
    Vertrag für mlx_lm.stream_generate().
    """

    def __call__(
        self,
        model: object,
        tokenizer: object,
        *,
        prompt: str,
        max_tokens: int,
        temp: float,
        top_p: float,
    ) -> Iterator[object]:
        ...


class MLXBindings:
    """
    Fest typisierte Referenzen auf die optionale mlx-lm-Bibliothek.
    """

    def __init__(
        self,
        *,
        load_model: MLXLoadProtocol,
        stream_generate: MLXStreamGenerateProtocol,
    ) -> None:
        self.load_model = load_model
        self.stream_generate = stream_generate


class _StreamToken:
    """
    Textfragment aus dem MLX-Worker.
    """

    def __init__(
        self,
        text: str,
    ) -> None:
        self.text = text


class _StreamFailure:
    """
    Fehler aus dem MLX-Worker.
    """

    def __init__(
        self,
        error: BaseException,
    ) -> None:
        self.error = error


class _StreamEnd:
    """
    Markiert das Ende des MLX-Streams.
    """


StreamQueueItem: TypeAlias = (
    _StreamToken
    | _StreamFailure
    | _StreamEnd
)


def _load_mlx_bindings(
) -> MLXBindings | None:
    """
    Lädt mlx-lm ausschließlich über einen festen Modulnamen.

    Eine fehlende optionale Abhängigkeit verhindert nicht den Start
    der Kernanwendung.
    """

    try:
        mlx_lm_module: ModuleType = importlib.import_module(
            "mlx_lm",
        )

    except ImportError:
        logger.info(
            "mlx-lm ist nicht installiert. "
            "Der MLX-Provider bleibt deaktiviert.",
        )
        return None

    except Exception:
        logger.exception(
            "mlx-lm konnte nicht initialisiert werden.",
        )
        return None

    raw_load: object = getattr(
        mlx_lm_module,
        "load",
        None,
    )

    raw_stream_generate: object = getattr(
        mlx_lm_module,
        "stream_generate",
        None,
    )

    if not callable(
        raw_load,
    ):
        logger.error(
            "mlx_lm.load ist nicht verfügbar.",
        )
        return None

    if not callable(
        raw_stream_generate,
    ):
        logger.error(
            "mlx_lm.stream_generate ist nicht verfügbar.",
        )
        return None

    return MLXBindings(
        load_model=cast(
            MLXLoadProtocol,
            raw_load,
        ),
        stream_generate=cast(
            MLXStreamGenerateProtocol,
            raw_stream_generate,
        ),
    )


_MLX_BINDINGS = _load_mlx_bindings()


class MLXProvider(
    BaseModelBackend,
):
    """
    Lokaler Modellprovider auf Basis von Apple MLX.

    MLX wird ausschließlich auf macOS mit Apple Silicon als verfügbar
    betrachtet. Das konfigurierte Modell wird nicht automatisch
    freigegeben oder dynamisch erkannt.
    """

    def __init__(
        self,
        config: JsonMapping,
    ) -> None:
        self._model_path = (
            _read_optional_string(
                config,
                "path",
            )
            or _read_optional_string(
                config,
                "model_name",
            )
        )

        configured_model_id = _read_optional_string(
            config,
            "default_model",
        )

        if configured_model_id is not None:
            self._model_id = configured_model_id

        elif self._model_path is not None:
            model_name = Path(
                self._model_path,
            ).name.strip()

            self._model_id = (
                model_name
                if model_name
                else DEFAULT_MODEL_ID
            )

        else:
            self._model_id = DEFAULT_MODEL_ID

        self._local_files_only = _read_bool(
            config,
            "local_files_only",
            default=True,
        )

        self._model: object | None = None
        self._tokenizer: object | None = None
        self._load_lock = asyncio.Lock()

    @property
    def backend_name(
        self,
    ) -> str:
        return "mlx"

    async def is_available(
        self,
    ) -> bool:
        """
        Prüft Plattform, Bibliothek und Modellkonfiguration.
        """

        if platform.system() != "Darwin":
            return False

        machine = platform.machine().lower()

        if machine not in {
            "arm64",
            "aarch64",
        }:
            return False

        if _MLX_BINDINGS is None:
            return False

        if self._model_path is None:
            return False

        if not self._local_files_only:
            return True

        model_path = Path(
            self._model_path,
        ).expanduser()

        try:
            return await asyncio.to_thread(
                model_path.exists,
            )

        except OSError:
            return False

    async def list_models(
        self,
    ) -> list[ModelInfo]:
        return [
            self._create_model_info(),
        ]

    async def get_model(
        self,
        model_id: str,
    ) -> ModelInfo:
        self._resolve_model_id(
            model_id,
        )

        return self._create_model_info()

    def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        return self._stream_request(
            request,
        )

    async def shutdown(
        self,
    ) -> None:
        """
        Entfernt die Modellreferenzen.

        MLX besitzt hier keinen dauerhaft geöffneten Netzwerkclient.
        """

        async with self._load_lock:
            self._model = None
            self._tokenizer = None

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

            model, tokenizer = await self._ensure_loaded()

            prompt = _create_prompt(
                tokenizer,
                request.messages,
            )

            bindings = _require_mlx_bindings()

            max_tokens = _resolve_max_tokens(
                request.max_tokens,
            )

            temperature = _normalize_temperature(
                request.temperature,
            )

            top_p = _normalize_top_p(
                request.top_p,
            )

            queue: asyncio.Queue[StreamQueueItem] = (
                asyncio.Queue()
            )

            event_loop = asyncio.get_running_loop()

            def produce() -> None:
                try:
                    responses = bindings.stream_generate(
                        model,
                        tokenizer,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temp=temperature,
                        top_p=top_p,
                    )

                    for raw_response in responses:
                        text = _read_generation_text(
                            raw_response,
                        )

                        if not text:
                            continue

                        event_loop.call_soon_threadsafe(
                            queue.put_nowait,
                            _StreamToken(
                                text,
                            ),
                        )

                except BaseException as exc:
                    event_loop.call_soon_threadsafe(
                        queue.put_nowait,
                        _StreamFailure(
                            exc,
                        ),
                    )

                finally:
                    event_loop.call_soon_threadsafe(
                        queue.put_nowait,
                        _StreamEnd(),
                    )

            producer_task = asyncio.create_task(
                asyncio.to_thread(
                    produce,
                ),
            )

            while True:
                queue_item = await queue.get()

                if isinstance(
                    queue_item,
                    _StreamEnd,
                ):
                    break

                if isinstance(
                    queue_item,
                    _StreamFailure,
                ):
                    raise queue_item.error

                yield StreamEvent.create(
                    type=StreamEventType.TOKEN,
                    content=queue_item.text,
                )

            await producer_task

            yield StreamEvent.create(
                type=StreamEventType.END,
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "finish_reason": "stop",
                },
            )

        except MLXProviderError as exc:
            logger.exception(
                "MLX provider rejected the request",
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
                "Unexpected MLX provider error",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "error_type": type(exc).__name__,
                },
            )

            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=(
                    "Bei der lokalen MLX-Generierung ist ein "
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
        if request.tools:
            raise MLXConfigurationError(
                "Tool-Aufrufe sind in dieser MLX-Provider-Version "
                "noch nicht implementiert.",
            )

        if request.tool_choice is not None:
            raise MLXConfigurationError(
                "tool_choice wird in dieser MLX-Provider-Version "
                "noch nicht unterstützt.",
            )

        if request.stop:
            raise MLXConfigurationError(
                "Stop-Sequenzen werden in dieser MLX-Provider-Version "
                "noch nicht unterstützt.",
            )

    async def _ensure_loaded(
        self,
    ) -> tuple[object, object]:
        if (
            self._model is not None
            and self._tokenizer is not None
        ):
            return (
                self._model,
                self._tokenizer,
            )

        async with self._load_lock:
            if (
                self._model is not None
                and self._tokenizer is not None
            ):
                return (
                    self._model,
                    self._tokenizer,
                )

            if self._model_path is None:
                raise MLXConfigurationError(
                    "Für den MLX-Provider fehlt "
                    "'model_name' oder 'path'.",
                )

            if self._local_files_only:
                model_path = Path(
                    self._model_path,
                ).expanduser()

                exists = await asyncio.to_thread(
                    model_path.exists,
                )

                if not exists:
                    raise MLXConfigurationError(
                        "Der konfigurierte lokale MLX-Modellpfad "
                        "existiert nicht.",
                    )

            bindings = _require_mlx_bindings()

            model, tokenizer = await asyncio.to_thread(
                bindings.load_model,
                self._model_path,
            )

            self._model = model
            self._tokenizer = tokenizer

            return (
                model,
                tokenizer,
            )

    def _resolve_model_id(
        self,
        requested_model_id: str,
    ) -> str:
        normalized_model_id = requested_model_id.strip()

        model_id = (
            normalized_model_id
            if normalized_model_id
            else self._model_id
        )

        if model_id != self._model_id:
            raise MLXModelNotFoundError(
                f"Das MLX-Modell '{model_id}' "
                "ist nicht freigegeben.",
            )

        return model_id

    def _create_model_info(
        self,
    ) -> ModelInfo:
        capabilities: set[ModelCapability] = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.STREAMING,
        }

        metadata: dict[str, JsonValue] = {
            "configured": self._model_path is not None,
            "remote": not self._local_files_only,
            "local_files_only": self._local_files_only,
            "platform": "apple_silicon",
        }

        if self._model_path is not None:
            metadata["path"] = self._model_path

        return ModelInfo.create(
            id=self._model_id,
            backend=self.backend_name,
            display_name=self._model_id,
            provider="Apple MLX",
            capabilities=capabilities,
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            metadata=metadata,
        )


def _require_mlx_bindings(
) -> MLXBindings:
    if _MLX_BINDINGS is None:
        raise MLXConfigurationError(
            "Der MLX-Provider benötigt das Paket 'mlx-lm' "
            "auf einem Apple-Silicon-Mac.",
        )

    return _MLX_BINDINGS


def _read_generation_text(
    value: object,
) -> str:
    """
    Liest das inkrementelle Textfragment aus einer MLX-Antwort.
    """

    if isinstance(
        value,
        MLXGenerationResponseProtocol,
    ):
        return value.text

    raw_text: object = getattr(
        value,
        "text",
        None,
    )

    if isinstance(
        raw_text,
        str,
    ):
        return raw_text

    raise MLXConfigurationError(
        "mlx_lm.stream_generate() lieferte ein "
        "unbekanntes Antwortformat.",
    )


def _create_prompt(
    tokenizer: object,
    messages: Sequence[ChatMessage],
) -> str:
    converted_messages = _convert_messages(
        messages,
    )

    if isinstance(
        tokenizer,
        MLXTokenizerProtocol,
    ):
        try:
            rendered = tokenizer.apply_chat_template(
                converted_messages,
                tokenize=False,
                add_generation_prompt=True,
            )

        except Exception:
            logger.exception(
                "Das MLX-Chat-Template konnte nicht angewendet "
                "werden. Verwende Fallback-Prompt.",
            )

        else:
            if isinstance(
                rendered,
                str,
            ) and rendered:
                return rendered

    prompt_parts: list[str] = []

    for message in converted_messages:
        prompt_parts.append(
            f"{message['role']}: {message['content']}",
        )

    prompt_parts.append(
        "assistant:",
    )

    return "\n".join(
        prompt_parts,
    )


def _convert_messages(
    messages: Sequence[ChatMessage],
) -> ConvertedMessages:
    result: ConvertedMessages = []

    for message in messages:
        content = message.content.strip()

        if not content:
            continue

        role = "user"

        if message.role is MessageRole.SYSTEM:
            role = "system"

        elif message.role is MessageRole.ASSISTANT:
            role = "assistant"

        elif message.role is MessageRole.TOOL:
            role = "tool"

        result.append(
            {
                "role": role,
                "content": content,
            },
        )

    if not result:
        raise MLXConfigurationError(
            "Die MLX-Anfrage enthält keine verwendbare Nachricht.",
        )

    return result


def _resolve_max_tokens(
    value: int | None,
) -> int:
    if value is None:
        return DEFAULT_MAX_TOKENS

    if value <= 0:
        raise MLXConfigurationError(
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


def _normalize_top_p(
    value: float | None,
) -> float:
    if value is None:
        return DEFAULT_TOP_P

    if value <= 0.0:
        raise MLXConfigurationError(
            "top_p muss größer als null sein.",
        )

    if value > 1.0:
        raise MLXConfigurationError(
            "top_p darf nicht größer als 1 sein.",
        )

    return value


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


def _read_bool(
    config: JsonMapping,
    key: str,
    *,
    default: bool,
) -> bool:
    value = config.get(
        key,
    )

    if not isinstance(
        value,
        bool,
    ):
        return default

    return value


def create_mlx_backend(
    *,
    provider_config: JsonMapping,
    dependencies: ProviderDependencies | None = None,
) -> BaseModelBackend:
    """
    Factory für die feste Modell-Provider-Registry.
    """

    del dependencies

    return MLXProvider(
        provider_config,
    )


__all__ = [
    "MLXConfigurationError",
    "MLXModelNotFoundError",
    "MLXProvider",
    "MLXProviderError",
    "create_mlx_backend",
]