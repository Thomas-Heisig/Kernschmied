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
    options: tuple[SettingsOption, ...] = (),
    minimum: float | None = None,
    maximum: float | None = None,
    order: int = 0,
) -> SettingsFieldDescriptor:
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
        options=options,
        minimum=minimum,
        maximum=maximum,
        order=order,
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
    requires_confirmation: bool = False,
) -> SettingsFieldDescriptor:
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
        requires_confirmation=requires_confirmation,
        options=options,
        minimum=minimum,
        maximum=maximum,
        order=order,
    )


def _resource_link(
    field_id: str,
    title: str,
    *,
    description: str,
    endpoint: str,
    availability: SettingsAvailability,
    order: int,
) -> SettingsFieldDescriptor:
    return _field(
        field_id,
        title,
        description=description,
        source=SettingsSource.RESOURCE,
        availability=availability,
        control=SettingsControl.LINK,
        endpoint=endpoint,
        order=order,
    )


def _runtime_field(
    field_id: str,
    title: str,
    *,
    description: str,
    endpoint: str,
    availability: SettingsAvailability,
    order: int,
) -> SettingsFieldDescriptor:
    return _field(
        field_id,
        title,
        description=description,
        source=SettingsSource.RUNTIME,
        availability=availability,
        control=SettingsControl.READONLY,
        endpoint=endpoint,
        order=order,
    )


@lru_cache(maxsize=1)
def build_settings_catalog() -> SettingsCatalogResponse:
    available = SettingsAvailability.AVAILABLE
    prepared = SettingsAvailability.PREPARED
    planned = SettingsAvailability.PLANNED

    groups = (
        SettingsGroupDescriptor(
            id="identity",
            title="Identität und Verhalten",
            description="Grundauftrag, Kommunikationsverhalten, Autonomie und Selbstprüfung.",
            icon="bot",
            order=10,
            availability=available,
            sections=(
                SettingsSectionDescriptor(
                    id="identity.core",
                    title="Identität",
                    order=10,
                    availability=available,
                    fields=(
                        _config_field("identity.name", "Name", description="Anzeigename der KI.", group="identity", key="name", control=SettingsControl.TEXT, order=10),
                        _config_field("identity.role", "Rollenbeschreibung", description="Allgemeine Rolle der KI-Arbeitskraft.", group="identity", key="role_description", control=SettingsControl.TEXTAREA, order=20),
                        _config_field("identity.mission", "Grundauftrag", description="Übergreifender Arbeitsauftrag von Kernschmied.", group="identity", key="mission", control=SettingsControl.TEXTAREA, order=30),
                        _config_field("identity.language", "Standardsprache", description="Bevorzugte Arbeitssprache.", group="identity", key="default_language", control=SettingsControl.SELECT, options=(SettingsOption(value="de", label="Deutsch"), SettingsOption(value="en", label="Englisch")), order=40),
                        _config_field("identity.timezone", "Zeitzone", description="Zeitzone für Datums- und Fristberechnungen.", group="identity", key="timezone", control=SettingsControl.TEXT, order=50),
                    ),
                ),
                SettingsSectionDescriptor(
                    id="identity.autonomy",
                    title="Autonomie",
                    order=20,
                    availability=available,
                    fields=(
                        _config_field("identity.autonomy_level", "Autonomiegrad", description="Legt fest, ob Kernschmied berät, Entwürfe erzeugt oder freigegebene Aktionen ausführt.", group="identity", key="autonomy_level", control=SettingsControl.SELECT, options=(SettingsOption(value="advisory", label="Nur beraten"), SettingsOption(value="draft", label="Entwürfe erstellen"), SettingsOption(value="prepare", label="Änderungen vorbereiten"), SettingsOption(value="execute_allowed", label="Freigegebene Aktionen ausführen")), order=10, requires_confirmation=True),
                        _config_field("identity.mark_uncertainty", "Unsicherheiten kennzeichnen", description="Unsichere Aussagen sichtbar markieren.", group="identity", key="mark_uncertainty", control=SettingsControl.BOOLEAN, order=20),
                        _config_field("identity.self_check", "Selbstprüfung aktivieren", description="Ergebnisse vor Abschluss auf Vollständigkeit und Plausibilität prüfen.", group="identity", key="self_check_enabled", control=SettingsControl.BOOLEAN, order=30),
                    ),
                ),
            ),
        ),
        SettingsGroupDescriptor(
            id="prompts",
            title="Prompts und Arbeitsanweisungen",
            description="Versionierte System-, Aufgaben- und Kontextprompts.",
            icon="message-square-code",
            order=20,
            availability=prepared,
            sections=(
                SettingsSectionDescriptor(id="prompts.resources", title="Prompt-Ressourcen", order=10, availability=prepared, fields=(
                    _resource_link("prompts.manage", "Prompts verwalten", description="Versionierte Prompts, Gültigkeitsbereiche und Revisionen.", endpoint="/api/v1/prompts", availability=prepared, order=10),
                    _config_field("prompts.inheritance", "Prompt-Vererbung", description="Prompt-Vererbung über Hierarchieebenen aktivieren.", group="prompts", key="inheritance_enabled", control=SettingsControl.BOOLEAN, order=20),
                    _config_field("prompts.max_length", "Maximale Prompt-Länge", description="Obergrenze für zusammengesetzte Prompts.", group="prompts", key="max_composed_length", control=SettingsControl.NUMBER, minimum=1000, maximum=500000, order=30),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="models",
            title="Modelle und Provider",
            description="Provider, Modellregistrierung, Routing und Generierungswerte.",
            icon="cpu",
            order=30,
            availability=available,
            sections=(
                SettingsSectionDescriptor(id="models.registry", title="Registries", order=10, availability=available, fields=(
                    _resource_link("models.list", "Modelle", description="Registrierte und freigegebene Modelle.", endpoint="/api/v1/models?include_disabled=true", availability=available, order=10),
                    _resource_link("providers.manage", "Provider", description="Providerverwaltung und Secret-Referenzen.", endpoint="/api/v1/providers", availability=prepared, order=20),
                    _config_field("models.default", "Standardmodell", description="Modell für Aufgaben ohne explizites Routing.", group="models", key="default_model_id", control=SettingsControl.TEXT, order=30),
                    _config_field("models.fallback", "Fallback-Modell", description="Ersatzmodell bei Nichtverfügbarkeit.", group="models", key="fallback_model_id", control=SettingsControl.TEXT, order=40),
                )),
                SettingsSectionDescriptor(id="models.generation", title="Generierung", order=20, availability=available, fields=(
                    _config_field("models.temperature", "Temperature", description="Standardwert für die Antwortvarianz.", group="models", key="temperature", control=SettingsControl.NUMBER, minimum=0, maximum=2, order=10),
                    _config_field("models.top_p", "Top P", description="Nucleus-Sampling-Grenze.", group="models", key="top_p", control=SettingsControl.NUMBER, minimum=0, maximum=1, order=20),
                    _config_field("models.max_output_tokens", "Maximale Ausgabetokens", description="Standardlimit für Modellantworten.", group="models", key="max_output_tokens", control=SettingsControl.NUMBER, minimum=1, maximum=200000, order=30),
                )),
                SettingsSectionDescriptor(id="models.health", title="Status und Routing", order=30, availability=prepared, fields=(
                    _runtime_field("models.health", "Provider- und Modellstatus", description="Health, Latenz und Fehlerraten.", endpoint="/api/v1/diagnostics/models", availability=prepared, order=10),
                    _resource_link("models.routing", "Routing-Regeln", description="Dynamisches Routing nach Aufgabe, Fähigkeit, Kosten und Verfügbarkeit.", endpoint="/api/v1/model-routing", availability=planned, order=20),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="tools",
            title="Tools und Fähigkeiten",
            description="Tool-Registry, Ausführung, Freigaben und Simulation.",
            icon="wrench",
            order=40,
            availability=available,
            sections=(
                SettingsSectionDescriptor(id="tools.registry", title="Registry", order=10, availability=available, fields=(
                    _resource_link("tools.list", "Tools", description="Entdeckte, registrierte und verfügbare Tools.", endpoint="/api/v1/tools?include_disabled=true&include_unavailable=true", availability=available, order=10),
                    _config_field("tools.auto_select", "Automatische Tool-Auswahl", description="Das Modell darf geeignete freigegebene Tools selbst auswählen.", group="tools", key="automatic_selection", control=SettingsControl.BOOLEAN, order=20),
                    _config_field("tools.max_rounds", "Maximale Tool-Runden", description="Obergrenze je Aufgabe.", group="tools", key="max_rounds", control=SettingsControl.NUMBER, minimum=0, maximum=100, order=30),
                    _config_field("tools.timeout", "Standard-Timeout", description="Maximale Standardlaufzeit eines Tool-Aufrufs in Sekunden.", group="tools", key="default_timeout_seconds", control=SettingsControl.NUMBER, minimum=1, maximum=3600, order=40),
                )),
                SettingsSectionDescriptor(id="tools.confirmation", title="Bestätigungen", order=20, availability=available, fields=(
                    _config_field("tools.confirm_write", "Schreibaktionen bestätigen", description="Schreibende Aktionen erfordern eine Bestätigung.", group="tools", key="confirm_write_actions", control=SettingsControl.BOOLEAN, order=10, requires_confirmation=True),
                    _config_field("tools.confirm_delete", "Löschaktionen bestätigen", description="Löschende Aktionen erfordern immer eine Bestätigung.", group="tools", key="confirm_delete_actions", control=SettingsControl.BOOLEAN, order=20, requires_confirmation=True),
                    _config_field("tools.confirm_external", "Externe Kommunikation bestätigen", description="Versand, Veröffentlichung und externe Kommunikation bestätigen.", group="tools", key="confirm_external_communication", control=SettingsControl.BOOLEAN, order=30, requires_confirmation=True),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="knowledge",
            title="Wissen, Gedächtnis und Kontext",
            description="Kontextquellen, Gedächtnis, Wissenskandidaten und Pflege.",
            icon="brain",
            order=50,
            availability=prepared,
            sections=(
                SettingsSectionDescriptor(id="knowledge.context", title="Kontextauswahl", order=10, availability=available, fields=(
                    _config_field("knowledge.auto_context", "Automatische Kontextauswahl", description="Relevante freigegebene Quellen automatisch auswählen.", group="knowledge", key="automatic_context_selection", control=SettingsControl.BOOLEAN, order=10),
                    _config_field("knowledge.max_sources", "Maximale Quellenzahl", description="Maximale Zahl kombinierter Kontextquellen.", group="knowledge", key="max_context_sources", control=SettingsControl.NUMBER, minimum=1, maximum=100, order=20),
                    _config_field("knowledge.relevance", "Relevanzschwelle", description="Mindestwert für die Aufnahme einer Quelle.", group="knowledge", key="relevance_threshold", control=SettingsControl.NUMBER, minimum=0, maximum=1, order=30),
                )),
                SettingsSectionDescriptor(id="knowledge.resources", title="Wissen und Kandidaten", order=20, availability=prepared, fields=(
                    _resource_link("knowledge.entries", "Wissenseinträge", description="Versionierte Wissenseinträge mit Herkunft und Vertrauensgrad.", endpoint="/api/v1/knowledge", availability=prepared, order=10),
                    _resource_link("knowledge.candidates", "Wissenskandidaten", description="Aus Interaktionen erkannte, noch nicht freigegebene Fakten.", endpoint="/api/v1/knowledge/candidates", availability=planned, order=20),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="planning",
            title="Planung und Arbeitsweise",
            description="Aufgabenerkennung, Planung, Ausführung und Qualitätssicherung.",
            icon="workflow",
            order=60,
            availability=prepared,
            sections=(
                SettingsSectionDescriptor(id="planning.execution", title="Planung und Ausführung", order=10, availability=available, fields=(
                    _config_field("planning.enabled", "Planung aktivieren", description="Vor komplexen Aufgaben einen expliziten Arbeitsplan erzeugen.", group="planning", key="enabled", control=SettingsControl.BOOLEAN, order=10),
                    _config_field("planning.max_steps", "Maximale Schritte", description="Obergrenze der Ausführungsschritte.", group="planning", key="max_steps", control=SettingsControl.NUMBER, minimum=1, maximum=500, order=20),
                    _config_field("planning.max_duration", "Maximale Dauer", description="Maximale Laufzeit einer Aufgabe in Sekunden.", group="planning", key="max_duration_seconds", control=SettingsControl.NUMBER, minimum=1, maximum=86400, order=30),
                    _config_field("planning.show_progress", "Zwischenstände anzeigen", description="Sichere Fortschrittszusammenfassungen im Frontend anzeigen.", group="planning", key="show_progress", control=SettingsControl.BOOLEAN, order=40),
                )),
                SettingsSectionDescriptor(id="planning.workflows", title="Arbeitsdefinitionen", order=20, availability=prepared, fields=(
                    _resource_link("planning.workflows", "Workflows", description="Versionierte, dynamische Plan- und Ausführungsdefinitionen.", endpoint="/api/v1/workflows", availability=planned, order=10),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="data",
            title="Daten und Speicherung",
            description="Artifacts, Schemas, Versionierung und Aufbewahrung.",
            icon="database",
            order=70,
            availability=prepared,
            sections=(
                SettingsSectionDescriptor(id="data.artifacts", title="Artifacts", order=10, availability=prepared, fields=(
                    _resource_link("artifacts.list", "Arbeitsergebnisse", description="Angebote, Bilanzen, Briefe und weitere strukturierte Ergebnisse.", endpoint="/api/v1/artifacts", availability=planned, order=10),
                    _resource_link("artifacts.schemas", "Artifact-Schemas", description="Versionierte Ausgabeschemas und Renderer.", endpoint="/api/v1/artifact-schemas", availability=planned, order=20),
                    _config_field("artifacts.default_status", "Standardstatus", description="Status neuer Arbeitsergebnisse.", group="artifacts", key="default_status", control=SettingsControl.SELECT, options=(SettingsOption(value="draft", label="Entwurf"), SettingsOption(value="review", label="In Prüfung")), order=30),
                )),
                SettingsSectionDescriptor(id="data.retention", title="Aufbewahrung", order=20, availability=available, fields=(
                    _config_field("data.retention_days", "Standard-Aufbewahrung", description="Standard-Aufbewahrungsdauer in Tagen; rechtliche Sperrfristen bleiben vorrangig.", group="data", key="default_retention_days", control=SettingsControl.NUMBER, minimum=1, maximum=36500, order=10, requires_confirmation=True),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="communication",
            title="Kommunikation und Kanäle",
            description="Chat, E-Mail, Kalender, Kontakte und weitere Connectoren.",
            icon="messages-square",
            order=80,
            availability=prepared,
            sections=(
                SettingsSectionDescriptor(id="communication.channels", title="Kanäle", order=10, availability=prepared, fields=(
                    _config_field("communication.proactive", "Proaktiv informieren", description="Bei wichtigen Ereignissen aktiv informieren.", group="communication", key="proactive_notifications", control=SettingsControl.BOOLEAN, order=10),
                    _resource_link("communication.connectors", "Connectoren", description="Kommunikations- und Datenquellen verwalten.", endpoint="/api/v1/connectors", availability=planned, order=20),
                    _resource_link("communication.email", "E-Mail", description="Postfächer, Lesen, Entwürfe und Versandfreigaben.", endpoint="/api/v1/connectors/email", availability=planned, order=30),
                    _resource_link("communication.calendar", "Kalender", description="Kalenderkonten und Aktionsfreigaben.", endpoint="/api/v1/connectors/calendar", availability=planned, order=40),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="appearance",
            title="Darstellung und Ausgabe",
            description="Oberfläche, Ergebnisansichten, Bearbeitung und Export.",
            icon="palette",
            order=90,
            availability=available,
            sections=(
                SettingsSectionDescriptor(id="appearance.ui", title="Oberfläche", order=10, availability=available, fields=(
                    _field("appearance.theme", "Theme", description="Lokale Benutzerpräferenz für Hell, Dunkel oder System.", source=SettingsSource.LOCAL_PREFERENCE, availability=available, control=SettingsControl.SELECT, editable=True, options=(SettingsOption(value="system", label="System"), SettingsOption(value="light", label="Hell"), SettingsOption(value="dark", label="Dunkel")), order=10),
                    _field("appearance.density", "Darstellungsdichte", description="Lokale Präferenz für kompakte oder komfortable Darstellung.", source=SettingsSource.LOCAL_PREFERENCE, availability=available, control=SettingsControl.SELECT, editable=True, options=(SettingsOption(value="compact", label="Kompakt"), SettingsOption(value="comfortable", label="Komfortabel")), order=20),
                    _config_field("appearance.show_tools", "Tool-Aktivität anzeigen", description="Tool-Aufrufe und sichere Ergebniszusammenfassungen anzeigen.", group="appearance", key="show_tool_activity", control=SettingsControl.BOOLEAN, order=30),
                    _config_field("appearance.show_sources", "Quellen anzeigen", description="Verwendete Quellen in Ergebnissen anzeigen.", group="appearance", key="show_sources", control=SettingsControl.BOOLEAN, order=40),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="security",
            title="Sicherheit und Governance",
            description="Berechtigungen, Klassifizierung, Audit und unveränderliche Untergrenzen.",
            icon="shield-check",
            order=100,
            availability=prepared,
            sections=(
                SettingsSectionDescriptor(id="security.policy", title="Sicherheitsrichtlinien", order=10, availability=available, fields=(
                    _runtime_field("security.profile", "Aktives Sicherheitsprofil", description="Development, Intranet oder Internet; Bootstrap-/Infrastrukturwert.", endpoint="/api/v1/bootstrap", availability=available, order=10),
                    _config_field("security.default_classification", "Standard-Datenklassifizierung", description="Standardklassifizierung neuer Inhalte.", group="security", key="default_data_classification", control=SettingsControl.SELECT, options=(SettingsOption(value="public", label="Öffentlich"), SettingsOption(value="internal", label="Intern"), SettingsOption(value="confidential", label="Vertraulich"), SettingsOption(value="highly_confidential", label="Besonders vertraulich")), order=20, requires_confirmation=True),
                    _runtime_field("security.audit", "Auditstatus", description="Status des Audit-Subsystems.", endpoint="/api/v1/diagnostics/audit", availability=planned, order=30),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="diagnostics",
            title="Diagnose und Qualität",
            description="Status, Laufzeitmessungen, Fehler und Qualitätsbewertungen.",
            icon="activity",
            order=110,
            availability=prepared,
            sections=(
                SettingsSectionDescriptor(id="diagnostics.current", title="Aktueller Zustand", order=10, availability=available, fields=(
                    _runtime_field("diagnostics.health", "Systemzustand", description="Aktueller Health-Status der Dienste.", endpoint="/api/v1/health", availability=available, order=10),
                    _runtime_field("diagnostics.models", "Modellstatus", description="Verfügbarkeit der registrierten Modelle.", endpoint="/api/v1/models?include_unavailable=true", availability=available, order=20),
                    _runtime_field("diagnostics.tools", "Toolstatus", description="Verfügbarkeit der registrierten Tools.", endpoint="/api/v1/tools?include_unavailable=true", availability=available, order=30),
                    _resource_link("diagnostics.evaluations", "Qualitätsbewertungen", description="Aufgabenbezogene Tests und Qualitätsmetriken.", endpoint="/api/v1/evaluations", availability=planned, order=40),
                )),
            ),
        ),
        SettingsGroupDescriptor(
            id="learning",
            title="Lernen und Optimierung",
            description="Erfahrungen, Lernkandidaten, Bewertung und kontrollierte Freigabe.",
            icon="sparkles",
            order=120,
            availability=prepared,
            sections=(
                SettingsSectionDescriptor(id="learning.behavior", title="Lernverhalten", order=10, availability=available, fields=(
                    _config_field("learning.mode", "Lernmodus", description="Legt fest, ob Erfahrungen nicht, passiv oder aktiv als Kandidaten erfasst werden.", group="learning", key="mode", control=SettingsControl.SELECT, options=(SettingsOption(value="off", label="Aus"), SettingsOption(value="passive", label="Passiv protokollieren"), SettingsOption(value="candidate", label="Lernkandidaten erzeugen")), order=10),
                    _config_field("learning.auto_apply", "Produktive Änderungen automatisch anwenden", description="Bleibt aus: produktive Änderungen benötigen Freigabe.", group="learning", key="auto_apply_productive_changes", control=SettingsControl.BOOLEAN, order=20, requires_confirmation=True),
                )),
                SettingsSectionDescriptor(id="learning.resources", title="Kandidaten und Auswertung", order=20, availability=prepared, fields=(
                    _resource_link("learning.experiences", "Erfahrungen", description="Protokollierte erfolgreiche, fehlgeschlagene und korrigierte Aufgaben.", endpoint="/api/v1/learning/experiences", availability=planned, order=10),
                    _resource_link("learning.candidates", "Optimierungsvorschläge", description="Versionierte Vorschläge für Prompts, Routing, Wissen und Arbeitsregeln.", endpoint="/api/v1/learning/candidates", availability=planned, order=20),
                )),
            ),
        ),
    )

    return SettingsCatalogResponse(groups=groups)
