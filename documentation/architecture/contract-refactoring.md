# Kernschmied – Refactoring-Konzept für den maximalen Vertragsrahmen

**Zieldatei:** `documentation/architecture/contract-refactoring.md`
**Stand:** 2026-08-03
**Status:** Arbeitsdokument und verbindliche Refactoring-Grundlage
**Geltungsbereich:** Backend, Frontend, API-Verträge, SSE, Registries, dynamische Definitionen, Tests und Dokumentation

---

# 1. Zweck dieses Dokuments

Dieses Dokument beschreibt das schrittweise Refactoring der öffentlichen und internen Verträge von Kernschmied.

Ziel ist ein maximal vorbereiteter, aber zunächst nur minimal implementierter Vertragsrahmen.

Die Architektur soll langfristig folgende Fähigkeiten tragen:

* generische Hierarchie
* Chat als Intentions- und Kommunikationszentrum
* serverseitige Kontextauflösung
* Prompt-Vererbung
* dynamische Ressourcentypen
* dynamische Knotentypen
* dynamisch konfigurierte Widgets
* generische Aktionen
* semantische Konzepte und sprachliche Aliase
* geführte Workflows
* Mandantenfähigkeit
* Berechtigungen
* Datenschutzprofile
* Revisionen und Cache-Invalidierung
* System- und Integrationsereignisse
* sichere Erweiterung im laufenden Betrieb

Dabei gilt:

> Maximal definieren, minimal implementieren.

Der Vertragsrahmen soll die langfristigen Erweiterungspunkte bereits strukturell berücksichtigen. Die tatsächliche Laufzeitimplementierung wird jedoch über kleine vertikale Arbeitspakete eingeführt.

---

# 2. Zentrale Architekturentscheidung

Kernschmied ist:

* dynamisch konfigurierbar
* dynamisch strukturierbar
* dynamisch erweiterbar
* aber nicht unkontrolliert dynamisch ausführbar

Die wichtigste Sicherheitsgrenze lautet:

```text
Dynamisch ergänzbar:

- Definitionen
- Schemas
- Prompts
- Zuordnungen
- Instanzen
- Aliase
- Konzepte
- Workflows aus bekannten Schritten
- Widget-Konfigurationen
- Ressourcen
- Vorlagenpakete
- Integrationskonfigurationen

Statisch oder kontrolliert registriert:

- Python-Implementierungen
- React-Komponenten
- Action-Handler
- Tool-Handler
- Workflow-Schrittimplementierungen
- Transportarten
- Sicherheitsprüfungen
- Autorisierungslogik
```

Kernschmied lädt niemals beliebigen ausführbaren Python-, JavaScript- oder React-Code aus:

* Datenbankfeldern
* Konfigurationsdateien
* Manifestwerten
* Benutzerinhalten
* externen URLs
* nicht kontrollierten Verzeichnissen

---

# 3. Fachneutralität

Der technische Kern kennt keine fest eingebauten Fachrichtungen.

Nicht fest im Kern verankert werden:

* Firma
* Handwerk
* Schule
* Verein
* Familie
* Kundenverwaltung
* Angebote
* Baustellen
* Mannschaften
* Softwareentwicklung

Diese Bedeutungen entstehen durch:

* Prompts
* dynamische Ressourcenschemas
* semantische Konzepte
* Aliase
* Vorlagenpakete
* Widget-Konfigurationen
* Hierarchiestrukturen
* Beziehungen
* Daten
* Berechtigungen

Beispiel:

```text
Technischer Ressourcentyp:
record

Dynamische Definition:
offer

Sprachliche Aliase:
Angebot
Kostenvoranschlag
/angebot
```

Das Backend arbeitet weiterhin mit generischen Aktionen wie:

```text
resource.create
resource.update
resource.link
document.render
message.send
```

Die fachliche Bedeutung entsteht aus der aktiven Definition und dem aktuellen Kontext.

---

# 4. Chat-zentriertes Zielbild

Der Chat bleibt das Intentions- und Kommunikationszentrum.

Der Chat ist zuständig für:

* Nutzerabsicht
* natürliche Sprache
* Kommunikation
* Interpretation
* Zusammenfassung
* Aktionsvorschläge
* Bestätigungen
* Fehlerdarstellung
* Ergebnisprotokoll
* Nachvollziehbarkeit
* Austausch mit anderen Teilnehmern

Widgets bleiben ergänzende strukturierte Arbeitsflächen.

```text
Chat:
Was soll geschehen und warum?

Widget:
Welche Informationen müssen übersichtlich dargestellt oder bearbeitet werden?

Backend:
Darf die Aktion ausgeführt werden und wie wird sie korrekt verarbeitet?
```

Widgets dürfen:

* Daten anzeigen
* Aktionen auslösen
* strukturierte Bearbeitung ermöglichen

Widgets dürfen jedoch niemals:

* Autorisierung umgehen
* unregistrierte Aktionen ausführen
* freie URLs aufrufen
* eigene Geschäftslogik aus Backenddaten laden
* beliebigen Code ausführen

---

# 5. Leitprinzipien des Refactorings

## 5.1 Stabile Verträge

Öffentliche Verträge werden:

* explizit benannt
* versioniert
* getestet
* dokumentiert
* nur bewusst inkompatibel geändert

## 5.2 Backend als öffentliche Vertragsquelle

Öffentliche API-Modelle werden im Backend als Pydantic-v2-Modelle definiert.

Router dürfen keine umfangreichen öffentlichen Verträge lokal definieren.

## 5.3 Frontend-Laufzeitvalidierung

TypeScript-Typen allein reichen nicht aus.

Alle Daten aus:

* REST
* SSE
* Bootstrap
* dynamischen Definitionen
* Registry-Endpunkten
* UI-Schemas

werden als `unknown` behandelt und vor der Übernahme validiert.

## 5.4 Keine Geschäftslogik im Frontend

Das Frontend:

* rendert bekannte Komponenten
* validiert Transportdaten
* verwaltet lokalen UI-Zustand
* sendet registrierte Aktionen

Das Frontend entscheidet nicht über:

* Berechtigungen
* fachliche Gültigkeit
* Sicherheitsklassen
* Mandantenzugehörigkeit
* Toolfreigabe
* Actionfreigabe

## 5.5 Eine Laufzeitwahrheit

Für jede Domäne darf es nur eine verbindliche Laufzeitquelle geben.

Insbesondere:

* keine parallele In-Memory- und SQL-Hierarchie als Wahrheitsquelle
* keine voneinander abweichenden Frontend- und Backend-Knotentypregeln
* keine doppelt gepflegten Promptauflösungen
* keine getrennten Actiondefinitionen ohne Revision und Herkunft

---

# 6. Wichtige Korrekturen gegenüber dem Vorentwurf

## 6.1 `SchemaVersion` nicht als globales `Literal["1.0"]`

Eine globale Definition wie:

```python
SchemaVersion = Literal["1.0"]
```

würde jede spätere Vertragsentwicklung unnötig blockieren.

Stattdessen wird eine allgemeine Version-Zeichenkette verwendet:

```python
SchemaVersion = Annotated[
    str,
    Field(pattern=r"^[0-9]+\.[0-9]+$")
]
```

Jeder einzelne Vertrag darf zusätzlich eine bekannte aktuelle Version definieren:

```python
HIERARCHY_SCHEMA_VERSION = "1.0"
RESOURCE_SCHEMA_VERSION = "1.0"
```

Bei inkompatiblen Änderungen kann ein Vertrag auf `2.0` wechseln, ohne alle anderen Vertragsfamilien zu ändern.

---

## 6.2 Keine untypisierte Registry als alleinige Wahrheit

Ein allgemeines Feld wie:

```python
definition: dict[str, JsonValue]
```

ist als Speicher- und Transportumschlag sinnvoll, darf aber nicht die einzige Validierungsebene sein.

Jeder Registry-Eintrag muss nach `registry_type` durch einen bekannten typspezifischen Validator geprüft werden.

Beispiel:

```text
registry_type = resource_type
→ ResourceTypeDefinition validieren

registry_type = node_type
→ NodeTypeDefinition validieren

registry_type = concept
→ ConceptDefinition validieren
```

Unbekannte Registry-Typen werden nicht aktiviert.

---

## 6.3 Definition und Registry-Metadaten trennen

Status, Aktivierung, Herkunft und Revision gehören zum Registry-Eintrag.

Die eigentliche fachneutrale Definition sollte diese Lifecycle-Felder nicht an mehreren Stellen duplizieren.

Besser:

```text
RuntimeRegistryEntry
├── Status
├── Herkunft
├── Tenant
├── Revision
├── Aktivierungsdaten
└── Definition
    └── typspezifischer Vertrag
```

Ein `NodeTypeDefinition` sollte deshalb nicht zusätzlich denselben vollständigen Lifecycle verwalten, sofern er bereits durch den Registry-Eintrag verwaltet wird.

Systemdefinitionen können über denselben Registry-Umschlag ausgeliefert werden.

---

## 6.4 `enabled` und `status` nicht widersprüchlich verwenden

Ein Eintrag mit:

```text
status = active
enabled = false
```

wäre unklar.

Daher gilt:

* `status` beschreibt den Lifecycle.
* `enabled` beschreibt eine zusätzliche betriebliche Sperre nur dort, wo dies wirklich erforderlich ist.

Für allgemeine Registry-Einträge sollte bevorzugt ausschließlich `status` verwendet werden.

Ein Eintrag ist produktiv auflösbar, wenn:

```text
status == active
```

Eine getrennte temporäre Betriebssperre kann später als eigenes Feld hinzukommen:

```text
runtime_disabled
```

---

## 6.5 Aktivierungsanfrage nicht redundant gestalten

Bei einem Endpunkt wie:

```text
POST /registries/{registry_type}/{entry_id}/activate
```

müssen `registry_type` und `entry_id` nicht erneut verpflichtend im Request-Body vorkommen.

Ein geeigneter Body lautet:

```json
{
  "expected_revision": 4,
  "reason": "Freigabe nach erfolgreicher Prüfung"
}
```

Dadurch werden widersprüchliche Pfad- und Bodywerte vermieden.

---

## 6.6 Statusübergänge sind Service-Logik

Pydantic-Modelle validieren Formate und Feldkombinationen.

Sie führen keine Lifecycle-Übergänge durch.

Die Regeln:

```text
draft → validated
validated → pending_approval
pending_approval → active
active → disabled
disabled → active
active → deprecated
deprecated → archived
```

werden in einem Registry-Service kontrolliert.

Nicht jeder theoretisch mögliche Übergang ist erlaubt.

---

## 6.7 Antwortmodelle im Backend ebenfalls streng halten

Die frühere Idee:

```text
Requests: extra="forbid"
Responses: extra="ignore"
```

ist für Backend-Pydantic-Modelle nicht optimal.

Empfehlung:

* öffentliche Mutationsanfragen: `extra="forbid"`
* öffentliche Antwortmodelle: ebenfalls `extra="forbid"`
* interne Datenbank- oder Adaptermodelle: separat behandeln
* Frontend-Antwortvalidatoren: kontrolliert vorwärtskompatibel

Das Backend sollte nicht versehentlich zusätzliche interne Felder serialisieren.

Vorwärtskompatibilität wird im Frontend dadurch erreicht, dass Antwortvalidatoren bekannte Felder lesen und zusätzliche Felder kontrolliert zulassen.

---

## 6.8 Frontend-Request- und Response-Schemas trennen

Im Frontend gilt:

* Request-Schemas: `.strict()`
* Response-Schemas: bekannte Felder prüfen, zusätzliche Felder kontrolliert akzeptieren
* diskriminierte Typen: unbekannte Varianten nicht unkontrolliert übernehmen

Beispiel:

```typescript
const hierarchyNodeResponseSchema = z
  .object({
    id: z.string(),
    node_type: z.string(),
    name: z.string(),
  })
  .passthrough();
```

Für sicherheitsrelevante oder ausführungssteuernde Antworten kann weiterhin `.strict()` erforderlich sein.

Dies muss pro Vertrag bewusst entschieden werden.

---

## 6.9 Keine `StructuredError`-Namenskollision

Eigene Fehlermodelle dürfen nicht mit eingebauten Python-Ausnahmen oder allgemeinen Begriffen kollidieren.

Empfohlene Namen:

```text
ApiErrorResponse
ValidationIssue
ActionExecutionError
RegistryValidationIssue
```

Nicht verwenden:

```text
PermissionError
ValidationError
```

als eigene öffentliche Klassen, da diese Namen bereits bekannte Bedeutungen besitzen.

---

## 6.10 Keine veränderlichen Standardwerte

Statt:

```python
capabilities: list[str] = []
```

immer:

```python
capabilities: list[str] = Field(default_factory=list)
```

Das gilt für:

* Listen
* Dictionaries
* verschachtelte Modelle
* Standardkonfigurationen

---

# 7. Vertragsfamilien

Der maximale Vertragsrahmen wird in getrennte Familien gegliedert.

```text
Contracts
├── Common
├── Errors
├── Revisions
├── Capabilities
├── Identity and Tenancy
├── Hierarchy
├── Effective Context
├── Prompts
├── Chats
├── Messages
├── Visibility
├── Participants
├── Resources
├── Widgets
├── Actions
├── Concepts
├── Workflows
├── Registries
├── Integrations
├── Events
└── Packages
```

---

# 8. Zielstruktur Backend

```text
backend/app/contracts/
├── __init__.py
├── base.py
├── common.py
├── errors.py
├── revisions.py
├── capabilities.py
├── tenancy.py
├── identity.py
├── hierarchy.py
├── context.py
├── prompts.py
├── chat.py
├── messages.py
├── participants.py
├── visibility.py
├── resources.py
├── widgets.py
├── actions.py
├── concepts.py
├── workflows.py
├── registry.py
├── registry_validation.py
├── integrations.py
├── events.py
└── packages.py
```

Bestehende Vertragsdateien werden nicht blind ersetzt.

Vor jeder Verschiebung wird geprüft:

* Welche Router importieren den Typ?
* Welche Services verwenden ihn?
* Welche Tests hängen davon ab?
* Ist er bereits in OpenAPI sichtbar?
* Besteht ein öffentlich genutzter Name?

Bei Verschiebungen werden vorübergehend kompatible Re-Exports verwendet.

---

# 9. Zielstruktur Frontend

```text
frontend/src/contracts/
├── common.ts
├── errors.ts
├── revisions.ts
├── capabilities.ts
├── tenancy.ts
├── identity.ts
├── hierarchy.ts
├── context.ts
├── prompts.ts
├── chat.ts
├── messages.ts
├── participants.ts
├── visibility.ts
├── resources.ts
├── widgets.ts
├── actions.ts
├── concepts.ts
├── workflows.ts
├── registry.ts
├── integrations.ts
├── events.ts
└── packages.ts
```

Optional können Validatoren getrennt abgelegt werden:

```text
frontend/src/contracts/schemas/
```

Dies ist sinnvoll, wenn einzelne Vertragsdateien zu groß werden.

---

# 10. Gemeinsame Backend-Basistypen

## 10.1 Basismodell für Mutationsanfragen

```python
from pydantic import BaseModel, ConfigDict


class StrictRequestModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )
```

## 10.2 Basismodell für öffentliche Antworten

```python
class PublicResponseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )
```

## 10.3 JSON-Wert

```python
from typing import TypeAlias

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = (
    JsonScalar
    | list["JsonValue"]
    | dict[str, "JsonValue"]
)
```

Alternativ kann bei Problemen mit rekursiven Typen ein bereits bestehender stabiler JSON-Vertrag weiterverwendet werden.

## 10.4 Opaque IDs

IDs bleiben zur Laufzeit Strings.

Zur statischen Lesbarkeit können `NewType` oder `Annotated` verwendet werden.

```python
from typing import NewType

TenantId = NewType("TenantId", str)
UserId = NewType("UserId", str)
NodeId = NewType("NodeId", str)
ChatId = NewType("ChatId", str)
MessageId = NewType("MessageId", str)
ResourceId = NewType("ResourceId", str)
WidgetId = NewType("WidgetId", str)
ActionId = NewType("ActionId", str)
RequestId = NewType("RequestId", str)
```

Aus IDs darf keine fachliche Bedeutung abgeleitet werden.

## 10.5 Revision

```python
Revision = Annotated[int, Field(ge=0)]
```

Die Entscheidung, ob neue Objekte bei Revision `0` oder `1` beginnen, muss zentral dokumentiert werden.

Empfehlung:

```text
Nicht persistierter Entwurf: Revision 0
Erstmals persistiertes Objekt: Revision 1
```

---

# 11. Trennung der Vertragsebenen

## 11.1 Transportverträge

Beschreiben HTTP und SSE:

* Requests
* Responses
* Pagination
* Fehler
* Event-Envelope
* Request-ID
* Revisionen

## 11.2 Domainverträge

Beschreiben fachneutrale Kernobjekte:

* Hierarchieknoten
* Chat
* Nachricht
* Ressource
* Widget-Instanz
* Action-Definition
* Promptzuordnung
* Registry-Eintrag

## 11.3 UI-Verträge

Beschreiben Darstellung:

* Komponenten
* Felder
* Layout
* Widget-Präsentation
* Action-Präsentation
* Formulare

Ein Domainobjekt enthält keine React-spezifischen Eigenschaften.

Darstellungsmetadaten werden getrennt ausgeliefert.

---

# 12. Mandanten- und Identitätsmodell

Technische Zielstruktur:

```text
System
└── Tenant
    └── unsichtbarer Hierarchie-Root
        └── Benutzerknoten
            └── workspace
                └── project
                    └── chat
```

Dabei gilt:

* Tenant ist eine Sicherheits- und Isolationsgrenze.
* Tenant ist nicht der Hierarchie-Root.
* Der Hierarchie-Root ist nicht auswählbar.
* Der Benutzerknoten ist ein fachlicher Kontextknoten.
* Ein Benutzer kann mehreren Tenants angehören.
* Die Beziehung wird über Membership modelliert.

```text
User
↔ Membership
↔ Tenant
```

Für das lokale MVP kann ein Default-Tenant verwendet werden:

```text
local-default
```

Dies darf keine spätere Mehrmandantenfähigkeit verhindern.

---

# 13. Hierarchieverträge

## 13.1 Stabile Basisknotentypen

```text
root
user
workspace
project
chat
```

Begriffsklärung:

```text
Fachlicher Anzeigename: Bereich
Technischer Basisknotentyp: workspace
```

Der Anzeigename kann über Übersetzung oder Schema geändert werden.

Der technische Typ bleibt stabil.

## 13.2 Dynamische Knotentypen

Zusätzliche Knotentypen dürfen zur Laufzeit definiert werden.

Beispiel:

```json
{
  "node_type": "collection",
  "definition_version": "1.0",
  "label": "Sammlung",
  "allowed_parent_types": [
    "workspace",
    "project",
    "chat"
  ],
  "allowed_child_types": [
    "collection",
    "chat"
  ],
  "selectable": true,
  "prompt_capable": true,
  "widget_capable": true,
  "resource_capable": true,
  "ui": {
    "icon": "folder",
    "component": "generic_node_view"
  }
}
```

Die Definition darf nur bekannte:

* Icons
* Komponenten
* Aktionen
* Fähigkeiten

referenzieren.

## 13.3 Hierarchieknoten

Ein öffentlicher Leservertrag berücksichtigt mindestens:

```text
id
tenant_id
parent_id
node_type
name
description
position
depth
selectable
archived
capabilities
metadata
revision
schema_version
created_at
updated_at
```

## 13.4 Regeln

* Der Root kann nicht normal erstellt oder verschoben werden.
* Ein Knoten kann nicht unter sich selbst verschoben werden.
* Zyklen sind verboten.
* Parent- und Child-Typ müssen laut aktiver Definition kompatibel sein.
* Tenant-Grenzen dürfen nicht überschritten werden.
* Chats dürfen Chats als Kinder besitzen.
* `node_type` wird nach Erstellung nicht frei geändert.
* Verschieben erfolgt über eine eigene Mutation.
* Reorder und Move müssen getrennt oder eindeutig dokumentiert sein.

---

# 14. Chat und Conversation

Hierarchieknoten und Chatdatensatz bleiben getrennte Identitäten.

```text
HierarchyNode
├── id
└── node_type = chat

ChatConversation
├── id
└── hierarchy_node_id
```

Für den MVP kann eine 1:1-Beziehung gelten:

```text
Ein permanenter Chatknoten besitzt genau eine Conversation.
```

Die IDs dürfen trotzdem nicht stillschweigend gleichgesetzt werden.

Dies hält spätere Möglichkeiten offen:

* temporäre Conversations
* mehrere Kommunikationskanäle
* archivierte Conversation-Versionen
* Chatcontainer mit mehreren Threads

---

# 15. Effective Context

Der Effective Context wird ausschließlich serverseitig berechnet.

Er setzt sich zusammen aus:

```text
Tenant Policy
+ Benutzerkontext
+ Hierarchiepfad
+ Knotenkonfiguration
+ Chatkonfiguration
+ Promptbeiträge
+ Datenschutzprofil
+ Berechtigungen
+ Runtime-Kontext
```

Öffentlicher Vertrag:

```text
schema_version
tenant_id
user_id
active_node_id
active_chat_id
path
effective_revisions
registry_revisions
available_action_ids
available_widget_ids
data_profile
capabilities
```

Nicht ausgegeben werden:

* vollständige Sicherheitsprompts
* interne Policytexte
* Secretreferenzen
* ungefilterte Rollenauflösung
* interne Modellrouting-Regeln
* nicht öffentliche Toolkonfigurationen

---

# 16. Revisionen

## 16.1 Objekt-Revisionen

Veränderbare Objekte besitzen eine monotone Revision.

Verwendung:

* Optimistic Locking
* Konflikterkennung
* Cache-Invalidierung
* Auditbezug

## 16.2 Registry-Revisionen

```python
class RegistryRevisionSet(PublicResponseModel):
    values: dict[str, Revision] = Field(default_factory=dict)
```

Beispiel:

```json
{
  "values": {
    "node_types": 8,
    "resource_types": 14,
    "widget_types": 4,
    "widget_instances": 12,
    "actions": 6,
    "concepts": 21,
    "workflows": 2
  }
}
```

## 16.3 Effective Revision Set

```text
config
permissions
prompts
widgets
hierarchy
registry
```

Die Registry-Revisionen bleiben als separates verschachteltes Objekt erhalten.

Dadurch müssen bei neuen Registry-Arten keine inkompatiblen Felder zum Hauptvertrag ergänzt werden.

---

# 17. Promptverträge

Promptbeiträge werden generisch nach Scope und Hierarchiepfad aufgelöst.

Kein fest verdrahteter Resolver wie:

```python
if node.type == "project":
    ...
```

Stattdessen:

```text
Systemrichtlinie
→ Tenant-Richtlinie
→ Beiträge der Hierarchievorfahren
→ Beitrag des aktiven Knotens
→ Chatkontext
→ aktuelle Aufgabe
```

Promptdefinitionen benötigen:

```text
id
tenant_id
name
prompt_type
content
scope_type
scope_id
inheritance_mode
inherit_to_children
status
revision
previous_revision_id
created_by
activated_by
created_at
updated_at
```

Promptstatus:

```text
draft
validated
pending_approval
active
disabled
deprecated
archived
rejected
```

Prompts dürfen:

* Verhalten erklären
* fachlichen Kontext geben
* Sprache und Arbeitsweise beeinflussen

Prompts dürfen nicht:

* Berechtigungen vergeben
* Sicherheitsregeln entfernen
* Toolfreigaben erzwingen
* Datenschutzprofile überschreiben
* unbekannte Aktionen registrieren

---

# 18. Registry-Grundmodell

## 18.1 Registry-Arten

Zunächst bekannte Arten:

```text
node_type
resource_type
prompt
widget_instance
concept
workflow
template_package
integration_definition
```

Technische Implementierungsregistries bleiben separat:

```text
widget_type
action_handler
tool_handler
workflow_step_type
ui_component_type
integration_transport
```

Diese können nicht beliebig aus der Datenbank erweitert werden.

## 18.2 Registry-Status

```text
draft
validated
pending_approval
active
disabled
deprecated
archived
rejected
```

## 18.3 Gemeinsamer Registry-Eintrag

```python
class RuntimeRegistryEntry(PublicResponseModel):
    id: str
    registry_type: str
    definition_version: str
    schema_version: SchemaVersion

    tenant_id: TenantId | None
    source_type: RegistrySourceType

    status: RegistryEntryStatus
    definition: dict[str, JsonValue]

    revision: Revision

    created_by: UserId | None
    updated_by: UserId | None
    activated_by: UserId | None

    created_at: datetime
    updated_at: datetime
    activated_at: datetime | None
```

`definition` wird vor Speicherung und erneut vor Aktivierung mit dem zugehörigen typspezifischen Validator geprüft.

## 18.4 Quelltypen

```text
system
manifest
database
package
user_configuration
```

`source_type` beschreibt die Herkunft, nicht die Vertrauensstufe.

Eine Paketdefinition muss genauso validiert und freigegeben werden wie eine manuelle Definition.

---

# 19. Registry-Lifecycle

Erlaubte Hauptübergänge:

```text
draft
  ↓ validate
validated
  ↓ submit
pending_approval
  ↓ activate
active
  ↓ disable
disabled
  ↓ reactivate
active
  ↓ deprecate
deprecated
  ↓ archive
archived
```

Zusätzlich:

```text
draft → rejected
validated → rejected
pending_approval → rejected
```

Nicht erlaubt:

```text
draft → active
rejected → active
archived → active
```

Ein archivierter oder abgelehnter Eintrag muss bei erneuter Verwendung kopiert oder als neue Revision angelegt werden.

---

# 20. Validierung dynamischer Definitionen

Eine Definition durchläuft:

```text
Syntaxvalidierung
→ Vertragsschemavalidierung
→ Referenzvalidierung
→ Versionsprüfung
→ Tenant-Prüfung
→ Berechtigungsprüfung
→ Sicherheitsprüfung
→ Konfliktprüfung
→ Kompatibilitätsprüfung
→ Aktivierungsprüfung
```

Validierungsergebnis:

```python
class RegistryValidationIssue(PublicResponseModel):
    code: str
    message: str
    path: list[str | int] = Field(default_factory=list)
    severity: Literal["error", "warning", "info"]


class DefinitionValidationResult(PublicResponseModel):
    valid: bool
    issues: list[RegistryValidationIssue] = Field(default_factory=list)
    checked_definition_version: str
    checked_revision: Revision
```

Strukturierte Issues sind einer einfachen `list[str]` vorzuziehen.

---

# 21. Aktivierung

Aktivierungsrequest:

```python
class DefinitionActivationRequest(StrictRequestModel):
    expected_revision: Revision
    reason: str | None = Field(default=None, max_length=1000)
```

Aktivierungsergebnis:

```python
class DefinitionActivationResult(PublicResponseModel):
    entry_id: str
    registry_type: str
    previous_status: RegistryEntryStatus
    new_status: RegistryEntryStatus
    previous_revision: Revision
    new_revision: Revision
    activated_at: datetime
    activated_by: UserId
```

Aktivierung erfordert:

* gültige Definition
* passende Berechtigung
* aktuelle Revision
* erfüllte Abhängigkeiten
* keine Sicherheitsverletzung
* Audit-Eintrag
* Registry-Revisionssteigerung
* Cache-Invalidierung
* Ereignis

---

# 22. Dynamische Ressourcentypen

Ressourcentypen können ohne Neustart definiert werden.

Beispiel:

```json
{
  "resource_type": "note",
  "definition_version": "1.0",
  "display_name": "Notiz",
  "data_schema": {
    "type": "object",
    "required": [
      "title",
      "content"
    ],
    "properties": {
      "title": {
        "type": "string",
        "minLength": 1,
        "maxLength": 200
      },
      "content": {
        "type": "string",
        "maxLength": 50000
      }
    },
    "additionalProperties": false
  },
  "ui_schema": {
    "fields": [
      {
        "key": "title",
        "component": "text"
      },
      {
        "key": "content",
        "component": "textarea"
      }
    ]
  },
  "default_classification": "internal"
}
```

Der Ressourcenservice bleibt generisch:

```text
resource.create
resource.read
resource.update
resource.delete
resource.search
resource.link
resource.unlink
```

Jede Mutation validiert gegen:

* aktive Definition
* konkrete Definitionversion
* Tenant
* Berechtigung
* Datenklassifikation
* aktuelle Ressourcenrevision

---

# 23. Ressourcenversionen

Eine Ressource speichert:

```text
resource_type
resource_definition_version
resource_schema_version
```

Bestehende Ressourcen werden durch eine neue Definition nicht automatisch verändert.

## Kompatible Änderung

Beispiele:

* optionales Feld ergänzt
* zusätzliche Anzeigeinformation
* neuer Alias
* neue Sortieroption

Kann eine neue Registry-Revision derselben Definitionversion sein.

## Inkompatible Änderung

Beispiele:

* Feldtyp geändert
* Pflichtfeld ergänzt
* Feld entfernt
* Semantik verändert

Erfordert:

* neue Definitionversion
* Migrationsstrategie
* Prüfung bestehender Instanzen
* gegebenenfalls parallele Unterstützung mehrerer Versionen

---

# 24. Widget-System

## 24.1 Widget-Typ

Technisch fest im Frontend registriert.

Beispiele:

```text
resource_list
resource_table
resource_form
timeline
calendar
file_list
document_preview
activity_feed
statistics
```

## 24.2 Widget-Instanz

Dynamisch konfigurierbar.

```text
widget_type
title
scope
config
layout
interaction_class
supported_action_ids
revision
```

## 24.3 Interaktionsklassen

```text
read_only
trigger_only
structured_edit
```

Eine Instanz darf die technische Interaktionsklasse ihres Widget-Typs nicht erweitern.

Beispiel:

```text
Technischer Typ: trigger_only
Instanz verlangt: structured_edit
→ Definition ungültig
```

## 24.4 Grenzen

Dynamisch:

* Filter
* Spalten
* Sortierung
* Titel
* Layout
* Datenquelle
* Zuordnung
* bekannte Aktionen

Nicht dynamisch:

* React-Komponente
* JavaScript
* Renderfunktion
* freies HTML
* beliebige API-Ziele

---

# 25. Actions

## 25.1 Technische Action

Fest registriert:

```text
resource.create
resource.update
resource.delete
hierarchy.node.create
hierarchy.node.move
message.send
document.export
integration.invoke
```

## 25.2 Action-Definition

Beschreibt Sicherheits- und Ausführungsgrenzen:

```text
id
risk_class
transaction_mode
confirmation_policy
audit_policy
idempotency_policy
required_permissions
input_schema
output_schema
```

## 25.3 Risikoklassen

```text
A – lokal und reversibel
B – fachlich relevant, aber reversibel
C – extern wirksam oder schwer reversibel
D – sicherheitskritisch
```

## 25.4 Sicherheitsregel

Eine dynamische semantische Definition darf die technische Action nicht abschwächen.

```text
Technische Action:
risk_class = C

Konzept:
risk_class = A

Ergebnis:
ungültig
```

Die effektive Risikoklasse ist immer mindestens so streng wie die technische Definition.

---

# 26. Konzepte und Aliase

Ein Konzept übersetzt Nutzersprache in eine generische Action.

```json
{
  "id": "note.create",
  "scope_type": "hierarchy_node",
  "scope_id": "node_123",
  "display_name": "Notiz erstellen",
  "action_id": "resource.create",
  "parameter_mapping": {
    "resource_type": "note"
  },
  "defaults": {
    "classification": "internal"
  },
  "aliases": [
    "Notiz erstellen",
    "neue Notiz",
    "/notiz"
  ]
}
```

Aliase können entstehen durch:

* Administration
* berechtigte Benutzer
* Vorlagenpakete
* bestätigte Lernvorschläge

Automatisch erkannte Aliase werden niemals ungefragt aktiviert.

---

# 27. Workflows

Workflows sind dynamisch zusammensetzbar, aber nur aus bekannten Schritten.

Bekannte Schrittarten:

```text
message
dynamic_form
selection
confirmation
action
condition
wait
complete
cancel
```

Nicht zulässig:

* Python-Code
* JavaScript-Code
* `eval`
* Shell-Kommandos
* freie Funktionsnamen
* nicht registrierte Action-Handler

Workflowdefinitionen benötigen:

```text
id
definition_version
steps
transitions
entry_step
maximum_steps
timeout_policy
status
revision
```

Schleifen müssen:

* explizit erlaubt
* begrenzt
* validiert

sein.

---

# 28. Vorlagenpakete

Ein Vorlagenpaket kann enthalten:

```text
package.json
prompts/
resource-types/
node-types/
widget-instances/
concepts/
aliases/
workflows/
templates/
```

Importablauf:

```text
Paket auswählen
→ Manifest validieren
→ Kompatibilität prüfen
→ Inhalt in Staging laden
→ Definitionen typspezifisch validieren
→ Konflikte anzeigen
→ Vorschau erzeugen
→ bestätigen
→ Definitionen speichern
→ einzeln oder gemeinsam aktivieren
→ Revisionen erhöhen
→ Ereignisse senden
```

Pakete enthalten keine ausführbaren Implementierungen.

---

# 29. Integrationen

Integrationen werden in zwei Ebenen geteilt.

## Technische Transportimplementierung

Fest registriert:

```text
http
webhook
email
calendar_connector
file_import
```

## Dynamische Integrationskonfiguration

Darf enthalten:

```text
provider_type
endpoint_reference
authentication_reference
allowed_actions
allowed_events
timeout
retry_policy
mapping
```

Secrets werden ausschließlich über sichere Referenzen eingebunden.

Secrets dürfen nicht enthalten sein in:

* Registry-Definition
* Prompt
* Widget-Konfiguration
* Auditdetails
* Frontend-Antworten

---

# 30. Registry-API

Langfristig vorgesehene Endpunkte:

```text
GET    /api/v1/registries
GET    /api/v1/registries/{registry_type}
GET    /api/v1/registries/{registry_type}/{entry_id}

POST   /api/v1/registries/{registry_type}
PATCH  /api/v1/registries/{registry_type}/{entry_id}

POST   /api/v1/registries/{registry_type}/{entry_id}/validate
POST   /api/v1/registries/{registry_type}/{entry_id}/submit
POST   /api/v1/registries/{registry_type}/{entry_id}/activate
POST   /api/v1/registries/{registry_type}/{entry_id}/disable
POST   /api/v1/registries/{registry_type}/{entry_id}/deprecate
POST   /api/v1/registries/{registry_type}/{entry_id}/archive
```

Diese Endpunkte werden nicht alle im ersten Refactoring-Paket implementiert.

Sie werden zunächst vertraglich vorbereitet.

Für häufig genutzte Definitionen können später zusätzlich typisierte Komfortendpunkte bereitgestellt werden:

```text
GET /api/v1/resource-types
GET /api/v1/node-types
GET /api/v1/concepts
```

---

# 31. Generische oder spezifische Registry-Endpunkte

Ein vollständig generischer Registry-Endpunkt ist flexibel, aber schwerer:

* in OpenAPI abzubilden
* im Frontend zu validieren
* verständlich zu dokumentieren
* granular zu autorisieren

Daher gilt:

## Generischer Kern

Für Lifecycle, Speicherung, Revision und Aktivierung.

## Typspezifische Validatoren und Services

Für:

* NodeTypeDefinition
* ResourceTypeDefinition
* ConceptDefinition
* WorkflowDefinition
* PromptDefinition

## Optionale typisierte API-Fassaden

Für häufig verwendete Definitionen.

Dadurch wird kein untypisierter „Alles-Endpunkt“ zur einzigen öffentlichen Schnittstelle.

---

# 32. Capability Negotiation

Bootstrap liefert nur:

* aktivierte Fähigkeiten
* Versionen
* Featurekennungen
* Registry-Revisionen
* Endpointschlüssel

Beispiel:

```json
{
  "capabilities": {
    "dynamic_resource_types": {
      "enabled": true,
      "version": "1.0",
      "features": [
        "draft",
        "validate",
        "activate"
      ]
    },
    "dynamic_workflows": {
      "enabled": false,
      "version": "1.0",
      "features": [],
      "reason": "not_implemented"
    }
  },
  "registry_revisions": {
    "resource_types": 4,
    "node_types": 2,
    "concepts": 1
  }
}
```

Bootstrap überträgt nicht alle Definitionen vollständig.

Das Frontend lädt nur benötigte Registries.

---

# 33. Definition Resolver

Ein zentraler Resolver löst aktive Definitionen auf.

```python
class DefinitionResolver:
    async def resolve_node_type(
        self,
        *,
        tenant_id: TenantId,
        node_type: str,
    ) -> NodeTypeDefinition:
        ...

    async def resolve_resource_type(
        self,
        *,
        tenant_id: TenantId,
        resource_type: str,
        definition_version: str | None = None,
    ) -> ResourceTypeDefinition:
        ...

    async def resolve_concept(
        self,
        *,
        tenant_id: TenantId,
        concept_id: str,
        context_node_id: NodeId | None,
    ) -> ConceptDefinition:
        ...

    async def resolve_action(
        self,
        *,
        tenant_id: TenantId,
        action_id: ActionId,
    ) -> ActionDefinition:
        ...
```

Der Resolver berücksichtigt:

```text
Systemdefinition
→ globale Definition
→ Tenant-Definition
→ Knotenzuordnung
→ aktive Revision
```

Nicht aktive Definitionen werden niemals im normalen Laufzeitpfad verwendet.

---

# 34. Caching und Invalidierung

Definitionen dürfen gecacht werden.

Cache-Schlüssel berücksichtigen mindestens:

```text
tenant_id
registry_type
entry_id oder definition key
registry_revision
definition_version
```

Änderungsablauf:

```text
Definition speichern
→ validieren
→ aktivieren
→ Registry-Revision erhöhen
→ Cache logisch ungültig
→ SSE-Ereignis
→ Frontend lädt betroffene Registry neu
```

Keine globalen Singleton-Caches ohne Invalidierungsweg.

---

# 35. Multi-Worker-Betrieb

MVP:

* Registry-Revision in der Datenbank
* lokale Cache-Schlüssel enthalten Revision
* kontrollierte Revisionsprüfung
* kein stiller dauerhafter Cache

Später:

* PostgreSQL `LISTEN/NOTIFY`
* Redis Pub/Sub
* anderer verteilter Invalidierungsmechanismus

Die Verträge dürfen nicht von einer konkreten Cache-Technologie abhängen.

---

# 36. Ereignisvertrag

Ein gemeinsamer Event-Envelope:

```text
schema_version
event_id
event_type
conversation_id
sequence
timestamp
request_id
payload
```

Bestehende Chatereignisse dürfen nicht ohne Migrationspfad umbenannt werden.

Neue Ereignisse:

```text
registry.entry.created
registry.entry.updated
registry.entry.validated
registry.entry.activated
registry.entry.disabled
registry.entry.deprecated
registry.entry.archived
registry.revision.changed

resource.created
resource.updated
resource.deleted

widget.invalidated
context.changed
capabilities.changed
```

Das Frontend verarbeitet nur bekannte Ereignisse aktiv.

Unbekannte Ereignisse:

* zerstören den Stream nicht
* werden optional protokolliert
* lösen keine unbekannte Aktion aus

---

# 37. Frontend-Registry

Die technische Registry bleibt fest im Frontend.

```typescript
export const widgetRegistry = {
  resource_list: ResourceListWidget,
  resource_table: ResourceTableWidget,
  resource_form: ResourceFormWidget,
  timeline: TimelineWidget,
} as const;
```

Das Backend kann konfigurieren:

```json
{
  "widget_type": "resource_table",
  "config": {
    "resource_type": "note",
    "columns": [
      "title",
      "updated_at"
    ]
  }
}
```

Es kann nicht konfigurieren:

```json
{
  "widget_type": "https://example.com/widget.js"
}
```

Unbekannte Typen werden sichtbar als nicht unterstützt dargestellt.

---

# 38. Frontend-Laufzeitvalidierung

Mindestens folgende Response-Verträge benötigen Validatoren:

* Bootstrap
* Hierarchieknoten
* Knotentypdefinition
* Effective Context
* Registry-Eintrag
* DefinitionValidationResult
* ResourceTypeDefinition
* ResourceRead
* WidgetInstance
* ActionDefinition
* ConceptDefinition
* EventEnvelope
* ApiErrorResponse

Keine ungeprüften Daten werden in den Store übernommen.

## Alte Antworten dürfen neue Zustände nicht überschreiben

Jeder Ladeprozess muss berücksichtigen:

* AbortSignal
* Request-ID
* Revision
* aktuelle Auswahl
* Reihenfolge asynchroner Antworten

---

# 39. API-Fehlervertrag

Einheitlicher Fehler:

```json
{
  "code": "REGISTRY_ENTRY_INVALID",
  "message": "Die Definition konnte nicht aktiviert werden.",
  "details": {
    "entry_id": "entry_123",
    "issues": []
  },
  "request_id": "request_123"
}
```

Wichtige Registry-Fehlercodes:

```text
REGISTRY_TYPE_UNKNOWN
REGISTRY_ENTRY_NOT_FOUND
REGISTRY_ENTRY_INVALID
REGISTRY_STATUS_TRANSITION_INVALID
REGISTRY_REVISION_CONFLICT
REGISTRY_PERMISSION_DENIED
REGISTRY_DEPENDENCY_MISSING
REGISTRY_DEFINITION_VERSION_UNSUPPORTED
REGISTRY_ENTRY_NOT_ACTIVE
REGISTRY_ENTRY_ALREADY_ACTIVE
REGISTRY_TENANT_MISMATCH
```

---

# 40. Datenbankmodell – Vorbereitung

Langfristig benötigte Tabellen:

```text
runtime_registry_entries
registry_revisions
registry_validation_runs
registry_activation_history
```

Mögliche Struktur `runtime_registry_entries`:

```text
id
tenant_id
registry_type
definition_key
definition_version
schema_version
status
source_type
definition_json
revision
created_by
updated_by
activated_by
created_at
updated_at
activated_at
```

Wichtige Constraints:

* eindeutige aktive Definition pro Tenant, Typ, Schlüssel und Version
* Revision nicht negativ
* Tenant-Grenzen
* Statuswerte begrenzt
* JSON-Inhalt validiert vor Aktivierung
* keine Secrets in `definition_json`

---

# 41. Audit

Immer auditieren:

* Definition erstellt
* Definition aktualisiert
* Validierung ausgeführt
* Aktivierung
* Deaktivierung
* Deprecation
* Archivierung
* fehlgeschlagene Aktivierung
* Berechtigungsfehler
* Paketimport

Auditdaten enthalten:

* Akteur
* Tenant
* Registry-Typ
* Eintrags-ID
* alte Revision
* neue Revision
* Statuswechsel
* Request-ID
* Zeitstempel
* Grund

Auditdaten enthalten nicht ungeprüft:

* vollständige Prompts
* Secrets
* personenbezogene Inhalte
* komplette große Definitionen

Stattdessen können Hash, Diff-Metadaten oder sichere Referenzen verwendet werden.

---

# 42. Berechtigungen

Beispielberechtigungen:

```text
registry:read

registry:create
registry:update
registry:validate
registry:submit
registry:activate
registry:disable
registry:deprecate
registry:archive

node_type:create
resource_type:create
concept:create
workflow:create
package:import
package:activate
```

Erstellen und Aktivieren bleiben getrennte Rechte.

Development darf beide Rechte demselben lokalen Benutzer geben.

Die Trennung muss im Vertrag trotzdem bestehen.

---

# 43. Sicherheitsinvarianten

Folgende Regeln sind unveränderlich:

1. Eine dynamische Definition registriert keinen ausführbaren Code.
2. Eine Definition kann nur bekannte technische IDs referenzieren.
3. Eine Action kann nicht auf eine niedrigere Risikoklasse herabgestuft werden.
4. Pflichtberechtigungen können nicht entfernt werden.
5. Datenschutzklassifikationen können nicht unzulässig gelockert werden.
6. Tenant-Grenzen können nicht durch Links oder Aliase überschritten werden.
7. Nicht aktive Definitionen werden nicht produktiv verwendet.
8. Unbekannte Widget- oder Komponentenarten werden nicht ausgeführt.
9. Prompts ersetzen keine Validierung.
10. Modellantworten aktivieren keine Definitionen.
11. Discovery bedeutet niemals Aktivierung.
12. Aktivierung ist revisionsgeschützt und auditierbar.

---

# 44. Refactoring-Phasen

## Phase 0 – Bestandsaufnahme

* bestehende Backend-Verträge inventarisieren
* Router-lokale Modelle erfassen
* bestehende Frontend-Typen erfassen
* SSE-Verträge dokumentieren
* OpenAPI prüfen
* Importabhängigkeiten erfassen
* doppelte Typen identifizieren

Ergebnis:

```text
documentation/architecture/contracts-inventory.md
```

---

## Phase 1 – Gemeinsame Basistypen

* `base.py`
* `common.py`
* `errors.py`
* `revisions.py`
* stabile ConfigDict-Policies
* JSON-Wert
* IDs
* Revision
* Zeitstempel
* Request-ID

Noch keine Laufzeitfunktion ändern.

---

## Phase 2 – Bestehende Verträge konsolidieren

Priorität:

1. Hierarchie
2. Chat
3. Nachrichten
4. Fehler
5. Events
6. Bootstrap
7. Config

Bestehende öffentliche Namen über Re-Exports kompatibel halten.

---

## Phase 3 – Maximale neue Vertragsfamilien

Anlegen:

* context
* registry
* registry_validation
* resources
* widgets
* actions
* concepts
* workflows
* capabilities
* tenancy
* packages

Noch keine vollständige Laufzeitimplementierung.

---

## Phase 4 – Frontend-Spiegelung

* TypeScript-Verträge
* Zod-Validatoren
* API-Parsing
* Fehlerbehandlung
* unbekannte Typen
* Revisionsprüfung

---

## Phase 5 – Dynamischer Ressourcentyp `note`

Minimal implementieren:

* systemseitige Registry-Definition
* Status `active`
* Resource-Type-Revision
* Registry-Leseendpunkt
* ResourceCreate
* ResourceRead
* Schema-Validierung
* generische `resource.create`-Action
* Audit
* Tests

---

## Phase 6 – Walking Skeleton

```text
HierarchyNode
→ EffectiveContext
→ Chat
→ Message
→ Registry
→ ResourceType note
→ Resource note
→ Widget resource_list
→ Action resource.create
→ SSE resource.created
→ widget.invalidated
```

---

## Phase 7 – Registry-Verwaltung

Erst nach erfolgreichem Walking Skeleton:

* Entwurf erstellen
* aktualisieren
* validieren
* aktivieren
* deaktivieren
* archivieren
* Statusübergänge
* Berechtigungen
* Audit
* Revisionskonflikte

---

## Phase 8 – Weitere Definitionstypen

Reihenfolge:

1. ConceptDefinition
2. PromptDefinition
3. WidgetInstance
4. NodeTypeDefinition
5. WorkflowDefinition
6. TemplatePackage
7. IntegrationDefinition

---

# 45. Erster Walking Skeleton

Der erste vollständige Ablauf:

1. System registriert den Ressourcentyp `note`.
2. Definition wird typspezifisch validiert.
3. Definition ist aktiv.
4. Registry-Revision wird ausgeliefert.
5. Frontend erkennt die Revision.
6. Frontend lädt die aktive Ressourcentypdefinition.
7. Das UI rendert ein Formular mit bekannten Komponenten.
8. Nutzer bittet im Chat um Erstellung einer Notiz.
9. Kernschmied schlägt `resource.create` vor.
10. Backend prüft Berechtigung.
11. Backend löst die aktive `note`-Definition auf.
12. Eingabedaten werden gegen das Schema validiert.
13. Ressource wird gespeichert.
14. Audit-Eintrag wird geschrieben.
15. `resource.created` wird per SSE ausgegeben.
16. `widget.invalidated` wird gesendet.
17. Resource-List-Widget lädt neu.
18. Chat zeigt das Ergebnis.
19. Verlauf bleibt nach Serverneustart erhalten.

---

# 46. Backend-Tests

Mindestens:

## Basistypen

* ungültige Schema-Version
* negative Revision
* ungültige ID
* zusätzliche Request-Felder
* veränderliche Defaults ausgeschlossen

## Registry

* gültiger Registry-Eintrag
* unbekannter Registry-Typ
* ungültige Definition
* Entwurf nicht produktiv auflösbar
* validierter Eintrag noch nicht aktiv
* Aktivierung mit falscher Revision
* ungültiger Statusübergang
* Aktivierung erhöht Revision
* Registry-Gesamtrevision steigt
* Audit wird geschrieben
* anderer Tenant erhält keinen Zugriff

## Ressourcen

* aktiven `note`-Typ auflösen
* Ressource gültig
* Pflichtfeld fehlt
* zusätzliches Feld verboten
* falsche Definitionversion
* deaktivierter Typ
* Revision-Konflikt

## Aktionen

* unbekannte Action
* fehlende Berechtigung
* Risikoklasse nicht absenkbar
* Action-Parameter ungültig
* Idempotency-Key doppelt

## SSE

* `resource.created`
* `widget.invalidated`
* Registry-Ereignis
* unbekannter Eventtyp stört Stream nicht
* Request-ID
* genau ein Abschlussereignis

---

# 47. Frontend-Tests

Mindestens:

* gültiger Registry-Eintrag
* ungültiger Registry-Eintrag
* unbekannter Registry-Typ
* gültige Ressourcentypdefinition
* unbekannte UI-Komponente
* Widget-Typ nicht registriert
* Effective Context mit Registry-Revisionen
* alte Antwort überschreibt keine neuere Revision
* Registry-Änderung lädt nur betroffene Definitionen neu
* unbekanntes SSE-Ereignis wird sicher ignoriert
* strukturierter Fehler wird korrekt angezeigt
* keine ungeprüften Daten im Store

---

# 48. OpenAPI

Neue Verträge erscheinen nur dann zuverlässig in OpenAPI, wenn sie:

* von öffentlichen Endpunkten verwendet werden oder
* bewusst über ein OpenAPI-Schema eingebunden werden

Es ist nicht notwendig, jeden Zukunftsvertrag sofort künstlich in OpenAPI aufzunehmen.

Dokumentation und Python-Verträge dürfen bereits existieren, während die Capability deaktiviert ist.

OpenAPI soll nur tatsächlich erreichbare öffentliche Laufzeitverträge versprechen.

---

# 49. Kompatibilitätsstrategie

## Additive Änderung

* optionales Feld
* neuer Endpoint
* neue Capability
* neue Eventart

Kann innerhalb derselben Hauptversion möglich sein.

## Inkompatible Änderung

* Feld entfernt
* Feldtyp geändert
* Bedeutung geändert
* Pflichtfeld ergänzt
* Eventstruktur geändert

Erfordert:

* neue Vertragsversion
* Migrationsphase
* parallele Unterstützung oder klaren Mindestclient
* Dokumentation
* Tests
* OpenAPI-Diff

---

# 50. Re-Exports

Wenn bestehende Typen verschoben werden:

```python
# alter Pfad
from app.contracts.hierarchy import HierarchyNodeRead

__all__ = ["HierarchyNodeRead"]
```

Re-Exports sind Übergangslösungen.

Für jeden Re-Export wird dokumentiert:

* alter Pfad
* neuer Pfad
* Einführungsdatum
* geplantes Entfernungsrelease

Keine unbegrenzten Aliasstrukturen.

---

# 51. Nichtziele dieses Refactorings

Nicht Bestandteil des ersten Vertragsrefactorings:

* vollständige Adminoberfläche für alle Registries
* beliebiges Plugin-Loading
* Remote-Python-Plugins
* automatische Migration aller Ressourcentypen
* vollständige Workflow-Engine
* vollständiges RAG
* Multi-Agenten-System
* komplexe Policy Engine
* produktiver Multi-Tenant-Wechsel
* PostgreSQL-Optimierung
* öffentliche Paketplattform

Diese Bereiche werden vertraglich vorbereitet, aber nicht vollständig implementiert.

---

# 52. Abnahmekriterien des Vertragsrefactorings

Das Refactoring gilt als erfolgreich, wenn:

* öffentliche Backend-Verträge zentral liegen
* Router keine großen eigenen Vertragsmodelle mehr definieren
* Backend-Anfragen unbekannte Felder ablehnen
* Frontend-Antworten laufzeitvalidiert werden
* Hierarchie- und Chatverträge kompatibel weiterlaufen
* Effective Context definiert ist
* Registry-Lifecycle definiert ist
* Registry-Revisionen definiert sind
* dynamische Definitionen keinen Code laden können
* `note` als dynamischer Ressourcentyp abbildbar ist
* Action-Risikoklassen vertraglich vorhanden sind
* Widget-Typ und Widget-Instanz getrennt sind
* unbekannte Komponenten sicher behandelt werden
* bestehende SSE-Ereignisse kompatibel bleiben
* neue Registry- und Ressourcenereignisse vorbereitet sind
* Backendtests bestehen
* Frontendtests bestehen
* Produktionsbuild besteht
* OpenAPI dem tatsächlichen Laufzeitstand entspricht
* Dokumentation und Code dieselben Begriffe verwenden

---

# 53. Konkrete Dateiarbeiten

## Backend neu oder zu prüfen

```text
backend/app/contracts/base.py
backend/app/contracts/common.py
backend/app/contracts/errors.py
backend/app/contracts/revisions.py
backend/app/contracts/capabilities.py
backend/app/contracts/tenancy.py
backend/app/contracts/identity.py
backend/app/contracts/hierarchy.py
backend/app/contracts/context.py
backend/app/contracts/prompts.py
backend/app/contracts/chat.py
backend/app/contracts/messages.py
backend/app/contracts/participants.py
backend/app/contracts/visibility.py
backend/app/contracts/resources.py
backend/app/contracts/widgets.py
backend/app/contracts/actions.py
backend/app/contracts/concepts.py
backend/app/contracts/workflows.py
backend/app/contracts/registry.py
backend/app/contracts/registry_validation.py
backend/app/contracts/integrations.py
backend/app/contracts/events.py
backend/app/contracts/packages.py
backend/app/contracts/__init__.py
```

## Frontend neu oder zu prüfen

```text
frontend/src/contracts/common.ts
frontend/src/contracts/errors.ts
frontend/src/contracts/revisions.ts
frontend/src/contracts/capabilities.ts
frontend/src/contracts/tenancy.ts
frontend/src/contracts/identity.ts
frontend/src/contracts/hierarchy.ts
frontend/src/contracts/context.ts
frontend/src/contracts/prompts.ts
frontend/src/contracts/chat.ts
frontend/src/contracts/messages.ts
frontend/src/contracts/participants.ts
frontend/src/contracts/visibility.ts
frontend/src/contracts/resources.ts
frontend/src/contracts/widgets.ts
frontend/src/contracts/actions.ts
frontend/src/contracts/concepts.ts
frontend/src/contracts/workflows.ts
frontend/src/contracts/registry.ts
frontend/src/contracts/integrations.ts
frontend/src/contracts/events.ts
frontend/src/contracts/packages.ts
```

## Dokumentation

```text
documentation/architecture/contracts.md
documentation/architecture/contract-refactoring.md
documentation/architecture/registry-system.md
documentation/architecture/effective-context.md
documentation/architecture/schema-versioning.md
documentation/architecture/dynamic-definitions.md
```

---

# 54. Empfohlene Arbeitsreihenfolge

1. Bestand inventarisieren.
2. Keine bestehenden Verträge blind ersetzen.
3. Basismodelle und ConfigDict-Regeln festlegen.
4. Fehler- und Revisionsverträge stabilisieren.
5. Hierarchieverträge konsolidieren.
6. Chat- und Message-Verträge konsolidieren.
7. bestehenden SSE-Vertrag dokumentieren.
8. Effective Context hinzufügen.
9. Registry-Verträge hinzufügen.
10. Ressourcen-, Widget- und Action-Verträge hinzufügen.
11. Frontend-Verträge spiegeln.
12. Runtime-Validatoren ergänzen.
13. Backend-Vertragstests ergänzen.
14. Frontend-Vertragstests ergänzen.
15. OpenAPI prüfen.
16. Produktionsbuild prüfen.
17. Walking Skeleton `note` implementieren.
18. erst danach Registry-Schreiboperationen implementieren.

---

# 55. Abschlussbericht je Arbeitspaket

Jedes Arbeitspaket berichtet:

1. analysierte bestehende Dateien
2. neu angelegte Dateien
3. geänderte Dateien
4. verschobene Verträge
5. Re-Exports
6. öffentliche API-Auswirkungen
7. Frontend-Vertragsänderungen
8. neue Validatoren
9. neue Tests
10. ausgeführte Prüfungen
11. bewusst nicht implementierte Funktionen
12. bekannte Restinkonsistenzen
13. vollständigen Output von `git status --short`

---

# 56. Verbindliches Ergebnis

Nach Abschluss dieses Refactorings gilt:

```text
Kernschmied besitzt einen stabilen technischen Vertragskern.

Neue fachliche Bedeutungen können im laufenden Betrieb ergänzt werden.

Neue Datenstrukturen werden über validierte, versionierte Definitionen ergänzt.

Neue Ansichten werden über bekannte Widgets dynamisch konfiguriert.

Neue Arbeitsabläufe werden aus bekannten Schritten zusammengesetzt.

Neue Aktionen greifen ausschließlich auf registrierte Handler zurück.

Jede Aktivierung ist validiert, autorisiert, revisioniert und auditierbar.

Kein Datenbankeintrag kann neuen ausführbaren Code in das System laden.
```

Damit bleibt Kernschmied fachneutral, dynamisch, erweiterbar und sicher.
