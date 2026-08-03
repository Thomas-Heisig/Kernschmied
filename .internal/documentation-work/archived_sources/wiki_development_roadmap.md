# Roadmap – Kernschmied

Stand: 01.08.2026

Die Roadmap beschreibt die geplante Entwicklung von Kernschmied von der aktuellen lokalen MVP-Anwendung zu einer modularen, sicheren und erweiterbaren KI-Plattform.

Sie definiert keine festen Veröffentlichungstermine. Stattdessen ist sie nach technischen und fachlichen Reifegraden gegliedert. Jede Phase soll auf stabilen Verträgen aufbauen und die Anwendung in einem startbaren, testbaren und wartbaren Zustand hinterlassen.

Die konkreten aktuellen Arbeitspakete werden in [[TODO]] geführt.
Hinweis: Die priorisierten, unmittelbar wichtigen Arbeitspakete wurden in der TODO‑Seite zusammengefasst. Siehe [[TODO]] für Blocker und Kurzaufgaben.

---

## Zielbild

Kernschmied soll eine lokal betreibbare, schema-gesteuerte Chat- und Assistenzplattform werden, die später ohne grundlegenden Architekturwechsel im Intranet oder abgesichert über das Internet betrieben werden kann.

Das langfristige Ziel verbindet:

```text
Versionierte Verträge

+

Runtime-Konfiguration

+

Schema-gesteuerte Oberfläche

+

Modell- und Tool-Registries

+

Generische Hierarchie

+

Sichere Erweiterungspunkte

↓

Modulare KI-Plattform

```

Die Plattform soll neue Modelle, Provider, Tools, Knotentypen, Formulare und Oberflächenkonfigurationen aufnehmen können, ohne den Anwendungskern für jede Erweiterung umbauen zu müssen.

---

## Entwicklungsphilosophie

Kernschmied entwickelt sich in kleinen, überprüfbaren Architekturphasen:

```text
Stabile Grundlage

↓

Vollständige Administration

↓

Produktive KI-Funktionen

↓

Zusammenarbeit und Persistenz

↓

Sicherer Intranet- und Internetbetrieb

↓

Erweiterbares Ökosystem

```

Jede Phase soll:

- Backend und Frontend gemeinsam startbar halten
- öffentliche Verträge stabilisieren
- Sicherheitsgrenzen beibehalten
- Tests und Dokumentation ergänzen
- technische Schulden nicht unnötig vermehren
- Änderungen möglichst rückwärtskompatibel ausführen
- neue dynamische Funktionen nur über bekannte Registries zulassen

---

## Leitprinzipien

Die folgenden Prinzipien gelten über alle Phasen hinweg:

- Architektur vor kurzfristiger Funktionsfülle
- stabile und versionierte API-Verträge
- Backend als maßgebliche Autoritätsinstanz
- Schema-gesteuerte statt fachlich fest verdrahtete Oberflächen
- dynamische Erkennung bedeutet niemals automatische Freigabe
- jede Benutzeraktion wird serverseitig autorisiert
- Providerunabhängigkeit durch stabile interne Verträge
- keine Secrets in fachlicher Konfiguration
- keine unkontrollierten Python- oder React-Imports
- keine Verwendung von `eval()` oder vergleichbaren Mechanismen
- SQLite und PostgreSQL über dieselbe Anwendungsarchitektur
- lokale Nutzung bleibt ein vollwertiges Betriebsprofil
- Dokumentation und Tests sind Teil der Implementierung
- Sicherheitsuntergrenzen dürfen nicht durch Laufzeitkonfiguration abgeschaltet werden

---

## Aktueller Stand

Kernschmied besitzt inzwischen eine funktionsfähige technische Grundlage.

## Backend

Vorhanden und grundsätzlich funktionsfähig:

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy Async
- SQLite
- Alembic-Grundlagen
- Bootstrap-Prozess
- Runtime-Konfiguration
- Config-Revision
- generische Hierarchie
- UI-Schema-Endpunkt
- Modell-Registry
- Tool-Registry
- Modellprovider-Verträge
- Ollama-Provider
- Modelllisten-Endpunkt
- Toollisten-Endpunkt
- SSE-Chat
- strukturierte Chatfehler
- Development-Identity
- Server-seitige Chat-Autorisierung
- Provider-Streamnormalisierung
- Usage- und Token-Verarbeitung
- OpenAPI-Dokumentation

## Frontend

Vorhanden und grundsätzlich funktionsfähig:

- React
- TypeScript
- Vite
- Tailwind CSS
- zentrale Anwendungseinbettung
- generischer rekursiver Hierarchiebaum
- Chatoberfläche
- SSE-Verarbeitung
- Theme-Umschaltung
- Einstellungsdialog
- zentrale API-Grundlagen
- Component- und Action-Registry-Grundlagen
- SchemaRenderer-Platzhalter
- strukturierte Layout-Komponenten

## Erfolgreich stabilisierte Chatpipeline

Die Chatpipeline erreicht inzwischen vollständig:

```text
React-Frontend

↓

POST /api/v1/chat/stream

↓

Chat-API

↓

ChatService

↓

ModelService

↓

Provider

↓

Ollama

↓

SSE-Antwort

```

Behoben wurden unter anderem:

- fehlende beziehungsweise falsch diagnostizierte Development-Identität
- falscher Ollama-Modellname
- nicht unterstützte Provider-Streamereignisse
- inkonsistente Abschlussereignisse
- fehlerhafte Usage-Serialisierung
- nicht JSON-kompatible `Usage`-Dataclass
- nicht erwartete Coroutine im Bootstrap-Zähler

Damit ist der einfache lokale Chat als MVP-Funktion grundsätzlich hergestellt.

---

## Reifegradübersicht

| Phase                        | Status                   | Schwerpunkt                                   |
| ---------------------------- | ------------------------ | --------------------------------------------- |
| 1. Technische Grundlage      | weitgehend abgeschlossen | Backend, Frontend, Bootstrap, Registries, SSE |
| 2. Vertragskonsolidierung    | in Bearbeitung           | API-, UI- und Config-Verträge                 |
| 3. Administration            | in Bearbeitung           | Settings, Provider, Modelle, Hierarchie       |
| 4. Produktiver Chat          | teilweise umgesetzt      | Persistenz, Verlauf, Tools, Prompts           |
| 5. Intranetbetrieb           | geplant                  | Authentifizierung, Audit, Rechte              |
| 6. Internetbetrieb           | geplant                  | Sessions, HTTPS, Rate Limiting                |
| 7. Erweiterungsplattform     | später                   | Plugins, Templates, Workflows                 |
| 8. Enterprise und Skalierung | langfristig              | PostgreSQL, Multi-Worker, HA                  |

---

## Phase 1 – Technische Grundlage

### Status: weitgehend abgeschlossen

Diese Phase schafft den stabilen Anwendungskern.

## Erreichte Meilensteine

- FastAPI-Anwendung
- React-Anwendung
- gemeinsamer Entwicklungsstart
- Bootstrap-Prozess
- zentrale Settings-Grundlagen
- Config-Service
- Config-Revision
- generische Hierarchie
- UI-Schema-Pipeline
- Modell-Registry
- Tool-Registry
- Modellprovider-Abstraktion
- Ollama-Anbindung
- SSE-Chat
- strukturierte Fehlergrundlagen
- Development-Authentifizierung
- zentrale Frontend-Registries
- versionierte API-Grundverträge

## Noch abzuschließen

- Bootstrap im Frontend verbindlich als ersten Request verwenden
- hart codierte Fachendpunkte vollständig entfernen
- Laufzeitvalidierung aller öffentlichen Antworten
- Fehlerantworten über alle Router hinweg vereinheitlichen
- Shutdown und Cleanup aller Provider und Registries
- OpenAPI-Verträge gegen das tatsächliche Laufzeitverhalten testen

Diese Phase gilt als vollständig abgeschlossen, wenn alle Kernendpunkte versioniert, getestet und im Frontend über den Bootstrap angebunden sind.

---

## Phase 2 – Vertragskonsolidierung

### Status: in Bearbeitung

Diese Phase vereinheitlicht die öffentlichen Verträge zwischen Backend und Frontend.

## Ziele

- ein stabiler Bootstrap-Vertrag
- ein eindeutiger Hierarchievertrag
- ein eindeutiger UI-Schema-Vertrag
- ein stabiler Chat- und SSE-Vertrag
- vollständige Config-Metadaten
- konsistente strukturierte Fehler
- zentrale Versionen und Revisionen
- TypeScript-Verträge passend zu Pydantic-Modellen

## Schwerpunkte

### Bootstrap

Der Bootstrap wird der einzige dauerhaft fest verdrahtete fachliche Einstiegspunkt des Frontends.

Er liefert:

- Anwendung
- Umgebung
- Benutzer
- Sicherheitsprofil
- Capabilities
- Features
- Vertragsversionen
- Endpunkte
- Registry-Revisionen
- Config-Revision
- Mindest-Clientversion

### UI-Schema

Transportantwort und fachliches Schema-Dokument werden eindeutig getrennt.

Unbekannte Elemente werden:

- nicht ausgeführt
- nicht dynamisch importiert
- sichtbar als nicht unterstützt dargestellt

### Hierarchie

Der öffentliche Hierarchievertrag wird vollständig typisiert und versioniert.

Er unterstützt langfristig:

- Baumrevision
- Knotenrevision
- Parent-Beziehungen
- Sortierung
- Auswahlstatus
- Deaktivierung
- Aktionen
- Metadaten
- sichere Mutationen

### Fehlerverträge

Alle API-Fehler sollen dieses Format verwenden:

```json
{
  "code": "stable_error_code",
  "message": "Verständliche Fehlermeldung",
  "details": {},
  "request_id": "..."
}
```

---

## Phase 3 – Administration

### Status: in Bearbeitung

Administratoren sollen Kernschmied vollständig über die Anwendung verwalten können, ohne Fachwerte manuell in Dateien einzutragen.

## 3.1 Schema-gesteuerte Settings

Die vorhandene `ConfigDefinition`-Registry bildet bereits ab:

- Gruppe und Schlüssel
- Standardwert
- JSON-Schema
- erlaubte Scopes
- Merge-Strategie
- Laufzeitverhalten
- Berechtigungen
- UI-Komponente
- Auswahloptionen
- dynamische Optionsquellen
- Sichtbarkeit
- Deprecation
- Audit-Regeln

Die nächste Ausbaustufe umfasst:

- vollständige Ausgabe der Definitionsmetadaten über die API
- feldspezifisches Rendering im Frontend
- lokale Validierung
- serverseitige Validierung
- Dirty-State
- Reset
- Kategorien
- Abschnitte
- erweiterte Einstellungen
- Batch-Updates
- revisionsgeschützte Speicherung

## 3.2 Provider- und Modellauswahl

Provider und Modelle werden als abhängige Einstellungen dargestellt.

```text
Provider auswählen

↓

passende Modelle des Providers laden

↓

Modell auswählen

↓

Kombination serverseitig prüfen

↓

beide Werte atomar speichern

```

Geplante beziehungsweise laufende Funktionen:

- `GET /api/v1/models/providers`
- Provider-Auswahlliste
- Modellfilter über `provider`
- `depends_on`
- `dependency_parameter`
- Prüfung auf:

  - registriert
  - aktiviert
  - verfügbar
  - auswählbar
  - Chatfähigkeit
  - Providerzugehörigkeit

- atomare Speicherung von Provider und Modell
- verständliche Fehlercodes

## 3.3 Modelladministration

Geplant:

- Modellübersicht
- Aktivierung und Deaktivierung
- Providerzuordnung
- Capability-Anzeige
- Status und Erreichbarkeit
- Standardmodell
- Limits
- Timeout
- Diagnosetest
- Modellmanifest-Anzeige
- keine Ausgabe von Secrets

## 3.4 Tooladministration

Geplant:

- Toolübersicht
- Aktivierung
- Verfügbarkeit
- Berechtigungen
- Kategorien
- Bestätigungspflicht
- Eingabeschema
- Laufzeitstatus
- Ausführungshistorie
- Diagnose

## 3.5 Promptadministration

Geplant:

- Prompteditor
- Scope-Auswahl
- Prompt-Vererbung
- effektive Promptvorschau
- Merge-Diagnose
- Versionshistorie
- Berechtigungen
- Audit

## 3.6 Hierarchieeditor

Die bisher lesende Hierarchie wird erweitert um:

- Hinzufügen
- Umbenennen
- Bearbeiten
- Verschieben
- Sortieren
- Löschen
- kontextabhängige Aktionen
- generische Formulare
- Revisionsprüfung
- Audit-Log
- Zyklusprüfung

## 3.7 Audit und Revisionen

Geplant:

- Audit-Log-Viewer
- Revisionsübersicht
- Änderungsvergleich
- Benutzer
- Zeitpunkt
- Änderungsgrund
- alte und neue Revision
- betroffene Konfiguration
- betroffene Hierarchie
- keine Secret-Werte

---

## Phase 4 – Schema-gesteuerte Oberfläche

### Status: begonnen

Das Frontend soll keine fachlich fest verdrahteten Ansichten für jeden neuen Knotentyp benötigen.

## Component Registry

Bekannte Komponenten werden über eine feste Registry bereitgestellt.

Geplante Grundkomponenten:

- Text
- Überschrift
- Absatz
- Hinweis
- Badge
- Button
- Stack
- Grid
- Section
- Card
- Divider
- Formular
- Textfeld
- Textarea
- Zahlenfeld
- Checkbox
- Select
- Multi-Select
- Tags
- JSON-Editor
- Tabelle
- Baum
- Chatansicht
- Modellselector
- Toolselector
- Dateiupload
- Unsupported-Komponente

## SchemaRenderer

Der vorhandene Platzhalter wird zu einem kontrollierten rekursiven Renderer ausgebaut.

Der Renderer:

- akzeptiert nur bekannte Komponententypen
- validiert Props komponentenspezifisch
- rendert Kinder rekursiv
- unterstützt kontrollierte Formwerte
- führt Aktionen nur über die Action Registry aus
- zeigt unbekannte Komponenten sichtbar an
- isoliert fehlerhafte Einzelkomponenten
- behandelt Backend-Schema niemals als Autorisierung

## Action Registry

Aktionen werden nur aus einer festen Registry ausgeführt.

Ein Backend-Schema darf:

- eine bekannte Aktion referenzieren
- Parameter liefern
- Darstellungshinweise liefern

Es darf nicht:

- neue Handler registrieren
- beliebige URLs ausführen
- JavaScript liefern
- React-Komponenten importieren
- Autorisierung ersetzen

---

## Phase 5 – Produktiver Chat und KI-Plattform

### Status: teilweise umgesetzt

Der einfache Chat funktioniert. Die nächste Stufe macht ihn zu einer vollständigen produktiven Arbeitsoberfläche.

## Konversationen

Geplant:

- mehrere Chats
- neue Unterhaltung
- Laden bestehender Unterhaltung
- Umbenennen
- Archivieren
- Löschen
- Verlauf
- Persistenz
- Zuordnung zur Hierarchie
- Nachrichtenrevisionen
- Suche

## Chatkontext

Jede Anfrage kann enthalten:

- `conversation_id`
- `hierarchy_node_id`
- `model_id`
- `tool_ids`
- `metadata`

Der Server prüft weiterhin alle Werte.

## Prompt-Vererbung

Geplante Ebenen:

```text
System

↓

Hierarchieknoten

↓

Projekt

↓

Chat

↓

Benutzer

↓

Request

```

Die Reihenfolge bleibt konfigurierbar, aber serverseitig validiert.

## Streaming

Weitere Verbesserungen:

- Heartbeats
- Abbruch
- Wiederverbindung
- Tokenanzeige
- Reasoning-Anzeige
- Tool-Ereignisse
- genau ein Abschlussereignis
- stabiler öffentlicher Streamvertrag
- Providerfehler-Normalisierung

## Tool-Orchestrierung

Geplant:

- Modellauswahl von Tools
- serverseitige Freigabe
- Benutzerbestätigung
- Toolausführung
- Toolresultat
- Fortsetzung der Modellgenerierung
- Timeout
- Abbruch
- Audit
- idempotente Ausführung
- sichere Fehlerbehandlung

## Strukturierte Ausgaben

Spätere Funktionen:

- JSON-Schema-Ausgaben
- Formularantworten
- Tabellen
- Aktionsvorschläge
- validierte Datenobjekte
- providerunabhängige strukturierte Ergebnisse

---

## Phase 6 – Dokumentation und Benutzerhandbuch

### Status: begonnen

Die Dokumentation wird Bestandteil der Anwendung.

## Internes Wiki

Geplant beziehungsweise vorbereitet:

- Dokumentationsbutton im Header
- großes modales Dokumentationsfenster
- Navigation
- Suche
- Benutzerhandbuch
- Entwicklerdokumentation
- sichere Markdown-Darstellung
- Dark Mode
- responsive Oberfläche
- Tastaturbedienung
- kontrollierte Backend-Dokumentregistry

## Benutzerhandbuch

Vorgesehene Inhalte:

- Erste Schritte
- Anwendung starten
- Chat verwenden
- Hierarchie verwenden
- Provider wählen
- Modell wählen
- Tools verwenden
- Einstellungen verwalten
- Dokumentation öffnen
- Fehlerbehebung
- Ollama prüfen
- logische und providerinterne Modellnamen unterscheiden

## Entwicklerhandbuch

Vorgesehene Inhalte:

- Architektur
- Contracts
- Bootstrap
- Config-System
- Model Registry
- Tool Registry
- Provider
- Chatpipeline
- SSE
- SchemaRenderer
- Hierarchie
- Sicherheitsgrenzen
- Testing
- Deployment
- Migrationen

---

## Phase 7 – Intranetbetrieb

### Status: geplant

Nach Stabilisierung des lokalen MVP folgt ein kontrollierter Intranetbetrieb.

## Ziele (2)

- verpflichtende Authentifizierung
- Benutzerverwaltung oder vertrauenswürdige Identitätsquelle
- Session- oder Reverse-Proxy-Authentifizierung
- rollen- und objektbezogene Berechtigungen
- Audit-Logging
- PostgreSQL-Option
- Multi-Worker-Kompatibilität
- zentrale Logs
- sichere Cookies
- CORS-Regeln
- Backupkonzept

## Berechtigungen

Geplante Ebenen:

- systemweit
- Arbeitsbereich
- Projekt
- Hierarchieknoten
- Chat
- Modell
- Tool
- Konfiguration
- Administration

Die UI zeigt verfügbare Aktionen an, aber die endgültige Entscheidung bleibt immer beim Backend.

---

## Phase 8 – Internetbetrieb

### Status: langfristig geplant

Der Internetbetrieb erfordert ein deutlich strengeres Sicherheitsprofil.

## Geplante Mindestanforderungen

- HTTPS
- sichere Sessionauthentifizierung
- CSRF-Schutz
- sichere Cookies
- Rate Limiting
- Login-Schutz
- Sessionablauf
- zentrale Secretverwaltung
- Security-Header
- streng kontrollierte Origins
- Audit
- revisionsgeschützte Administration
- Uploadprüfung
- begrenzte Requestgrößen
- Provider- und Tool-Allowlisting
- sichere Fehlerantworten

## Sicherheitsprinzip

Das Internetprofil darf nicht durch Datenbankkonfiguration auf ein unsicheres Niveau abgesenkt werden.

Beispiele:

- HTTPS darf nicht dynamisch abgeschaltet werden.
- Sessionauthentifizierung darf nicht durch `auth_mode=none` ersetzt werden.
- Rate Limiting darf nicht unter die Sicherheitsuntergrenze fallen.
- unsichere CORS-Konfigurationen dürfen den Start verhindern.

---

## Phase 9 – Persistenz und Zusammenarbeit

### Status: später

Nach einem stabilen Einzelbenutzer- und Intranetbetrieb folgen kollaborative Funktionen.

## Geplante Funktionen

- persistente Konversationen
- gemeinsame Arbeitsbereiche
- Projektzuordnung
- Benutzergruppen
- Eigentümer
- Teilnehmer
- geteilte Chats
- Aktivitätsfeed
- Kommentare
- Änderungsverlauf
- Benachrichtigungen
- Vorlagen
- gemeinsame Promptbibliothek
- gemeinsame Toolfreigaben

## Hierarchische Zusammenarbeit

Die generische Hierarchie dient dabei als Grundlage für:

- Mandanten
- Organisationen
- Benutzer
- Arbeitsbereiche
- Projekte
- Vorgänge
- Chats
- Dokumente
- kundenspezifische Knotentypen

Neue fachliche Ebenen sollen weiterhin ohne neue hart codierte React-Komponente möglich sein.

---

## Phase 10 – Retrieval und Dokumentintelligenz

### Status: nicht Teil des aktuellen MVP

Geplante spätere Funktionen:

- Dateiupload
- Text- und PDF-Extraktion
- Metadaten
- Chunking
- Embeddings
- lokale Vektorsuche
- Quellenanzeige
- Berechtigungsvererbung
- Dokumentzuordnung zur Hierarchie
- Aktualisierung und Löschung
- Indexrevisionen
- RAG-Diagnose
- dokumentbasierte Chats

Die Retrieval-Schicht soll dieselben Sicherheits- und Hierarchiegrenzen verwenden wie die übrige Anwendung.

---

## Phase 11 – Multimodale und sprachbasierte Funktionen

### Status: langfristig

Mögliche Funktionen:

- Bilder im Chat
- visuelle Dokumentanalyse
- Bildgenerierung
- Spracheingabe
- Speech-to-Text
- Text-to-Speech
- Audioanhänge
- Kamera- und Scanverarbeitung
- OCR
- multimodale Provider
- lokaler Offlinebetrieb

Lokale Modelle und externe Dienste sollen über denselben stabilen Modellvertrag angebunden werden.

---

## Phase 12 – Workflows und Automatisierung

### Status: langfristig

Erst nach stabilen Modell-, Tool-, Berechtigungs- und Auditverträgen werden komplexere Automatisierungen ergänzt.

## Geplante Funktionen (2)

- definierte Workflows
- Trigger
- zeitgesteuerte Abläufe
- Toolketten
- Freigabeschritte
- Benachrichtigungen
- Wiederholungen
- Fehlerbehandlung
- Status
- Audit
- Vorlagen
- rollenbasierte Freigabe

## Sicherheitsgrenze

Keine autonome Aktion darf allein deshalb ausgeführt werden, weil ein Modell sie vorgeschlagen hat.

Jede relevante Aktion bleibt:

- registriert
- validiert
- autorisiert
- gegebenenfalls bestätigt
- auditiert

---

## Phase 13 – Plugin- und Erweiterungssystem

### Status: Grundlagen vorhanden, Ausbau später

Modelle und Tools verwenden bereits Manifest- und Registry-Grundlagen.

## Geplante Erweiterungen

- Plugin-Deskriptoren
- Versionen
- Abhängigkeiten
- Lifecycle
- Diagnose
- Health-Status
- Aktivierung
- Deaktivierung
- signierte Manifeste
- vertrauenswürdige Quellen
- Kompatibilitätsprüfung
- Updatefähigkeit

## Nicht vorgesehen

Auch langfristig nicht automatisch erlaubt:

- beliebiger Python-Code aus unkontrollierten Verzeichnissen
- Remote-Code-Ausführung über Manifestfelder
- automatische Freigabe erkannter Plugins
- unkontrollierte Frontend-Komponenten
- direkte Imports aus Backendstrings

Ein Marktplatz oder Remote-Plugin-System wird erst geprüft, wenn Signierung, Berechtigungen, Sandboxing und Updateprozesse stabil gelöst sind.

---

## Phase 14 – Enterprise und Skalierung

### Status: langfristig

## Datenbank

- PostgreSQL
- größere Datenmengen
- Connection Pooling
- Migrationen
- Sicherungen
- Restore
- Replikation

## Multi-Worker

- revisionsbasierte Cache-Invalidierung
- verteilte Sperren
- zentrale Eventverteilung
- Registry-Synchronisierung
- Sessionkonsistenz
- Hintergrundjobs

## Hochverfügbarkeit

- mehrere Instanzen
- Load Balancer
- Health Checks
- Readiness
- Graceful Shutdown
- Rolling Updates
- Disaster Recovery

## Observability

- Metriken
- strukturierte Logs
- Tracing
- Fehlerquoten
- Modelllatenzen
- Toollatenzen
- Tokenverbrauch
- Kapazitätsplanung
- Alarmierung

## Enterprise-Authentifizierung

- OIDC
- SAML über geeignete Infrastruktur
- Verzeichnisdienste
- Gruppenmapping
- Richtlinien
- MFA
- Sessionverwaltung
- zentrale Abmeldung

---

## Frontend-Roadmap

Die Frontend-Entwicklung konzentriert sich auf eine generische, barrierearme und schema-gesteuerte Anwendung.

## Kurzfristig

- Settings-Renderer
- ProviderSelect
- abhängiger ModelSelect
- vollständiger SchemaRenderer
- Unsupported-Komponenten
- Hierarchie-Kontextmenü
- Wiki-Popup
- bessere Lade- und Fehlerzustände
- zentrale Laufzeitvalidierung
- Bootstrap-zentrierter Ladefluss

## Mittelfristig

- Hierarchieeditor
- Prompteditor
- Modelladministration
- Tooladministration
- Audit-Viewer
- Revisionsanzeige
- mehrere Chats
- Chatverlauf
- responsive Optimierung
- Tastaturbedienung
- Accessibility

## Langfristig

- konfigurierbare Dashboards
- Widget-System
- personalisierte Arbeitsbereiche
- kollaborative Ansichten
- Benachrichtigungszentrum
- visuelle Workflowdarstellung
- multimodale Oberflächen

---

## Backend-Roadmap

## Kurzfristig (2)

- Config-API vervollständigen
- Batch-Updates
- Provider-Endpunkt
- Provider-Modell-Validierung
- Hierarchiemutationen
- Fehlerverträge vereinheitlichen
- Bootstrap- und OpenAPI-Tests
- Providerdiagnose
- Registry-Health

## Mittelfristig (2)

- Chatpersistenz
- Prompt-Resolver
- Tool-Orchestrierung
- Audit-Log
- objektbezogene Autorisierung
- PostgreSQL-Unterstützung
- Multi-Worker-Invalidierung
- Hintergrundaufgaben

## Langfristig (2)

- Workflow Engine
- Notification Framework
- Policy Engine
- verteilte Laufzeitdienste
- Skalierung
- hochverfügbare Provideranbindung

---

## KI-Roadmap

## Aktuell

- lokaler Ollama-Chat
- Streaming
- Modellregistrierung
- Providerabstraktion
- Usage-Daten
- Modell- und Capability-Metadaten

## Nächste Schritte

- Providerwahl
- Modellwahl
- Capability-Prüfung
- Tool Calling
- Reasoning-Ereignisse
- strukturierte Ausgaben
- Prompt-Vererbung
- Persistenz
- Modellhealth
- Timeouts und Abbruch

## Später

- Modellrouting
- Fallbackmodelle
- Lastverteilung
- Kosten- und Latenzregeln
- multimodale Modelle
- Embeddings
- Retrieval
- Sprache
- lokale und externe Providerkombinationen

---

## Konfigurations-Roadmap

## Aktuell (2)

- versionierte Definitionen
- JSON-Schema-Validierung
- Scopes
- Merge-Strategien
- UI-Metadaten
- Berechtigungen
- Revisionen
- Runtime-Editierbarkeit

## Nächste Schritte (2)

- vollständige API-Ausgabe
- schema-gesteuertes Frontend
- dynamische Auswahlquellen
- Abhängigkeiten zwischen Feldern
- Provider-/Modellkopplung
- Batch-Updates
- atomare Validierung
- Audit

## Später (2)

- Vergleichsansicht
- Rollback
- Vorlagen
- Export und Import
- staged activation
- geplante Aktivierung
- Umgebungsoverrides
- Konfigurationsanalyse

---

## Sicherheits-Roadmap

## Kurzfristig (3)

- Development-Fallback eindeutig kennzeichnen
- strukturierte Autorisierungsfehler
- zentrale Request-ID
- Config-Berechtigungen
- Hierarchie-Berechtigungen
- Modell- und Toolprüfung
- Secret-Ausgabe verhindern

## Mittelfristig (3)

- Intranet-Authentifizierung
- Sessions
- Audit
- objektbezogene Berechtigungen
- CSRF-Vorbereitung
- sichere Cookies
- Rate Limiting

## Langfristig (3)

- MFA
- OIDC
- Policy Engine
- Zero-Trust-Betrieb
- Secret Rotation
- Hardware-Credentials
- erweiterte Audits
- Compliance-Berichte

---

## Deployment-Roadmap

## Aktueller MVP

- lokaler Windows-Betrieb
- Start über PowerShell
- kein Docker erforderlich
- SQLite
- Vite Development Server
- Uvicorn

## Intranet

- Reverse Proxy
- HTTPS im internen Netz
- PostgreSQL optional
- zentraler Prozessbetrieb
- Logs
- Sicherungen
- Authentifizierung
- Updates

## Internet

- gehärteter Reverse Proxy
- HTTPS
- sichere Sessions
- Rate Limiting
- zentralisierte Secrets
- Monitoring
- Backup und Recovery
- Updateprozess
- Sicherheitsprüfungen

## Später (3)

- containerisierte Bereitstellung
- automatisierte Releases
- Infrastrukturvorlagen
- Rolling Updates
- Clusterbetrieb

Docker bleibt außerhalb des ersten MVP und wird erst eingeführt, wenn die lokale Architektur stabil ist.

---

## Dokumentations-Roadmap

Dokumentation wird parallel zur Implementierung gepflegt.

## Kurzfristig (4)

- TODO und Roadmap synchronisieren
- Benutzerhandbuch
- Chatdokumentation
- Provider- und Modelldokumentation
- Settings-Dokumentation
- Hierarchiedokumentation
- Fehlerbehebung
- internes Wiki-Popup

## Mittelfristig (4)

- Administratorhandbuch
- Entwicklerleitfaden
- API-Beispiele
- Prompt-Vererbung
- Toolentwicklung
- Modellmanifest
- Toolmanifest
- Migrationen
- Deployment-Handbuch

## Langfristig (4)

- Plugin-Autorenhandbuch
- Betriebskochbuch
- Security-Handbuch
- Enterprise-Betrieb
- Architekturdiagramme
- Upgrade- und Rollbackanleitungen

---

## Test- und Qualitäts-Roadmap

## Kurzfristig (5)

- Vertrags-Tests
- Provider-Tests
- SSE-Tests
- Config-Tests
- Provider-Modell-Abhängigkeit
- Frontend-Validatoren
- SchemaRenderer-Tests
- Integrationsstart

## Mittelfristig (5)

- End-to-End-Tests
- visuelle Regression
- Performance-Tests
- Datenbankmigrationen
- Intranet-Sicherheitsfälle
- Audit-Tests
- Tool-Orchestrierung

## Langfristig (5)

- Lasttests
- Failover
- Multi-Worker-Konsistenz
- Disaster-Recovery-Tests
- Internet-Härtung
- Kompatibilitätsmatrix
- automatisierte Deployment-Validierung

---

## Nicht Teil des aktuellen MVP

Folgende Punkte sind bewusst zurückgestellt:

- Docker
- öffentlicher Registrierungsprozess
- Multi-Agenten-System
- beliebiges Remote-Plugin-Loading
- vollständiges RAG
- Telefonie
- WhatsApp
- öffentliche Plugin-Plattform
- Clusterbetrieb
- Cloud-Native-Infrastruktur

Diese Funktionen dürfen die Stabilisierung der Kernarchitektur nicht verzögern.

---

## Erfolgskriterien

Die Roadmap ist erfolgreich, wenn Kernschmied schrittweise wächst und dabei folgende Eigenschaften bewahrt:

- stabile öffentliche Verträge
- deterministisches Verhalten
- sichere Autorisierung
- nachvollziehbare Änderungen
- providerunabhängige Fachlogik
- schema-gesteuerte Oberfläche
- wiederverwendbare Komponenten
- klare Sicherheitsgrenzen
- wartbare Module
- testbare Services
- dokumentierte Erweiterungspunkte
- gemeinsamer Start von Backend und Frontend
- keine ungeprüfte dynamische Codeausführung

---

## Übergang zum nächsten Meilenstein

Der nächste zentrale Meilenstein ist die **vollständig schema-gesteuerte Administration**.

Dazu gehören:

1. Providerliste
2. abhängige Modellauswahl
3. vollständige Config-Metadaten
4. atomare Config-Updates
5. Settings-Renderer
6. SchemaRenderer
7. bearbeitbare Hierarchie
8. internes Wiki
9. vollständige Tests
10. aktualisierte Dokumentation

Nach Abschluss dieses Meilensteins kann Kernschmied erstmals als konsistente lokale Administrations- und Chatplattform betrachtet werden.

---

## Verhältnis zur TODO-Liste

Die Roadmap beschreibt die strategische Entwicklungsrichtung.

Die [[TODO]]-Liste beschreibt:

- konkrete Dateien
- aktuelle Fehler
- technische Einzelaufgaben
- Prioritäten
- Tests
- unmittelbar nächste Schritte

```text
Roadmap = Wohin entwickelt sich Kernschmied?

TODO = Was wird als Nächstes konkret umgesetzt?

```

---

## Verwandte Dokumentation

## Entwicklung

- [[TODO]]
- [[Coding Guidelines]]
- [[Release Process]]
- [[Testing]]
- [[Development Environment]]

## Architektur

- [[Repository-Structure]]
- [[Extension-Points]]
- [[Manifest-System]]
- [[Registry-Architecture]]

## Konzepte

- [[Runtime Configuration]]
- [[Configuration Revisions]]
- [[Plugin-System]]
- [[Dynamic-UI]]
- [[Schema Versioning]]
- [[Prompt Inheritance]]

## Betrieb

- [[Development]]
- [[Intranet]]
- [[Internet]]

---

## Zusammenfassung

Kernschmied hat die erste technische Grundlage erreicht: Backend und Frontend starten gemeinsam, die zentralen Registry- und Config-Strukturen sind vorhanden und die lokale SSE-Chatpipeline funktioniert bis zum Ollama-Provider.

Die aktuelle Entwicklungsphase konzentriert sich auf die Konsolidierung der Verträge und die vollständige Administration. Im Mittelpunkt stehen die schema-gesteuerten Settings, die abhängige Provider- und Modellauswahl, der zentrale SchemaRenderer, die bearbeitbare Hierarchie und das integrierte Benutzerhandbuch.

Darauf aufbauend folgen Chatpersistenz, Tool-Orchestrierung, Promptverwaltung, Intranet-Authentifizierung und später ein gehärteter Internetbetrieb.

Das langfristige Ziel bleibt eine modulare, sichere und providerunabhängige KI-Plattform, die neue Fachbereiche, Modelle und Tools aufnehmen kann, ohne ihre grundlegende Architektur zu verändern.

Back to [[Home]].
