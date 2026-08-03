# ADR-0003: Registry-basierte Erweiterungsarchitektur

* **Status:** Angenommen – konsolidiert
* **Datum der ursprünglichen Entscheidung:** 2026-07-27
* **Letzte Überarbeitung:** 2026-08-03
* **Entscheidungsträger:** Kernschmied-Architekturteam
* **Ersetzt:** Keine
* **Ersetzt durch:** Keine
* **Verwandte Dokumente:**

  * `documentation/leitkonzept.md`
  * `documentation/architecture/contracts.md`
  * `documentation/architecture/contract-refactoring.md`
  * `documentation/architecture/dynamic-definitions.md`
  * `documentation/architecture/effective-context.md`
  * `documentation/architecture/decisions/ADR-0001-schema-driven-user-interface.md`
  * `documentation/architecture/decisions/ADR-0002-configuration-architecture-and-runtime-initialization.md`

---

## 1. Entscheidung in Kurzform

Kernschmied verwendet für alle technisch erweiterbaren Subsysteme eine **explizite, registry-basierte Erweiterungsarchitektur**.

Technische Implementierungen werden nicht durch verteilte Fallunterscheidungen im Anwendungskern ausgewählt, sondern über klar definierte Registries registriert, validiert, aufgelöst und verwaltet.

Kernschmied unterscheidet dabei verbindlich zwischen:

1. **technischen Implementierungsregistries**
2. **dynamischen Runtime-Registries**
3. **Definitionen**
4. **Instanzen**
5. **Zuordnungen**
6. **Aktivierung und Freigabe**

Die zentrale Regel lautet:

> Der Anwendungskern hängt von stabilen Registry-Verträgen ab.
> Technische Implementierungen werden kontrolliert registriert.
> Dynamische Definitionen dürfen bekannte technische Fähigkeiten konfigurieren, aber niemals neuen ausführbaren Code registrieren.

---

# 2. Kontext

Kernschmied ist als fachneutrale, dynamische Kommunikations- und Assistenzplattform ausgelegt.

Die Plattform soll im Laufe ihrer Entwicklung neue Fähigkeiten aufnehmen können, ohne dass der bestehende Kern für jede neue Implementierung umgebaut werden muss.

Mögliche Erweiterungspunkte sind:

* Modellprovider,
* Modelle,
* Tools,
* Frontend-Komponenten,
* Widgets,
* Frontend-Aktionen,
* Hierarchieknotentypen,
* Promptdefinitionen,
* Ressourcentypen,
* Workflow-Schritte,
* Workflowdefinitionen,
* Authentifizierungsprovider,
* Speicherprovider,
* Import- und Exportformate,
* Integrationen,
* Vorlagenpakete,
* spätere Plugins.

Diese Erweiterungspunkte müssen:

* vorhersehbar,
* sicher,
* testbar,
* versioniert,
* wartbar,
* auffindbar,
* revisionsfähig,
* auditierbar

bleiben.

Gleichzeitig darf dynamische Erweiterbarkeit nicht dazu führen, dass beliebiger Code aus:

* Datenbanken,
* Manifesten,
* Benutzerkonfigurationen,
* externen URLs,
* nicht kontrollierten Verzeichnissen

geladen und ausgeführt wird.

---

# 3. Problemstellung

Ohne ein einheitliches Erweiterungsmodell wird neue Funktionalität häufig direkt in bestehende Kernmodule eingebaut.

Beispiele:

```python
if provider == "ollama":
    ...

elif provider == "openai":
    ...

elif provider == "transformers":
    ...
```

oder:

```typescript
if (component.type === "table") {
  ...
}

if (component.type === "tree") {
  ...
}

if (component.type === "calendar") {
  ...
}
```

Dieser Ansatz verursacht mehrere Probleme.

## 3.1 Verteilte Fallunterscheidungen

Jede neue Implementierung erfordert zusätzliche Bedingungen.

Mit zunehmender Anzahl wachsen:

* Verschachtelung,
* Abhängigkeiten,
* Seiteneffekte,
* Testaufwand,
* Risiko unbeabsichtigter Änderungen.

## 3.2 Direkte Kopplung

Der Anwendungskern kennt jede konkrete Implementierung.

Beispiel:

```text
ChatService
├── kennt Ollama
├── kennt OpenAI
├── kennt Transformers
├── kennt llama.cpp
└── kennt jeden zukünftigen Provider
```

Dadurch wird der Kern bei jeder Erweiterung verändert.

## 3.3 Mehrere Änderungsstellen

Eine neue Implementierung kann Änderungen erfordern in:

* Initialisierung,
* Konfiguration,
* Auswahl,
* API,
* UI,
* Health-Check,
* Tests,
* Shutdown,
* Dokumentation.

## 3.4 Schlechte Fehlerisolation

Ein fehlerhafter Provider, ein ungültiges Tool oder eine unbekannte Komponente kann andere Teile des Systems beeinflussen, wenn kein kontrollierter Registrierungs- und Initialisierungspfad existiert.

## 3.5 Unklare Aktivierung

Ohne Registry-Lifecycle ist unklar:

* ob eine Implementierung nur entdeckt wurde,
* ob sie valide ist,
* ob sie freigegeben wurde,
* ob sie aktiv ist,
* ob sie betriebsbereit ist.

## 3.6 Verletzung des Open/Closed-Prinzips

Der Kern muss ständig modifiziert werden, anstatt über stabile Verträge erweitert zu werden.

## 3.7 Unsichere Plugin-Ansätze

Ein unkontrolliertes Plugin-System könnte Manifestwerte oder Datenbankfelder als Importpfade interpretieren.

Dadurch entstünden Risiken wie:

* beliebige Codeausführung,
* unkontrollierte Abhängigkeiten,
* schwer prüfbare Lebenszyklen,
* fehlende Vertrauensgrenzen,
* unsichere Updates.

---

# 4. Abgrenzung: technische Registry und Runtime-Registry

Kernschmied unterscheidet zwei grundlegend verschiedene Registry-Arten.

## 4.1 Technische Implementierungsregistry

Verwaltet tatsächlich ausführbare Implementierungen.

Beispiele:

* Modellprovider,
* Tool-Handler,
* Action-Handler,
* Widget-Komponenten,
* UI-Komponenten,
* Workflow-Schrittimplementierungen,
* Integrationstransporte,
* Speicherprovider,
* Authentifizierungsprovider.

Diese Implementierungen stammen aus:

* kontrolliertem Anwendungscode,
* vertrauenswürdigen lokalen Modulen,
* explizit freigegebenen Paketpfaden,
* beim Build oder Start bekannten Registrierungen.

## 4.2 Dynamische Runtime-Registry

Verwaltet Definitionen und Konfigurationen.

Beispiele:

* Ressourcentypen,
* zusätzliche Knotentypen,
* Promptdefinitionen,
* Widget-Instanzen,
* Konzepte,
* Aliase,
* Workflowdefinitionen,
* Vorlagenpakete,
* Integrationskonfigurationen.

Diese Einträge dürfen zur Laufzeit aus der Datenbank geladen werden.

Sie enthalten keine ausführbaren Implementierungen.

---

# 5. Aktueller Zustand – IST

Zum Zeitpunkt dieser Überarbeitung besitzt Kernschmied bereits mehrere Registry-Grundlagen.

## 5.1 Bereits vorhanden

* ModelProviderRegistry,
* Modell-Registry,
* Tool-Registry,
* feste Frontend-Komponenten-Registry als Architekturprinzip,
* feste Action-Registry als Architekturprinzip,
* Icon-Registry,
* Modell- und Toolmanifeste,
* isolierte Providerinitialisierung,
* Modell- und Toollisten-Endpunkte,
* Capability-Grundlagen im Bootstrap,
* kontrollierte Providerauflösung,
* keine beliebigen Importpfade aus Modellmanifesten,
* teilweise isolierte Fehlerbehandlung.

## 5.2 Teilweise implementiert

* vollständige Manifestvalidierung,
* Registry-Revisionen,
* Health-Status pro Eintrag,
* Aktivierungsstatus,
* zentrale Diagnose,
* Lifecycle-Management,
* Shutdown,
* Frontend-Registry-Validierung,
* dynamische Runtime-Registries,
* Action-Risikoklassen,
* Registry-Auditierung,
* Registry-basierte Cache-Invalidierung.

## 5.3 Derzeitige Inkonsistenzen

* einzelne Fallunterscheidungen können noch außerhalb der Registries bestehen,
* Registry-Verträge sind noch nicht vollständig vereinheitlicht,
* Modell-, Tool-, Komponenten- und Action-Registries verwenden noch nicht zwingend denselben Lifecycle,
* Discovery, Validierung, Freigabe und Aktivierung sind noch nicht überall getrennt,
* Registry-Revisionsstände sind noch nicht vollständig im Effective Context enthalten,
* dynamische Definitionen und technische Implementierungen sind noch nicht durchgängig getrennt,
* nicht alle Registryfehler besitzen stabile Fehlercodes,
* Diagnose- und Health-Informationen sind noch nicht einheitlich.

---

# 6. Zielzustand – SOLL

Kernschmied soll eine konsistente Registry-Architektur besitzen.

```text
Anwendungskern
        ↓
Registry-Vertrag
        ↓
Registry-Service
        ↓
registrierte Implementierungen oder Definitionen
        ↓
validierte Auflösung
        ↓
kontrollierte Nutzung
```

Für technische Implementierungen:

```text
Code / vertrauenswürdiges Paket
        ↓
explizite Registrierung
        ↓
Vertragsprüfung
        ↓
Initialisierung
        ↓
Health-Prüfung
        ↓
Freigabe
        ↓
aktive Nutzung
```

Für dynamische Definitionen:

```text
Datenbank / Manifest / Paket
        ↓
Discovery oder Erstellung
        ↓
typspezifische Validierung
        ↓
Review
        ↓
Aktivierung
        ↓
Runtime-Auflösung
```

---

# 7. Entscheidung

Kernschmied verwendet dauerhaft eine registry-basierte Erweiterungsarchitektur.

Die Entscheidung umfasst folgende verbindliche Punkte.

## 7.1 Der Kern kennt Registry-Schnittstellen

Services hängen nicht direkt von konkreten Implementierungen ab.

Beispiel:

```text
ModelService
    ↓
ModelProviderRegistry
    ↓
ModelProvider
```

Nicht:

```text
ModelService
├── OllamaProvider
├── OpenAIProvider
├── TransformersProvider
└── weitere Provider
```

## 7.2 Registrierung erfolgt explizit

Eine Implementierung wird nicht allein dadurch verfügbar, dass eine Datei existiert.

## 7.3 Discovery ist keine Aktivierung

Gefundene Implementierungen oder Definitionen werden zunächst nur als Kandidaten erfasst.

## 7.4 Registries validieren zentrale Invarianten

Registries prüfen mindestens:

* eindeutige ID,
* bekannte Version,
* gültigen Vertrag,
* erlaubte Herkunft,
* notwendige Capabilities,
* Abhängigkeiten,
* Status,
* Tenant-Scope,
* Freigabe.

## 7.5 Fehler werden isoliert

Ein fehlerhafter Eintrag darf nicht automatisch die gesamte Registry oder Anwendung unbrauchbar machen.

Ausnahmen gelten für ausdrücklich als verpflichtend definierte Kernimplementierungen.

## 7.6 Technische und dynamische Registries bleiben getrennt

Runtime-Daten können keine neue ausführbare Implementierung registrieren.

---

# 8. Architekturprinzip

Die ursprüngliche Formulierung:

> Kernsysteme hängen von Registries ab.
> Registries hängen von Implementierungen ab.
> Implementierungen verändern den Kern nicht.

wird präzisiert zu:

> Der Anwendungskern verwendet stabile Registry-Schnittstellen.
> Technische Registries verwalten kontrolliert registrierte Implementierungen.
> Runtime-Registries verwalten validierte Definitionen.
> Keine dynamische Definition darf neue ausführbare Implementierungen laden oder Sicherheitsgrenzen umgehen.

---

# 9. Zielarchitektur

```text
                    Anwendungskern

                          │
                          ▼

                 Registry-Schnittstelle

                          │

        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼

 technische          technische         technische
Implementierung A   Implementierung B   Implementierung C
```

Für Runtime-Definitionen:

```text
                    Anwendungskern

                          │
                          ▼

                  Definition Resolver

                          │
                          ▼

                  Runtime Registry

                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼

      Definition A    Definition B    Definition C
```

---

# 10. Registry-Arten

## 10.1 Modellprovider-Registry

Verwaltet Providerimplementierungen wie:

* Ollama,
* OpenAI-kompatible APIs,
* Azure OpenAI,
* Anthropic,
* Google Gemini,
* llama.cpp,
* Transformers,
* lokale HTTP-Provider.

## 10.2 Modell-Registry

Verwaltet logische Modelle und deren Zuordnung zu Providern.

## 10.3 Tool-Registry

Verwaltet bekannte Toolimplementierungen.

## 10.4 UI-Komponenten-Registry

Verwaltet bekannte React-Komponenten.

## 10.5 Widget-Registry

Verwaltet bekannte Widget-Typen.

## 10.6 Action-Registry

Verwaltet technische Action-Handler.

## 10.7 Workflow-Step-Registry

Verwaltet bekannte Schrittimplementierungen.

## 10.8 Runtime-Registry

Verwaltet dynamische Definitionen.

## 10.9 Integrations-Transport-Registry

Verwaltet bekannte technische Transportarten.

## 10.10 Format-Registry

Verwaltet bekannte Import- und Exportformate.

---

# 11. Gemeinsamer Registry-Vertrag

Jede technische Registry sollte mindestens folgende Operationen unterstützen:

```text
register
unregister
get
require
list
validate
initialize
shutdown
health
capabilities
revision
```

Nicht jede Registry muss alle Operationen öffentlich anbieten.

Die Semantik bleibt jedoch konsistent.

Beispiel:

```python
class RegistryProtocol(Protocol):
    def get(self, entry_id: str) -> object | None:
        ...

    def require(self, entry_id: str) -> object:
        ...

    def list(self) -> Sequence[object]:
        ...

    @property
    def revision(self) -> int:
        ...
```

Registries werden über Dependency Injection bereitgestellt.

---

# 12. Registrierung

## 12.1 Explizite Registrierung

Technische Implementierungen werden bewusst registriert.

Beispiel:

```python
registry.register(
    provider_id="ollama",
    factory=create_ollama_provider,
    capabilities={"chat", "streaming"},
)
```

## 12.2 Keine automatische Freigabe durch Dateifund

Das Vorhandensein einer Datei bedeutet nicht:

* gültig,
* freigegeben,
* aktiv,
* verwendbar.

## 12.3 Keine freien Importpfade

Manifestdaten dürfen nicht enthalten:

```json
{
  "implementation": "some.package.arbitrary_class"
}
```

wenn dieser Pfad anschließend ungeprüft importiert wird.

Stattdessen referenziert ein Manifest eine bekannte Implementierungskennung:

```json
{
  "provider_type": "ollama"
}
```

Diese wird durch die feste Registry aufgelöst.

---

# 13. Discovery, Registrierung und Aktivierung

Kernschmied trennt folgende Zustände:

```text
discovered
registered
validated
approved
initialized
active
degraded
disabled
failed
deprecated
archived
```

Nicht jede Registry benötigt alle Zustände, aber deren Bedeutung darf nicht vermischt werden.

## 13.1 Discovered

Ein Kandidat wurde gefunden.

## 13.2 Registered

Der Eintrag wurde in die Registry aufgenommen.

## 13.3 Validated

Vertrag, Manifest und Referenzen sind gültig.

## 13.4 Approved

Die Verwendung wurde administrativ freigegeben.

## 13.5 Initialized

Technische Ressourcen wurden erfolgreich initialisiert.

## 13.6 Active

Der Eintrag darf produktiv verwendet werden.

## 13.7 Degraded

Der Eintrag ist teilweise verwendbar oder besitzt einen Fehlerzustand.

## 13.8 Disabled

Der Eintrag ist bewusst deaktiviert.

---

# 14. Registry-Identitäten

Jeder Eintrag besitzt eine stabile, opaque ID.

Beispiele:

```text
ollama
openai
calculator
resource.create
resource_table
dynamic_form
```

IDs müssen:

* eindeutig,
* normalisiert,
* versionierbar,
* nicht lokalisierungsabhängig

sein.

Anzeigenamen sind getrennt.

Beispiel:

```text
Technische ID: resource_table
Deutsche Anzeige: Ressourcentabelle
```

---

# 15. Versionierung

Registries unterscheiden mehrere Versionen.

## 15.1 Vertragsversion

Version des Registry- oder Manifestvertrags.

## 15.2 Implementierungsversion

Version der technischen Implementierung.

## 15.3 Definitionsversion

Version einer dynamischen Definition.

## 15.4 Registry-Revision

Monotoner Stand der Registry.

Beispiel:

```json
{
  "registry_type": "tools",
  "contract_version": "1.0",
  "revision": 14
}
```

Die Registry-Revision steigt bei relevanten Änderungen wie:

* Registrierung,
* Aktivierung,
* Deaktivierung,
* Entfernung,
* Statusänderung,
* Capability-Änderung.

---

# 16. Manifest-System

Manifeste beschreiben Metadaten und Konfiguration.

Sie enthalten keine frei ausführbare Implementierungslogik.

## 16.1 Modellmanifest

Beispiel:

```text
model.json
```

Kann beschreiben:

* logische Modell-ID,
* Provider-Typ,
* providerinternen Modellnamen,
* Capabilities,
* Limits,
* Konfigurationsschema,
* Aktivierungsstatus.

## 16.2 Toolmanifest

Beispiel:

```text
tool.json
```

Kann beschreiben:

* Tool-ID,
* Name,
* Version,
* Eingabeschema,
* Ausgabeschema,
* Berechtigungen,
* Bestätigungspflicht,
* Capability-Metadaten.

## 16.3 Sicherheitsgrenze

Ein Manifest bestimmt nicht:

* Python-Importpfad,
* Shell-Befehl,
* React-Komponente,
* JavaScript-Funktion,
* freie Netzwerkziele.

---

# 17. Capability-Metadaten

Registry-Einträge beschreiben ihre Fähigkeiten explizit.

Beispiele für Modelle:

```text
chat
streaming
tools
vision
reasoning
embeddings
structured_output
```

Beispiele für Tools:

```text
read
write
external_effect
destructive
requires_confirmation
```

Beispiele für Widgets:

```text
read_only
trigger_only
structured_edit
```

Der Anwendungskern verwendet Capability-Abfragen statt konkreter Implementierungsnamen.

Nicht:

```python
if provider_id == "ollama":
    ...
```

Sondern:

```python
if provider.supports("streaming"):
    ...
```

---

# 18. Lifecycle-Management

Technische Registries verwalten den Lifecycle ihrer Einträge.

Mögliche Schritte:

```text
register
→ validate
→ initialize
→ health_check
→ activate
→ use
→ shutdown
```

## 18.1 Lazy Initialization

Provider und Tools sollen nach Möglichkeit erst bei tatsächlicher Nutzung initialisiert werden.

Vorteile:

* schnellerer Start,
* geringerer Ressourcenverbrauch,
* bessere Fehlerisolation,
* optionale Erweiterungen blockieren den Start nicht.

## 18.2 Shutdown

Registries müssen geordnetes Herunterfahren ermöglichen.

Ein Fehler beim Shutdown eines Eintrags darf andere Einträge nicht blockieren.

## 18.3 Timeout

Initialisierung und Shutdown benötigen kontrollierte Timeouts.

---

# 19. Fehlerisolation

Ein fehlerhafter Eintrag führt zu einem eigenen Status.

Beispiel:

```json
{
  "id": "provider-x",
  "status": "failed",
  "error": {
    "code": "PROVIDER_INITIALIZATION_FAILED",
    "message": "Provider konnte nicht initialisiert werden."
  }
}
```

Andere Einträge bleiben nutzbar.

Ausnahmen:

* verpflichtende Datenbank,
* verpflichtende Sicherheitskomponente,
* unverzichtbare Kernregistry.

Diese können die Readiness verhindern.

---

# 20. Health und Diagnose

Jede Registry kann Diagnoseinformationen liefern.

Beispiele:

* registrierte Einträge,
* aktive Einträge,
* deaktivierte Einträge,
* fehlerhafte Einträge,
* Registry-Revision,
* letzter Health-Check,
* Capability-Übersicht.

Sensitive Informationen dürfen nicht ausgegeben werden.

Nicht ausgeben:

* API-Schlüssel,
* Tokens,
* vollständige Providerkonfigurationen,
* interne Stacktraces,
* Secrets.

---

# 21. Technische Implementierungsregistries

Technische Registries sind codegebunden.

Beispiele:

```text
ModelProviderRegistry
ToolHandlerRegistry
ActionHandlerRegistry
WidgetComponentRegistry
UIComponentRegistry
WorkflowStepRegistry
IntegrationTransportRegistry
```

Sie dürfen nur kontrolliert erweitert werden.

Mögliche Wege:

* direkter Codeeintrag,
* vertrauenswürdiges lokales Paket,
* später signiertes Pluginpaket,
* statische Importliste.

Nicht erlaubt:

* beliebige Datenbankpfade,
* freie Modulnamen,
* unkontrollierte Dateisystemsuche,
* Remote-Code-Download.

---

# 22. Dynamische Runtime-Registries

Runtime-Registries verwalten nicht ausführbare Definitionen.

Beispiele:

```text
node_types
resource_types
prompts
widget_instances
concepts
workflows
template_packages
integration_definitions
```

Diese Definitionen können im Betrieb:

* erstellt,
* validiert,
* aktiviert,
* deaktiviert,
* revisioniert,
* archiviert

werden.

Sie referenzieren ausschließlich bekannte technische Fähigkeiten.

---

# 23. Definition Resolver

Ein zentraler Resolver kombiniert:

```text
Systemdefinition
→ globale Definition
→ Tenant-Definition
→ Kontextzuordnung
→ aktive Revision
```

Beispiel:

```python
class DefinitionResolver:
    async def resolve_resource_type(
        self,
        *,
        tenant_id: str,
        resource_type: str,
        definition_version: str | None = None,
    ) -> ResourceTypeDefinition:
        ...
```

Nicht aktive Definitionen werden im normalen Laufzeitpfad nicht verwendet.

---

# 24. Frontend-Registries

Das Frontend besitzt feste technische Registries.

Beispiel:

```typescript
export const componentRegistry = {
  text: TextField,
  textarea: TextAreaField,
  select: SelectField,
  resource_table: ResourceTableWidget,
} as const;
```

Das Backend darf referenzieren:

```json
{
  "component_type": "resource_table"
}
```

Das Backend darf nicht referenzieren:

```json
{
  "component_type": "https://example.com/widget.js"
}
```

Unbekannte Typen werden sichtbar und sicher abgelehnt.

---

# 25. Action-Registry

Die Action-Registry trennt:

## 25.1 Technischen Handler

Fest im Code registriert.

```text
resource.create
resource.update
message.send
hierarchy.node.move
```

## 25.2 Semantisches Konzept

Dynamisch konfigurierbar.

```text
note.create
offer.create
task.assign
```

## 25.3 Alias

Sprachlich und kontextabhängig.

```text
Notiz erstellen
/Notiz
neuen Eintrag anlegen
```

Ein Alias registriert keine neue Ausführungslogik.

---

# 26. Action-Sicherheitsgrenzen

Eine dynamische Definition darf technische Action-Grenzen nicht abschwächen.

Beispiel:

```text
Technischer Handler:
risk_class = C
required_permission = resource:delete

Dynamisches Konzept:
risk_class = A
required_permissions = []

Ergebnis:
Definition ungültig
```

Die effektive Konfiguration verwendet immer die strengste Kombination.

---

# 27. Tools und Modelle

## 27.1 Modellprovider

Providerimplementierungen werden über die Provider-Registry aufgelöst.

Ein Modellmanifest referenziert nur bekannte Provider-Typen.

## 27.2 Modelle

Logische Modell-ID und providerinterner Modellname bleiben getrennt.

## 27.3 Tools

Toolmanifest und Toolimplementierung bleiben getrennt.

Discovery eines Toolmanifests bedeutet nicht:

* Freigabe,
* Aktivierung,
* Benutzerberechtigung,
* automatische Nutzung.

Jeder Toolaufruf wird zusätzlich serverseitig autorisiert.

---

# 28. Plugins

Ein zukünftiges Plugin-System baut auf Registries auf.

Ein Plugin kann kontrolliert bereitstellen:

* technische Implementierungen,
* Manifeste,
* UI-Registry-Einträge,
* Action-Handler,
* Workflow-Schritte,
* Dokumentation.

Für das MVP gilt weiterhin:

* kein Remote-Plugin-Loading,
* keine beliebigen Importpfade,
* keine unkontrollierte Codeausführung,
* keine automatische Aktivierung.

Spätere Pluginpakete benötigen möglicherweise:

* Signaturen,
* Vertrauensstufen,
* Versionierung,
* Abhängigkeitsprüfung,
* Installationsfreigabe,
* Isolation.

---

# 29. Registry-API

Öffentliche Registry-Endpunkte dienen vor allem der Abfrage und Administration.

Mögliche Endpunkte:

```text
GET /api/v1/models
GET /api/v1/models/providers
GET /api/v1/tools
GET /api/v1/registries
GET /api/v1/registries/{registry_type}
GET /api/v1/registries/{registry_type}/{entry_id}
```

Für Runtime-Definitionen später:

```text
POST  /api/v1/registries/{registry_type}
PATCH /api/v1/registries/{registry_type}/{entry_id}

POST /api/v1/registries/{registry_type}/{entry_id}/validate
POST /api/v1/registries/{registry_type}/{entry_id}/activate
POST /api/v1/registries/{registry_type}/{entry_id}/disable
POST /api/v1/registries/{registry_type}/{entry_id}/archive
```

Technische Registries dürfen nicht zwingend über dieselben Schreibendpunkte veränderbar sein.

---

# 30. Registry-Revision und Cache-Invalidierung

Jede Registry besitzt eine Revision.

Beispiel:

```json
{
  "registry_revisions": {
    "models": 4,
    "providers": 3,
    "tools": 8,
    "resource_types": 2,
    "concepts": 5
  }
}
```

Bei Änderungen:

```text
Eintrag ändern
→ validieren
→ speichern oder registrieren
→ Registry-Revision erhöhen
→ Cache invalidieren
→ Ereignis senden
→ Frontend lädt gezielt neu
```

---

# 31. Ereignisse

Registry-Änderungen können folgende Ereignisse erzeugen:

```text
registry.entry.discovered
registry.entry.registered
registry.entry.validated
registry.entry.activated
registry.entry.disabled
registry.entry.failed
registry.entry.deprecated
registry.entry.archived
registry.revision.changed
```

Unbekannte Ereignisse dürfen den SSE-Stream nicht beschädigen.

---

# 32. Dependency Injection

Registries werden nicht als versteckte globale Singletons verwendet.

Beispiel:

```python
def get_model_service(
    provider_registry: ModelProviderRegistry = Depends(get_provider_registry),
) -> ModelService:
    ...
```

Vorteile:

* testbar,
* austauschbar,
* explizite Abhängigkeiten,
* kontrollierter Lifecycle,
* mehrere Instanzen möglich.

---

# 33. Sicherheitsinvarianten

1. Kein Manifest darf beliebige Python-Importpfade ausführen.
2. Keine Datenbankdefinition darf ausführbaren Code registrieren.
3. Discovery bedeutet niemals Aktivierung.
4. Registrierung bedeutet nicht automatische Benutzerfreigabe.
5. Jede ID muss eindeutig sein.
6. Jede Implementierung muss ihren Vertrag erfüllen.
7. Unbekannte Registry-Typen werden nicht aktiviert.
8. Unbekannte UI-Komponenten werden nicht ausgeführt.
9. Unbekannte Actions werden nicht ausgeführt.
10. Toolaufrufe werden serverseitig autorisiert.
11. Sicherheitsgrenzen können dynamisch nur verschärft werden.
12. Fehler eines Eintrags werden isoliert.
13. Secrets werden nicht über Diagnose-APIs ausgegeben.
14. Tenant-Grenzen gelten auch für Runtime-Registries.
15. Registry-Änderungen sind revisionsgeschützt und auditierbar.
16. Technische Registries werden nur aus vertrauenswürdigen Quellen erweitert.
17. Keine globale Singleton-Magie ohne klaren Lifecycle.
18. Shutdown-Fehler eines Eintrags blockieren andere Einträge nicht.

---

# 34. Positive Konsequenzen

## 34.1 Geringere Kopplung

Der Kern hängt von Verträgen statt konkreten Implementierungen ab.

## 34.2 Bessere Erweiterbarkeit

Neue Implementierungen können ergänzt werden, ohne bestehende Services umfassend zu ändern.

## 34.3 Zentrale Validierung

IDs, Versionen, Capabilities und Verträge werden an einer Stelle geprüft.

## 34.4 Bessere Fehlerisolation

Fehlerhafte Einträge können deaktiviert oder degradiert werden.

## 34.5 Laufzeitdiagnose

Administrative Oberflächen können Registry-Zustände anzeigen.

## 34.6 Einheitlicher Lifecycle

Registrierung, Initialisierung, Health und Shutdown folgen konsistenten Regeln.

## 34.7 Dynamische fachliche Erweiterung

Runtime-Definitionen können ergänzt werden, ohne neuen Code zu laden.

## 34.8 Bessere Testbarkeit

Registries und Implementierungen können getrennt getestet werden.

---

# 35. Negative Konsequenzen

## 35.1 Höhere Anfangskomplexität

Registry-Schnittstellen, Lifecycle und Fehlerbehandlung müssen zuerst entworfen werden.

## 35.2 Zusätzliche Abstraktion

Für wenige Implementierungen kann eine Registry zunächst umfangreicher wirken als eine direkte Fallunterscheidung.

## 35.3 Versionsmanagement

Implementierung, Manifest, Vertrag und Definition können unterschiedliche Versionen besitzen.

## 35.4 Debugging über mehrere Ebenen

Fehler können entstehen in:

* Discovery,
* Registrierung,
* Manifestvalidierung,
* Initialisierung,
* Capability-Auflösung,
* Runtime-Definition,
* Berechtigung,
* konkreter Implementierung.

## 35.5 Gefahr übergenerischer Registries

Eine einzige Registry für alles wäre schwer typisierbar und unsicher.

Daher bleiben typspezifische Registries und Validatoren notwendig.

---

# 36. Verworfene Alternativen

## 36.1 Verteilte `if`- und `match`-Blöcke

### Vorteile

* einfach für wenige Varianten,
* keine zusätzliche Abstraktion.

### Nachteile

* starke Kopplung,
* ständig wachsende Kernmodule,
* schlechte Erweiterbarkeit,
* hohe Änderungsrisiken.

**Entscheidung:** Als grundlegendes Erweiterungsmodell verworfen.

Lokale Fallunterscheidungen innerhalb einer Implementierung bleiben erlaubt.

---

## 36.2 Vollständig automatische Modul-Discovery

Alle Module eines Verzeichnisses werden automatisch importiert.

### Vorteile

* geringe manuelle Registrierung,
* scheinbar einfache Erweiterung.

### Nachteile

* unkontrollierte Codeausführung,
* unklare Reihenfolge,
* schwer prüfbare Fehler,
* Discovery wird mit Aktivierung vermischt,
* unsichere Dateisystemabhängigkeit.

**Entscheidung:** Verworfen.

---

## 36.3 Importpfade in Manifesten

### Vorteile

* flexible Zuordnung zwischen Manifest und Implementierung.

### Nachteile

* Manifest kontrolliert Codeausführung,
* Sicherheitsrisiko,
* schwer auditierbar,
* unklare Vertrauensgrenzen.

**Entscheidung:** Vollständig verworfen.

---

## 36.4 Eine globale Universal-Registry

### Vorteile

* einheitliche Oberfläche,
* wenig Registryklassen.

### Nachteile

* schwache Typisierung,
* unklare Lifecycle-Regeln,
* vermischte Sicherheitsgrenzen,
* komplizierte Validierung,
* schwer verständliche API.

**Entscheidung:** Verworfen.

Gemeinsame Basisverträge sind erlaubt, konkrete Registries bleiben typspezifisch.

---

## 36.5 Service Locator als globaler Singleton

### Vorteile

* einfacher globaler Zugriff,
* wenig Dependency-Injection-Code.

### Nachteile

* versteckte Abhängigkeiten,
* schwer testbar,
* unklarer Lifecycle,
* problematisch für Multi-Tenancy und Multi-Worker.

**Entscheidung:** Verworfen.

---

## 36.6 Unkontrolliertes Remote-Plugin-System

### Vorteile

* maximale Erweiterbarkeit,
* schnelle Installation.

### Nachteile

* erhebliche Supply-Chain-Risiken,
* Remote-Code-Ausführung,
* schwierige Isolation,
* komplexe Update- und Vertrauensmodelle.

**Entscheidung:** Nicht Teil des MVP.

---

# 37. Migrationsstrategie vom IST zum SOLL

## Phase 1 – Registry-Bestand inventarisieren

* vorhandene Registries erfassen,
* direkte Implementierungsabhängigkeiten suchen,
* verteilte Fallunterscheidungen dokumentieren,
* Manifestpfade prüfen,
* Registry-APIs erfassen.

## Phase 2 – Gemeinsame Registry-Begriffe definieren

* Entry-ID,
* Status,
* Version,
* Revision,
* Capability,
* Health,
* Fehlervertrag.

## Phase 3 – Modellprovider konsolidieren

* Provider-Registry als einzige Auflösungsquelle,
* direkte Providerinstanziierung entfernen,
* Lazy Initialization,
* isolierter Shutdown,
* stabile Fehlercodes.

## Phase 4 – Modell-Registry konsolidieren

* logische Modell-ID,
* Providerzuordnung,
* Capability-Metadaten,
* Verfügbarkeit,
* Auswählbarkeit.

## Phase 5 – Tool-Registry konsolidieren

* Manifestvalidierung,
* Implementierungsauflösung,
* Berechtigung,
* Bestätigung,
* Ausführungshistorie.

## Phase 6 – Frontend-Registries finalisieren

* Komponenten,
* Widgets,
* Actions,
* Icons,
* unbekannte Typen,
* Prop-Validierung.

## Phase 7 – Runtime-Registry-Verträge

* RegistryEntryStatus,
* RuntimeRegistryEntry,
* RegistryRevisionSet,
* DefinitionValidationResult,
* Aktivierungsverträge.

## Phase 8 – Dynamischer Ressourcentyp `note`

* Definition registrieren,
* validieren,
* aktivieren,
* auflösen,
* verwenden,
* Ereignis senden.

## Phase 9 – Diagnose und Health

* Registry-Status,
* Fehlerisolation,
* Readiness-Auswirkung,
* sichere Adminansicht.

---

# 38. Abnahmekriterien

Die Entscheidung gilt als technisch umgesetzt, wenn:

* der Kern keine direkten Provider-Fallunterscheidungen benötigt,
* Provider ausschließlich über die Provider-Registry aufgelöst werden,
* Modelle über die Modell-Registry aufgelöst werden,
* Tools über die Tool-Registry aufgelöst werden,
* Frontend-Komponenten ausschließlich aus fester Registry stammen,
* Actions ausschließlich über bekannte Handler ausgeführt werden,
* unbekannte IDs sicher abgelehnt werden,
* doppelte IDs verhindert werden,
* Manifestversionen validiert werden,
* Discovery und Aktivierung getrennt sind,
* Eintragsfehler isoliert werden,
* Registry-Revisionen verfügbar sind,
* Lifecycle und Shutdown kontrolliert funktionieren,
* keine Importpfade aus Manifesten ausgeführt werden,
* Runtime-Definitionen keinen ausführbaren Code registrieren,
* Registry-Änderungen auditierbar sind,
* OpenAPI und Dokumentation den Laufzeitstand korrekt abbilden.

---

# 39. Konkrete Auswirkungen auf Kernschmied

## Backend

Zielbereiche:

```text
backend/app/models/registry.py
backend/app/models/providers/
backend/app/tools/registry.py
backend/app/registries/
backend/app/contracts/registry.py
backend/app/contracts/capabilities.py
backend/app/contracts/actions.py
backend/app/services/
backend/app/bootstrap/
```

## Frontend

Zielbereiche:

```text
frontend/src/registry/
frontend/src/contracts/registry.ts
frontend/src/contracts/actions.ts
frontend/src/contracts/widgets.ts
frontend/src/components/schema/
frontend/src/components/widgets/
```

## Tests

Zielbereiche:

```text
backend/tests/registries/
backend/tests/models/
backend/tests/tools/
frontend/src/registry/__tests__/
frontend/src/contracts/__tests__/
```

---

# 40. Verbindliche Architekturregeln

1. Der Anwendungskern hängt von Registry-Verträgen ab.
2. Konkrete Implementierungen verändern den Kern nicht direkt.
3. Technische Registries und Runtime-Registries bleiben getrennt.
4. Discovery bedeutet niemals Aktivierung.
5. Registrierung bedeutet niemals automatische Benutzerfreigabe.
6. Jede Registry-ID ist eindeutig.
7. Jede Implementierung wird vor Nutzung validiert.
8. Manifeste enthalten keine frei ausführbaren Importpfade.
9. Runtime-Definitionen enthalten keinen ausführbaren Code.
10. Unbekannte Komponenten, Actions und Tools werden sicher abgelehnt.
11. Registry-Einträge besitzen stabile Versionen und Revisionen.
12. Fehler einzelner optionaler Einträge werden isoliert.
13. Pflichtkomponenten dürfen Readiness blockieren.
14. Registries werden über Dependency Injection bereitgestellt.
15. Keine unkontrollierten globalen Singleton-Registries.
16. Lifecycle, Health und Shutdown werden explizit verwaltet.
17. Capabilities werden abgefragt, nicht aus Implementierungsnamen abgeleitet.
18. Tenant-Grenzen gelten auch innerhalb von Runtime-Registries.
19. Registry-Änderungen sind autorisiert, revisioniert und auditierbar.
20. Remote-Plugin-Loading bleibt außerhalb des MVP.

---

# 41. Endgültige Entscheidung

Kernschmied verwendet dauerhaft eine registry-basierte Erweiterungsarchitektur.

Das System kombiniert:

```text
stabile Registry-Verträge
+
explizit registrierte technische Implementierungen
+
validierte Manifeste
+
dynamische Runtime-Definitionen
+
Lifecycle-Management
+
Capability-Metadaten
+
Registry-Revisionen
+
Fehlerisolation
+
Dependency Injection
```

Dadurch kann Kernschmied neue Modelle, Provider, Tools, Komponenten, Actions, Definitionen und spätere Erweiterungen aufnehmen, ohne den Anwendungskern dauerhaft mit konkreten Implementierungen zu koppeln.

Gleichzeitig bleibt die technische Ausführung kontrolliert, nachvollziehbar und sicher.
