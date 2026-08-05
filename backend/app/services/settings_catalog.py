# F:\Kernschmied\backend\app\services\settings_catalog.py

from __future__ import annotations

from functools import lru_cache

from app.schemas.settings_catalog import (
    SettingsAvailability,
    SettingsCatalogResponse,
    SettingsControl,
    SettingsFieldDescriptor,
    SettingsGroupDescriptor,
    SettingsOption,
    SettingsSectionDescriptor,
    SettingsSource,
)

# ============================================================
# Wiederverwendbare Optionen
# ============================================================

LANGUAGE_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="de",
        label="Deutsch",
    ),
    SettingsOption(
        value="en",
        label="Englisch",
    ),
)

TONE_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="professional",
        label="Professionell",
    ),
    SettingsOption(
        value="friendly",
        label="Freundlich",
    ),
    SettingsOption(
        value="direct",
        label="Direkt",
    ),
    SettingsOption(
        value="formal",
        label="Formell",
    ),
    SettingsOption(
        value="adaptive",
        label="Situativ anpassen",
    ),
)

RESPONSE_DEPTH_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="compact",
        label="Kompakt",
    ),
    SettingsOption(
        value="balanced",
        label="Ausgewogen",
    ),
    SettingsOption(
        value="detailed",
        label="Detailliert",
    ),
    SettingsOption(
        value="comprehensive",
        label="Umfassend",
    ),
)

AUTONOMY_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="advisory",
        label="Nur beraten",
    ),
    SettingsOption(
        value="draft",
        label="Entwürfe erstellen",
    ),
    SettingsOption(
        value="prepare",
        label="Änderungen vorbereiten",
    ),
    SettingsOption(
        value="execute_approved",
        label="Freigegebene Aktionen ausführen",
    ),
)

THEME_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="system",
        label="System",
    ),
    SettingsOption(
        value="light",
        label="Hell",
    ),
    SettingsOption(
        value="dark",
        label="Dunkel",
    ),
)

DENSITY_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="compact",
        label="Kompakt",
    ),
    SettingsOption(
        value="comfortable",
        label="Komfortabel",
    ),
    SettingsOption(
        value="spacious",
        label="Großzügig",
    ),
)

DATA_CLASSIFICATION_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="public",
        label="Öffentlich",
    ),
    SettingsOption(
        value="internal",
        label="Intern",
    ),
    SettingsOption(
        value="confidential",
        label="Vertraulich",
    ),
    SettingsOption(
        value="highly_confidential",
        label="Besonders vertraulich",
    ),
)

LEARNING_MODE_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="off",
        label="Aus",
    ),
    SettingsOption(
        value="passive",
        label="Passiv protokollieren",
    ),
    SettingsOption(
        value="candidate",
        label="Lernkandidaten erzeugen",
    ),
)

ARTIFACT_STATUS_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="draft",
        label="Entwurf",
    ),
    SettingsOption(
        value="review",
        label="In Prüfung",
    ),
)

CONTEXT_STRATEGY_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="automatic",
        label="Automatisch",
    ),
    SettingsOption(
        value="conservative",
        label="Konservativ",
    ),
    SettingsOption(
        value="broad",
        label="Breit",
    ),
    SettingsOption(
        value="manual",
        label="Manuell",
    ),
)

FAILURE_STRATEGY_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="stop",
        label="Abbrechen",
    ),
    SettingsOption(
        value="retry",
        label="Wiederholen",
    ),
    SettingsOption(
        value="fallback",
        label="Alternative verwenden",
    ),
    SettingsOption(
        value="ask",
        label="Benutzer fragen",
    ),
)

SOURCE_DISPLAY_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="never",
        label="Nie",
    ),
    SettingsOption(
        value="when_available",
        label="Wenn vorhanden",
    ),
    SettingsOption(
        value="always",
        label="Immer",
    ),
)

PROMPT_CONFLICT_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="more_specific",
        label="Spezifischere Ebene gewinnt",
    ),
    SettingsOption(
        value="higher_priority",
        label="Höhere Priorität gewinnt",
    ),
    SettingsOption(
        value="reject",
        label="Konflikt ablehnen",
    ),
)

MODEL_ROUTING_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="manual",
        label="Manuelle Auswahl",
    ),
    SettingsOption(
        value="capability",
        label="Nach Fähigkeiten",
    ),
    SettingsOption(
        value="balanced",
        label="Qualität, Kosten und Geschwindigkeit",
    ),
    SettingsOption(
        value="local_first",
        label="Lokale Modelle bevorzugen",
    ),
)

EXPORT_FORMAT_OPTIONS: tuple[SettingsOption, ...] = (
    SettingsOption(
        value="pdf",
        label="PDF",
    ),
    SettingsOption(
        value="docx",
        label="DOCX",
    ),
    SettingsOption(
        value="xlsx",
        label="XLSX",
    ),
    SettingsOption(
        value="html",
        label="HTML",
    ),
    SettingsOption(
        value="markdown",
        label="Markdown",
    ),
    SettingsOption(
        value="json",
        label="JSON",
    ),
)


# ============================================================
# Katalog-Hilfsfunktionen
# ============================================================


def _field(
    field_id: str,
    title: str,
    *,
    description: str,
    source: SettingsSource,
    availability: SettingsAvailability,
    control: SettingsControl = SettingsControl.READONLY,
    config_group: str | None = None,
    config_key: str | None = None,
    endpoint: str | None = None,
    editable: bool = False,
    sensitive: bool = False,
    requires_confirmation: bool = False,
    restart_required: bool = False,
    options: tuple[SettingsOption, ...] = (),
    minimum: float | None = None,
    maximum: float | None = None,
    order: int = 0,
    tags: tuple[str, ...] = (),
) -> SettingsFieldDescriptor:
    """
    Erstellt einen einzelnen Katalogeintrag.

    Der Katalog beschreibt ausschließlich:

    - Sichtbarkeit,
    - Quelle,
    - Darstellung,
    - Zielressource,
    - Bearbeitbarkeit,
    - Schutzmerkmale.

    Er führt selbst keine Änderung aus und ersetzt keine Autorisierung.
    """

    return SettingsFieldDescriptor(
        id=field_id,
        title=title,
        description=description,
        source=source,
        availability=availability,
        control=control,
        config_group=config_group,
        config_key=config_key,
        endpoint=endpoint,
        editable=editable,
        sensitive=sensitive,
        requires_confirmation=requires_confirmation,
        restart_required=restart_required,
        options=options,
        minimum=minimum,
        maximum=maximum,
        order=order,
        tags=tags,
    )


def _config_field(
    field_id: str,
    title: str,
    *,
    description: str,
    group: str,
    key: str,
    control: SettingsControl,
    order: int,
    options: tuple[SettingsOption, ...] = (),
    minimum: float | None = None,
    maximum: float | None = None,
    sensitive: bool = False,
    requires_confirmation: bool = False,
    restart_required: bool = False,
    tags: tuple[str, ...] = (),
) -> SettingsFieldDescriptor:
    """
    Beschreibt einen über den ConfigService verwalteten Wert.
    """

    return _field(
        field_id,
        title,
        description=description,
        source=SettingsSource.CONFIG,
        availability=SettingsAvailability.AVAILABLE,
        control=control,
        config_group=group,
        config_key=key,
        editable=True,
        sensitive=sensitive,
        requires_confirmation=requires_confirmation,
        restart_required=restart_required,
        options=options,
        minimum=minimum,
        maximum=maximum,
        order=order,
        tags=tags,
    )


def _resource_link(
    field_id: str,
    title: str,
    *,
    description: str,
    endpoint: str,
    availability: SettingsAvailability,
    order: int,
    tags: tuple[str, ...] = (),
) -> SettingsFieldDescriptor:
    """
    Beschreibt eine verwaltete Ressource mit eigenem API-Vertrag.

    Beispiele:

    - Prompts,
    - Provider,
    - Modelle,
    - Tools,
    - Workflows,
    - Wissenseinträge,
    - Artifacts.
    """

    return _field(
        field_id,
        title,
        description=description,
        source=SettingsSource.RESOURCE,
        availability=availability,
        control=SettingsControl.LINK,
        endpoint=endpoint,
        order=order,
        tags=tags,
    )


def _runtime_field(
    field_id: str,
    title: str,
    *,
    description: str,
    endpoint: str,
    availability: SettingsAvailability,
    order: int,
    tags: tuple[str, ...] = (),
) -> SettingsFieldDescriptor:
    """
    Beschreibt einen schreibgeschützten Laufzeit- oder Diagnosestatus.
    """

    return _field(
        field_id,
        title,
        description=description,
        source=SettingsSource.RUNTIME,
        availability=availability,
        control=SettingsControl.READONLY,
        endpoint=endpoint,
        order=order,
        tags=tags,
    )


def _local_preference(
    field_id: str,
    title: str,
    *,
    description: str,
    control: SettingsControl,
    order: int,
    options: tuple[SettingsOption, ...] = (),
    tags: tuple[str, ...] = (),
) -> SettingsFieldDescriptor:
    """
    Beschreibt eine lokale Frontend-Präferenz.

    Lokale Präferenzen dürfen keine serverseitige Sicherheitsentscheidung
    beeinflussen.
    """

    return _field(
        field_id,
        title,
        description=description,
        source=SettingsSource.LOCAL_PREFERENCE,
        availability=SettingsAvailability.AVAILABLE,
        control=control,
        editable=True,
        options=options,
        order=order,
        tags=tags,
    )


# ============================================================
# Identität und Verhalten
# ============================================================


def _build_identity_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE

    return SettingsGroupDescriptor(
        id="identity",
        title="Identität und Verhalten",
        description=(
            "Grundidentität, Auftrag, Kommunikationsstil, Autonomie und "
            "kontrollierte Selbstprüfung von Kernschmied."
        ),
        icon="identity",
        order=10,
        availability=available,
        sections=(
            SettingsSectionDescriptor(
                id="identity.general",
                title="Identität",
                description=(
                    "Name, Rolle, Grundauftrag, Organisation, Sprache und "
                    "allgemeine Verhaltensgrundsätze."
                ),
                order=10,
                availability=available,
                fields=(
                    _config_field(
                        "identity.name",
                        "Name",
                        description="Anzeigename der KI-Arbeitskraft.",
                        group="identity",
                        key="name",
                        control=SettingsControl.TEXT,
                        order=10,
                        tags=(
                            "identity",
                            "name",
                        ),
                    ),
                    _config_field(
                        "identity.role_description",
                        "Rollenbeschreibung",
                        description=(
                            "Beschreibt die grundsätzliche Rolle von "
                            "Kernschmied innerhalb der Organisation."
                        ),
                        group="identity",
                        key="role_description",
                        control=SettingsControl.TEXTAREA,
                        order=20,
                        tags=(
                            "identity",
                            "role",
                        ),
                    ),
                    _config_field(
                        "identity.mission",
                        "Grundauftrag",
                        description=(
                            "Übergeordneter Auftrag, an dem sich Kernschmied "
                            "bei Planung, Ausführung und Ergebnisprüfung "
                            "orientiert."
                        ),
                        group="identity",
                        key="mission",
                        control=SettingsControl.TEXTAREA,
                        requires_confirmation=True,
                        order=30,
                        tags=(
                            "identity",
                            "mission",
                            "high-impact",
                        ),
                    ),
                    _config_field(
                        "identity.organization_description",
                        "Organisationsbeschreibung",
                        description=(
                            "Beschreibung des Unternehmens oder der "
                            "Organisation, für die Kernschmied arbeitet."
                        ),
                        group="identity",
                        key="organization_description",
                        control=SettingsControl.TEXTAREA,
                        order=40,
                        tags=(
                            "identity",
                            "organization",
                        ),
                    ),
                    _config_field(
                        "identity.default_language",
                        "Standardsprache",
                        description=(
                            "Bevorzugte Sprache für Antworten, Dokumente "
                            "und andere Arbeitsergebnisse."
                        ),
                        group="identity",
                        key="default_language",
                        control=SettingsControl.SELECT,
                        options=LANGUAGE_OPTIONS,
                        order=50,
                        tags=(
                            "identity",
                            "language",
                        ),
                    ),
                    _config_field(
                        "identity.timezone",
                        "Zeitzone",
                        description=(
                            "IANA-Zeitzone für Termine, Fristen und "
                            "zeitabhängige Aufgaben."
                        ),
                        group="identity",
                        key="timezone",
                        control=SettingsControl.TEXT,
                        order=60,
                        tags=(
                            "identity",
                            "timezone",
                        ),
                    ),
                    _config_field(
                        "identity.behavior_principles",
                        "Allgemeine Verhaltensgrundsätze",
                        description=(
                            "Grundlegende Regeln für sorgfältiges, "
                            "nachvollziehbares, lösungsorientiertes und "
                            "sicheres Arbeiten."
                        ),
                        group="identity",
                        key="behavior_principles",
                        control=SettingsControl.TEXTAREA,
                        requires_confirmation=True,
                        order=70,
                        tags=(
                            "identity",
                            "behavior",
                            "high-impact",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="identity.communication",
                title="Kommunikationsverhalten",
                description=(
                    "Vorgaben für Tonalität, Antworttiefe, Rückfragen, "
                    "Unsicherheiten, Quellen und Alternativen."
                ),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "identity.tone",
                        "Tonalität",
                        description=("Bevorzugter Kommunikationsstil von Kernschmied."),
                        group="identity",
                        key="tone",
                        control=SettingsControl.SELECT,
                        options=TONE_OPTIONS,
                        order=10,
                        tags=(
                            "identity",
                            "communication",
                            "tone",
                        ),
                    ),
                    _config_field(
                        "identity.response_depth",
                        "Antworttiefe",
                        description=(
                            "Bestimmt den standardmäßigen Umfang und "
                            "Detailgrad von Antworten."
                        ),
                        group="identity",
                        key="response_depth",
                        control=SettingsControl.SELECT,
                        options=RESPONSE_DEPTH_OPTIONS,
                        order=20,
                        tags=(
                            "identity",
                            "communication",
                            "verbosity",
                        ),
                    ),
                    _config_field(
                        "identity.ask_when_unclear",
                        "Bei Unklarheit nachfragen",
                        description=(
                            "Bei entscheidenden fehlenden Informationen "
                            "gezielt Rückfragen stellen."
                        ),
                        group="identity",
                        key="ask_when_unclear",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "identity",
                            "communication",
                            "questions",
                        ),
                    ),
                    _config_field(
                        "identity.allow_reasonable_assumptions",
                        "Vertretbare Annahmen zulassen",
                        description=(
                            "Bei nicht kritischen Informationslücken klar "
                            "gekennzeichnete, plausible Annahmen treffen."
                        ),
                        group="identity",
                        key="allow_reasonable_assumptions",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "identity",
                            "communication",
                            "assumptions",
                        ),
                    ),
                    _config_field(
                        "identity.mark_uncertainty",
                        "Unsicherheit kennzeichnen",
                        description=(
                            "Unsichere Annahmen, Schätzungen und nicht "
                            "bestätigte Informationen sichtbar kennzeichnen."
                        ),
                        group="identity",
                        key="mark_uncertainty",
                        control=SettingsControl.BOOLEAN,
                        order=50,
                        tags=(
                            "identity",
                            "communication",
                            "uncertainty",
                        ),
                    ),
                    _config_field(
                        "identity.cite_sources",
                        "Quellen nennen",
                        description=(
                            "Verwendete interne oder externe Quellen in "
                            "Ergebnissen sichtbar ausweisen."
                        ),
                        group="identity",
                        key="cite_sources",
                        control=SettingsControl.BOOLEAN,
                        order=60,
                        tags=(
                            "identity",
                            "communication",
                            "sources",
                        ),
                    ),
                    _config_field(
                        "identity.show_alternatives",
                        "Alternativen darstellen",
                        description=(
                            "Bei mehreren sinnvollen Lösungswegen geeignete "
                            "Alternativen und deren Unterschiede darstellen."
                        ),
                        group="identity",
                        key="show_alternatives",
                        control=SettingsControl.BOOLEAN,
                        order=70,
                        tags=(
                            "identity",
                            "communication",
                            "alternatives",
                        ),
                    ),
                    _config_field(
                        "identity.include_recommendations",
                        "Handlungsempfehlungen geben",
                        description=(
                            "Geeignete nächste Schritte und konkrete "
                            "Handlungsempfehlungen ergänzen."
                        ),
                        group="identity",
                        key="include_recommendations",
                        control=SettingsControl.BOOLEAN,
                        order=80,
                        tags=(
                            "identity",
                            "communication",
                            "recommendations",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="identity.autonomy",
                title="Autonomie",
                description=(
                    "Steuert, wie selbstständig Kernschmied Aufgaben "
                    "planen, vorbereiten und freigegebene Aktionen ausführen darf."
                ),
                order=30,
                availability=available,
                fields=(
                    _config_field(
                        "identity.autonomy_level",
                        "Autonomiegrad",
                        description=(
                            "Allgemeiner Standard für selbstständige "
                            "Planung und Ausführung."
                        ),
                        group="identity",
                        key="autonomy_level",
                        control=SettingsControl.SELECT,
                        options=AUTONOMY_OPTIONS,
                        requires_confirmation=True,
                        order=10,
                        tags=(
                            "identity",
                            "autonomy",
                            "high-impact",
                        ),
                    ),
                    _config_field(
                        "identity.prepare_actions_without_confirmation",
                        "Aktionen ohne Bestätigung vorbereiten",
                        description=(
                            "Kernschmied darf Entwürfe und Aktionsvorschläge "
                            "ohne vorherige Bestätigung vorbereiten."
                        ),
                        group="identity",
                        key="prepare_actions_without_confirmation",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "identity",
                            "autonomy",
                            "draft",
                        ),
                    ),
                    _config_field(
                        "identity.confirm_high_impact_actions",
                        "Wirkungsstarke Aktionen bestätigen",
                        description=(
                            "Aktionen mit erheblichen externen, finanziellen "
                            "oder dauerhaften Auswirkungen bestätigen lassen."
                        ),
                        group="identity",
                        key="confirm_high_impact_actions",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=30,
                        tags=(
                            "identity",
                            "autonomy",
                            "confirmation",
                            "high-impact",
                        ),
                    ),
                    _config_field(
                        "identity.stop_on_security_uncertainty",
                        "Bei Sicherheitsunsicherheit stoppen",
                        description=(
                            "Die Ausführung abbrechen, wenn Berechtigung, "
                            "Datenzugriff oder Auswirkung nicht sicher bestimmt "
                            "werden können."
                        ),
                        group="identity",
                        key="stop_on_security_uncertainty",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=40,
                        tags=(
                            "identity",
                            "autonomy",
                            "security",
                        ),
                    ),
                    _config_field(
                        "identity.propose_follow_up_actions",
                        "Folgeaktionen vorschlagen",
                        description=(
                            "Nach Abschluss einer Aufgabe sinnvolle nächste "
                            "Schritte vorschlagen."
                        ),
                        group="identity",
                        key="propose_follow_up_actions",
                        control=SettingsControl.BOOLEAN,
                        order=50,
                        tags=(
                            "identity",
                            "autonomy",
                            "follow-up",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="identity.adaptation",
                title="Anpassung",
                description=(
                    "Legt fest, welche freigegebenen Kontexte und Präferenzen "
                    "bei der Arbeitsweise berücksichtigt werden."
                ),
                order=40,
                availability=available,
                fields=(
                    _config_field(
                        "identity.use_user_preferences",
                        "Benutzerpräferenzen berücksichtigen",
                        description=(
                            "Freigegebene, versionierte Benutzerpräferenzen "
                            "bei Kommunikation und Ergebnissen berücksichtigen."
                        ),
                        group="identity",
                        key="use_user_preferences",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "identity",
                            "adaptation",
                            "user",
                        ),
                    ),
                    _config_field(
                        "identity.use_organization_context",
                        "Organisationskontext berücksichtigen",
                        description=(
                            "Freigegebenes Organisationswissen bei Planung "
                            "und Ergebniserstellung berücksichtigen."
                        ),
                        group="identity",
                        key="use_organization_context",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "identity",
                            "adaptation",
                            "organization",
                        ),
                    ),
                    _config_field(
                        "identity.use_project_context",
                        "Projektkontext berücksichtigen",
                        description=(
                            "Den aktiven Projekt- und Hierarchiekontext "
                            "bei Aufgaben berücksichtigen."
                        ),
                        group="identity",
                        key="use_project_context",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "identity",
                            "adaptation",
                            "project",
                        ),
                    ),
                    _config_field(
                        "identity.adapt_communication_style",
                        "Kommunikationsstil anpassen",
                        description=(
                            "Den Stil innerhalb der freigegebenen Grenzen an "
                            "Benutzer, Aufgabe und Kommunikationskanal anpassen."
                        ),
                        group="identity",
                        key="adapt_communication_style",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "identity",
                            "adaptation",
                            "communication",
                        ),
                    ),
                    _resource_link(
                        "identity.learned_preferences",
                        "Gelernte Präferenzen",
                        description=(
                            "Versionierte und freigegebene Präferenzen sowie "
                            "noch offene Präferenzkandidaten anzeigen."
                        ),
                        endpoint="/api/v1/knowledge/preferences",
                        availability=SettingsAvailability.PLANNED,
                        order=50,
                        tags=(
                            "identity",
                            "adaptation",
                            "preferences",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="identity.self_check",
                title="Selbstprüfung",
                description=(
                    "Kontrollierte Prüfung von Ergebnissen vor Abschluss "
                    "oder Ausführung einer Aufgabe."
                ),
                order=50,
                availability=available,
                fields=(
                    _config_field(
                        "identity.self_check_enabled",
                        "Selbstprüfung aktivieren",
                        description=(
                            "Ergebnisse vor Abschluss auf offensichtliche "
                            "Fehler, Widersprüche und Regelverletzungen prüfen."
                        ),
                        group="identity",
                        key="self_check_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "identity",
                            "self-check",
                        ),
                    ),
                    _config_field(
                        "identity.check_goal_completion",
                        "Zielerreichung prüfen",
                        description=(
                            "Prüfen, ob die ursprüngliche Aufgabe vollständig "
                            "und angemessen erfüllt wurde."
                        ),
                        group="identity",
                        key="check_goal_completion",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "identity",
                            "self-check",
                            "goal",
                        ),
                    ),
                    _config_field(
                        "identity.check_completeness",
                        "Vollständigkeit prüfen",
                        description=(
                            "Prüfen, ob erforderliche Bestandteile und Angaben "
                            "im Ergebnis enthalten sind."
                        ),
                        group="identity",
                        key="check_completeness",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "identity",
                            "self-check",
                            "completeness",
                        ),
                    ),
                    _config_field(
                        "identity.check_consistency",
                        "Konsistenz prüfen",
                        description=(
                            "Zahlen, Aussagen, Einheiten und Bezüge auf "
                            "innere Widersprüche prüfen."
                        ),
                        group="identity",
                        key="check_consistency",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "identity",
                            "self-check",
                            "consistency",
                        ),
                    ),
                    _config_field(
                        "identity.check_plausibility",
                        "Plausibilität prüfen",
                        description=(
                            "Zahlen, Aussagen und Schlussfolgerungen auf "
                            "offensichtliche Unplausibilitäten prüfen."
                        ),
                        group="identity",
                        key="check_plausibility",
                        control=SettingsControl.BOOLEAN,
                        order=50,
                        tags=(
                            "identity",
                            "self-check",
                            "plausibility",
                        ),
                    ),
                    _config_field(
                        "identity.detect_missing_information",
                        "Fehlende Informationen erkennen",
                        description=(
                            "Fehlende Angaben erkennen und als Rückfrage, "
                            "Annahme oder offene Stelle sichtbar machen."
                        ),
                        group="identity",
                        key="detect_missing_information",
                        control=SettingsControl.BOOLEAN,
                        order=60,
                        tags=(
                            "identity",
                            "self-check",
                            "missing-information",
                        ),
                    ),
                    _config_field(
                        "identity.allow_correction_attempt",
                        "Korrekturversuch erlauben",
                        description=(
                            "Bei erkannten Fehlern einen kontrollierten "
                            "Korrekturversuch durchführen."
                        ),
                        group="identity",
                        key="allow_correction_attempt",
                        control=SettingsControl.BOOLEAN,
                        order=70,
                        tags=(
                            "identity",
                            "self-check",
                            "correction",
                        ),
                    ),
                    _config_field(
                        "identity.max_correction_attempts",
                        "Maximale Korrekturversuche",
                        description=(
                            "Begrenzt automatische Korrekturversuche vor "
                            "Abbruch oder Rückfrage."
                        ),
                        group="identity",
                        key="max_correction_attempts",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=10,
                        order=80,
                        tags=(
                            "identity",
                            "self-check",
                            "limits",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Prompts und Arbeitsanweisungen
# ============================================================


def _build_prompts_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    prepared = SettingsAvailability.PREPARED

    return SettingsGroupDescriptor(
        id="prompts",
        title="Prompts und Arbeitsanweisungen",
        description=(
            "Versionierte System-, Aufgaben- und Kontextprompts sowie "
            "Vererbung, Komposition und Auswertung."
        ),
        icon="message-square-code",
        order=20,
        availability=prepared,
        sections=(
            SettingsSectionDescriptor(
                id="prompts.resources",
                title="Prompt-Ressourcen",
                description=(
                    "Versionierte Prompts und Arbeitsanweisungen mit "
                    "Gültigkeitsbereichen und Freigabestatus."
                ),
                order=10,
                availability=prepared,
                fields=(
                    _resource_link(
                        "prompts.manage",
                        "Prompts verwalten",
                        description=(
                            "Versionierte System-, Aufgaben- und "
                            "Kontextprompts verwalten."
                        ),
                        endpoint="/api/v1/prompts",
                        availability=prepared,
                        order=10,
                        tags=(
                            "prompts",
                            "resource",
                        ),
                    ),
                    _resource_link(
                        "prompts.test_cases",
                        "Prompt-Testfälle",
                        description=(
                            "Testaufgaben, Referenzergebnisse und "
                            "Qualitätskriterien verwalten."
                        ),
                        endpoint="/api/v1/prompts/test-cases",
                        availability=SettingsAvailability.PLANNED,
                        order=20,
                        tags=(
                            "prompts",
                            "evaluation",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="prompts.composition",
                title="Komposition und Vererbung",
                description=(
                    "Steuert die kontrollierte Zusammenstellung mehrerer Prompt-Ebenen."
                ),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "prompts.inheritance",
                        "Prompt-Vererbung",
                        description=(
                            "Prompt-Vererbung über Organisation, "
                            "Arbeitsbereich, Projekt und Aufgabe aktivieren."
                        ),
                        group="prompts",
                        key="inheritance_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "prompts",
                            "inheritance",
                        ),
                    ),
                    _config_field(
                        "prompts.conflict_strategy",
                        "Konfliktstrategie",
                        description=(
                            "Legt fest, wie widersprüchliche "
                            "Prompt-Anweisungen behandelt werden."
                        ),
                        group="prompts",
                        key="conflict_strategy",
                        control=SettingsControl.SELECT,
                        options=PROMPT_CONFLICT_OPTIONS,
                        requires_confirmation=True,
                        order=20,
                        tags=(
                            "prompts",
                            "conflict",
                        ),
                    ),
                    _config_field(
                        "prompts.max_length",
                        "Maximale Prompt-Länge",
                        description=(
                            "Obergrenze für den vollständig zusammengesetzten Prompt."
                        ),
                        group="prompts",
                        key="max_composed_length",
                        control=SettingsControl.NUMBER,
                        minimum=1_000,
                        maximum=500_000,
                        order=30,
                        tags=(
                            "prompts",
                            "limits",
                        ),
                    ),
                    _config_field(
                        "prompts.include_examples",
                        "Beispiele berücksichtigen",
                        description=(
                            "Freigegebene positive und negative Beispiele "
                            "in Aufgabenprompts einbeziehen."
                        ),
                        group="prompts",
                        key="include_examples",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "prompts",
                            "examples",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="prompts.runtime",
                title="Laufzeitverhalten",
                description=(
                    "Steuert die Auswahl und Verwendung freigegebener "
                    "Prompts während einer Aufgabe."
                ),
                order=30,
                availability=available,
                fields=(
                    _config_field(
                        "prompts.automatic_selection",
                        "Automatische Prompt-Auswahl",
                        description=(
                            "Passende freigegebene Aufgabenprompts anhand "
                            "der erkannten Absicht auswählen."
                        ),
                        group="prompts",
                        key="automatic_selection",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "prompts",
                            "routing",
                        ),
                    ),
                    _config_field(
                        "prompts.require_active_revision",
                        "Nur aktive Revisionen verwenden",
                        description=(
                            "Entwürfe und archivierte Revisionen von der "
                            "produktiven Verwendung ausschließen."
                        ),
                        group="prompts",
                        key="require_active_revision",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=20,
                        tags=(
                            "prompts",
                            "versioning",
                        ),
                    ),
                    _config_field(
                        "prompts.fallback_enabled",
                        "Fallback-Prompt verwenden",
                        description=(
                            "Bei unbekannten Aufgaben einen freigegebenen "
                            "allgemeinen Arbeits-Prompt verwenden."
                        ),
                        group="prompts",
                        key="fallback_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "prompts",
                            "fallback",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Modelle und Provider
# ============================================================


def _build_models_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    prepared = SettingsAvailability.PREPARED
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="models",
        title="Modelle und Provider",
        description=(
            "Provider, Modellregistrierung, Routing, Generierungswerte "
            "und Ausfallsicherheit."
        ),
        icon="cpu",
        order=30,
        availability=available,
        sections=(
            SettingsSectionDescriptor(
                id="models.registry",
                title="Registries",
                description=(
                    "Freigegebene Modelle und vorbereitete Providerverwaltung."
                ),
                order=10,
                availability=available,
                fields=(
                    _resource_link(
                        "models.list",
                        "Modelle",
                        description=(
                            "Registrierte, verfügbare und freigegebene Modelle."
                        ),
                        endpoint="/api/v1/models?include_disabled=true",
                        availability=available,
                        order=10,
                        tags=(
                            "models",
                            "registry",
                        ),
                    ),
                    _resource_link(
                        "providers.manage",
                        "Provider",
                        description=(
                            "Provider, Endpoints, Secret-Referenzen und "
                            "Verbindungsparameter verwalten."
                        ),
                        endpoint="/api/v1/providers",
                        availability=prepared,
                        order=20,
                        tags=(
                            "models",
                            "providers",
                        ),
                    ),
                    _config_field(
                        "models.default",
                        "Standardmodell",
                        description=(
                            "Standardmodell für Aufgaben ohne explizite "
                            "Modellzuordnung."
                        ),
                        group="models",
                        key="default_model",
                        control=SettingsControl.TEXT,
                        order=30,
                        tags=(
                            "models",
                            "default",
                        ),
                    ),
                    _config_field(
                        "models.fallback",
                        "Fallback-Modell",
                        description=(
                            "Ersatzmodell bei Nichtverfügbarkeit oder "
                            "geeignetem Providerfehler."
                        ),
                        group="models",
                        key="fallback_model_id",
                        control=SettingsControl.TEXT,
                        order=40,
                        tags=(
                            "models",
                            "fallback",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="models.routing",
                title="Modell-Routing",
                description=(
                    "Dynamische Auswahl innerhalb der kontrolliert "
                    "freigegebenen Modellmenge."
                ),
                order=20,
                availability=prepared,
                fields=(
                    _config_field(
                        "models.routing_mode",
                        "Routing-Modus",
                        description=(
                            "Strategie für die Auswahl eines geeigneten "
                            "freigegebenen Modells."
                        ),
                        group="models",
                        key="routing_mode",
                        control=SettingsControl.SELECT,
                        options=MODEL_ROUTING_OPTIONS,
                        order=10,
                        tags=(
                            "models",
                            "routing",
                        ),
                    ),
                    _config_field(
                        "models.prefer_local",
                        "Lokale Modelle bevorzugen",
                        description=(
                            "Geeignete lokale Modelle vor externen "
                            "Providern priorisieren."
                        ),
                        group="models",
                        key="prefer_local_models",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "models",
                            "routing",
                            "local",
                        ),
                    ),
                    _config_field(
                        "models.allow_paid",
                        "Kostenpflichtige Modelle erlauben",
                        description=(
                            "Freigegebene kostenpflichtige Provider bei "
                            "Bedarf in das Routing einbeziehen."
                        ),
                        group="models",
                        key="allow_paid_models",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=30,
                        tags=(
                            "models",
                            "routing",
                            "cost",
                        ),
                    ),
                    _resource_link(
                        "models.routing_rules",
                        "Routing-Regeln",
                        description=(
                            "Versionierte Regeln nach Aufgabe, Fähigkeit, "
                            "Datenschutzklasse, Kosten und Verfügbarkeit."
                        ),
                        endpoint="/api/v1/model-routing",
                        availability=planned,
                        order=40,
                        tags=(
                            "models",
                            "routing",
                            "resource",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="models.generation",
                title="Generierung",
                description=(
                    "Standardwerte für Modellgenerierung. "
                    "Modellspezifische Grenzen bleiben vorrangig."
                ),
                order=30,
                availability=available,
                fields=(
                    _config_field(
                        "models.temperature",
                        "Temperature",
                        description="Standardwert für die Antwortvarianz.",
                        group="models",
                        key="temperature",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=2,
                        order=10,
                        tags=(
                            "models",
                            "generation",
                        ),
                    ),
                    _config_field(
                        "models.top_p",
                        "Top P",
                        description="Nucleus-Sampling-Grenze.",
                        group="models",
                        key="top_p",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=1,
                        order=20,
                        tags=(
                            "models",
                            "generation",
                        ),
                    ),
                    _config_field(
                        "models.top_k",
                        "Top K",
                        description=(
                            "Optionale Begrenzung der berücksichtigten Tokens."
                        ),
                        group="models",
                        key="top_k",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=1_000,
                        order=30,
                        tags=(
                            "models",
                            "generation",
                        ),
                    ),
                    _config_field(
                        "models.repeat_penalty",
                        "Repeat Penalty",
                        description=(
                            "Standardwert zur Verringerung unnötiger Wiederholungen."
                        ),
                        group="models",
                        key="repeat_penalty",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=5,
                        order=40,
                        tags=(
                            "models",
                            "generation",
                        ),
                    ),
                    _config_field(
                        "models.max_output_tokens",
                        "Maximale Ausgabetokens",
                        description=("Standardlimit für Modellantworten."),
                        group="models",
                        key="max_output_tokens",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=200_000,
                        order=50,
                        tags=(
                            "models",
                            "generation",
                            "limits",
                        ),
                    ),
                    _config_field(
                        "models.structured_output",
                        "Strukturierte Ausgabe bevorzugen",
                        description=(
                            "Bei geeigneten Aufgaben und Modellen "
                            "strukturierte Ausgaben bevorzugen."
                        ),
                        group="models",
                        key="prefer_structured_output",
                        control=SettingsControl.BOOLEAN,
                        order=60,
                        tags=(
                            "models",
                            "generation",
                            "structured-output",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="models.resilience",
                title="Ausfallsicherheit",
                description=(
                    "Timeouts, Wiederholungen, Failover und Statusüberwachung."
                ),
                order=40,
                availability=prepared,
                fields=(
                    _config_field(
                        "models.request_timeout",
                        "Request-Timeout",
                        description=(
                            "Standard-Timeout einer Modellanfrage in Sekunden."
                        ),
                        group="models",
                        key="request_timeout_seconds",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=86_400,
                        order=10,
                        tags=(
                            "models",
                            "resilience",
                            "timeout",
                        ),
                    ),
                    _config_field(
                        "models.max_retries",
                        "Maximale Wiederholungen",
                        description=(
                            "Maximale Wiederholungen bei geeigneten "
                            "vorübergehenden Providerfehlern."
                        ),
                        group="models",
                        key="max_retries",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=20,
                        order=20,
                        tags=(
                            "models",
                            "resilience",
                            "retry",
                        ),
                    ),
                    _config_field(
                        "models.failover_enabled",
                        "Failover aktivieren",
                        description=(
                            "Bei geeigneten Fehlern ein freigegebenes "
                            "Fallback-Modell verwenden."
                        ),
                        group="models",
                        key="failover_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "models",
                            "resilience",
                            "failover",
                        ),
                    ),
                    _runtime_field(
                        "models.health",
                        "Provider- und Modellstatus",
                        description=(
                            "Health, Latenzen und Fehlerraten der "
                            "registrierten Modelle."
                        ),
                        endpoint="/api/v1/diagnostics/models",
                        availability=prepared,
                        order=40,
                        tags=(
                            "models",
                            "diagnostics",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Tools und Fähigkeiten
# ============================================================


def _build_tools_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    prepared = SettingsAvailability.PREPARED
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="tools",
        title="Tools und Fähigkeiten",
        description=(
            "Tool-Registry, automatische Auswahl, Ausführungsgrenzen, "
            "Bestätigungen und Simulation."
        ),
        icon="wrench",
        order=40,
        availability=available,
        sections=(
            SettingsSectionDescriptor(
                id="tools.registry",
                title="Registry und Auswahl",
                description=(
                    "Registrierte Tools und kontrollierte automatische Auswahl."
                ),
                order=10,
                availability=available,
                fields=(
                    _resource_link(
                        "tools.list",
                        "Tools",
                        description=(
                            "Entdeckte, registrierte, freigegebene und "
                            "verfügbare Tools."
                        ),
                        endpoint=(
                            "/api/v1/tools"
                            "?include_disabled=true"
                            "&include_unavailable=true"
                        ),
                        availability=available,
                        order=10,
                        tags=(
                            "tools",
                            "registry",
                        ),
                    ),
                    _config_field(
                        "tools.auto_select",
                        "Automatische Tool-Auswahl",
                        description=(
                            "Das Modell darf geeignete freigegebene Tools "
                            "selbst auswählen."
                        ),
                        group="tools",
                        key="automatic_selection",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "tools",
                            "selection",
                        ),
                    ),
                    _config_field(
                        "tools.max_selected",
                        "Maximale Tool-Anzahl",
                        description=(
                            "Maximale Zahl gleichzeitig für eine Aufgabe "
                            "ausgewählter Tools."
                        ),
                        group="tools",
                        key="max_selected_tools",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=100,
                        order=30,
                        tags=(
                            "tools",
                            "selection",
                            "limits",
                        ),
                    ),
                    _config_field(
                        "tools.max_rounds",
                        "Maximale Tool-Runden",
                        description="Obergrenze der Tool-Runden je Aufgabe.",
                        group="tools",
                        key="max_rounds",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=100,
                        order=40,
                        tags=(
                            "tools",
                            "execution",
                            "limits",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="tools.execution",
                title="Ausführung",
                description=(
                    "Timeouts, Wiederholungen, Parallelität und Ausgabegrenzen."
                ),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "tools.timeout",
                        "Standard-Timeout",
                        description=(
                            "Maximale Standardlaufzeit eines Tool-Aufrufs in Sekunden."
                        ),
                        group="tools",
                        key="default_timeout_seconds",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=3_600,
                        order=10,
                        tags=(
                            "tools",
                            "execution",
                            "timeout",
                        ),
                    ),
                    _config_field(
                        "tools.max_retries",
                        "Maximale Wiederholungen",
                        description=(
                            "Maximale Wiederholungen bei geeigneten "
                            "vorübergehenden Fehlern."
                        ),
                        group="tools",
                        key="max_retries",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=20,
                        order=20,
                        tags=(
                            "tools",
                            "execution",
                            "retry",
                        ),
                    ),
                    _config_field(
                        "tools.max_parallel",
                        "Maximale Parallelität",
                        description=("Maximale Zahl parallel laufender Tool-Aufrufe."),
                        group="tools",
                        key="max_parallel_calls",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=50,
                        order=30,
                        tags=(
                            "tools",
                            "execution",
                            "parallel",
                        ),
                    ),
                    _config_field(
                        "tools.max_output_size",
                        "Maximale Ausgabegröße",
                        description=("Maximale normalisierte Tool-Ausgabe in Bytes."),
                        group="tools",
                        key="max_output_bytes",
                        control=SettingsControl.NUMBER,
                        minimum=1_024,
                        maximum=100_000_000,
                        order=40,
                        tags=(
                            "tools",
                            "execution",
                            "limits",
                        ),
                    ),
                    _config_field(
                        "tools.send_progress",
                        "Fortschritt anzeigen",
                        description=(
                            "Sichere Fortschrittsmeldungen bei längeren "
                            "Tool-Ausführungen übertragen."
                        ),
                        group="tools",
                        key="send_progress",
                        control=SettingsControl.BOOLEAN,
                        order=50,
                        tags=(
                            "tools",
                            "execution",
                            "progress",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="tools.confirmation",
                title="Bestätigungen",
                description=(
                    "Schutzregeln für Aktionen mit externen oder "
                    "dauerhaften Auswirkungen."
                ),
                order=30,
                availability=available,
                fields=(
                    _config_field(
                        "tools.confirm_write",
                        "Schreibaktionen bestätigen",
                        description=(
                            "Schreibende Aktionen erfordern eine Benutzerbestätigung."
                        ),
                        group="tools",
                        key="confirm_write_actions",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=10,
                        tags=(
                            "tools",
                            "confirmation",
                            "write",
                        ),
                    ),
                    _config_field(
                        "tools.confirm_delete",
                        "Löschaktionen bestätigen",
                        description=(
                            "Löschende Aktionen erfordern immer eine Bestätigung."
                        ),
                        group="tools",
                        key="confirm_delete_actions",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=20,
                        tags=(
                            "tools",
                            "confirmation",
                            "delete",
                        ),
                    ),
                    _config_field(
                        "tools.confirm_external",
                        "Externe Kommunikation bestätigen",
                        description=(
                            "Versand, Veröffentlichung und sonstige externe "
                            "Kommunikation bestätigen."
                        ),
                        group="tools",
                        key="confirm_external_communication",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=30,
                        tags=(
                            "tools",
                            "confirmation",
                            "external",
                        ),
                    ),
                    _config_field(
                        "tools.confirm_financial",
                        "Finanzielle Aktionen bestätigen",
                        description=(
                            "Zahlungen, Buchungen und andere finanzielle "
                            "Aktionen benötigen eine ausdrückliche Bestätigung."
                        ),
                        group="tools",
                        key="confirm_financial_actions",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=40,
                        tags=(
                            "tools",
                            "confirmation",
                            "financial",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="tools.processing",
                title="Ergebnisverarbeitung",
                description=(
                    "Validierung, Normalisierung und Speicherung von Tool-Ergebnissen."
                ),
                order=40,
                availability=prepared,
                fields=(
                    _config_field(
                        "tools.validate_results",
                        "Ergebnisse validieren",
                        description=(
                            "Tool-Ergebnisse vor weiterer Verwendung gegen "
                            "den bekannten Vertrag prüfen."
                        ),
                        group="tools",
                        key="validate_results",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "tools",
                            "results",
                            "validation",
                        ),
                    ),
                    _config_field(
                        "tools.store_intermediate",
                        "Zwischenergebnisse speichern",
                        description=(
                            "Relevante Zwischenergebnisse innerhalb des "
                            "Auftragskontexts speichern."
                        ),
                        group="tools",
                        key="store_intermediate_results",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "tools",
                            "results",
                            "intermediate",
                        ),
                    ),
                    _config_field(
                        "tools.record_provenance",
                        "Herkunft dokumentieren",
                        description=(
                            "Verwendetes Tool, Version, Eingabe und "
                            "Ergebnisreferenz nachvollziehbar speichern."
                        ),
                        group="tools",
                        key="record_result_provenance",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "tools",
                            "results",
                            "provenance",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="tools.simulation",
                title="Test und Simulation",
                description=(
                    "Vorbereitete Ressourcen für Dry Runs und Auswirkungsanalysen."
                ),
                order=50,
                availability=planned,
                fields=(
                    _resource_link(
                        "tools.simulations",
                        "Tool-Simulationen",
                        description=(
                            "Dry Runs, simulierte Ergebnisse und "
                            "Auswirkungsanalysen verwalten."
                        ),
                        endpoint="/api/v1/tools/simulations",
                        availability=planned,
                        order=10,
                        tags=(
                            "tools",
                            "simulation",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Wissen, Gedächtnis und Kontext
# ============================================================


def _build_knowledge_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    prepared = SettingsAvailability.PREPARED
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="knowledge",
        title="Wissen, Gedächtnis und Kontext",
        description=(
            "Kontextquellen, Retrieval, Wissenseinträge, Gedächtnis "
            "und kontrollierte Wissenspflege."
        ),
        icon="brain",
        order=50,
        availability=prepared,
        sections=(
            SettingsSectionDescriptor(
                id="knowledge.context",
                title="Kontextauswahl",
                description=(
                    "Grenzen und Strategien für die automatische "
                    "Zusammenstellung relevanter Kontexte."
                ),
                order=10,
                availability=available,
                fields=(
                    _config_field(
                        "knowledge.auto_context",
                        "Automatische Kontextauswahl",
                        description=(
                            "Relevante freigegebene Quellen automatisch auswählen."
                        ),
                        group="knowledge",
                        key="automatic_context_selection",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "knowledge",
                            "context",
                            "selection",
                        ),
                    ),
                    _config_field(
                        "knowledge.context_strategy",
                        "Kontextstrategie",
                        description=(
                            "Steuert Breite und Vorsicht der Kontextzusammenstellung."
                        ),
                        group="knowledge",
                        key="context_strategy",
                        control=SettingsControl.SELECT,
                        options=CONTEXT_STRATEGY_OPTIONS,
                        order=20,
                        tags=(
                            "knowledge",
                            "context",
                            "strategy",
                        ),
                    ),
                    _config_field(
                        "knowledge.max_sources",
                        "Maximale Quellenzahl",
                        description=("Maximale Zahl kombinierter Kontextquellen."),
                        group="knowledge",
                        key="max_context_sources",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=100,
                        order=30,
                        tags=(
                            "knowledge",
                            "context",
                            "limits",
                        ),
                    ),
                    _config_field(
                        "knowledge.max_context_tokens",
                        "Maximale Kontexttokens",
                        description=(
                            "Obergrenze des aus Wissensquellen erzeugten Kontexts."
                        ),
                        group="knowledge",
                        key="max_context_tokens",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=1_000_000,
                        order=40,
                        tags=(
                            "knowledge",
                            "context",
                            "limits",
                        ),
                    ),
                    _config_field(
                        "knowledge.relevance",
                        "Relevanzschwelle",
                        description=("Mindestwert für die Aufnahme einer Quelle."),
                        group="knowledge",
                        key="relevance_threshold",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=1,
                        order=50,
                        tags=(
                            "knowledge",
                            "context",
                            "relevance",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="knowledge.fusion",
                title="Kontext-Fusion",
                description=(
                    "Zusammenführung, Deduplizierung und Bewertung mehrerer Quellen."
                ),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "knowledge.remove_duplicates",
                        "Duplikate entfernen",
                        description=(
                            "Inhaltlich gleiche oder nahezu gleiche "
                            "Kontextbestandteile zusammenführen."
                        ),
                        group="knowledge",
                        key="remove_duplicate_context",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "knowledge",
                            "fusion",
                            "deduplication",
                        ),
                    ),
                    _config_field(
                        "knowledge.mark_conflicts",
                        "Widersprüche markieren",
                        description=(
                            "Widersprüchliche Quellen nicht still auflösen, "
                            "sondern sichtbar kennzeichnen."
                        ),
                        group="knowledge",
                        key="mark_context_conflicts",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "knowledge",
                            "fusion",
                            "conflicts",
                        ),
                    ),
                    _config_field(
                        "knowledge.prefer_recent",
                        "Aktuelle Quellen bevorzugen",
                        description=(
                            "Bei vergleichbarer Vertrauenswürdigkeit "
                            "aktuellere Quellen bevorzugen."
                        ),
                        group="knowledge",
                        key="prefer_recent_sources",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "knowledge",
                            "fusion",
                            "recency",
                        ),
                    ),
                    _config_field(
                        "knowledge.compress_context",
                        "Kontext komprimieren",
                        description=(
                            "Lange Kontextbestandteile kontrolliert zusammenfassen."
                        ),
                        group="knowledge",
                        key="compress_context",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "knowledge",
                            "fusion",
                            "compression",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="knowledge.memory",
                title="Gedächtnis",
                description=(
                    "Steuert die Verwendung freigegebener kurz- und "
                    "langfristiger Gedächtnisebenen."
                ),
                order=30,
                availability=prepared,
                fields=(
                    _config_field(
                        "knowledge.conversation_memory",
                        "Gesprächsgedächtnis",
                        description=(
                            "Relevante Inhalte der aktuellen Unterhaltung "
                            "als Kontext verwenden."
                        ),
                        group="knowledge",
                        key="conversation_memory_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "knowledge",
                            "memory",
                            "conversation",
                        ),
                    ),
                    _config_field(
                        "knowledge.project_memory",
                        "Projektgedächtnis",
                        description=(
                            "Freigegebenes Wissen des aktiven Projekts verwenden."
                        ),
                        group="knowledge",
                        key="project_memory_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "knowledge",
                            "memory",
                            "project",
                        ),
                    ),
                    _config_field(
                        "knowledge.organization_memory",
                        "Organisationsgedächtnis",
                        description=("Freigegebenes Organisationswissen verwenden."),
                        group="knowledge",
                        key="organization_memory_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "knowledge",
                            "memory",
                            "organization",
                        ),
                    ),
                    _config_field(
                        "knowledge.auto_persist",
                        "Gesprächsinhalte automatisch übernehmen",
                        description=(
                            "Bleibt standardmäßig aus: dauerhafte "
                            "Wissensübernahme erfolgt über geprüfte Kandidaten."
                        ),
                        group="knowledge",
                        key="auto_persist_conversation_facts",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=40,
                        tags=(
                            "knowledge",
                            "memory",
                            "persistence",
                            "high-impact",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="knowledge.resources",
                title="Wissen und Kandidaten",
                description=(
                    "Versionierte Wissenseinträge und noch nicht "
                    "freigegebene Kandidaten."
                ),
                order=40,
                availability=prepared,
                fields=(
                    _resource_link(
                        "knowledge.entries",
                        "Wissenseinträge",
                        description=(
                            "Versionierte Wissenseinträge mit Herkunft, "
                            "Vertrauensgrad und Gültigkeitsbereich."
                        ),
                        endpoint="/api/v1/knowledge",
                        availability=prepared,
                        order=10,
                        tags=(
                            "knowledge",
                            "resource",
                        ),
                    ),
                    _resource_link(
                        "knowledge.candidates",
                        "Wissenskandidaten",
                        description=(
                            "Aus Interaktionen erkannte, noch nicht "
                            "freigegebene Fakten."
                        ),
                        endpoint="/api/v1/knowledge/candidates",
                        availability=planned,
                        order=20,
                        tags=(
                            "knowledge",
                            "candidates",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Planung und Arbeitsweise
# ============================================================


def _build_planning_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    prepared = SettingsAvailability.PREPARED
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="planning",
        title="Planung und Arbeitsweise",
        description=(
            "Aufgabenerkennung, Planung, Ausführung, Fehlerbehandlung, "
            "Nutzerinteraktion und Qualitätssicherung."
        ),
        icon="workflow",
        order=60,
        availability=prepared,
        sections=(
            SettingsSectionDescriptor(
                id="planning.execution",
                title="Planung und Ausführung",
                description=(
                    "Globale Grenzen und Standards für geplante mehrstufige Aufgaben."
                ),
                order=10,
                availability=available,
                fields=(
                    _config_field(
                        "planning.enabled",
                        "Planung aktivieren",
                        description=(
                            "Vor komplexen Aufgaben einen expliziten "
                            "internen Arbeitsplan erzeugen."
                        ),
                        group="planning",
                        key="enabled",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "planning",
                            "execution",
                        ),
                    ),
                    _config_field(
                        "planning.max_steps",
                        "Maximale Schritte",
                        description=("Obergrenze der Ausführungsschritte."),
                        group="planning",
                        key="max_steps",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=500,
                        order=20,
                        tags=(
                            "planning",
                            "execution",
                            "limits",
                        ),
                    ),
                    _config_field(
                        "planning.max_duration",
                        "Maximale Dauer",
                        description=("Maximale Laufzeit einer Aufgabe in Sekunden."),
                        group="planning",
                        key="max_duration_seconds",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=86_400,
                        order=30,
                        tags=(
                            "planning",
                            "execution",
                            "timeout",
                        ),
                    ),
                    _config_field(
                        "planning.parallel_execution",
                        "Parallelisierung zulassen",
                        description=(
                            "Unabhängige, sichere Arbeitsschritte parallel ausführen."
                        ),
                        group="planning",
                        key="parallel_execution_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "planning",
                            "execution",
                            "parallel",
                        ),
                    ),
                    _config_field(
                        "planning.show_progress",
                        "Zwischenstände anzeigen",
                        description=(
                            "Sichere Fortschrittszusammenfassungen im "
                            "Frontend anzeigen."
                        ),
                        group="planning",
                        key="show_progress",
                        control=SettingsControl.BOOLEAN,
                        order=50,
                        tags=(
                            "planning",
                            "progress",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="planning.failure",
                title="Fehlerbehandlung",
                description=(
                    "Steuert Wiederholungen, Alternativen und kontrollierte Abbrüche."
                ),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "planning.failure_strategy",
                        "Standard-Fehlerstrategie",
                        description=(
                            "Standardreaktion bei nicht sicher behebbaren "
                            "Ausführungsfehlern."
                        ),
                        group="planning",
                        key="failure_strategy",
                        control=SettingsControl.SELECT,
                        options=FAILURE_STRATEGY_OPTIONS,
                        order=10,
                        tags=(
                            "planning",
                            "failure",
                        ),
                    ),
                    _config_field(
                        "planning.max_replans",
                        "Maximale Neuplanungen",
                        description=(
                            "Begrenzt automatische Anpassungen eines "
                            "fehlgeschlagenen Plans."
                        ),
                        group="planning",
                        key="max_replans",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=20,
                        order=20,
                        tags=(
                            "planning",
                            "failure",
                            "limits",
                        ),
                    ),
                    _config_field(
                        "planning.save_checkpoints",
                        "Zwischenstände speichern",
                        description=(
                            "Relevante Zwischenstände für Wiederaufnahme "
                            "und Diagnose speichern."
                        ),
                        group="planning",
                        key="save_checkpoints",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "planning",
                            "failure",
                            "checkpoints",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="planning.quality",
                title="Qualitätssicherung",
                description=("Automatische Prüfungen vor Abschluss einer Aufgabe."),
                order=30,
                availability=available,
                fields=(
                    _config_field(
                        "planning.quality_check",
                        "Qualitätsprüfung aktivieren",
                        description=(
                            "Ergebnisse vor Abschluss gegen verfügbare "
                            "Qualitätsregeln prüfen."
                        ),
                        group="planning",
                        key="quality_check_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "planning",
                            "quality",
                        ),
                    ),
                    _config_field(
                        "planning.check_format",
                        "Format prüfen",
                        description=("Erwartete Struktur und Ausgabeform prüfen."),
                        group="planning",
                        key="check_output_format",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "planning",
                            "quality",
                            "format",
                        ),
                    ),
                    _config_field(
                        "planning.check_rules",
                        "Regelkonformität prüfen",
                        description=(
                            "Ergebnis gegen freigegebene fachliche und "
                            "technische Regeln prüfen."
                        ),
                        group="planning",
                        key="check_rule_compliance",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "planning",
                            "quality",
                            "rules",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="planning.interaction",
                title="Nutzerinteraktion",
                description=(
                    "Steuert Rückfragen, Warnungen und sichtbare "
                    "Entwurfskennzeichnungen."
                ),
                order=40,
                availability=available,
                fields=(
                    _config_field(
                        "planning.ask_before_blocked",
                        "Bei Blockierung nachfragen",
                        description=(
                            "Bei fehlenden entscheidenden Informationen "
                            "oder Freigaben gezielt nachfragen."
                        ),
                        group="planning",
                        key="ask_when_blocked",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "planning",
                            "interaction",
                            "questions",
                        ),
                    ),
                    _config_field(
                        "planning.warn_before_risk",
                        "Vor Risiken warnen",
                        description=(
                            "Erkannte relevante Risiken vor Ausführung "
                            "sichtbar darstellen."
                        ),
                        group="planning",
                        key="warn_before_risky_actions",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "planning",
                            "interaction",
                            "risk",
                        ),
                    ),
                    _config_field(
                        "planning.mark_drafts",
                        "Entwürfe kennzeichnen",
                        description=(
                            "Noch nicht freigegebene Ergebnisse deutlich "
                            "als Entwurf markieren."
                        ),
                        group="planning",
                        key="mark_draft_results",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "planning",
                            "interaction",
                            "draft",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="planning.workflows",
                title="Arbeitsdefinitionen",
                description=(
                    "Versionierte, dynamische Plan- und Ausführungsdefinitionen."
                ),
                order=50,
                availability=planned,
                fields=(
                    _resource_link(
                        "planning.workflows",
                        "Workflows",
                        description=("Versionierte Plan- und Ausführungsdefinitionen."),
                        endpoint="/api/v1/workflows",
                        availability=planned,
                        order=10,
                        tags=(
                            "planning",
                            "workflows",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Daten und Speicherung
# ============================================================


def _build_data_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    prepared = SettingsAvailability.PREPARED
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="data",
        title="Daten und Speicherung",
        description=(
            "Artifacts, Speicherziele, Versionierung, Herkunft, "
            "Schemas und Aufbewahrung."
        ),
        icon="database",
        order=70,
        availability=prepared,
        sections=(
            SettingsSectionDescriptor(
                id="data.artifacts",
                title="Artifacts",
                description=(
                    "Generische Arbeitsergebnisse wie Angebote, Bilanzen, "
                    "Briefe, Berichte und Kalkulationen."
                ),
                order=10,
                availability=prepared,
                fields=(
                    _resource_link(
                        "artifacts.list",
                        "Arbeitsergebnisse",
                        description=("Versionierte strukturierte Arbeitsergebnisse."),
                        endpoint="/api/v1/artifacts",
                        availability=planned,
                        order=10,
                        tags=(
                            "data",
                            "artifacts",
                        ),
                    ),
                    _resource_link(
                        "artifacts.schemas",
                        "Artifact-Schemas",
                        description=(
                            "Versionierte Ausgabeschemas, Validierung und Renderer."
                        ),
                        endpoint="/api/v1/artifact-schemas",
                        availability=planned,
                        order=20,
                        tags=(
                            "data",
                            "artifacts",
                            "schemas",
                        ),
                    ),
                    _config_field(
                        "artifacts.default_status",
                        "Standardstatus",
                        description=("Status neuer Arbeitsergebnisse."),
                        group="artifacts",
                        key="default_status",
                        control=SettingsControl.SELECT,
                        options=ARTIFACT_STATUS_OPTIONS,
                        order=30,
                        tags=(
                            "data",
                            "artifacts",
                            "status",
                        ),
                    ),
                    _config_field(
                        "artifacts.auto_version",
                        "Automatisch versionieren",
                        description=(
                            "Änderungen an gespeicherten Artifacts als "
                            "neue Revision ablegen."
                        ),
                        group="artifacts",
                        key="automatic_versioning",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "data",
                            "artifacts",
                            "versioning",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="data.storage",
                title="Speicherverhalten",
                description=(
                    "Grundlegende Regeln für strukturierte Ergebnisse "
                    "und gerenderte Ausgaben."
                ),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "data.store_structured_content",
                        "Strukturierte Inhalte speichern",
                        description=(
                            "Neben gerenderten Dokumenten den strukturierten "
                            "Inhalt versioniert speichern."
                        ),
                        group="data",
                        key="store_structured_content",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "data",
                            "storage",
                            "structured",
                        ),
                    ),
                    _config_field(
                        "data.store_rendered_outputs",
                        "Gerenderte Ausgaben speichern",
                        description=(
                            "Erzeugte PDF-, DOCX- oder andere Ausgaben "
                            "als referenzierte Dateien speichern."
                        ),
                        group="data",
                        key="store_rendered_outputs",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "data",
                            "storage",
                            "rendered",
                        ),
                    ),
                    _config_field(
                        "data.record_provenance",
                        "Herkunft speichern",
                        description=(
                            "Benutzeranfrage, Prompts, Modelle, Tools, "
                            "Quellen und Annahmen nachvollziehbar speichern."
                        ),
                        group="data",
                        key="record_provenance",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "data",
                            "storage",
                            "provenance",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="data.retention",
                title="Aufbewahrung",
                description=(
                    "Standardwerte für Aufbewahrung und Archivierung. "
                    "Gesetzliche Sperrfristen bleiben vorrangig."
                ),
                order=30,
                availability=available,
                fields=(
                    _config_field(
                        "data.retention_days",
                        "Standard-Aufbewahrung",
                        description=("Standard-Aufbewahrungsdauer in Tagen."),
                        group="data",
                        key="default_retention_days",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=36_500,
                        requires_confirmation=True,
                        order=10,
                        tags=(
                            "data",
                            "retention",
                            "high-impact",
                        ),
                    ),
                    _config_field(
                        "data.archive_before_delete",
                        "Vor Löschung archivieren",
                        description=(
                            "Daten vor einer zulässigen Löschung in einen "
                            "Archivstatus überführen."
                        ),
                        group="data",
                        key="archive_before_delete",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=20,
                        tags=(
                            "data",
                            "retention",
                            "archive",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="data.export",
                title="Export",
                description=(
                    "Standardformate für erzeugte und exportierte Ergebnisse."
                ),
                order=40,
                availability=available,
                fields=(
                    _config_field(
                        "data.default_export_format",
                        "Standard-Exportformat",
                        description=("Bevorzugtes Format für allgemeine Exporte."),
                        group="data",
                        key="default_export_format",
                        control=SettingsControl.SELECT,
                        options=EXPORT_FORMAT_OPTIONS,
                        order=10,
                        tags=(
                            "data",
                            "export",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Kommunikation und Kanäle
# ============================================================


def _build_communication_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    prepared = SettingsAvailability.PREPARED
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="communication",
        title="Kommunikation und Kanäle",
        description=(
            "Chat, E-Mail, Kalender, Kontakte, Benachrichtigungen "
            "und zukünftige Connectoren."
        ),
        icon="messages-square",
        order=80,
        availability=prepared,
        sections=(
            SettingsSectionDescriptor(
                id="communication.behavior",
                title="Interaktionsverhalten",
                description=(
                    "Steuert proaktive Informationen, Rückfragen und "
                    "Abschlussmeldungen."
                ),
                order=10,
                availability=available,
                fields=(
                    _config_field(
                        "communication.proactive",
                        "Proaktiv informieren",
                        description=(
                            "Bei wichtigen Ereignissen und relevanten "
                            "Abweichungen aktiv informieren."
                        ),
                        group="communication",
                        key="proactive_notifications",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "communication",
                            "behavior",
                            "proactive",
                        ),
                    ),
                    _config_field(
                        "communication.progress_updates",
                        "Fortschritt melden",
                        description=(
                            "Bei längeren Aufgaben sichere Zwischenstände anzeigen."
                        ),
                        group="communication",
                        key="progress_updates",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "communication",
                            "behavior",
                            "progress",
                        ),
                    ),
                    _config_field(
                        "communication.completion_notice",
                        "Abschluss melden",
                        description=(
                            "Nach Abschluss einer Aufgabe eine eindeutige "
                            "Abschlussmeldung erzeugen."
                        ),
                        group="communication",
                        key="completion_notifications",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "communication",
                            "behavior",
                            "completion",
                        ),
                    ),
                    _config_field(
                        "communication.error_notice",
                        "Fehler melden",
                        description=(
                            "Fehler, Abbrüche und blockierende Zustände "
                            "sichtbar kommunizieren."
                        ),
                        group="communication",
                        key="error_notifications",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "communication",
                            "behavior",
                            "error",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="communication.chat",
                title="Chat",
                description=("Darstellung und Laufzeitverhalten des Chat-Kanals."),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "communication.chat_streaming",
                        "Streaming aktivieren",
                        description=("Antworten als SSE-Stream übertragen."),
                        group="communication",
                        key="chat_streaming_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "communication",
                            "chat",
                            "streaming",
                        ),
                    ),
                    _config_field(
                        "communication.max_message_length",
                        "Maximale Nachrichtenlänge",
                        description=("Maximale Länge einer Chat-Nachricht."),
                        group="communication",
                        key="max_message_length",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=1_000_000,
                        order=20,
                        tags=(
                            "communication",
                            "chat",
                            "limits",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="communication.channels",
                title="Connectoren",
                description=("Vorbereitete Kommunikations- und Datenkanäle."),
                order=30,
                availability=prepared,
                fields=(
                    _resource_link(
                        "communication.connectors",
                        "Connectoren",
                        description=("Kommunikations- und Datenquellen verwalten."),
                        endpoint="/api/v1/connectors",
                        availability=planned,
                        order=10,
                        tags=(
                            "communication",
                            "connectors",
                        ),
                    ),
                    _resource_link(
                        "communication.email",
                        "E-Mail",
                        description=(
                            "Postfächer, Lesen, Entwürfe und Versandfreigaben."
                        ),
                        endpoint="/api/v1/connectors/email",
                        availability=planned,
                        order=20,
                        tags=(
                            "communication",
                            "email",
                        ),
                    ),
                    _resource_link(
                        "communication.calendar",
                        "Kalender",
                        description=("Kalenderkonten, Termine und Aktionsfreigaben."),
                        endpoint="/api/v1/connectors/calendar",
                        availability=planned,
                        order=30,
                        tags=(
                            "communication",
                            "calendar",
                        ),
                    ),
                    _resource_link(
                        "communication.contacts",
                        "Kontakte",
                        description=("Kontaktquellen und Zugriffsfreigaben."),
                        endpoint="/api/v1/connectors/contacts",
                        availability=planned,
                        order=40,
                        tags=(
                            "communication",
                            "contacts",
                        ),
                    ),
                    _resource_link(
                        "communication.telephony",
                        "Telefonie",
                        description=(
                            "SIP-Konten, Anrufverarbeitung und Transkription."
                        ),
                        endpoint="/api/v1/connectors/telephony",
                        availability=planned,
                        order=50,
                        tags=(
                            "communication",
                            "telephony",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Darstellung und Ausgabe
# ============================================================


def _build_appearance_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="appearance",
        title="Darstellung und Ausgabe",
        description=(
            "Oberfläche, Chatdarstellung, Ergebnisansichten, Bearbeitung und Export."
        ),
        icon="palette",
        order=90,
        availability=available,
        sections=(
            SettingsSectionDescriptor(
                id="appearance.ui",
                title="Oberfläche",
                description=("Lokale und serverseitige Darstellungspräferenzen."),
                order=10,
                availability=available,
                fields=(
                    _local_preference(
                        "appearance.theme",
                        "Theme",
                        description=(
                            "Lokale Benutzerpräferenz für Hell, Dunkel oder System."
                        ),
                        control=SettingsControl.SELECT,
                        options=THEME_OPTIONS,
                        order=10,
                        tags=(
                            "appearance",
                            "theme",
                        ),
                    ),
                    _local_preference(
                        "appearance.density",
                        "Darstellungsdichte",
                        description=(
                            "Lokale Präferenz für kompakte oder großzügige Darstellung."
                        ),
                        control=SettingsControl.SELECT,
                        options=DENSITY_OPTIONS,
                        order=20,
                        tags=(
                            "appearance",
                            "density",
                        ),
                    ),
                    _config_field(
                        "appearance.show_tools",
                        "Tool-Aktivität anzeigen",
                        description=(
                            "Tool-Aufrufe und sichere "
                            "Ergebniszusammenfassungen anzeigen."
                        ),
                        group="appearance",
                        key="show_tool_activity",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "appearance",
                            "tools",
                        ),
                    ),
                    _config_field(
                        "appearance.show_sources",
                        "Quellen anzeigen",
                        description=("Verwendete Quellen in Ergebnissen anzeigen."),
                        group="appearance",
                        key="show_sources",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "appearance",
                            "sources",
                        ),
                    ),
                    _config_field(
                        "appearance.source_display_mode",
                        "Quellendarstellung",
                        description=(
                            "Legt fest, wann Quellen sichtbar dargestellt werden."
                        ),
                        group="appearance",
                        key="source_display_mode",
                        control=SettingsControl.SELECT,
                        options=SOURCE_DISPLAY_OPTIONS,
                        order=50,
                        tags=(
                            "appearance",
                            "sources",
                            "display",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="appearance.results",
                title="Ergebnisdarstellung",
                description=("Standardverhalten für strukturierte Ergebnisse."),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "appearance.auto_select_view",
                        "Ansicht automatisch auswählen",
                        description=(
                            "Je nach Ergebnis eine bekannte generische "
                            "Ansicht wie Text, Tabelle oder Baum auswählen."
                        ),
                        group="appearance",
                        key="automatic_result_view",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=(
                            "appearance",
                            "results",
                            "view",
                        ),
                    ),
                    _config_field(
                        "appearance.show_draft_status",
                        "Entwurfsstatus anzeigen",
                        description=(
                            "Nicht freigegebene Ergebnisse sichtbar als "
                            "Entwurf kennzeichnen."
                        ),
                        group="appearance",
                        key="show_draft_status",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "appearance",
                            "results",
                            "draft",
                        ),
                    ),
                    _config_field(
                        "appearance.show_revision",
                        "Revision anzeigen",
                        description=(
                            "Versions- und Revisionsinformationen bei "
                            "gespeicherten Ergebnissen anzeigen."
                        ),
                        group="appearance",
                        key="show_revision_information",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "appearance",
                            "results",
                            "revision",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="appearance.editor",
                title="Bearbeitung",
                description=(
                    "Vorbereitete generische Bearbeitungs- und Freigabeansichten."
                ),
                order=30,
                availability=planned,
                fields=(
                    _resource_link(
                        "appearance.editors",
                        "Editor-Registry",
                        description=(
                            "Bekannte generische Editoren und Darstellungskomponenten."
                        ),
                        endpoint="/api/v1/ui/editors",
                        availability=planned,
                        order=10,
                        tags=(
                            "appearance",
                            "editors",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Sicherheit und Governance
# ============================================================


def _build_security_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    prepared = SettingsAvailability.PREPARED
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="security",
        title="Sicherheit und Governance",
        description=(
            "Berechtigungen, Datenklassifizierung, Bestätigungen, "
            "Audit und unveränderliche Sicherheitsuntergrenzen."
        ),
        icon="shield-check",
        order=100,
        availability=prepared,
        sections=(
            SettingsSectionDescriptor(
                id="security.profile",
                title="Sicherheitsprofil",
                description=(
                    "Aktiver Betriebsmodus und unveränderliche Sicherheitsuntergrenzen."
                ),
                order=10,
                availability=available,
                fields=(
                    _runtime_field(
                        "security.profile",
                        "Aktives Sicherheitsprofil",
                        description=(
                            "Development, Intranet oder Internet. "
                            "Dieser Wert stammt aus der "
                            "Bootstrap-Konfiguration."
                        ),
                        endpoint="/api/v1/bootstrap",
                        availability=available,
                        order=10,
                        tags=("security", "profile"),
                    ),
                    _runtime_field(
                        "security.authorization",
                        "Serverseitige Autorisierung",
                        description=(
                            "Status der serverseitigen Autorisierungsgrenzen."
                        ),
                        endpoint="/api/v1/bootstrap",
                        availability=available,
                        order=20,
                        tags=("security", "authorization"),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="security.authentication",
                title="Authentifizierung",
                description=(
                    "Konfiguration und Status der Authentifizierungsmechanismen."
                ),
                order=15,
                availability=available,
                fields=(
                    _config_field(
                        "security.authentication.development_fallback",
                        "Entwicklungs-Authentifizierungs-Fallback",
                        description=(
                            "Erlaubt lokale Entwicklungsauthentifizierung als Fallback."
                        ),
                        group="security",
                        key="development_auth_fallback_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=("security", "authentication", "development"),
                    ),
                    _config_field(
                        "security.authentication.development_admin_login_enabled",
                        "Entwickler-Admin-Login aktiv",
                        description=(
                            "Ermöglicht einen passwortlosen Admin-Login in Development-Umgebungen."
                        ),
                        group="security",
                        key="development_admin_login_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=("security", "authentication", "development"),
                    ),
                    _config_field(
                        "security.authentication.self_registration_enabled",
                        "Selbstregistrierung aktiv",
                        description=(
                            "Erlaubt Benutzern, sich selbst zu registrieren."
                        ),
                        group="security",
                        key="self_registration_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=("security", "authentication", "registration"),
                    ),
                    _config_field(
                        "security.authentication.development_self_registration_enabled",
                        "Selbstregistrierung in Development erlauben",
                        description=(
                            "Erlaubt Selbstregistrierung nur in Entwicklungsumgebungen."
                        ),
                        group="security",
                        key="development_self_registration_enabled",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=("security", "authentication", "development"),
                    ),
                    _config_field(
                        "security.authentication.registration_requires_invitation",
                        "Registrierung erfordert Einladung",
                        description=(
                            "Erfordert eine Einladung für die Benutzerregistrierung."
                        ),
                        group="security",
                        key="registration_requires_invitation",
                        control=SettingsControl.BOOLEAN,
                        order=50,
                        tags=("security", "authentication", "registration"),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="security.data",
                title="Datenklassifizierung",
                description=("Standardklassifizierung und Schutz sensibler Inhalte."),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "security.default_classification",
                        "Standard-Datenklassifizierung",
                        description=("Standardklassifizierung neuer Inhalte."),
                        group="security",
                        key="default_data_classification",
                        control=SettingsControl.SELECT,
                        options=DATA_CLASSIFICATION_OPTIONS,
                        requires_confirmation=True,
                        order=10,
                        tags=("security", "classification", "high-impact"),
                    ),
                    _config_field(
                        "security.block_secret_output",
                        "Secret-Ausgabe blockieren",
                        description=(
                            "Verhindert die Ausgabe bekannter Secrets "
                            "über normale Ergebnis- und Chatkanäle."
                        ),
                        group="security",
                        key="block_secret_output",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=20,
                        tags=("security", "secrets"),
                    ),
                    _config_field(
                        "security.mask_sensitive_logs",
                        "Sensible Logdaten maskieren",
                        description=(
                            "Bekannte sensible Werte in Protokollen maskieren."
                        ),
                        group="security",
                        key="mask_sensitive_logs",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=30,
                        tags=("security", "logging", "sensitive"),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="security.threats",
                title="Bedrohungserkennung",
                description=(
                    "Kontrollierte Erkennung und Reaktion auf "
                    "verdächtige Eingaben und Tool-Ketten."
                ),
                order=30,
                availability=prepared,
                fields=(
                    _config_field(
                        "security.prompt_injection_detection",
                        "Prompt-Injection-Prüfung",
                        description=(
                            "Externe Inhalte auf manipulative Anweisungen prüfen."
                        ),
                        group="security",
                        key="prompt_injection_detection",
                        control=SettingsControl.BOOLEAN,
                        order=10,
                        tags=("security", "threats", "prompt-injection"),
                    ),
                    _config_field(
                        "security.tool_manipulation_detection",
                        "Tool-Manipulation prüfen",
                        description=(
                            "Tool-Eingaben und Tool-Ergebnisse auf "
                            "Manipulationsversuche prüfen."
                        ),
                        group="security",
                        key="tool_manipulation_detection",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=("security", "threats", "tools"),
                    ),
                    _config_field(
                        "security.exfiltration_detection",
                        "Datenexfiltration prüfen",
                        description=(
                            "Verdächtige Massenexporte und unerlaubte "
                            "Datenübertragungen erkennen."
                        ),
                        group="security",
                        key="data_exfiltration_detection",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=("security", "threats", "exfiltration"),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="security.audit",
                title="Audit und Governance",
                description=(
                    "Status und vorbereitete Ressourcen für "
                    "nachvollziehbare Änderungen."
                ),
                order=40,
                availability=prepared,
                fields=(
                    _runtime_field(
                        "security.audit_status",
                        "Auditstatus",
                        description="Status des Audit-Subsystems.",
                        endpoint="/api/v1/diagnostics/audit",
                        availability=planned,
                        order=10,
                        tags=("security", "audit"),
                    ),
                    _resource_link(
                        "security.audit_entries",
                        "Audit-Einträge",
                        description=(
                            "Nachvollziehbare Konfigurations-, Tool- und "
                            "Ressourcenänderungen."
                        ),
                        endpoint="/api/v1/audit",
                        availability=planned,
                        order=20,
                        tags=("security", "audit", "resource"),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Diagnose und Qualität
# ============================================================


def _build_diagnostics_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="diagnostics",
        title="Diagnose und Qualität",
        description=(
            "Systemstatus, Laufzeitmessungen, Fehleranalyse, "
            "Qualitätsbewertungen und Optimierungsvorschläge."
        ),
        icon="activity",
        order=110,
        availability=SettingsAvailability.PREPARED,
        sections=(
            SettingsSectionDescriptor(
                id="diagnostics.current",
                title="Aktueller Zustand",
                description=("Vorhandene Laufzeit- und Registry-Endpunkte."),
                order=10,
                availability=available,
                fields=(
                    _runtime_field(
                        "diagnostics.health",
                        "Systemzustand",
                        description=(
                            "Aktueller Health-Status der verfügbaren Dienste."
                        ),
                        endpoint="/api/v1/health",
                        availability=available,
                        order=10,
                        tags=(
                            "diagnostics",
                            "health",
                        ),
                    ),
                    _runtime_field(
                        "diagnostics.models",
                        "Modellstatus",
                        description=("Verfügbarkeit der registrierten Modelle."),
                        endpoint="/api/v1/models?include_disabled=true",
                        availability=available,
                        order=20,
                        tags=(
                            "diagnostics",
                            "models",
                        ),
                    ),
                    _runtime_field(
                        "diagnostics.tools",
                        "Toolstatus",
                        description=("Verfügbarkeit der registrierten Tools."),
                        endpoint=(
                            "/api/v1/tools"
                            "?include_disabled=true"
                            "&include_unavailable=true"
                        ),
                        availability=available,
                        order=30,
                        tags=(
                            "diagnostics",
                            "tools",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="diagnostics.metrics",
                title="Messwerte",
                description=("Vorbereitete Laufzeit-, Kosten- und Qualitätsmetriken."),
                order=20,
                availability=planned,
                fields=(
                    _runtime_field(
                        "diagnostics.runtime_metrics",
                        "Laufzeitmetriken",
                        description=(
                            "Antwortzeiten, Planungsdauer, Tool-Laufzeiten "
                            "und Fehlerquoten."
                        ),
                        endpoint="/api/v1/diagnostics/runtime",
                        availability=planned,
                        order=10,
                        tags=(
                            "diagnostics",
                            "metrics",
                            "runtime",
                        ),
                    ),
                    _runtime_field(
                        "diagnostics.cost_metrics",
                        "Kostenmetriken",
                        description=("Tokenverbrauch und Providerkosten je Aufgabe."),
                        endpoint="/api/v1/diagnostics/costs",
                        availability=planned,
                        order=20,
                        tags=(
                            "diagnostics",
                            "metrics",
                            "cost",
                        ),
                    ),
                    _resource_link(
                        "diagnostics.evaluations",
                        "Qualitätsbewertungen",
                        description=("Aufgabenbezogene Tests und Qualitätsmetriken."),
                        endpoint="/api/v1/evaluations",
                        availability=planned,
                        order=30,
                        tags=(
                            "diagnostics",
                            "evaluations",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Lernen und Optimierung
# ============================================================


def _build_learning_group() -> SettingsGroupDescriptor:
    available = SettingsAvailability.AVAILABLE
    planned = SettingsAvailability.PLANNED

    return SettingsGroupDescriptor(
        id="learning",
        title="Lernen und Optimierung",
        description=(
            "Erfahrungen, Lernkandidaten, Bewertung und kontrollierte "
            "Freigabe von Verbesserungen."
        ),
        icon="sparkles",
        order=120,
        availability=SettingsAvailability.PREPARED,
        sections=(
            SettingsSectionDescriptor(
                id="learning.behavior",
                title="Lernverhalten",
                description=(
                    "Steuert, ob und wie Erfahrungen als Lernkandidaten erfasst werden."
                ),
                order=10,
                availability=available,
                fields=(
                    _config_field(
                        "learning.mode",
                        "Lernmodus",
                        description=(
                            "Legt fest, ob Erfahrungen nicht, passiv oder "
                            "als Lernkandidaten erfasst werden."
                        ),
                        group="learning",
                        key="mode",
                        control=SettingsControl.SELECT,
                        options=LEARNING_MODE_OPTIONS,
                        order=10,
                        tags=(
                            "learning",
                            "mode",
                        ),
                    ),
                    _config_field(
                        "learning.record_successes",
                        "Erfolgreiche Aufgaben erfassen",
                        description=(
                            "Erfolgreiche Aufgaben für spätere "
                            "Mustererkennung protokollieren."
                        ),
                        group="learning",
                        key="record_successful_tasks",
                        control=SettingsControl.BOOLEAN,
                        order=20,
                        tags=(
                            "learning",
                            "experience",
                            "success",
                        ),
                    ),
                    _config_field(
                        "learning.record_failures",
                        "Fehlgeschlagene Aufgaben erfassen",
                        description=(
                            "Fehler und Abbrüche für spätere "
                            "Ursachenanalyse protokollieren."
                        ),
                        group="learning",
                        key="record_failed_tasks",
                        control=SettingsControl.BOOLEAN,
                        order=30,
                        tags=(
                            "learning",
                            "experience",
                            "failure",
                        ),
                    ),
                    _config_field(
                        "learning.record_corrections",
                        "Nutzerkorrekturen erfassen",
                        description=(
                            "Nachträgliche Korrekturen als Signal für "
                            "Lernkandidaten erfassen."
                        ),
                        group="learning",
                        key="record_user_corrections",
                        control=SettingsControl.BOOLEAN,
                        order=40,
                        tags=(
                            "learning",
                            "experience",
                            "correction",
                        ),
                    ),
                    _config_field(
                        "learning.auto_apply",
                        "Produktive Änderungen automatisch anwenden",
                        description=(
                            "Soll aus Sicherheitsgründen deaktiviert bleiben: "
                            "produktive Änderungen benötigen Freigabe."
                        ),
                        group="learning",
                        key="auto_apply_productive_changes",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=50,
                        tags=(
                            "learning",
                            "approval",
                            "high-impact",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="learning.thresholds",
                title="Bewertung",
                description=(
                    "Mindestanforderungen für Lern- und Optimierungskandidaten."
                ),
                order=20,
                availability=available,
                fields=(
                    _config_field(
                        "learning.min_observations",
                        "Mindestanzahl Beobachtungen",
                        description=(
                            "Mindestzahl ähnlicher Beobachtungen vor "
                            "Erzeugung eines Kandidaten."
                        ),
                        group="learning",
                        key="minimum_observations",
                        control=SettingsControl.NUMBER,
                        minimum=1,
                        maximum=10_000,
                        order=10,
                        tags=(
                            "learning",
                            "evaluation",
                            "threshold",
                        ),
                    ),
                    _config_field(
                        "learning.min_confidence",
                        "Mindestvertrauen",
                        description=(
                            "Mindestvertrauensgrad für einen Optimierungsvorschlag."
                        ),
                        group="learning",
                        key="minimum_confidence",
                        control=SettingsControl.NUMBER,
                        minimum=0,
                        maximum=1,
                        order=20,
                        tags=(
                            "learning",
                            "evaluation",
                            "confidence",
                        ),
                    ),
                    _config_field(
                        "learning.require_manual_approval",
                        "Manuelle Freigabe verlangen",
                        description=(
                            "Produktive Lern- und Optimierungsänderungen "
                            "müssen manuell freigegeben werden."
                        ),
                        group="learning",
                        key="require_manual_approval",
                        control=SettingsControl.BOOLEAN,
                        requires_confirmation=True,
                        order=30,
                        tags=(
                            "learning",
                            "approval",
                        ),
                    ),
                ),
            ),
            SettingsSectionDescriptor(
                id="learning.resources",
                title="Kandidaten und Auswertung",
                description=(
                    "Vorbereitete Ressourcen für Erfahrungen und "
                    "versionierte Optimierungsvorschläge."
                ),
                order=30,
                availability=planned,
                fields=(
                    _resource_link(
                        "learning.experiences",
                        "Erfahrungen",
                        description=(
                            "Protokollierte erfolgreiche, fehlgeschlagene "
                            "und korrigierte Aufgaben."
                        ),
                        endpoint="/api/v1/learning/experiences",
                        availability=planned,
                        order=10,
                        tags=(
                            "learning",
                            "experiences",
                        ),
                    ),
                    _resource_link(
                        "learning.candidates",
                        "Optimierungsvorschläge",
                        description=(
                            "Versionierte Vorschläge für Prompts, Routing, "
                            "Wissen und Arbeitsregeln."
                        ),
                        endpoint="/api/v1/learning/candidates",
                        availability=planned,
                        order=20,
                        tags=(
                            "learning",
                            "candidates",
                        ),
                    ),
                ),
            ),
        ),
    )


# ============================================================
# Öffentlicher Katalog
# ============================================================


@lru_cache(maxsize=1)
def build_settings_catalog() -> SettingsCatalogResponse:
    """
    Erzeugt den versionierten Settings-Katalog.

    Der Katalog ist eine Navigations- und Metadatenstruktur.

    Er enthält keine Secrets, keine produktiven Zugangsdaten und keine
    dynamisch ausführbaren Importpfade.

    Wichtig:

    - Ein Eintrag mit ``availability=available`` bedeutet, dass der
      beschriebene Vertrag oder Konfigurationswert vorgesehen ist.
    - Ein sichtbarer Eintrag ersetzt keine serverseitige Berechtigung.
    - Ressourcenlinks dürfen auf noch nicht implementierte Endpunkte
      verweisen, müssen dann jedoch als ``prepared`` oder ``planned``
      gekennzeichnet sein.
    - Produktive Änderungen erfolgen ausschließlich über die jeweiligen
      versionierten API-Verträge und den ConfigService.
    """

    groups = (
        _build_identity_group(),
        _build_prompts_group(),
        _build_models_group(),
        _build_tools_group(),
        _build_knowledge_group(),
        _build_planning_group(),
        _build_data_group(),
        _build_communication_group(),
        _build_appearance_group(),
        _build_security_group(),
        _build_diagnostics_group(),
        _build_learning_group(),
    )

    ordered_groups = tuple(
        sorted(
            groups,
            key=lambda group: group.order,
        ),
    )

    return SettingsCatalogResponse(
        groups=ordered_groups,
    )
