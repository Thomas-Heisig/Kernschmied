from __future__ import annotations

import asyncio
import importlib
import logging
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Final, Protocol, TypeAlias, cast

from pydantic import TypeAdapter, ValidationError

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
LlamaMessage: TypeAlias = dict[str, str]
LlamaChunk: TypeAlias = dict[str, JsonValue]

DEFAULT_MODEL_ID: Final[str] = "llama-cpp"
DEFAULT_CONTEXT_SIZE: Final[int] = 8192
DEFAULT_GPU_LAYERS: Final[int] = -1
DEFAULT_MAX_TOKENS: Final[int] = 4096
DEFAULT_TOP_P: Final[float] = 0.95

_CHUNK_ADAPTER: Final[TypeAdapter[LlamaChunk]] = TypeAdapter(
    LlamaChunk,
)


class LlamaInstanceProtocol(Protocol):
    """Minimaler, stabiler Vertrag der verwendeten llama.cpp-Instanz."""

    def create_chat_completion(
        self,
        *,
        messages: list[LlamaMessage],
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop: list[str] | None,
        stream: bool,
    ) -> Iterator[object]: ...


class LlamaFactoryProtocol(Protocol):
    """Minimaler Konstruktorvertrag von ``llama_cpp.Llama``."""

    def __call__(
        self,
        **kwargs: object,
    ) -> LlamaInstanceProtocol: ...


LlamaFactory: TypeAlias = LlamaFactoryProtocol


class LlamaCppProviderError(RuntimeError):
    """Basisklasse kontrollierter llama.cpp-Providerfehler."""


class LlamaCppConfigurationError(LlamaCppProviderError):
    """Die Provider-Konfiguration oder Anfrage ist ungültig."""


class LlamaCppModelNotFoundError(LlamaCppProviderError):
    """Das angeforderte lokale Modell ist nicht freigegeben."""


@dataclass(frozen=True, slots=True)
class _StreamChunk:
    value: object


@dataclass(frozen=True, slots=True)
class _StreamFailure:
    error: BaseException


@dataclass(frozen=True, slots=True)
class _StreamEnd:
    pass


StreamQueueItem: TypeAlias = _StreamChunk | _StreamFailure | _StreamEnd
_STREAM_END: Final[_StreamEnd] = _StreamEnd()


def _load_llama_factory() -> LlamaFactory | None:
    """Lädt ausschließlich die fest bekannte optionale Abhängigkeit."""

    try:
        module: ModuleType = importlib.import_module(
            "llama_cpp",
        )
    except ImportError:
        logger.info(
            "llama-cpp-python ist nicht installiert. "
            "Der llama.cpp-Provider bleibt deaktiviert.",
        )
        return None
    except Exception:
        logger.exception(
            "llama-cpp-python konnte nicht initialisiert werden.",
        )
        return None

    raw_factory: object = getattr(
        module,
        "Llama",
        None,
    )

    if not callable(raw_factory):
        logger.error(
            "llama_cpp.Llama ist nicht verfügbar oder nicht aufrufbar.",
        )
        return None

    return cast(
        LlamaFactory,
        raw_factory,
    )


_LLAMA_FACTORY: Final[LlamaFactory | None] = _load_llama_factory()


class LlamaCppProvider(BaseModelBackend):
    """Lokales Chat-Backend für GGUF-Modelle über llama-cpp-python."""

    def get_model_info(
        self,
    ) -> ModelInfo:
        """
        Liefert die Beschreibung des durch diese Providerinstanz
        repräsentierten Modells.
        """

        return self._create_model_info()

    def __init__(
        self,
        config: JsonMapping,
    ) -> None:
        self._model_path = _read_optional_string(
            config,
            "path",
        )

        configured_model_id = _read_optional_string(
            config,
            "default_model",
        )

        inferred_model_id = (
            Path(self._model_path).stem
            if self._model_path is not None
            else DEFAULT_MODEL_ID
        )

        self._model_id = configured_model_id or inferred_model_id
        self._n_ctx = _read_positive_int(
            config,
            "n_ctx",
            default=DEFAULT_CONTEXT_SIZE,
        )
        self._n_gpu_layers = _read_int(
            config,
            "n_gpu_layers",
            default=DEFAULT_GPU_LAYERS,
        )
        self._chat_format = _read_optional_string(
            config,
            "chat_format",
        )

        self._model: LlamaInstanceProtocol | None = None
        self._load_lock = asyncio.Lock()

    @property
    def backend_name(self) -> str:
        return "llama_cpp"

    async def is_available(self) -> bool:
        """Prüft nur Bibliothek und lokalen Modellpfad."""

        if _LLAMA_FACTORY is None or self._model_path is None:
            return False

        try:
            return await asyncio.to_thread(
                Path(self._model_path).is_file,
            )
        except OSError:
            return False

    async def list_models(self) -> list[ModelInfo]:
        return [
            self._create_model_info(),
        ]

    async def get_model(
        self,
        model_id: str,
    ) -> ModelInfo:
        resolved_model_id = model_id.strip() or self._model_id

        if resolved_model_id != self._model_id:
            raise LlamaCppModelNotFoundError(
                f"Das llama.cpp-Modell '{resolved_model_id}' ist nicht freigegeben.",
            )

        return self._create_model_info()

    def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        return self._stream_request(
            request,
        )

    async def shutdown(self) -> None:
        """Gibt die lokale Modellreferenz kontrolliert frei."""

        async with self._load_lock:
            self._model = None

    async def _stream_request(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        model_id = request.model.strip() or self._model_id

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
                model_id=model_id,
            )

            model = await self._get_model_instance()
            messages = _convert_messages(
                request.messages,
            )
            max_tokens = _resolve_max_tokens(
                request.max_tokens,
            )
            temperature = _normalize_temperature(
                request.temperature,
            )
            top_p = _normalize_top_p(
                request.top_p,
            )
            stop_sequences = _normalize_stop_sequences(
                request.stop,
            )

            queue: asyncio.Queue[StreamQueueItem] = asyncio.Queue()
            loop = asyncio.get_running_loop()

            producer_task = asyncio.create_task(
                asyncio.to_thread(
                    _produce_chunks,
                    model,
                    messages,
                    max_tokens,
                    temperature,
                    top_p,
                    stop_sequences,
                    loop,
                    queue,
                ),
            )

            finish_reason: str | None = None

            while True:
                item = await queue.get()

                if isinstance(item, _StreamEnd):
                    break

                if isinstance(item, _StreamFailure):
                    raise item.error

                parsed_chunk = _parse_chunk(
                    item.value,
                )

                chunk_finish_reason = _read_finish_reason(
                    parsed_chunk,
                )

                if chunk_finish_reason is not None:
                    finish_reason = chunk_finish_reason

                content = _read_content(
                    parsed_chunk,
                )

                if content:
                    yield StreamEvent.create(
                        type=StreamEventType.TOKEN,
                        content=content,
                    )

            await producer_task

            end_data: dict[str, JsonValue] = {
                "backend": self.backend_name,
                "model": model_id,
            }

            if finish_reason is not None:
                end_data["finish_reason"] = finish_reason

            yield StreamEvent.create(
                type=StreamEventType.COMPLETE,
                data=end_data,
            )

        except LlamaCppProviderError as exc:
            logger.exception(
                "llama.cpp provider rejected the request",
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
            logger.exception(
                "Unexpected llama.cpp provider error",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "error_type": type(exc).__name__,
                },
            )

            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=(
                    "Bei der lokalen llama.cpp-Generierung ist ein "
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
        *,
        model_id: str,
    ) -> None:
        if model_id != self._model_id:
            raise LlamaCppModelNotFoundError(
                f"Das llama.cpp-Modell '{model_id}' ist nicht freigegeben.",
            )

        if request.tools:
            raise LlamaCppConfigurationError(
                "Tool-Aufrufe sind in dieser llama.cpp-Provider-Version "
                "noch nicht implementiert.",
            )

        if request.tool_choice is not None:
            raise LlamaCppConfigurationError(
                "llama.cpp tool_choice wird in dieser Provider-Version "
                "noch nicht unterstützt.",
            )

    async def _get_model_instance(
        self,
    ) -> LlamaInstanceProtocol:
        model = self._model

        if model is not None:
            return model

        async with self._load_lock:
            model = self._model

            if model is not None:
                return model

            factory = _LLAMA_FACTORY

            if factory is None:
                raise LlamaCppConfigurationError(
                    "llama-cpp-python ist nicht installiert.",
                )

            model_path = self._model_path

            if model_path is None:
                raise LlamaCppConfigurationError(
                    "Der GGUF-Modellpfad fehlt.",
                )

            path = Path(
                model_path,
            )

            if not await asyncio.to_thread(path.is_file):
                raise LlamaCppConfigurationError(
                    "Der konfigurierte GGUF-Modellpfad ist ungültig.",
                )

            factory_kwargs: dict[str, object] = {
                "model_path": model_path,
                "n_ctx": self._n_ctx,
                "n_gpu_layers": self._n_gpu_layers,
                "verbose": False,
            }

            if self._chat_format is not None:
                factory_kwargs["chat_format"] = self._chat_format

            loaded_model = await asyncio.to_thread(
                factory,
                **factory_kwargs,
            )

            self._model = loaded_model

            return loaded_model

    def _create_model_info(self) -> ModelInfo:
        return ModelInfo.create(
            id=self._model_id,
            backend=self.backend_name,
            display_name=self._model_id,
            provider="llama.cpp",
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.COMPLETION,
                ModelCapability.STREAMING,
            },
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            metadata={
                "configured": self._model_path is not None,
                "remote": False,
                "path": self._model_path,
                "n_ctx": self._n_ctx,
                "n_gpu_layers": self._n_gpu_layers,
            },
        )


def _produce_chunks(
    model: LlamaInstanceProtocol,
    messages: list[LlamaMessage],
    max_tokens: int,
    temperature: float,
    top_p: float,
    stop_sequences: list[str] | None,
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue[StreamQueueItem],
) -> None:
    try:
        response = model.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop_sequences,
            stream=True,
        )

        for chunk in response:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                _StreamChunk(
                    chunk,
                ),
            )

    except BaseException as exc:
        loop.call_soon_threadsafe(
            queue.put_nowait,
            _StreamFailure(
                exc,
            ),
        )

    finally:
        loop.call_soon_threadsafe(
            queue.put_nowait,
            _STREAM_END,
        )


def _parse_chunk(
    value: object,
) -> LlamaChunk:
    try:
        return _CHUNK_ADAPTER.validate_python(
            value,
        )
    except ValidationError as exc:
        raise LlamaCppProviderError(
            "llama.cpp lieferte ein ungültiges Streaming-Ereignis.",
        ) from exc


def _read_finish_reason(
    chunk: LlamaChunk,
) -> str | None:
    choices = chunk.get(
        "choices",
    )

    if not isinstance(choices, list) or not choices:
        return None

    first_choice = choices[0]

    if not isinstance(first_choice, dict):
        return None

    finish_reason = first_choice.get(
        "finish_reason",
    )

    return finish_reason if isinstance(finish_reason, str) else None


def _read_content(
    chunk: LlamaChunk,
) -> str | None:
    choices = chunk.get(
        "choices",
    )

    if not isinstance(choices, list) or not choices:
        return None

    first_choice = choices[0]

    if not isinstance(first_choice, dict):
        return None

    delta = first_choice.get(
        "delta",
    )

    if not isinstance(delta, dict):
        return None

    content = delta.get(
        "content",
    )

    return content if isinstance(content, str) and content else None


def _convert_messages(
    messages: Sequence[ChatMessage],
) -> list[LlamaMessage]:
    result: list[LlamaMessage] = []

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
        raise LlamaCppConfigurationError(
            "Die llama.cpp-Anfrage enthält keine verwendbare Nachricht.",
        )

    return result


def _resolve_max_tokens(
    value: int | None,
) -> int:
    if value is None:
        return DEFAULT_MAX_TOKENS

    if value <= 0:
        raise LlamaCppConfigurationError(
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

    if value <= 0.0 or value > 1.0:
        raise LlamaCppConfigurationError(
            "top_p muss größer als null und höchstens 1 sein.",
        )

    return value


def _normalize_stop_sequences(
    value: list[str] | None,
) -> list[str] | None:
    if value is None:
        return None

    normalized = [item.strip() for item in value if item.strip()]

    return normalized or None


def _read_optional_string(
    config: JsonMapping,
    key: str,
) -> str | None:
    value = config.get(
        key,
    )

    if not isinstance(value, str):
        return None

    normalized = value.strip()

    return normalized or None


def _read_positive_int(
    config: JsonMapping,
    key: str,
    *,
    default: int,
) -> int:
    value = config.get(
        key,
    )

    if isinstance(value, bool):
        return default

    if isinstance(value, int) and value > 0:
        return value

    return default


def _read_int(
    config: JsonMapping,
    key: str,
    *,
    default: int,
) -> int:
    value = config.get(
        key,
    )

    if isinstance(value, bool):
        return default

    if isinstance(value, int):
        return value

    return default


def create_llama_cpp_backend(
    *,
    provider_config: JsonMapping,
    dependencies: ProviderDependencies | None = None,
) -> BaseModelBackend:
    """Factory für die feste Modell-Provider-Registry."""

    del dependencies

    return LlamaCppProvider(
        provider_config,
    )


__all__ = [
    "LlamaCppConfigurationError",
    "LlamaCppModelNotFoundError",
    "LlamaCppProvider",
    "LlamaCppProviderError",
    "create_llama_cpp_backend",
]
