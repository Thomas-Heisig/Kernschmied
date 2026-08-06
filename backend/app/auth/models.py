# F:\Kernschmied\backend\app\auth\models.py

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,  # NEU: Pydantic's JsonValue
    field_validator,
)

# Keine eigene rekursive JsonValue-Definition mehr - importiert aus pydantic
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonValue]


def normalize_string_collection_value(
    value: object,
) -> tuple[str, ...]:
    if value is None:
        return ()

    values: Sequence[object]

    if isinstance(
        value,
        str,
    ):
        values = (value,)

    else:
        normalized_sequence = as_object_sequence(
            value,
        )

        if normalized_sequence is None:
            return ()

        values = normalized_sequence

    result: list[str] = []

    for item in values:
        normalized = (
            str(
                item,
            )
            .strip()
            .casefold()
        )

        if not normalized:
            continue

        if normalized in result:
            continue

        result.append(
            normalized,
        )

    return tuple(
        result,
    )


def as_object_mapping(
    value: object,
) -> Mapping[object, object] | None:
    if not isinstance(
        value,
        Mapping,
    ):
        return None

    return cast(
        Mapping[object, object],
        value,
    )


def as_object_sequence(
    value: object,
) -> Sequence[object] | None:
    if isinstance(
        value,
        str | bytes | bytearray,
    ):
        return None

    if not isinstance(
        value,
        Sequence,
    ):
        return None

    return cast(
        Sequence[object],
        value,
    )


def normalize_bool(
    value: object,
    *,
    default: bool,
) -> bool:
    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return value != 0

    if isinstance(
        value,
        str,
    ):
        normalized = value.strip().casefold()

        if normalized in {
            "1",
            "true",
            "yes",
            "on",
            "ja",
        }:
            return True

        if normalized in {
            "0",
            "false",
            "no",
            "off",
            "nein",
        }:
            return False

    return default


def normalize_optional_string(
    value: object,
) -> str | None:
    if value is None:
        return None

    normalized = str(
        value,
    ).strip()

    return normalized or None


def normalize_json_value(
    value: object,
    *,
    depth: int = 0,
    max_depth: int = 16,
) -> JsonValue:
    if depth > max_depth:
        raise ValueError("Die Metadaten überschreiten die maximal erlaubte Tiefe.")

    if value is None:
        return None

    if isinstance(
        value,
        str | int | float | bool,
    ):
        return value

    mapping = as_object_mapping(
        value,
    )

    if mapping is not None:
        result: JsonObject = {}

        for raw_key, raw_value in mapping.items():
            key = str(
                raw_key,
            ).strip()

            if not key:
                continue

            result[key] = normalize_json_value(
                raw_value,
                depth=depth + 1,
                max_depth=max_depth,
            )

        return result

    sequence = as_object_sequence(
        value,
    )

    if sequence is not None:
        return [
            normalize_json_value(
                item,
                depth=depth + 1,
                max_depth=max_depth,
            )
            for item in sequence
        ]

    return str(
        value,
    )


def normalize_metadata(
    value: object,
) -> JsonObject:
    mapping = as_object_mapping(
        value,
    )

    if mapping is None:
        return {}

    normalized = normalize_json_value(
        mapping,
    )

    if not isinstance(
        normalized,
        dict,
    ):
        return {}

    return normalized


def read_principal_value(
    principal: object,
    *names: str,
    default: object = None,
) -> object:
    principal_mapping = as_object_mapping(
        principal,
    )

    for name in names:
        if principal_mapping is not None:
            if name in principal_mapping:
                return principal_mapping[name]

            continue

        if hasattr(
            principal,
            name,
        ):
            return getattr(
                principal,
                name,
            )

    return default


class UserContext(BaseModel):
    """
    Einheitlicher Benutzerkontext für Authentifizierung und Autorisierung.

    Dieses Modell enthält ausschließlich Informationen, die innerhalb
    einer Request-Verarbeitung benötigt werden. Passwörter, Tokens,
    Session-Secrets oder Provider-Zugangsdaten gehören niemals hier hinein.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    id: str = Field(
        min_length=1,
        max_length=255,
    )

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    authenticated: bool = False
    active: bool = True
    is_system_admin: bool = False

    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()

    tenant_id: str | None = Field(
        default=None,
        max_length=255,
    )

    authentication_method: str | None = Field(
        default=None,
        max_length=100,
    )

    session_id: str | None = Field(
        default=None,
        max_length=255,
    )

    metadata: JsonObject = Field(
        default_factory=dict,
    )

    @field_validator(
        "roles",
        "permissions",
        mode="before",
    )
    @classmethod
    def normalize_string_collection(
        cls,
        value: object,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        values: Sequence[object]

        if isinstance(
            value,
            str,
        ):
            values = (value,)

        else:
            normalized_sequence = as_object_sequence(
                value,
            )

            if normalized_sequence is None:
                return ()

            values = normalized_sequence

        result: list[str] = []

        for item in values:
            normalized = (
                str(
                    item,
                )
                .strip()
                .casefold()
            )

            if not normalized:
                continue

            if normalized in result:
                continue

            result.append(
                normalized,
            )

        return tuple(
            result,
        )

    @field_validator(
        "metadata",
        mode="before",
    )
    @classmethod
    def validate_metadata(
        cls,
        value: object,
    ) -> JsonObject:
        return normalize_metadata(
            value,
        )

    @classmethod
    def anonymous(
        cls,
    ) -> UserContext:
        # Return an unauthenticated placeholder user context.
        return cls(
            id="anonymous",
            name="Nicht angemeldet",
            authenticated=False,
            active=True,
            roles=(),
            permissions=(),
            authentication_method=None,
        )

    @classmethod
    def development_admin(
        cls,
        *,
        user_id: str = "local-development-admin",
        name: str = "Administrator",
    ) -> UserContext:
        return cls(
            id=user_id,
            name=name,
            authenticated=True,
            active=True,
            roles=("admin",),
            permissions=(
                "hierarchy.read",
                "hierarchy.create",
                "hierarchy.update",
                "hierarchy.delete",
                "hierarchy.move",
                "hierarchy.reorder",
                "config.read",
                "config.write",
                "models.read",
                "models.manage",
                "tools.read",
                "tools.manage",
                "users.read",
                "users.create",
                "users.update",
                "users.delete",
            ),
            authentication_method="development",
        )

    @classmethod
    def from_principal(
        cls,
        principal: object,
    ) -> UserContext:
        """
        Normalisiert Benutzerinformationen aus einer vorgeschalteten
        Authentifizierungsschicht.

        Unterstützt:

        - UserContext
        - Dictionary/Mapping
        - beliebige Objekte mit passenden Attributen
        """

        if isinstance(
            principal,
            cls,
        ):
            return principal

        user_id = read_principal_value(
            principal,
            "id",
            "user_id",
            "subject",
            "sub",
        )

        if user_id is None:
            raise ValueError("Der Principal besitzt keine Benutzer-ID.")

        normalized_user_id = str(
            user_id,
        ).strip()

        if not normalized_user_id:
            raise ValueError("Der Principal besitzt keine gültige Benutzer-ID.")

        raw_name = read_principal_value(
            principal,
            "name",
            "display_name",
            "username",
            default=normalized_user_id,
        )

        normalized_name = str(
            raw_name,
        ).strip()

        if not normalized_name:
            normalized_name = normalized_user_id

        raw_authenticated = read_principal_value(
            principal,
            "authenticated",
            "is_authenticated",
            default=True,
        )

        raw_active = read_principal_value(
            principal,
            "active",
            "is_active",
            default=True,
        )

        raw_roles = read_principal_value(
            principal,
            "roles",
            default=(),
        )

        raw_permissions = read_principal_value(
            principal,
            "permissions",
            default=(),
        )

        # Map legacy/system flags on DB principals to an admin role so
        # converted UserContext instances carry expected privileges.
        raw_is_system_admin = read_principal_value(
            principal,
            "is_system_admin",
            "is_admin",
            default=False,
        )

        raw_tenant_id = read_principal_value(
            principal,
            "tenant_id",
        )

        raw_authentication_method = read_principal_value(
            principal,
            "authentication_method",
            "auth_method",
        )

        raw_session_id = read_principal_value(
            principal,
            "session_id",
        )

        raw_metadata = read_principal_value(
            principal,
            "metadata",
            default={},
        )

        # Build normalized roles sequence and inject admin when indicated.
        _normalized_roles = normalize_string_collection_value(raw_roles)
        if normalize_bool(raw_is_system_admin, default=False):
            roles = ("admin", *_normalized_roles)
        else:
            roles = _normalized_roles

        # Determine explicit system admin flag: either explicit principal flag
        # or presence of an admin role.
        final_is_system_admin = bool(
            normalize_bool(raw_is_system_admin, default=False)
            or ("admin" in roles)
        )

        return cls(
            id=normalized_user_id,
            name=normalized_name,
            authenticated=normalize_bool(
                raw_authenticated,
                default=True,
            ),
            active=normalize_bool(
                raw_active,
                default=True,
            ),
            is_system_admin=final_is_system_admin,
            # Normalize roles/permissions and inject the `admin` role when the
            # backing principal indicates a system/admin user.
            roles=roles,
            permissions=normalize_string_collection_value(raw_permissions),
            tenant_id=normalize_optional_string(
                raw_tenant_id,
            ),
            authentication_method=normalize_optional_string(
                raw_authentication_method,
            ),
            session_id=normalize_optional_string(
                raw_session_id,
            ),
            metadata=normalize_metadata(
                raw_metadata,
            ),
        )


class AuthenticationResult(BaseModel):
    """
    Ergebnis einer späteren Authentifizierungsstrategie.

    Beispielsweise können Session-, OIDC- oder Reverse-Proxy-Adapter
    ein solches Ergebnis zurückgeben.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    user: UserContext
    credentials_refreshed: bool = False
