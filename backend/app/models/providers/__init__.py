"""
Kontrollierte Modell-Provider von Kernschmied.

Dieses Paket enthält ausschließlich bekannte und intern freigegebene
Provider-Implementierungen.

Eingebaute Provider:

- anthropic
- azure_openai
- google_gemini
- http_generic
- llama_cpp
- mlx
- ollama
- openai
- openai_compatible
- transformers

Architekturregeln:

- Der Import dieses Pakets öffnet keine Netzwerkverbindungen.
- Der Import dieses Pakets lädt keine Modelle.
- Optionale Provider-SDKs werden erst bei tatsächlicher Verwendung
  importiert.
- Manifeste dürfen keine beliebigen Python-Module oder Klassen bestimmen.
- Nur die in dieser Datei ausdrücklich registrierten Provider sind
  ausführbar.
- Dynamische Erkennung bedeutet niemals automatische Freigabe.
- Provider erhalten ihre Abhängigkeiten über Dependency Injection.
"""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias

from app.contracts.model_backend import (
    BaseModelBackend,
    JsonMapping,
)


# ============================================================
# Typen
# ============================================================


ProviderDependencies: TypeAlias = Mapping[str, object]


class ModelProviderFactory(Protocol):
    """
    Stabiler Aufrufvertrag einer Modell-Provider-Factory.

    Der Rückgabewert ist absichtlich zunächst `object`.

    Eine dynamisch importierte Python-Funktion kann ihren tatsächlichen
    Rückgabetyp zur Laufzeit nicht garantieren. Die Registry validiert
    deshalb das Ergebnis jeder Factory explizit, bevor es als
    BaseModelBackend akzeptiert wird.
    """

    def __call__(
        self,
        *,
        provider_config: JsonMapping,
        dependencies: ProviderDependencies | None = None,
    ) -> object:
        ...


# ============================================================
# Fehler
# ============================================================


class ModelProviderRegistryError(RuntimeError):
    """
    Basisklasse für Fehler der ModelProviderRegistry.
    """


class InvalidModelProviderTypeError(
    ModelProviderRegistryError,
    ValueError,
):
    """
    Ein Provider-Typ ist syntaktisch ungültig.
    """

    def __init__(
        self,
        provider_type: object,
        message: str,
    ) -> None:
        self.provider_type = provider_type

        super().__init__(
            f"Ungültiger Modell-Provider-Typ "
            f"'{provider_type}': {message}",
        )


class UnknownModelProviderError(
    ModelProviderRegistryError,
    LookupError,
):
    """
    Der im Manifest angegebene Provider ist nicht registriert.
    """

    def __init__(
        self,
        provider_type: str,
    ) -> None:
        self.provider_type = provider_type

        super().__init__(
            f"Der Modell-Provider '{provider_type}' "
            "ist nicht registriert.",
        )


class DuplicateModelProviderError(
    ModelProviderRegistryError,
):
    """
    Ein Provider-Typ wurde mehrfach registriert.
    """

    def __init__(
        self,
        provider_type: str,
    ) -> None:
        self.provider_type = provider_type

        super().__init__(
            f"Der Modell-Provider '{provider_type}' "
            "wurde mehrfach registriert.",
        )


class ModelProviderImportError(
    ModelProviderRegistryError,
    ImportError,
):
    """
    Das Python-Modul eines freigegebenen Providers konnte nicht
    importiert werden.
    """

    def __init__(
        self,
        *,
        provider_type: str,
        module_name: str,
        cause: BaseException,
    ) -> None:
        self.provider_type = provider_type
        self.module_name = module_name
        self.cause = cause

        super().__init__(
            f"Der Modell-Provider '{provider_type}' konnte nicht geladen "
            f"werden. Modul: '{module_name}'. Ursache: {cause}",
        )


class ModelProviderFactoryNotFoundError(
    ModelProviderRegistryError,
    AttributeError,
):
    """
    Die konfigurierte Factory wurde im Provider-Modul nicht gefunden.
    """

    def __init__(
        self,
        *,
        provider_type: str,
        module_name: str,
        factory_name: str,
    ) -> None:
        self.provider_type = provider_type
        self.module_name = module_name
        self.factory_name = factory_name

        super().__init__(
            f"Die Factory '{factory_name}' des Modell-Providers "
            f"'{provider_type}' wurde im Modul '{module_name}' "
            "nicht gefunden.",
        )


class InvalidModelProviderFactoryError(
    ModelProviderRegistryError,
    TypeError,
):
    """
    Eine registrierte oder importierte Provider-Factory ist ungültig.
    """

    def __init__(
        self,
        *,
        provider_type: str,
        message: str,
    ) -> None:
        self.provider_type = provider_type

        super().__init__(
            f"Ungültige Factory für Modell-Provider "
            f"'{provider_type}': {message}",
        )


class ModelProviderCreationError(
    ModelProviderRegistryError,
):
    """
    Eine Provider-Factory konnte kein Backend erzeugen.
    """

    def __init__(
        self,
        *,
        provider_type: str,
        cause: BaseException,
    ) -> None:
        self.provider_type = provider_type
        self.cause = cause

        super().__init__(
            f"Der Modell-Provider '{provider_type}' "
            f"konnte nicht erzeugt werden: {cause}",
        )


# ============================================================
# Validierung
# ============================================================


def _validate_backend_result(
    *,
    provider_type: str,
    result: object,
) -> BaseModelBackend:
    """
    Validiert das Ergebnis eines Provider-Factory-Aufrufs.

    Die Prüfung erfolgt zentral, damit sowohl lazy importierte als auch
    direkt registrierte Factorys denselben Sicherheitsgrenzen
    unterliegen.
    """

    if inspect.isawaitable(
        result,
    ):
        raise InvalidModelProviderFactoryError(
            provider_type=provider_type,
            message=(
                "Die Factory hat ein Awaitable zurückgegeben. "
                "Provider-Factories müssen synchron eine "
                "BaseModelBackend-Instanz zurückgeben."
            ),
        )

    if not isinstance(
        result,
        BaseModelBackend,
    ):
        raise InvalidModelProviderFactoryError(
            provider_type=provider_type,
            message=(
                "Die Factory hat keine BaseModelBackend-Instanz "
                "zurückgegeben."
            ),
        )

    return result


def _copy_provider_config(
    provider_config: JsonMapping,
) -> dict[str, object]:
    """
    Erstellt eine veränderbare, flache Kopie der Provider-Konfiguration.

    Die enthaltenen Werte bleiben auf JSON-kompatible Werte begrenzt.
    """

    return {
        key: value
        for key, value in provider_config.items()
    }


def _copy_dependencies(
    dependencies: ProviderDependencies | None,
) -> dict[str, object]:
    """
    Erstellt eine veränderbare Kopie der injizierten Abhängigkeiten.
    """

    if dependencies is None:
        return {}

    return dict(
        dependencies,
    )


# ============================================================
# Lazy Factory
# ============================================================


@dataclass(frozen=True, slots=True)
class LazyModelProviderFactory:
    """
    Verweis auf eine freigegebene Provider-Factory.

    Das zugehörige Modul wird erst beim ersten Erzeugen einer
    Backend-Instanz importiert. Dadurch bleiben optionale Abhängigkeiten
    voneinander isoliert.
    """

    provider_type: str
    module_name: str
    factory_name: str

    def __post_init__(self) -> None:
        provider_type = ModelProviderRegistry.normalize_provider_type(
            self.provider_type,
        )

        module_name = self.module_name.strip()
        factory_name = self.factory_name.strip()

        if not module_name:
            raise InvalidModelProviderFactoryError(
                provider_type=provider_type,
                message="module_name darf nicht leer sein.",
            )

        if not factory_name:
            raise InvalidModelProviderFactoryError(
                provider_type=provider_type,
                message="factory_name darf nicht leer sein.",
            )

        if not module_name.startswith(
            "app.models.providers.",
        ):
            raise InvalidModelProviderFactoryError(
                provider_type=provider_type,
                message=(
                    "Provider-Module müssen innerhalb von "
                    "'app.models.providers' liegen."
                ),
            )

        object.__setattr__(
            self,
            "provider_type",
            provider_type,
        )

        object.__setattr__(
            self,
            "module_name",
            module_name,
        )

        object.__setattr__(
            self,
            "factory_name",
            factory_name,
        )

    def resolve(self) -> ModelProviderFactory:
        """
        Importiert das freigegebene Modul und liefert einen typisierten
        Factory-Adapter.

        Das direkt über `getattr()` geladene Objekt wird nicht ungeprüft
        als ModelProviderFactory zurückgegeben. Stattdessen kapselt ein
        lokaler Adapter den dynamischen Aufruf.
        """

        try:
            module = importlib.import_module(
                self.module_name,
            )

        except Exception as exc:
            raise ModelProviderImportError(
                provider_type=self.provider_type,
                module_name=self.module_name,
                cause=exc,
            ) from exc

        candidate: object = getattr(
            module,
            self.factory_name,
            None,
        )

        if candidate is None:
            raise ModelProviderFactoryNotFoundError(
                provider_type=self.provider_type,
                module_name=self.module_name,
                factory_name=self.factory_name,
            )

        if not callable(
            candidate,
        ):
            raise InvalidModelProviderFactoryError(
                provider_type=self.provider_type,
                message=(
                    f"'{self.factory_name}' ist nicht aufrufbar."
                ),
            )

        def resolved_factory(
            *,
            provider_config: JsonMapping,
            dependencies: ProviderDependencies | None = None,
        ) -> object:
            return candidate(
                provider_config=_copy_provider_config(
                    provider_config,
                ),
                dependencies=_copy_dependencies(
                    dependencies,
                ),
            )

        return resolved_factory

    def __call__(
        self,
        *,
        provider_config: JsonMapping,
        dependencies: ProviderDependencies | None = None,
    ) -> object:
        """
        Löst die eigentliche Factory auf und führt sie aus.

        Die abschließende Backend-Typprüfung übernimmt die Registry
        zentral in `_validate_backend_result`.
        """

        factory = self.resolve()

        return factory(
            provider_config=provider_config,
            dependencies=dependencies,
        )


# ============================================================
# Registry
# ============================================================


class ModelProviderRegistry:
    """
    Feste Registry für intern bekannte Modell-Provider.

    Die Registry speichert Factory-Funktionen und keine bereits
    erzeugten Provider-Instanzen. Dadurch können Settings, HTTP-Clients,
    Secrets, Dateisystemrichtlinien und weitere Abhängigkeiten gezielt
    injiziert werden.

    Die Registry interpretiert keine Importpfade aus Modellmanifesten.
    """

    def __init__(
        self,
        factories: Mapping[
            str,
            ModelProviderFactory,
        ]
        | None = None,
    ) -> None:
        self._factories: dict[
            str,
            ModelProviderFactory,
        ] = {}

        if factories is None:
            return

        for provider_type, factory in factories.items():
            self.register(
                provider_type=provider_type,
                factory=factory,
            )

    def register(
        self,
        *,
        provider_type: str,
        factory: ModelProviderFactory,
    ) -> None:
        """
        Registriert eine Factory unter einem festen Provider-Typ.
        """

        normalized_provider_type = self.normalize_provider_type(
            provider_type,
        )

        if normalized_provider_type in self._factories:
            raise DuplicateModelProviderError(
                normalized_provider_type,
            )

        if not callable(
            factory,
        ):
            raise InvalidModelProviderFactoryError(
                provider_type=normalized_provider_type,
                message="Die Factory muss aufrufbar sein.",
            )

        self._factories[
            normalized_provider_type
        ] = factory

    def register_lazy(
        self,
        *,
        provider_type: str,
        module_name: str,
        factory_name: str,
    ) -> None:
        """
        Registriert einen ausdrücklich freigegebenen Provider lazy.

        module_name und factory_name stammen ausschließlich aus dieser
        serverseitigen Freigabeliste und niemals aus einem Modellmanifest.
        """

        normalized_provider_type = self.normalize_provider_type(
            provider_type,
        )

        lazy_factory = LazyModelProviderFactory(
            provider_type=normalized_provider_type,
            module_name=module_name,
            factory_name=factory_name,
        )

        self.register(
            provider_type=normalized_provider_type,
            factory=lazy_factory,
        )

    def unregister(
        self,
        provider_type: str,
    ) -> bool:
        """
        Entfernt einen Provider aus dieser Registry-Instanz.

        Die Default-Registry selbst bleibt unverändert; betroffen ist nur
        die konkrete Instanz.
        """

        normalized_provider_type = self.normalize_provider_type(
            provider_type,
        )

        removed_factory = self._factories.pop(
            normalized_provider_type,
            None,
        )

        return removed_factory is not None

    def has(
        self,
        provider_type: str,
    ) -> bool:
        """
        Prüft, ob ein Provider-Typ registriert ist.
        """

        normalized_provider_type = self.normalize_provider_type(
            provider_type,
        )

        return normalized_provider_type in self._factories

    def get_factory(
        self,
        provider_type: str,
    ) -> ModelProviderFactory:
        """
        Liefert die registrierte Factory eines Provider-Typs.
        """

        normalized_provider_type = self.normalize_provider_type(
            provider_type,
        )

        factory = self._factories.get(
            normalized_provider_type,
        )

        if factory is None:
            raise UnknownModelProviderError(
                normalized_provider_type,
            )

        return factory

    def create(
        self,
        *,
        provider_type: str,
        provider_config: JsonMapping,
        dependencies: ProviderDependencies | None = None,
    ) -> BaseModelBackend:
        """
        Erzeugt eine Provider-Instanz über eine registrierte Factory.

        Die Registry:

        - interpretiert keine Importpfade aus Manifesten,
        - lädt keinen beliebigen Python-Code,
        - verändert die ursprüngliche Provider-Konfiguration nicht,
        - validiert den zurückgegebenen Backend-Typ.
        """

        normalized_provider_type = self.normalize_provider_type(
            provider_type,
        )

        factory = self.get_factory(
            normalized_provider_type,
        )

        try:
            result = factory(
                provider_config=provider_config,
                dependencies=dependencies,
            )

        except ModelProviderRegistryError:
            raise

        except Exception as exc:
            raise ModelProviderCreationError(
                provider_type=normalized_provider_type,
                cause=exc,
            ) from exc

        return _validate_backend_result(
            provider_type=normalized_provider_type,
            result=result,
        )

    def list_provider_types(
        self,
    ) -> tuple[str, ...]:
        """
        Liefert alle freigegebenen Provider-Typen sortiert zurück.
        """

        return tuple(
            sorted(
                self._factories,
            ),
        )

    def describe(
        self,
    ) -> tuple[dict[str, object], ...]:
        """
        Liefert eine diagnostische Beschreibung der Registry.

        Provider werden dabei nicht importiert.
        """

        descriptions: list[dict[str, object]] = []

        for provider_type in self.list_provider_types():
            factory = self._factories[
                provider_type
            ]

            if isinstance(
                factory,
                LazyModelProviderFactory,
            ):
                descriptions.append(
                    {
                        "provider_type": provider_type,
                        "loading": "lazy",
                        "module_name": factory.module_name,
                        "factory_name": factory.factory_name,
                    },
                )

                continue

            factory_type = type(
                factory,
            )

            descriptions.append(
                {
                    "provider_type": provider_type,
                    "loading": "eager",
                    "module_name": factory_type.__module__,
                    "factory_name": factory_type.__qualname__,
                },
            )

        return tuple(
            descriptions,
        )

    @property
    def count(self) -> int:
        """
        Anzahl der registrierten Provider-Typen.
        """

        return len(
            self._factories,
        )

    @staticmethod
    def normalize_provider_type(
        provider_type: object,
    ) -> str:
        """
        Normalisiert und validiert einen Provider-Typ.

        Erlaubt sind:

        - Kleinbuchstaben
        - Ziffern
        - Punkt
        - Bindestrich
        - Unterstrich

        Der Eingabetyp ist bewusst `object`, weil diese Methode eine
        Systemgrenze validiert und auch fehlerhafte Laufzeitwerte sicher
        ablehnen muss.
        """

        if not isinstance(
            provider_type,
            str,
        ):
            raise InvalidModelProviderTypeError(
                provider_type,
                "Der Wert muss eine Zeichenkette sein.",
            )

        normalized = provider_type.strip().lower()

        if not normalized:
            raise InvalidModelProviderTypeError(
                provider_type,
                "Der Wert darf nicht leer sein.",
            )

        allowed_characters: Final[frozenset[str]] = frozenset(
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789"
            "._-",
        )

        if any(
            character not in allowed_characters
            for character in normalized
        ):
            raise InvalidModelProviderTypeError(
                provider_type,
                (
                    "Erlaubt sind nur Kleinbuchstaben, Ziffern, Punkte, "
                    "Bindestriche und Unterstriche."
                ),
            )

        return normalized


# ============================================================
# Feste Provider-Freigabeliste
# ============================================================


@dataclass(frozen=True, slots=True)
class BuiltinProviderDefinition:
    """
    Serverseitige Definition eines eingebauten Providers.
    """

    provider_type: str
    module_name: str
    factory_name: str


BUILTIN_PROVIDER_DEFINITIONS: Final[
    tuple[BuiltinProviderDefinition, ...]
] = (
    BuiltinProviderDefinition(
        provider_type="anthropic",
        module_name="app.models.providers.anthropic",
        factory_name="create_anthropic_backend",
    ),
    BuiltinProviderDefinition(
        provider_type="azure_openai",
        module_name="app.models.providers.azure_openai",
        factory_name="create_azure_openai_backend",
    ),
    BuiltinProviderDefinition(
        provider_type="google_gemini",
        module_name="app.models.providers.google_gemini",
        factory_name="create_google_gemini_backend",
    ),
    BuiltinProviderDefinition(
        provider_type="http_generic",
        module_name="app.models.providers.http_generic",
        factory_name="create_http_generic_backend",
    ),
    BuiltinProviderDefinition(
        provider_type="llama_cpp",
        module_name="app.models.providers.llama_cpp",
        factory_name="create_llama_cpp_backend",
    ),
    BuiltinProviderDefinition(
        provider_type="mlx",
        module_name="app.models.providers.mlx",
        factory_name="create_mlx_backend",
    ),
    BuiltinProviderDefinition(
        provider_type="ollama",
        module_name="app.models.providers.ollama",
        factory_name="create_ollama_backend",
    ),
    BuiltinProviderDefinition(
        provider_type="openai",
        module_name="app.models.providers.openai",
        factory_name="create_openai_backend",
    ),
    BuiltinProviderDefinition(
        provider_type="openai_compatible",
        module_name="app.models.providers.openai_compatible",
        factory_name="create_openai_compatible_backend",
    ),
    BuiltinProviderDefinition(
        provider_type="transformers",
        module_name="app.models.providers.transformers",
        factory_name="create_transformers_backend",
    ),
)


def create_default_provider_registry() -> ModelProviderRegistry:
    """
    Erstellt die Registry aller fest eingebauten Provider.

    Die Provider werden ausschließlich lazy registriert. Dadurch werden:

    - keine optionalen SDKs beim Anwendungsstart importiert,
    - keine Modelle geladen,
    - keine Netzwerkverbindungen geöffnet,
    - Fehler einzelner Provider voneinander isoliert.

    Das Vorhandensein eines Providers in dieser Freigabeliste erlaubt
    nur dessen technische Verwendung. Ob ein konkretes Modell aktiviert
    und für einen Benutzer freigegeben ist, entscheidet weiterhin die
    ModelRegistry beziehungsweise die serverseitige Autorisierung.
    """

    registry = ModelProviderRegistry()

    for definition in BUILTIN_PROVIDER_DEFINITIONS:
        registry.register_lazy(
            provider_type=definition.provider_type,
            module_name=definition.module_name,
            factory_name=definition.factory_name,
        )

    return registry


__all__ = [
    "BUILTIN_PROVIDER_DEFINITIONS",
    "BuiltinProviderDefinition",
    "DuplicateModelProviderError",
    "InvalidModelProviderFactoryError",
    "InvalidModelProviderTypeError",
    "LazyModelProviderFactory",
    "ModelProviderCreationError",
    "ModelProviderFactory",
    "ModelProviderFactoryNotFoundError",
    "ModelProviderImportError",
    "ModelProviderRegistry",
    "ModelProviderRegistryError",
    "ProviderDependencies",
    "UnknownModelProviderError",
    "create_default_provider_registry",
]