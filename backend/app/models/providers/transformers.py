# F:\Kernschmied\backend\app\models\providers\transformers.py

from __future__ import annotations

import asyncio
import importlib
import logging
from collections.abc import (
    AsyncIterator,
    Callable,
    Iterator,
    Mapping,
    Sequence,
)
from pathlib import Path
from types import ModuleType
from typing import Protocol, TypeAlias, runtime_checkable

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
PretrainedArguments: TypeAlias = dict[str, object]
GenerationArguments: TypeAlias = dict[str, object]


DEFAULT_MODEL_ID = "transformers"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_DEVICE_MAP = "auto"


# ============================================================
# Kontrollierte Providerfehler
# ============================================================


class TransformersProviderError(RuntimeError):
    """
    Basisklasse für kontrollierte Transformers-Providerfehler.
    """


class TransformersConfigurationError(
    TransformersProviderError,
):
    """
    Die Providerkonfiguration oder Anfrage ist ungültig.
    """


class TransformersModelNotFoundError(
    TransformersProviderError,
):
    """
    Das angeforderte Modell ist nicht freigegeben.
    """


# ============================================================
# Interne Verträge für optionale Bibliotheken
# ============================================================


@runtime_checkable
class TensorProtocol(Protocol):
    """
    Minimaler Vertrag eines Torch-Tensors.
    """

    def to(
        self,
        device: object,
    ) -> TensorProtocol:
        ...


@runtime_checkable
class TokenizerProtocol(Protocol):
    """
    Minimaler Vertrag des verwendeten Tokenizers.
    """

    def __call__(
        self,
        text: str,
        *,
        return_tensors: str,
    ) -> Mapping[str, object]:
        ...


@runtime_checkable
class ModelProtocol(Protocol):
    """
    Minimaler Vertrag eines kausalen Sprachmodells.
    """

    def generate(
        self,
        **kwargs: object,
    ) -> object:
        ...


@runtime_checkable
class PretrainedFactoryProtocol(Protocol):
    """
    Vertrag der Transformers-AutoFactory-Klassen.
    """

    def from_pretrained(
        self,
        pretrained_model_name_or_path: str,
        **kwargs: object,
    ) -> object:
        ...


@runtime_checkable
class ObjectIterableProtocol(Protocol):
    """
    Synchroner Iteratorvertrag ohne unbekannte Elementtypen.
    """

    def __iter__(
        self,
    ) -> Iterator[object]:
        ...


@runtime_checkable
class TorchCudaProtocol(Protocol):
    """
    Benötigter Teil von ``torch.cuda``.
    """

    def is_available(
        self,
    ) -> bool:
        ...

    def empty_cache(
        self,
    ) -> None:
        ...


StreamerFactory: TypeAlias = Callable[..., object]


class TransformersBindings:
    """
    Fest aufgelöste Referenzen auf optionale ML-Bibliotheken.

    Modellkonfigurationen können keine beliebigen Module oder
    Python-Importpfade bestimmen.
    """

    def __init__(
        self,
        *,
        tokenizer_factory: PretrainedFactoryProtocol,
        model_factory: PretrainedFactoryProtocol,
        streamer_factory: StreamerFactory,
        cuda: TorchCudaProtocol,
    ) -> None:
        self.tokenizer_factory = tokenizer_factory
        self.model_factory = model_factory
        self.streamer_factory = streamer_factory
        self.cuda = cuda


def _load_transformers_bindings(
) -> TransformersBindings | None:
    """
    Lädt Torch und Transformers ausschließlich über fest bekannte Namen.

    Fehlende optionale Abhängigkeiten verhindern nicht den Start der
    Kernanwendung.
    """

    try:
        torch_module: ModuleType = importlib.import_module(
            "torch",
        )
        transformers_module: ModuleType = importlib.import_module(
            "transformers",
        )

    except ImportError:
        logger.info(
            "Torch oder Transformers ist nicht installiert. "
            "Der Transformers-Provider bleibt deaktiviert.",
        )
        return None

    except Exception:
        logger.exception(
            "Torch oder Transformers konnte nicht initialisiert werden.",
        )
        return None

    raw_cuda: object = getattr(
        torch_module,
        "cuda",
        None,
    )

    raw_tokenizer_factory: object = getattr(
        transformers_module,
        "AutoTokenizer",
        None,
    )

    raw_model_factory: object = getattr(
        transformers_module,
        "AutoModelForCausalLM",
        None,
    )

    raw_streamer_factory: object = getattr(
        transformers_module,
        "TextIteratorStreamer",
        None,
    )

    if not isinstance(
        raw_cuda,
        TorchCudaProtocol,
    ):
        logger.error(
            "torch.cuda erfüllt nicht den benötigten Vertrag.",
        )
        return None

    if not isinstance(
        raw_tokenizer_factory,
        PretrainedFactoryProtocol,
    ):
        logger.error(
            "transformers.AutoTokenizer ist nicht verfügbar.",
        )
        return None

    if not isinstance(
        raw_model_factory,
        PretrainedFactoryProtocol,
    ):
        logger.error(
            "transformers.AutoModelForCausalLM ist nicht verfügbar.",
        )
        return None

    if not callable(
        raw_streamer_factory,
    ):
        logger.error(
            "transformers.TextIteratorStreamer ist nicht verfügbar.",
        )
        return None

    return TransformersBindings(
        tokenizer_factory=raw_tokenizer_factory,
        model_factory=raw_model_factory,
        streamer_factory=raw_streamer_factory,
        cuda=raw_cuda,
    )


_TRANSFORMERS_BINDINGS = _load_transformers_bindings()


# ============================================================
# Provider
# ============================================================


class TransformersProvider(
    BaseModelBackend,
):
    """
    Lokaler Provider für Hugging-Face-Transformers-Modelle.

    Unterstützte Konfiguration:

    - ``path``:
      Lokaler Modellpfad.

    - ``model_name``:
      Alternativ ein Modellname oder ein Modellpfad.

    - ``default_model``:
      Öffentliche Modell-ID innerhalb der Kernschmied-Registry.

    - ``local_files_only``:
      Verhindert standardmäßig Netzwerkdownloads.

    - ``trust_remote_code``:
      Bleibt standardmäßig deaktiviert.

    - ``device_map``:
      Transformers-Gerätezuordnung, standardmäßig ``auto``.

    Sicherheitsgrenzen:

    - Remote-Code wird niemals implizit freigegeben.
    - Netzwerkzugriffe sind standardmäßig deaktiviert.
    - Es wird immer nur das explizit konfigurierte Modell angeboten.
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
            path_name = Path(
                self._model_path,
            ).name.strip()

            self._model_id = (
                path_name
                if path_name
                else DEFAULT_MODEL_ID
            )

        else:
            self._model_id = DEFAULT_MODEL_ID

        self._trust_remote_code = _read_bool(
            config,
            "trust_remote_code",
            default=False,
        )

        self._local_files_only = _read_bool(
            config,
            "local_files_only",
            default=True,
        )

        self._device_map = (
            _read_optional_string(
                config,
                "device_map",
            )
            or DEFAULT_DEVICE_MAP
        )

        self._model: ModelProtocol | None = None
        self._tokenizer: TokenizerProtocol | None = None

        self._load_lock = asyncio.Lock()

    @property
    def backend_name(
        self,
    ) -> str:
        return "transformers"

    async def is_available(
        self,
    ) -> bool:
        """
        Prüft nur die Abhängigkeiten und lokale Konfiguration.

        Das Modell wird nicht geladen.
        """

        if _TRANSFORMERS_BINDINGS is None:
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
        """
        Liefert ausschließlich das explizit konfigurierte Modell.
        """

        return [
            self._create_model_info(),
        ]

    async def get_model(
        self,
        model_id: str,
    ) -> ModelInfo:
        """
        Liefert das freigegebene Modell oder lehnt die ID ab.
        """

        resolved_model_id = self._resolve_model_id(
            model_id,
        )

        if resolved_model_id != self._model_id:
            raise TransformersModelNotFoundError(
                f"Das Transformers-Modell '{resolved_model_id}' "
                "ist nicht freigegeben.",
            )

        return self._create_model_info()

    def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[StreamEvent]:
        """
        Liefert unmittelbar einen asynchronen Stream.
        """

        return self._stream_request(
            request,
        )

    async def shutdown(
        self,
    ) -> None:
        """
        Entfernt Modell- und Tokenizerreferenzen und leert optional CUDA.
        """

        async with self._load_lock:
            self._model = None
            self._tokenizer = None

        bindings = _TRANSFORMERS_BINDINGS

        if bindings is None:
            return

        try:
            if bindings.cuda.is_available():
                await asyncio.to_thread(
                    bindings.cuda.empty_cache,
                )

        except Exception:
            logger.exception(
                "Der CUDA-Cache konnte nicht geleert werden.",
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

            model, tokenizer = await self._ensure_loaded()

            prompt = _create_prompt(
                tokenizer,
                request.messages,
            )

            bindings = _require_transformers_bindings()

            raw_streamer = bindings.streamer_factory(
                tokenizer,
                skip_prompt=True,
                skip_special_tokens=True,
            )

            streamer_iterator = _require_object_iterator(
                raw_streamer,
            )

            tokenizer_output = tokenizer(
                prompt,
                return_tensors="pt",
            )

            input_ids = _require_tensor_from_mapping(
                tokenizer_output,
                "input_ids",
            )

            attention_mask = _read_optional_tensor_from_mapping(
                tokenizer_output,
                "attention_mask",
            )

            device = _read_optional_attribute(
                model,
                "device",
            )

            if device is not None:
                input_ids = input_ids.to(
                    device,
                )

                if attention_mask is not None:
                    attention_mask = attention_mask.to(
                        device,
                    )

            generation_arguments: GenerationArguments = {
                "input_ids": input_ids,
                "streamer": raw_streamer,
                "max_new_tokens": _resolve_max_tokens(
                    request.max_tokens,
                ),
                "temperature": _normalize_temperature(
                    request.temperature,
                ),
                "do_sample": request.temperature > 0.0,
            }

            if attention_mask is not None:
                generation_arguments["attention_mask"] = (
                    attention_mask
                )

            top_p = _normalize_optional_top_p(
                request.top_p,
            )

            if top_p is not None:
                generation_arguments["top_p"] = top_p

            pad_token_id = _read_optional_integer_attribute(
                tokenizer,
                "pad_token_id",
            )

            if pad_token_id is not None:
                generation_arguments["pad_token_id"] = (
                    pad_token_id
                )

            generation_task = asyncio.create_task(
                asyncio.to_thread(
                    _run_generation,
                    model,
                    generation_arguments,
                ),
            )

            while True:
                has_item, text = await asyncio.to_thread(
                    _read_next_stream_text,
                    streamer_iterator,
                )

                if not has_item:
                    break

                if not text:
                    continue

                yield StreamEvent.create(
                    type=StreamEventType.TOKEN,
                    content=text,
                )

            await generation_task

            yield StreamEvent.create(
                type=StreamEventType.END,
                data={
                    "backend": self.backend_name,
                    "model": model_id,
                    "finish_reason": "stop",
                },
            )

        except TransformersProviderError as exc:
            logger.exception(
                "Transformers provider rejected the request",
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
                "Unexpected Transformers provider error",
                extra={
                    "backend": self.backend_name,
                    "model": model_id,
                    "error_type": type(exc).__name__,
                },
            )

            yield StreamEvent.create(
                type=StreamEventType.ERROR,
                content=(
                    "Bei der lokalen Transformers-Generierung ist "
                    "ein unerwarteter Fehler aufgetreten."
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
        Lehnt nicht implementierte Vertragsfunktionen sichtbar ab.
        """

        if request.tools:
            raise TransformersConfigurationError(
                "Tool-Aufrufe sind in dieser Transformers-"
                "Provider-Version noch nicht implementiert.",
            )

        if request.tool_choice is not None:
            raise TransformersConfigurationError(
                "tool_choice wird in dieser Transformers-"
                "Provider-Version noch nicht unterstützt.",
            )

        if request.stop:
            raise TransformersConfigurationError(
                "Stop-Sequenzen werden in dieser Transformers-"
                "Provider-Version noch nicht unterstützt.",
            )

    async def _ensure_loaded(
        self,
    ) -> tuple[ModelProtocol, TokenizerProtocol]:
        """
        Lädt Modell und Tokenizer genau einmal.

        Die synchronen Bibliotheksaufrufe werden in einen Thread
        ausgelagert.
        """

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
                raise TransformersConfigurationError(
                    "Für den Transformers-Provider fehlt "
                    "'model_name' oder 'path'.",
                )

            bindings = _require_transformers_bindings()

            tokenizer_arguments: PretrainedArguments = {
                "trust_remote_code": self._trust_remote_code,
                "local_files_only": self._local_files_only,
            }

            model_arguments: PretrainedArguments = {
                "trust_remote_code": self._trust_remote_code,
                "local_files_only": self._local_files_only,
                "device_map": self._device_map,
            }

            raw_tokenizer = await asyncio.to_thread(
                _load_pretrained_object,
                bindings.tokenizer_factory,
                self._model_path,
                tokenizer_arguments,
            )

            tokenizer = _require_tokenizer(
                raw_tokenizer,
            )

            raw_model = await asyncio.to_thread(
                _load_pretrained_object,
                bindings.model_factory,
                self._model_path,
                model_arguments,
            )

            model = _require_model(
                raw_model,
            )

            self._tokenizer = tokenizer
            self._model = model

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
            raise TransformersModelNotFoundError(
                f"Das Transformers-Modell '{model_id}' "
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
            "trust_remote_code": self._trust_remote_code,
            "device_map": self._device_map,
        }

        if self._model_path is not None:
            metadata["path"] = self._model_path

        return ModelInfo.create(
            id=self._model_id,
            backend=self.backend_name,
            display_name=self._model_id,
            provider="Hugging Face Transformers",
            capabilities=capabilities,
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            metadata=metadata,
        )


# ============================================================
# Bibliotheksgrenzen
# ============================================================


def _require_transformers_bindings(
) -> TransformersBindings:
    if _TRANSFORMERS_BINDINGS is None:
        raise TransformersConfigurationError(
            "Der Transformers-Provider benötigt die Pakete "
            "'torch' und 'transformers'.",
        )

    return _TRANSFORMERS_BINDINGS


def _load_pretrained_object(
    factory: PretrainedFactoryProtocol,
    model_path: str,
    arguments: Mapping[str, object],
) -> object:
    return factory.from_pretrained(
        model_path,
        **arguments,
    )


def _require_tokenizer(
    value: object,
) -> TokenizerProtocol:
    if not isinstance(
        value,
        TokenizerProtocol,
    ):
        raise TransformersConfigurationError(
            "AutoTokenizer.from_pretrained() lieferte keinen "
            "verwendbaren Tokenizer.",
        )

    return value


def _require_model(
    value: object,
) -> ModelProtocol:
    if not isinstance(
        value,
        ModelProtocol,
    ):
        raise TransformersConfigurationError(
            "AutoModelForCausalLM.from_pretrained() lieferte kein "
            "verwendbares Sprachmodell.",
        )

    return value


def _require_object_iterator(
    value: object,
) -> Iterator[object]:
    if not isinstance(
        value,
        ObjectIterableProtocol,
    ):
        raise TransformersConfigurationError(
            "TextIteratorStreamer lieferte keinen gültigen Iterator.",
        )

    return iter(
        value,
    )


def _require_tensor_from_mapping(
    values: Mapping[str, object],
    key: str,
) -> TensorProtocol:
    value = values.get(
        key,
    )

    if not isinstance(
        value,
        TensorProtocol,
    ):
        raise TransformersConfigurationError(
            f"Der Tokenizer lieferte keinen gültigen Tensor "
            f"für '{key}'.",
        )

    return value


def _read_optional_tensor_from_mapping(
    values: Mapping[str, object],
    key: str,
) -> TensorProtocol | None:
    value = values.get(
        key,
    )

    if value is None:
        return None

    if not isinstance(
        value,
        TensorProtocol,
    ):
        raise TransformersConfigurationError(
            f"Der optionale Tokenizerwert '{key}' ist kein Tensor.",
        )

    return value


def _read_optional_attribute(
    value: object,
    attribute_name: str,
) -> object | None:
    return getattr(
        value,
        attribute_name,
        None,
    )


def _read_optional_integer_attribute(
    value: object,
    attribute_name: str,
) -> int | None:
    raw_value = getattr(
        value,
        attribute_name,
        None,
    )

    if isinstance(
        raw_value,
        bool,
    ):
        return None

    if isinstance(
        raw_value,
        int,
    ):
        return raw_value

    return None


def _run_generation(
    model: ModelProtocol,
    arguments: Mapping[str, object],
) -> None:
    model.generate(
        **arguments,
    )


def _read_next_stream_text(
    iterator: Iterator[object],
) -> tuple[bool, str]:
    """
    Fängt StopIteration innerhalb des Worker-Threads ab.

    StopIteration darf nicht direkt aus ``asyncio.to_thread`` in ein
    Future gelangen.
    """

    try:
        value = next(
            iterator,
        )

    except StopIteration:
        return (
            False,
            "",
        )

    if not isinstance(
        value,
        str,
    ):
        raise TransformersConfigurationError(
            "TextIteratorStreamer lieferte ein nichttextuelles Element.",
        )

    return (
        True,
        value,
    )


# ============================================================
# Prompt und Nachrichten
# ============================================================


def _create_prompt(
    tokenizer: TokenizerProtocol,
    messages: Sequence[ChatMessage],
) -> str:
    converted_messages = _convert_messages(
        messages,
    )

    raw_apply_template: object = getattr(
        tokenizer,
        "apply_chat_template",
        None,
    )

    if callable(
        raw_apply_template,
    ):
        try:
            rendered: object = raw_apply_template(
                converted_messages,
                tokenize=False,
                add_generation_prompt=True,
            )

        except Exception:
            logger.exception(
                "Das Chat-Template des Tokenizers konnte nicht "
                "angewendet werden. Verwende Fallback-Prompt.",
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
        raise TransformersConfigurationError(
            "Die Transformers-Anfrage enthält keine "
            "verwendbare Nachricht.",
        )

    return result


# ============================================================
# Optionsvalidierung
# ============================================================


def _resolve_max_tokens(
    value: int | None,
) -> int:
    if value is None:
        return DEFAULT_MAX_TOKENS

    if value <= 0:
        raise TransformersConfigurationError(
            "max_tokens muss größer als null sein.",
        )

    return value


def _normalize_temperature(
    value: float,
) -> float:
    if value <= 0.0:
        return 1.0

    if value > 5.0:
        return 5.0

    return value


def _normalize_optional_top_p(
    value: float | None,
) -> float | None:
    if value is None:
        return None

    if value <= 0.0:
        raise TransformersConfigurationError(
            "top_p muss größer als null sein.",
        )

    if value > 1.0:
        raise TransformersConfigurationError(
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


# ============================================================
# Registry-Factory
# ============================================================


def create_transformers_backend(
    *,
    provider_config: JsonMapping,
    dependencies: ProviderDependencies | None = None,
) -> BaseModelBackend:
    """
    Factory für die feste Modell-Provider-Registry.
    """

    del dependencies

    return TransformersProvider(
        provider_config,
    )


__all__ = [
    "TransformersConfigurationError",
    "TransformersModelNotFoundError",
    "TransformersProvider",
    "TransformersProviderError",
    "create_transformers_backend",
]