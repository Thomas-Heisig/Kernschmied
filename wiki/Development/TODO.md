# TODO – Kernschmied

## Stand: 01.08.2026

Diese Seite dokumentiert die konkreten technischen Arbeitspakete für Kernschmied.

Die langfristige strategische Entwicklung wird in der [[Roadmap]] beschrieben. Diese TODO-Liste konzentriert sich dagegen auf aktuelle Implementierungsaufgaben, technische Schulden, Tests, Dokumentation und die Konsolidierung der bestehenden Architektur.

Die Einträge stellen Entwicklungsziele dar und sind keine verbindlichen Zusagen für eine bestimmte Version.

---

## Statuslegende

- `[x]` umgesetzt und grundsätzlich funktionsfähig
- `[-]` begonnen oder teilweise umgesetzt
- `[ ]` offen
- `[!]` muss geprüft oder bewusst entschieden werden

---

## Leitprinzipien

Für alle Arbeiten gelten folgende Grundsätze:

- Architektur vor kurzfristigen Einzelmerkmalen
- stabile und versionierte Verträge
- kleine, überprüfbare Änderungen
- Backend und Frontend bleiben gemeinsam startbar
- Pydantic v2 an allen Backend-Systemgrenzen
- TypeScript-Verträge für alle öffentlichen API-Antworten
- keine automatische Freigabe durch dynamische Erkennung
- jede Benutzeraktion wird serverseitig autorisiert
- unbekannte Komponenten, Aktionen, Modelle und Tools werden sicher abgelehnt
- keine dynamischen Python- oder React-Imports aus Backenddaten
- keine Verwendung von `eval()` oder `Function()`
- Secrets niemals in fachlicher Konfiguration, API-Antworten oder Auditdetails ausgeben
- Tests und Dokumentation gehören zur Implementierung
- technische Schulden sichtbar halten und schrittweise abbauen

---

## Aktueller Projektstand

## Bereits funktionsfähig

- [x] FastAPI-Backend startet lokal.
- [x] React-/TypeScript-/Vite-Frontend startet lokal.
- [x] Gemeinsamer Entwicklungsstart über `start.ps1` ist vorhanden.
- [x] SQLite ist als Standarddatenbank eingebunden.
- [x] Bootstrap-Endpunkt ist vorhanden.
- [x] UI-Schema-Endpunkt ist vorhanden.
- [x] Hierarchie-Endpunkt ist vorhanden.
- [x] Modelllisten-Endpunkt ist vorhanden.
- [x] Toollisten-Endpunkt ist vorhanden.
- [x] Config-Listen- und Update-Endpunkte sind vorhanden.
- [x] SSE-Chat-Endpunkt ist vorhanden.
- [x] Development-Identity wird über die vorhandene Authentication-Middleware gesetzt.
- [x] Chat-Anfragen erhalten im Development-Profil den Benutzer `local-user`.
- [x] Die Chatpipeline erreicht den ausgewählten Modellprovider.
- [x] Ollama ist erreichbar und als Provider nutzbar.
- [x] Providerinterne Streamereignisse werden in öffentliche Chatereignisse übersetzt.
- [x] `Usage`-Objekte werden JSON-kompatibel verarbeitet.
- [x] Der Chat erzeugt wieder vollständige Modellantworten.
- [x] Modellfehler wie ein nicht vorhandener Ollama-Modellname können diagnostiziert werden.
- [x] Generischer rekursiver Hierarchiebaum ist vorhanden.
- [x] Theme-Umschaltung ist vorhanden.
- [x] Einstellungsdialog ist vorhanden.
- [x] Umfangreiche Config-Definitions-Registry ist vorhanden.
- [x] Config-Definitionen enthalten JSON-Schema, UI-Metadaten, Scopes, Berechtigungen und Sicherheitsinformationen.
- [x] OpenAPI dokumentiert die wichtigsten aktuellen Endpunkte.
- [x] Backend und Frontend besitzen zentrale Registry- und Contract-Grundlagen.

## Aktuell in Bearbeitung

- [-] Settings-API um vollständige Config-Definitionsmetadaten erweitern.
- [-] Settings-Frontend vollständig schema-gesteuert rendern.
- [-] Provider- und davon abhängige Modellauswahl in den Settings.
- [-] Providerliste aus den registrierten Modellen erzeugen.
- [-] Provider-Modell-Kombination serverseitig validieren.
- [-] Atomare Speicherung zusammengehöriger Konfigurationsänderungen.
- [-] Zentralen `SchemaRenderer` aus dem vorhandenen Platzhalter entwickeln.
- [-] Komponenten-Registry vervollständigen.
- [-] Internes Wiki und Benutzerhandbuch als Popup integrieren.
- [-] Hierarchieknoten im Frontend bearbeitbar machen.
- [-] Dokumentation an den tatsächlichen Projektstand anpassen.

---

## 1. Kritische Aufgaben

## 1.1 Konfigurationsverwaltung konsolidieren

### Backend

- [x] `ConfigDefinition` ist vorhanden.
- [x] Definitionen besitzen:

  - Gruppe und Schlüssel
  - Schema-Version
  - Anzeigename und Beschreibung
  - JSON-Schema
  - Standardwert
  - erlaubte Scopes
  - Merge-Strategie
  - Werttyp
  - Secret-Kennzeichnung
  - Restart-Anforderung
  - Runtime-Editierbarkeit
  - Berechtigungen
  - UI-Metadaten
  - Tags
  - Deprecation-Metadaten
  - Audit-Kennzeichnung

- [x] Globale Config-Definition-Registry ist vorhanden.
- [x] Doppelte Definitionen werden erkannt.
- [x] Ungültige `replaced_by`-Verweise werden erkannt.
- [x] Standardwerte werden gegen JSON-Schema validiert.
- [x] Merge-Strategien werden gegen den Schema-Typ geprüft.
- [x] Secret- und Scope-Regeln werden geprüft.
- [-] Öffentliche Config-API gibt derzeit noch nicht alle Definitionsmetadaten aus.
- [ ] `GET /api/v1/config` auf den erweiterten Config-Vertrag umstellen.
- [ ] Folgende Metadaten öffentlich und nicht sensibel ausgeben:

  - `full_key`
  - `display_name`
  - `description`
  - `schema_version`
  - `value_type`
  - `value_schema`
  - `default_value`
  - `requires_restart`
  - `runtime_editable`
  - `nullable`
  - `visibility`
  - `allowed_scopes`
  - `current_scope`
  - `ui`
  - `deprecated`
  - `deprecation_message`
  - `replaced_by`

- [ ] Sensitive Werte niemals als Klartext ausgeben.
- [ ] Für Secrets nur `secret_configured` ausgeben.
- [ ] Maskierungsstrings wie `********` nicht als speicherbaren Wert verwenden.
- [ ] `expected_revision` bei Änderungen verbindlich oder bewusst optional festlegen.
- [ ] Revisionskonflikte mit strukturiertem HTTP-409-Fehler beantworten.
- [ ] Config-Revision atomar erhöhen.
- [ ] Änderungen in einer Datenbanktransaktion speichern.
- [ ] Batch-Update für mehrere zusammengehörige Werte ergänzen.
- [ ] Fehlgeschlagene Validierung darf keine Teiländerung speichern.
- [ ] Audit-Log für jede erfolgreiche Config-Änderung schreiben.
- [ ] Secret-Werte nicht in Auditdaten aufnehmen.
- [ ] Auswirkungen auf Modell-, Tool- oder UI-Registry gezielt invalidieren.

### Frontend

- [-] `contracts/config.ts` ist vorhanden.
- [-] `SettingsField.tsx` ist vorhanden.
- [-] Einstellungswerte können bearbeitet und gespeichert werden.
- [ ] Frontend-Verträge auf den erweiterten Config-API-Vertrag bringen.
- [ ] `SettingsField` erhält den gesamten `ConfigEntry`.
- [ ] Eingabekomponente über `entry.ui.component` bestimmen.
- [ ] Werttyp nicht mehr ausschließlich über `typeof value` erraten.
- [ ] Unterstützte Komponenten:

  - `text`
  - `textarea`
  - `password`
  - `number`
  - `checkbox`
  - `select`
  - `multi_select`
  - `tags`
  - `json`
  - `url`
  - `provider_select`
  - `model_select`
  - `tool_select`
  - `node_select`
  - `hidden`

- [ ] Unbekannte Komponenten über `UnsupportedSetting` darstellen.
- [ ] Keine unbekannte Komponente automatisch als Textfeld behandeln.
- [ ] `placeholder`, `help_text`, `unit` und `description` anzeigen.
- [ ] `minimum`, `maximum`, `minLength` und `maxLength` aus dem Schema übernehmen.
- [ ] Lokale Validierungsfehler sichtbar darstellen.
- [ ] Ungültiges JSON nicht stillschweigend ignorieren.
- [ ] Nullable Zahlen- und Auswahlfelder unterstützen.
- [ ] Geänderte und gespeicherte Werte visuell unterscheiden.
- [ ] Reset auf gespeicherten Wert unterstützen.
- [ ] Reset auf Standardwert unterstützen.
- [ ] Ungespeicherte Änderungen vor Navigation schützen.
- [ ] Erweiterte Einstellungen ein- und ausblendbar machen.
- [ ] Einstellungen nach Kategorie, Abschnitt und Reihenfolge gruppieren.

---

## 1.2 Provider- und Modellauswahl

### Definitionen

- [x] `ConfigUIComponent.PROVIDER_SELECT` ergänzen.
- [x] `ConfigValueSource.PROVIDERS` ergänzen.
- [x] `ConfigDynamicOptions` um folgende Felder erweitert:

  - `depends_on`
  - `dependency_parameter`

- [ ] Abhängigkeitsfelder gemeinsam validieren.
- [ ] Selbstabhängigkeiten verhindern.
- [ ] Zukünftig zyklische Abhängigkeiten zwischen mehreren Definitionen erkennen.
- [x] `models.default_provider` als Config-Definition ergänzt.
- [x] `models.default_model` von `models.default_provider` abhängig gemacht und nullable gesetzt.
- [ ] Sicherstellen, dass der Standardwert eine logische Kernschmied-Modell-ID ist.
- [ ] Providerinterne Namen wie `qwen2.5-coder:7b` nicht direkt als Config-Modell-ID verwenden.

### Provider-API

- [x] `ProviderEntry` definiert.
- [x] `ProviderListResponse` definiert.
- [x] `GET /api/v1/models/providers` implementiert.
- [x] Provider werden aus registrierten Modellen aggregiert.
- [x] Anzahl registrierter Modelle je Provider ausgegeben (0 wenn leer).
- [x] Anzahl verfügbarer und auswählbarer Modelle ausgegeben.
- [x] Lesbare Provider-Anzeigenamen ausgegeben.
- [x] Keine Zugangsdaten oder internen Providerdetails werden ausgegeben.
- [x] Leere Registry mit `items=[]` beantwortet.
- [x] `Cache-Control: no-store, private` gesetzt.
- [x] Route `/providers` vor einer möglichen Route `/{model_id}` registriert.

### Frontend (2)

- [ ] Provider-Auswahl aus `/api/v1/models/providers` laden.
- [ ] Modelloptionen über `/api/v1/models?provider=<provider>` laden.
- [ ] `depends_on` und `dependency_parameter` aus dem Backendvertrag verwenden.
- [ ] Keine Abhängigkeit aus dem Feldnamen erraten.
- [ ] Ohne Provider keine Modellanfrage senden.
- [ ] Modellfeld sichtbar, aber deaktiviert darstellen.
- [ ] Hinweis anzeigen:

  - `Bitte zuerst einen Provider auswählen.`

- [ ] Bei Providerwechsel das Modell lokal auf `null` setzen.
- [ ] Laufende Modelllisten-Anfrage bei Providerwechsel abbrechen.
- [ ] Alte Antwort darf eine neuere Auswahl nicht überschreiben.
- [ ] Lade- und Fehlerzustände sichtbar darstellen.
- [ ] Nur erwartete API-Antwortstrukturen übernehmen.
- [ ] Dynamische Optionsendpunkte nur über kontrollierte interne API-Pfade laden.

### Serverseitige Validierung

- [ ] Modell existiert.
- [ ] Modell ist aktiviert.
- [ ] Modell ist verfügbar.
- [ ] Modell ist auswählbar.
- [ ] Modell unterstützt Chat.
- [ ] Modell gehört zum ausgewählten Provider.
- [ ] Fehlender Provider bei gesetztem Modell führt zu `PROVIDER_MISSING`.
- [ ] Unbekanntes Modell führt zu `MODEL_NOT_REGISTERED`.
- [ ] Falscher Provider führt zu `MODEL_PROVIDER_MISMATCH`.
- [ ] Nicht auswählbares Modell führt zu `MODEL_NOT_SELECTABLE`.
- [ ] Fehlende Chatfähigkeit führt zu `MODEL_NO_CHAT_CAPABILITY`.
- [ ] `default_model=null` bleibt erlaubt.
- [ ] Bei gemeinsamem Update den neuen Providerwert verwenden.
- [ ] Provider und Modell möglichst atomar speichern.
- [ ] Providerwechsel ohne Modellreset serverseitig ablehnen oder bewusst automatisch bereinigen.
- [ ] Automatische Bereinigung nur mit dokumentiertem Vertrag und Audit-Eintrag.

---

## 1.3 Chatpipeline

### Aktueller Stand

- [x] `POST /api/v1/chat/stream` ist erreichbar.
- [x] CORS-Preflight funktioniert.
- [x] SSE-Stream wird mit HTTP 200 geöffnet.
- [x] Development-Identity wird erkannt.
- [x] Autorisierung erhält `user_id="local-user"`.
- [x] ChatService ist registriert.
- [x] ModelService wird erreicht.
- [x] Ollama wird erreicht.
- [x] Falsche Modellnamen werden als Providerfehler erkannt.
- [x] Ein vorhandenes Ollama-Modell kann ausgewählt werden.
- [x] Provider-Streamereignisse werden verarbeitet.
- [x] `Usage` wird korrekt serialisiert.
- [x] Chatantworten werden wieder erzeugt.

### Noch offen

- [ ] Öffentlichen SSE-Vertrag final dokumentieren.
- [ ] Einheitlich `complete` statt paralleler Bezeichnungen wie `done` oder `end` verwenden.
- [ ] Übergangs-Aliase befristet dokumentieren.
- [ ] Ereignistypen verbindlich festlegen:

  - `start`
  - `token`
  - `message`
  - `reasoning`
  - `tool_call`
  - `tool_result`
  - `usage`
  - `complete`
  - `error`
  - `heartbeat`

- [ ] Payload jedes Ereignistyps dokumentieren.
- [ ] Doppelte Abschlussereignisse verhindern.
- [ ] Fehlendes Abschlussereignis als Protokollfehler behandeln.
- [ ] Clientabbruch vollständig testen.
- [ ] Providerabbruch unterstützen, soweit der Provider dies ermöglicht.
- [ ] Toolabbruch vorbereiten.
- [ ] Heartbeats implementieren oder abschließend prüfen.
- [ ] Providerinterne Details nicht ungefiltert an den Client senden.
- [ ] Streamfehler auf stabile öffentliche Fehlercodes abbilden.
- [ ] Frontend-SSE-Parser in ein eigenes Modul auslagern.
- [ ] Mehrzeilige `data:`-Felder unterstützen.
- [ ] Kommentare und unbekannte SSE-Felder ignorieren.
- [ ] Unbekannte Ereignistypen sicher behandeln.
- [ ] Abbruch, Fehler und vollständigen Abschluss unterscheiden.
- [ ] Leere Assistentenantworten verständlich behandeln.
- [ ] Mehrfachsenden während eines laufenden Streams kontrollieren.
- [ ] Aktiven Stream bei Wechsel von Chat oder Hierarchieknoten bewusst abbrechen oder weiterführen.

---

## 1.4 Hierarchieverwaltung

### Lesen und Anzeigen

- [x] `GET /api/v1/hierarchy` ist vorhanden.
- [x] Rekursiver generischer Baum ist vorhanden.
- [x] Knoten können ausgewählt werden.
- [x] Generische Knotentypen werden verwendet.
- [ ] Hierarchievertrag vollständig typisieren.
- [ ] `schema_version` als Pflichtfeld festlegen.
- [ ] Baumrevision vollständig anbinden.
- [ ] `request_id` konsistent behandeln.
- [ ] `children` immer als Array ausgeben.
- [ ] `actions` immer als Array ausgeben.
- [ ] `disabled` und `selectable` im Frontend korrekt auswerten.
- [ ] Nicht auswählbare Knoten weiterhin auf- und zuklappbar machen.
- [ ] Unbekannte Knotentypen mit sicherem Fallback darstellen.
- [ ] Doppelte IDs erkennen.
- [ ] Zyklen erkennen.
- [ ] Maximale Tiefe kontrollieren.
- [ ] Kindknoten deterministisch sortieren.
- [ ] Auswahl bei entfernten oder nicht mehr sichtbaren Knoten bereinigen.
- [ ] Expandierungszustand bei Reload möglichst erhalten.

### Bearbeiten

- [ ] Knoten hinzufügen.
- [ ] Knoten umbenennen.
- [ ] Knoten bearbeiten.
- [ ] Knoten verschieben.
- [ ] Knoten löschen.
- [ ] Sortierreihenfolge ändern.
- [ ] Kontextmenü über Kebab-Button bereitstellen.
- [ ] Berechtigungen pro Aktion serverseitig prüfen.
- [ ] Erlaubte Kindtypen serverseitig prüfen.
- [ ] Verschieben gegen Zyklen absichern.
- [ ] Löschen mit Bestätigung absichern.
- [ ] Optional rekursives Löschen bewusst entscheiden.
- [ ] Revision bei konkurrierenden Änderungen prüfen.
- [ ] Audit-Einträge für Mutationen schreiben.
- [ ] Mutationsergebnisse in den Baum übernehmen, ohne unnötigen Komplettreload.
- [ ] Hierarchieänderungen über generische Formulare abbilden.
- [ ] Keine fachlich fest verdrahteten Komponenten wie `ProjectNode` einführen.

---

## 2. UI-Schema und SchemaRenderer

## 2.1 Öffentlicher Vertrag

- [x] `GET /api/v1/ui/schema` ist vorhanden.
- [x] Transportantwort enthält:

  - `api_schema_version`
  - `ui_schema_version`
  - `config_revision`
  - `schema`
  - `request_id`

- [-] `UISchemaDocument` ist vorhanden.
- [-] Schema-Normalisierung unterstützt unterschiedliche Eingabeformen teilweise.
- [ ] Transportantwort und fachliches Dokument klar trennen.
- [ ] `api_schema_version`, `ui_schema_version` und Dokumentversion eindeutig unterscheiden.
- [ ] `minimum_client_version` ergänzen oder bewusst verwerfen.
- [ ] Komponenten, Aktionen, Knotentypen und Formulare eindeutig strukturieren.
- [ ] Keine dauerhaften konkurrierenden Schemaformen pflegen.
- [ ] Übergangsnormalisierung befristen.
- [ ] Komponenten-IDs auf Eindeutigkeit prüfen.
- [ ] Rekursionstiefe begrenzen.
- [ ] Maximale Komponentenanzahl begrenzen.
- [ ] Ungültige Schemaeinträge mit verständlichen Fehlern ablehnen.

## 2.2 Komponenten-Registry

- [-] Feste Komponenten-Registry ist vorgesehen.
- [-] Registry-Grundlagen sind vorhanden.
- [ ] `componentRegistry.tsx` finalisieren.
- [ ] Bekannte Typen explizit registrieren:

  - `text`
  - `heading`
  - `paragraph`
  - `alert`
  - `badge`
  - `button`
  - `stack`
  - `grid`
  - `section`
  - `card`
  - `divider`
  - `text_input`
  - `textarea`
  - `number_input`
  - `checkbox`
  - `select`
  - `multi_select`
  - `tags`
  - `json`
  - `tree`
  - `chat_view`
  - `message_list`
  - `chat_input`
  - `form`
  - `table`
  - `button_group`
  - `icon`
  - `prompt_editor`
  - `model_selector`
  - `tool_selector`
  - `file_upload`
  - `unsupported`

- [ ] Nicht implementierte bekannte Typen als „noch nicht verfügbar“ darstellen.
- [ ] Unbekannte Typen als „nicht unterstützt“ darstellen.
- [ ] Keine dynamischen React-Imports aus Backendwerten.
- [ ] Registryeinträge mit Prop-Validatoren verbinden.

## 2.3 SchemaRenderer

- [-] Datei `SchemaRenderer.tsx` ist vorhanden.
- [-] Aktuell existiert noch keine vollständige universelle Implementierung.
- [ ] Platzhalter zu einem kontrollierten rekursiven Renderer ausbauen.
- [ ] Vorgesehene Props stabilisieren:

  - `schema`
  - `value`
  - `disabled`
  - `readonly`
  - `context`
  - `onChange`
  - `onAction`

- [ ] Sichtbarkeit prüfen.
- [ ] Aktivierungszustand prüfen.
- [ ] Rekursive Kinder rendern.
- [ ] Formwerte kontrolliert verwalten.
- [ ] Aktionen nur über feste Action-Registry ausführen.
- [ ] Fehlergrenze pro Einzelkomponente ergänzen.
- [ ] Fehlerhafte Einzelkomponente darf nicht die gesamte App abstürzen lassen.
- [ ] Unbekannte Komponente über `UnsupportedSchemaComponent` darstellen.
- [ ] Development-Debuganzeige ohne Secrets ermöglichen.
- [ ] Renderzyklen und unnötige Neuberechnungen vermeiden.
- [ ] `SelectedNodePlaceholder` schrittweise ersetzen.
- [ ] Knotentyp `user` über den SchemaRenderer darstellen.
- [ ] Weitere Knotentypen anschließend migrieren.
- [ ] Schema-gesteuerte Darstellung darf niemals Autorisierung ersetzen.

## 2.4 Action-Registry

- [-] Feste Action-Registry ist vorgesehen.
- [ ] Aktionstyp und Aktionsinstanz klar trennen.
- [ ] Folgende Felder stabilisieren:

  - `id`
  - `type`
  - `label`
  - `icon`
  - `endpoint_key`
  - `method`
  - `required_permissions`
  - `confirmation_required`
  - `destructive`
  - `enabled`
  - `payload_schema`

- [ ] Direkte freie URLs möglichst durch `endpoint_key` ersetzen.
- [ ] Nur bekannte HTTP-Methoden zulassen.
- [ ] Endpunkte über Bootstrap auflösen.
- [ ] Backend-Schema darf keine neuen Handler registrieren.
- [ ] Unbekannte Aktionen sichtbar ablehnen.
- [ ] Destruktive Aktionen immer bestätigen.
- [ ] Jede Aktion serverseitig erneut autorisieren.

---

## 3. Bootstrap und Anwendungsladefluss

## 3.1 Backend

- [x] `GET /api/v1/bootstrap` ist vorhanden.
- [x] Bootstrap enthält:

  - Anwendung
  - Umgebung
  - Benutzer
  - Sicherheitsprofil
  - Capabilities
  - Features
  - Versionen
  - Endpunkte
  - Revisionen
  - Config-Revision
  - Request-ID

- [x] Bootstrap initialisiert zentrale Dienste.
- [x] Modell- und Tool-Registry sind eingebunden.
- [x] Development-Identity wird im Bootstrap-Kontext sichtbar.
- [x] Asynchroner `list_models()`-Aufruf im synchronen Registry-Zähler wurde als Fehler erkannt und bereinigt.
- [ ] Bootstrap-Antwort abschließend als stabilen Vertrag bestätigen.
- [ ] Dopplung von `application.environment` und oberem `environment` bewusst entscheiden.
- [ ] Nur nicht sensible Sicherheitsinformationen ausgeben.
- [ ] Keine Tokens, Secrets oder Session-IDs ausgeben.
- [ ] Endpointpfade aus dem konfigurierten API-Präfix erzeugen.
- [ ] Optionale und fatale Bootstrapfehler klar klassifizieren.
- [ ] Teilinitialisierte Zustände bei Fehlern bereinigen.
- [ ] Shutdown für Registries und Provider vervollständigen.
- [ ] Keine Initialisierung über versteckte globale Singletons.

## 3.2 Frontend

- [-] `AppProviders` ist vorhanden.
- [x] Anwendung startet zentral über `main.tsx`.
- [x] Root-Element wird geprüft.
- [ ] `contracts/bootstrap.ts` finalisieren.
- [ ] Bootstrap-Antwort zur Laufzeit validieren.
- [ ] Bootstrap vor allen fachlichen Ressourcen laden.
- [ ] Bootstrap im zentralen Anwendungskontext speichern.
- [ ] Fachliche Endpunkte aus `bootstrap.endpoints` verwenden.
- [ ] Versionsangaben aus `bootstrap.versions` verwenden.
- [ ] Capabilities und Features zentral auswerten.
- [ ] Benutzer- und Umgebungsinformationen zentral bereitstellen.
- [ ] Bei ungültigem Bootstrap keine Folgeanfragen starten.
- [ ] Unbekannte Endpointschlüssel nicht automatisch aktivieren.
- [ ] Entwicklungsfallbacks klar von produktiven Werten trennen.
- [ ] StrictMode-Doppelausführung berücksichtigen.

## 3.3 Endpoint-Auflösung

- [ ] API-Origin und API-Präfix eindeutig trennen.
- [ ] Bedeutung von `VITE_API_URL` dokumentieren.
- [ ] Zentralen Endpoint-Resolver implementieren.
- [ ] Relative und absolute interne Endpunkte kontrolliert unterstützen.
- [ ] Fremde Origins standardmäßig ablehnen.
- [ ] Same-Origin als Standard verwenden.
- [ ] Abweichende Origins nur über Infrastrukturkonfiguration zulassen.
- [ ] Doppelte Pfadteile verhindern.
- [ ] Endpointschlüssel und HTTP-Methode getrennt behandeln.

---

## 4. Modell- und Tool-Registries

## 4.1 Modell-Registry

- [x] Modell-Registry ist vorhanden.
- [x] Gemeinsame Modellbackend-Verträge sind vorhanden.
- [x] Provider-Verzeichnis ist vorhanden.
- [x] Ollama-Provider funktioniert grundsätzlich.
- [x] Modelllisten-Endpunkt ist vorhanden.
- [x] Modellfilter nach Provider ist vorgesehen.
- [x] Modellfilter nach Capability ist vorgesehen.
- [x] Providerfehler werden isoliert behandelt.
- [ ] `model.json` vollständig gegen das Manifest-Schema testen.
- [ ] Doppelte Modell-ID ablehnen.
- [ ] Ungültige Modell-ID ablehnen.
- [ ] Inkompatible Manifestversion ablehnen.
- [ ] Erkennung strikt von Aktivierung trennen.
- [ ] Keine Python-Importpfade aus Manifesten ausführen.
- [ ] Providerdiagnose ergänzen.
- [ ] Health-Checks ergänzen.
- [ ] Laufzeitstatus aktuell halten.
- [ ] Modellbenchmarking später vorbereiten.
- [ ] Logische Modell-ID und providerinternen Modellnamen klar dokumentieren.
- [ ] Mehrere Defaultmodelle als Fehler behandeln oder deterministisch auflösen.

## 4.2 Tool-Registry

- [x] Tool-Registry ist vorhanden.
- [x] Toollisten-Endpunkt ist vorhanden.
- [ ] `tool.json` vollständig validieren.
- [ ] Doppelte Tool-ID ablehnen.
- [ ] Ungültige IDs ablehnen.
- [ ] Fehler eines Tools isoliert behandeln.
- [ ] Tool-Erkennung von Freigabe trennen.
- [ ] Tool-Berechtigungen serverseitig prüfen.
- [ ] Tool-Kategorien ergänzen.
- [ ] Tool-Health-Checks ergänzen.
- [ ] Ausführungshistorie ergänzen.
- [ ] Nutzungsstatistik ergänzen.
- [ ] Bestätigungspflicht vollständig anbinden.
- [ ] Abbruch unterstützen.
- [ ] Toolresultate auf JSON-kompatible Werte begrenzen.
- [ ] Keine beliebigen Python-Module aus unkontrollierten Pfaden laden.

## 4.3 Frontend-Auswahl

- [-] Modell- und Toolinformationen können über API geladen werden.
- [ ] `ModelSelector` vollständig anbinden.
- [ ] Providerfilter integrieren.
- [ ] `ToolSelector` vollständig anbinden.
- [ ] Auswahl im zentralen State halten.
- [ ] Auswahl bei Registry-Revision validieren.
- [ ] Nicht mehr verfügbare Auswahl entfernen.
- [ ] Grund für nicht auswählbare Einträge anzeigen.
- [ ] Modell- und Toolauswahl an `ChatRequest` übergeben.
- [ ] Listung niemals als Berechtigungsentscheidung behandeln.

---

## 5. API-Client und Verträge

## 5.1 Zentraler API-Client

- [-] Zentraler API-Client ist vorhanden.
- [ ] Strukturierte Backendfehler zuverlässig erkennen.
- [ ] Fehlerklasse mit folgenden Feldern verwenden:

  - HTTP-Status
  - Fehlercode
  - Nachricht
  - Details
  - Request-ID

- [ ] FastAPI-`detail` nur befristet unterstützen.
- [ ] Request-ID aus Header und Body auslesen.
- [ ] Timeout und Abbruch unterscheiden.
- [ ] `AbortSignal` durchgängig unterstützen.
- [ ] `text/event-stream` nicht als JSON behandeln.
- [ ] Leere 204-/205-Antworten behandeln.
- [ ] Binäre Antworten vorbereiten.
- [ ] Datei-Uploads kontrolliert unterstützen.
- [ ] Credentials je Betriebsprofil setzen.
- [ ] CSRF-Unterstützung für spätere Sessionauthentifizierung vorbereiten.
- [ ] Sensitive Requestdaten nicht in Produktionslogs schreiben.

## 5.2 Typisierte API-Dienste

Zielstruktur:

```text
frontend/src/api/
├── client.ts
├── endpoints.ts
├── bootstrap.ts
├── schema.ts
├── hierarchy.ts
├── models.ts
├── tools.ts
├── chat.ts
├── config.ts
└── documentation.ts

```

- [ ] `loadBootstrap`
- [ ] `loadUISchema`
- [ ] `loadHierarchy`
- [ ] `loadModels`
- [ ] `loadProviders`
- [ ] `loadTools`
- [ ] `streamChat`
- [ ] `loadConfig`
- [ ] `updateConfig`
- [ ] `updateConfigBatch`
- [ ] `loadDocumentationIndex`
- [ ] `loadDocumentationPage`
- [ ] Alle Antworten vor Übernahme validieren.
- [ ] Keine ungeprüften `unknown`-Werte in den Store übernehmen.
- [ ] API-Funktionen unabhängig von React-Komponenten halten.

---

## 6. Strukturierte Fehler und Request-ID

- [x] Strukturierte Fehler mit `code`, `message`, `details` und `request_id` sind als Standard vorgesehen.
- [x] Chatfehler werden strukturiert im Stream ausgegeben.
- [-] Einige API-Endpunkte verwenden bereits strukturierte Fehler.
- [ ] Zentrales Fehler-Pydantic-Modell definieren oder finalisieren.
- [ ] Request-ID-Middleware prüfen und vervollständigen.
- [ ] `X-Request-ID` in allen Antworten setzen.
- [ ] Request-ID in allen Fehlerantworten ausgeben.
- [ ] FastAPI-Validierungsfehler zentral umwandeln.
- [ ] Starlette-HTTP-Fehler vereinheitlichen.
- [ ] Unbehandelte Exceptions zentral abfangen.
- [ ] Statuscodes konsistent verwenden:

  - `400` ungültige Anfrage
  - `401` nicht authentifiziert
  - `403` nicht autorisiert
  - `404` nicht gefunden
  - `409` Revision oder Zustandskonflikt
  - `422` Validierungsfehler
  - `429` Rate Limit
  - `500` interner Fehler
  - `503` Dienst nicht verfügbar

- [ ] Stacktraces nur serverseitig loggen.
- [ ] Keine internen oder sensitiven Details ausgeben.
- [ ] Fehlercodes zentral dokumentieren.

---

## 7. Authentifizierung und Autorisierung

## 7.1 Aktueller Stand

- [x] Authentication-Context-Middleware ist vorhanden.
- [x] Development-Fallback ist vorhanden.
- [x] Development-Fallback ist nur im Development-Profil aktivierbar.
- [x] `request.state.user` und `request.state.principal` werden gesetzt.
- [x] `UserContext.id` wird von der Chatautorisierung erkannt.
- [x] Development-User besitzt administrative Berechtigungen.
- [x] Chat erfordert eine Benutzer-ID.

## 7.2 Offene Aufgaben

- [ ] Development-Identität eindeutig in der UI kennzeichnen.
- [ ] Intranet-Authentifizierung implementieren.
- [ ] Internet-Sessionauthentifizierung implementieren.
- [ ] Sessionverwaltung ergänzen.
- [ ] Abmeldung ergänzen.
- [ ] Fine-grained Authorization vervollständigen.
- [ ] Objektbezogene Berechtigungen berücksichtigen.
- [ ] Jede Hierarchieaktion serverseitig autorisieren.
- [ ] Jede Modellwahl serverseitig autorisieren.
- [ ] Jede Toolwahl serverseitig autorisieren.
- [ ] Jeden Toolaufruf separat autorisieren.
- [ ] Config-Lesen und Config-Schreiben getrennt autorisieren.
- [ ] Administrative Endpunkte separat absichern.
- [ ] Unbekannte Aktion mit stabilem Fehlercode ablehnen.
- [ ] Bekannte, aber verbotene Aktion mit stabilem Fehlercode ablehnen.
- [ ] Keine Rechte allein aus UI-Schema, Capabilities oder Listen ableiten.

---

## 8. Betriebsprofile und Sicherheit

## Development

- [x] Vereinfachte lokale Identität ist möglich.
- [x] Development-Fallback kann konfiguriert werden.
- [ ] Development-spezifische Hinweise in UI und Logs ergänzen.
- [ ] Unsichere Development-Werte beim Wechsel in Intranet oder Internet ablehnen.

## Intranet

- [ ] Authentifizierung verpflichtend.
- [ ] Audit verpflichtend.
- [ ] Session- oder Reverse-Proxy-Modus unterstützen.
- [ ] Vertrauensgrenzen dokumentieren.
- [ ] CORS kontrollieren.
- [ ] Sichere Cookies konfigurieren.

## Internet

- [ ] HTTPS erzwingen.
- [ ] Sessionauthentifizierung erzwingen.
- [ ] Sichere Cookie-Einstellungen erzwingen.
- [ ] CSRF-Schutz ergänzen.
- [ ] Rate Limiting erzwingen.
- [ ] Strenge Sicherheitsuntergrenzen festlegen.
- [ ] Sicherheitsuntergrenzen nicht durch DB-Konfiguration abschaltbar machen.
- [ ] Unsichere Konfiguration beim Start ablehnen.
- [ ] Security-Header ergänzen.
- [ ] Reverse-Proxy-Betrieb dokumentieren.

## Frontend-Sicherheit

- [ ] Keine Backendwerte ungefiltert als HTML rendern.
- [ ] `dangerouslySetInnerHTML` für dynamische Inhalte vermeiden.
- [ ] Markdown ohne eingebettetes HTML rendern.
- [ ] Icons nur aus fester Registry laden.
- [ ] Aktionen nur aus fester Registry ausführen.
- [ ] URLs und Farben validieren.
- [ ] Keine Secrets oder Tokens in Local Storage speichern.
- [ ] Schema-Props nicht ungeprüft auf DOM-Elemente verteilen.
- [ ] Uploads nach Typ, Größe und Kontext validieren.

---

## 9. Dokumentation und internes Wiki

## Wiki-Popup

- [-] Konzept für Dokumentationsbutton im Header ist erstellt.
- [-] Patch für Backend-Dokumentations-API und Frontend-Dialog wurde vorbereitet.
- [ ] Patch in den aktuellen Projektstand integrieren.
- [ ] Header-Button mit `BookOpen` ergänzen.
- [ ] Dokumentationsdialog in `AppShell` verwalten.
- [ ] Navigation nach Dokumentationsbereichen anzeigen.
- [ ] Volltext- beziehungsweise Titelsuche ergänzen.
- [ ] Markdown sicher rendern.
- [ ] Kein eingebettetes HTML ausführen.
- [ ] Escape-Taste und Fokusmanagement ergänzen.
- [ ] Responsive Darstellung prüfen.
- [ ] Dark Mode prüfen.
- [ ] Dokumentpfade nur über feste Registry freigeben.
- [ ] Directory Traversal verhindern.
- [ ] Keine beliebigen Dateipfade aus Clientdaten öffnen.
- [ ] Optional Berechtigungen für interne Admin-Dokumentation ergänzen.

## Benutzerhandbuch

Neue beziehungsweise zu vervollständigende Seiten:

```text
wiki/User-Manual/Overview.md
wiki/User-Manual/Getting-Started.md
wiki/User-Manual/Chat.md
wiki/User-Manual/Models.md
wiki/User-Manual/Providers.md
wiki/User-Manual/Tools.md
wiki/User-Manual/Hierarchy.md
wiki/User-Manual/Settings.md
wiki/User-Manual/Documentation.md
wiki/User-Manual/Troubleshooting.md

```

- [ ] Erste Schritte dokumentieren.
- [ ] Development-Start dokumentieren.
- [ ] Chatbedienung dokumentieren.
- [ ] Provider- und Modellauswahl dokumentieren.
- [ ] Toolauswahl dokumentieren.
- [ ] Hierarchiebedienung dokumentieren.
- [ ] Einstellungen dokumentieren.
- [ ] Häufige Fehler dokumentieren.
- [ ] Ollama-Verbindung prüfen und dokumentieren.
- [ ] Unterschied zwischen logischer Modell-ID und Ollama-Modellname erklären.

## Entwicklerdokumentation

- [ ] Tatsächliche Modulpfade aktualisieren.
- [ ] Bootstrap-Ablauf dokumentieren.
- [ ] Chatpipeline dokumentieren.
- [ ] Provider-Streamvertrag dokumentieren.
- [ ] Config-Definitionen dokumentieren.
- [ ] Provider-Modell-Abhängigkeit dokumentieren.
- [ ] SchemaRenderer dokumentieren.
- [ ] Komponenten- und Action-Registry dokumentieren.
- [ ] Hierarchiemutationen dokumentieren.
- [ ] Fehlercodes dokumentieren.
- [ ] Revisionen und Cache-Invalidierung dokumentieren.
- [ ] Betriebsprofile dokumentieren.
- [ ] Sicherheitsuntergrenzen dokumentieren.
- [ ] OpenAPI nach Vertragsänderungen prüfen.
- [ ] README, TODO und Roadmap synchron halten.

---

## 10. Promptverwaltung

- [x] Prompt-Vererbung ist als Architekturprinzip vorgesehen.
- [x] Konfigurierbare Prompt-Ebenen sind in den Config-Definitionen abgebildet.
- [ ] Prompt-Resolver vollständig implementieren oder prüfen.
- [ ] Reihenfolge der Ebenen zentral auswerten.
- [ ] System-, Node-, Project-, Chat-, User- und Request-Prompt unterstützen.
- [ ] Prompteditor implementieren.
- [ ] Promptvorschau implementieren.
- [ ] Promptdiagnose implementieren.
- [ ] Effektiven Prompt anzeigen.
- [ ] Merge-Strategien nachvollziehbar darstellen.
- [ ] Promptversionen speichern.
- [ ] Prompt-Historie anzeigen.
- [ ] Berechtigungen serverseitig prüfen.
- [ ] Secrets und interne Systeminformationen nicht in Diagnoseansichten offenlegen.

---

## 11. Revisionen und Cache-Invalidierung

- [x] Config-Revision ist Teil der Architektur.
- [x] Bootstrap enthält Revisionsfelder.
- [ ] Config-Revision im Frontend vollständig speichern.
- [ ] Modell-Registry-Revision speichern.
- [ ] Tool-Registry-Revision speichern.
- [ ] Hierarchie-Revision speichern.
- [ ] UI-Schema-Revision ergänzen oder klar über Config-Revision ableiten.
- [ ] Regeln definieren, welche Revision welche Ressource invalidiert.
- [ ] Nach Config-Änderung nur betroffene Ressourcen neu laden.
- [ ] Keine unnötigen Komplettreloads.
- [ ] Mehrere Worker unterstützen.
- [ ] Datenbankgestützte oder andere Multi-Worker-Invalidierung vorbereiten.
- [ ] Optional `ETag` und `If-None-Match` prüfen.
- [ ] Polling nur verwenden, wenn keine bessere Benachrichtigung existiert.
- [ ] Pollingintervall konfigurierbar halten.
- [ ] Sichtbare UI bei Hintergrundreload nicht unnötig zurücksetzen.

---

## 12. Store und Ladezustände

- [-] Anwendung besitzt zentrale Provider-Struktur.
- [-] Knotenauswahl ist vorhanden.
- [ ] Zentralen Zustand ergänzen:

  - Bootstrap
  - UI-Schema
  - Hierarchie
  - Modelle
  - Provider
  - Tools
  - Config
  - Revisionen
  - ausgewählter Provider
  - ausgewähltes Modell
  - ausgewählte Tools
  - ausgewählter Knoten
  - expandierte Knoten
  - Ladezustände
  - Fehlerzustände

- [ ] Bootstrapfehler als fatal behandeln.
- [ ] Optionale Registryfehler als degradierte Funktion behandeln.
- [ ] Teilfehler getrennt darstellen.
- [ ] Modelle und Tools unabhängig neu laden.
- [ ] Chat-, Navigation- und Config-State trennen.
- [ ] Ältere Antworten dürfen neuere Daten nicht überschreiben.
- [ ] Bei Reload gültige Altdaten erhalten.
- [ ] Root nur auswählen, wenn auswählbar.
- [ ] Andernfalls ersten auswählbaren Knoten deterministisch wählen.
- [ ] StrictMode-sichere Initialisierung gewährleisten.

---

## 13. Testing

## 13.1 Bereits nachgewiesen

- [x] Backend startet.
- [x] Frontend startet.
- [x] Bootstrap antwortet.
- [x] UI-Schema antwortet.
- [x] Hierarchie antwortet.
- [x] Config antwortet.
- [x] Chat-POST antwortet mit SSE.
- [x] Development-Identity ist vorhanden.
- [x] Ollama-Version kann abgefragt werden.
- [x] Ollama-Modellliste kann abgefragt werden.
- [x] Nicht vorhandenes Modell erzeugt nachvollziehbaren Fehler.
- [x] Chatpipeline funktioniert nach Korrektur des Modells und der Usage-Verarbeitung.

## 13.2 Backend-Vertragstests

- [ ] Bootstrap gültig.
- [ ] Bootstrap enthält keine Secrets.
- [ ] Bootstrap bei optionalem Registryfehler.
- [ ] Bootstrap bei fatalem Startfehler.
- [ ] Hierarchievertrag gültig.
- [ ] Leere Hierarchie.
- [ ] Verschachtelte Hierarchie.
- [ ] Doppelte Knoten-ID.
- [ ] Zyklische Hierarchie.
- [ ] Ungültige Revision.
- [ ] UI-Schema mit ungültigem Eintrag.
- [ ] UI-Schema mit unbekannter Komponente.
- [ ] UI-Schema mit unbekannter Aktion.
- [ ] Doppelte Komponenten-ID.
- [ ] Modellliste.
- [ ] Providerliste.
- [ ] Toolliste.
- [ ] Vollständiger ChatRequest.
- [ ] Config-Update mit korrekter Revision.
- [ ] Config-Update mit Konflikt.
- [ ] Batch-Config-Update.
- [ ] Keine Teiländerung bei Validierungsfehler.
- [ ] Strukturierte Fehler für 404, 409, 422, 500 und 503.
- [ ] Request-ID im Header.
- [ ] Request-ID im Fehlerbody.
- [ ] OpenAPI referenziert korrekte Response-Modelle.

## 13.3 Provider- und Modelltests

- [ ] Leere Providerliste.
- [ ] Provideraggregation.
- [ ] Providerzählung.
- [ ] Deaktivierte Modelle ausblenden.
- [ ] `include_disabled=true`.
- [ ] Keine Secrets in Providerantwort.
- [ ] Gültiges Modellmanifest.
- [ ] Ungültiges Modellmanifest.
- [ ] Doppelte Modell-ID.
- [ ] Nicht erreichbarer Provider.
- [ ] Ollama-Modell nicht gefunden.
- [ ] Ollama-Timeout.
- [ ] Ollama-Stream normalisiert.
- [ ] Usage normalisiert.
- [ ] Provider und Modell passen.
- [ ] Provider fehlt.
- [ ] Modell unbekannt.
- [ ] Provider stimmt nicht.
- [ ] Modell deaktiviert.
- [ ] Modell nicht verfügbar.
- [ ] Modell nicht auswählbar.
- [ ] Modell ohne Chatfähigkeit.
- [ ] `default_model=null`.
- [ ] Provider und Modell gemeinsam geändert.
- [ ] Provider allein geändert bei inkompatiblem Modell.

## 13.4 Tooltests

- [ ] Gültiges Toolmanifest.
- [ ] Ungültiges Toolmanifest.
- [ ] Doppelte Tool-ID.
- [ ] Fehler eines Tools wird isoliert.
- [ ] Nicht autorisierter Toolaufruf.
- [ ] Bestätigungspflicht.
- [ ] Tooltimeout.
- [ ] Toolabbruch.
- [ ] Toolresultat ist JSON-kompatibel.
- [ ] Keine internen Implementierungsdetails in API-Antwort.

## 13.5 SSE-Tests

- [ ] Eventformatierung.
- [ ] `start`.
- [ ] Tokenstream.
- [ ] `message`.
- [ ] `reasoning`.
- [ ] `usage`.
- [ ] `tool_call`.
- [ ] `tool_result`.
- [ ] `complete`.
- [ ] Fehler nach Streamstart.
- [ ] Clientabbruch.
- [ ] Modellabbruch.
- [ ] Heartbeat.
- [ ] Mehrzeilige Daten.
- [ ] Request-ID im Stream.
- [ ] Keine internen Exceptiondetails.
- [ ] Genau ein Abschlussereignis.
- [ ] Unbekanntes Providerevent wird nicht ungeprüft weitergegeben.

## 13.6 Frontend-Unit-Tests

- [ ] Bootstrap-Validator.
- [ ] Hierarchie-Validator.
- [ ] UI-Schema-Validator.
- [ ] Modell-Validator.
- [ ] Provider-Validator.
- [ ] Tool-Validator.
- [ ] Config-Validator.
- [ ] SSE-Parser.
- [ ] Endpoint-Resolver.
- [ ] Fremde Origin wird abgelehnt.
- [ ] ComponentRegistry lehnt unbekannte Komponente ab.
- [ ] ActionRegistry lehnt unbekannte Aktion ab.
- [ ] GenericTree mit deaktiviertem Knoten.
- [ ] GenericTree mit nicht auswählbarem Knoten.
- [ ] SchemaRenderer mit unbekannter Komponente.
- [ ] SchemaRenderer mit fehlerhafter Einzelkomponente.
- [ ] SettingsField für alle bekannten Komponenten.
- [ ] ProviderSelect.
- [ ] ModelSelect mit Providerabhängigkeit.
- [ ] Providerwechsel setzt Modell zurück.
- [ ] Abgebrochene Anfrage ändert keinen State.
- [ ] ModelSelector.
- [ ] ToolSelector.
- [ ] Store bei Revisionswechsel.
- [ ] Alte Ladeantwort überschreibt neue nicht.

## 13.7 Integrationstests

- [ ] Bootstrap wird zuerst geladen.
- [ ] Danach UI-Schema und Hierarchie.
- [ ] Modelle und Tools nur bei Capability.
- [ ] App startet ohne optionale Registry degradiert.
- [ ] Root-Knoten wird dargestellt.
- [ ] Knotenauswahl öffnet schema-gesteuerte Ansicht.
- [ ] Knotentyp `user` wird über SchemaRenderer dargestellt.
- [ ] Provider werden geladen.
- [ ] Modellliste wird nach Provider gefiltert.
- [ ] Chat sendet Knoten-ID.
- [ ] Chat sendet Modell-ID.
- [ ] Chat sendet Tool-IDs.
- [ ] SSE wird inkrementell dargestellt.
- [ ] Config-Änderung löst gezielten Reload aus.
- [ ] Unbekannte Komponente wird sichtbar abgelehnt.
- [ ] Unbekannte Aktion wird nicht ausgeführt.
- [ ] Dokumentationsdialog lädt lokale Wiki-Seiten.
- [ ] Produktionsbuild ist erfolgreich.
- [ ] Backend und Frontend starten gemeinsam.
- [ ] StrictMode erzeugt keine dauerhaften Doppelrequests oder Doppelstreams.

---

## 14. Performance und Monitoring

## Performance

- [ ] Registryzugriffe optimieren.
- [ ] Config-Caching gezielt einsetzen.
- [ ] Hierarchie ohne N+1-Abfragen laden.
- [ ] Streaming-Pufferung prüfen.
- [ ] Speicherverbrauch profilieren.
- [ ] Große UI-Schemata profilieren.
- [ ] Große Hierarchien profilieren.
- [ ] Modelllisten cachen und revisionsbasiert invalidieren.
- [ ] Unnötige React-Neuberechnungen reduzieren.
- [ ] Lange Listen virtualisieren, wenn erforderlich.

## Monitoring

- [ ] Health-Live-Endpunkt.
- [ ] Health-Ready-Endpunkt.
- [ ] Providerstatus.
- [ ] Registrystatus.
- [ ] Config-Revision.
- [ ] Fehlerraten.
- [ ] Streamabbrüche.
- [ ] Modelllatenz.
- [ ] Toollatenz.
- [ ] Tokenverbrauch.
- [ ] Auditstatus.
- [ ] Metrik-Dashboard später ergänzen.
- [ ] Keine sensitiven Inhalte in Metriken speichern.

---

## 15. Plugin-System

- [x] Modell- und Toolmanifeste sind als Architekturgrundlage vorgesehen.
- [-] Registry-Grundlagen sind vorhanden.
- [ ] Plugin-Lifecycle definieren.
- [ ] Abhängigkeiten beschreiben.
- [ ] Plugin-Diagnose ergänzen.
- [ ] Manifestversionen prüfen.
- [ ] Signierte Manifeste untersuchen.
- [ ] Vertrauenswürdige Verzeichnisse festlegen.
- [ ] Remote-Plugin-Loading im MVP weiterhin nicht zulassen.
- [ ] Kein beliebiges Python-Modul aus Manifestdaten importieren.
- [ ] Sandboxing nur als zukünftiges Forschungsthema behandeln.
- [ ] Plugin-Entwicklerhandbuch erstellen.

---

## 16. Technische Schulden

Aktuell sichtbare technische Schulden:

- [-] Öffentliche API-Modelle befinden sich teilweise noch direkt in Routerdateien.
- [-] Frontend-Config-Vertrag bildet Backenddefinitionen noch nicht vollständig ab.
- [-] SettingsField errät Eingabetypen teilweise noch aus Laufzeitwerten.
- [-] SchemaRenderer ist noch nicht vollständig implementiert.
- [-] Teilweise bestehen Übergangs-Aliase bei Streamereignissen.
- [-] Einige Fehlerantworten verwenden noch FastAPI-Standardstrukturen.
- [-] Dokumentation und Code sind stellenweise nicht synchron.
- [-] Hierarchie ist bisher überwiegend lesend.
- [-] Config-Änderungen erfolgen noch nicht vollständig atomar als Batch.
- [-] Provider- und Modellauswahl sind noch nicht vollständig gekoppelt.
- [-] OpenAPI-`JsonValue` ist für TypeScript-Generatoren wenig aussagekräftig.
- [ ] Öffentliche Verträge aus Routerdateien in klar benannte Schema- oder Contract-Module verschieben.
- [ ] Doppelte oder veraltete Typen entfernen.
- [ ] Übergangscode nach erfolgreicher Migration entfernen.
- [ ] `type: ignore` nur mit dokumentierter Begründung verwenden.
- [ ] Pylance-, Ruff-, MyPy- und Pytest-Warnungen schrittweise auf null bringen.

---

## 17. Empfohlene nächste Arbeitspakete

## Priorität 1 – Provider und Modell in Settings

1. [ ] `PROVIDER_SELECT` und `PROVIDERS` ergänzen.
2. [ ] Abhängigkeitsfelder ergänzen.
3. [ ] Provider-Endpunkt implementieren.
4. [ ] Config-API-Mapping erweitern.
5. [ ] TypeScript-Verträge erweitern.
6. [ ] ProviderSelect implementieren.
7. [ ] abhängigen ModelSelect implementieren.
8. [ ] Provider-Modell-Kombination serverseitig validieren.
9. [ ] atomaren Batch-Update ergänzen.
10. [ ] Backend- und Frontendtests ergänzen.

## Priorität 2 – Settings-Renderer vervollständigen

1. [ ] vollständige Config-Metadaten ausgeben.
2. [ ] SettingsField auf `ui.component` umstellen.
3. [ ] Select-, Multi-Select-, Tags-, URL- und JSON-Felder ergänzen.
4. [ ] Schema-Grenzen in Eingaben übernehmen.
5. [ ] lokale Fehler anzeigen.
6. [ ] Kategorien und Abschnitte darstellen.
7. [ ] Advanced-Einstellungen einklappbar machen.
8. [ ] Reset und Dirty-State verbessern.

## Priorität 3 – SchemaRenderer

1. [ ] ComponentRegistry finalisieren.
2. [ ] Unsupported-Komponente erstellen oder vervollständigen.
3. [ ] rekursiven Renderer implementieren.
4. [ ] bekannte Layoutkomponenten ergänzen.
5. [ ] bekannte Formularfelder ergänzen.
6. [ ] Action-Registry anbinden.
7. [ ] Knotentyp `user` migrieren.
8. [ ] weitere Knotentypen migrieren.
9. [ ] Unit-Tests ergänzen.

## Priorität 4 – Hierarchie bearbeiten

1. [ ] Mutationsverträge definieren.
2. [ ] Backend-Endpunkte für Create, Update, Move und Delete.
3. [ ] Revisions- und Zyklusprüfung.
4. [ ] Autorisierung.
5. [ ] Audit.
6. [ ] Kontextmenü im Baum.
7. [ ] generische Dialoge.
8. [ ] optimistische oder gezielte Aktualisierung.
9. [ ] Tests.

## Priorität 5 – Dokumentationsdialog

1. [ ] vorhandenen Patch mit aktuellem Code abgleichen.
2. [ ] Backend-Dokumentationsrouter integrieren.
3. [ ] feste Dokumentregistry erstellen.
4. [ ] Header-Button ergänzen.
5. [ ] Dialog anbinden.
6. [ ] Benutzerhandbuch vervollständigen.
7. [ ] Responsive und barrierefreie Bedienung prüfen.
8. [ ] Dokumentationstest ergänzen.

---

## 18. MVP-Abnahmekriterien

Der aktuelle MVP gilt als konsistent, wenn:

- [x] Backend und Frontend lokal gemeinsam starten.
- [x] Bootstrap, UI-Schema, Hierarchie, Modelle, Tools und Config erreichbar sind.
- [x] Development-Identity funktioniert.
- [x] Chatpipeline erzeugt über einen registrierten Provider Antworten.
- [x] Provider-Streamereignisse werden normalisiert.
- [x] Usage-Daten verursachen keinen Serialisierungsfehler mehr.
- [ ] Frontend lädt den Bootstrap verbindlich zuerst.
- [ ] Fachliche Endpunkte werden aus dem Bootstrap bezogen.
- [ ] Öffentliche Verträge werden vor Store-Übernahme validiert.
- [ ] UI-Schema besitzt genau einen dokumentierten öffentlichen Vertrag.
- [ ] Hierarchie besitzt genau einen dokumentierten öffentlichen Vertrag.
- [ ] Unbekannte Komponenten werden sichtbar und sicher behandelt.
- [ ] Unbekannte Aktionen werden nicht ausgeführt.
- [ ] SchemaRenderer kann ausgewählte Knotenansichten darstellen.
- [ ] Provider können in den Settings ausgewählt werden.
- [ ] Modelle werden passend zum Provider gefiltert.
- [ ] Provider und Modell werden serverseitig gemeinsam validiert.
- [ ] Konfigurationsänderungen sind revisionsgeschützt.
- [ ] Zusammengehörige Config-Änderungen können atomar gespeichert werden.
- [ ] Hierarchieknoten können sicher hinzugefügt, bearbeitet, verschoben und gelöscht werden.
- [ ] Modell- und Toolauswahl werden an den Chat übertragen.
- [ ] SSE-Abschluss, Fehler und Abbruch werden sauber behandelt.
- [ ] Strukturierte Fehler inklusive Request-ID funktionieren.
- [ ] Betriebsprofile erzwingen ihre Sicherheitsuntergrenzen.
- [ ] Internes Wiki und Benutzerhandbuch sind aus dem Header erreichbar.
- [ ] Backendtests bestehen.
- [ ] Frontendtests bestehen.
- [ ] Produktionsbuild besteht.
- [ ] OpenAPI entspricht dem tatsächlichen Laufzeitverhalten.
- [ ] README, TODO, Roadmap und Wiki beschreiben denselben Projektstand.

---

## 19. Release-Vorbereitung

Vor jedem Release prüfen:

- [ ] Implementierung vollständig.
- [ ] Backendtests erfolgreich.
- [ ] Frontendtests erfolgreich.
- [ ] Produktionsbuild erfolgreich.
- [ ] Ruff erfolgreich.
- [ ] MyPy beziehungsweise Pylance ohne relevante Fehler.
- [ ] Bandit erfolgreich.
- [ ] npm audit geprüft.
- [ ] Markdownlint erfolgreich.
- [ ] Linkprüfung erfolgreich.
- [ ] OpenAPI-Diff geprüft.
- [ ] Schemas validiert.
- [ ] Manifeste validiert.
- [ ] Migrationen geprüft.
- [ ] Rollback geprüft.
- [ ] Dokumentation aktualisiert.
- [ ] Changelog aktualisiert.
- [ ] Release Notes erstellt.
- [ ] Gemeinsamer Start geprüft.
- [ ] Sicherheitsprofil geprüft.
- [ ] Keine Secrets im Repository.
- [ ] Keine Debug-Endpunkte unbeabsichtigt produktiv aktiv.

---

## 20. Zukünftige Themen

Diese Punkte gehören nicht zum aktuellen MVP.

## KI

- [ ] Multimodale Chats
- [ ] Bildverarbeitung
- [ ] Dokumentintelligenz
- [ ] Sprachsteuerung
- [ ] lokale STT-/TTS-Integration
- [ ] komplexe autonome Workflows
- [ ] Multi-Agenten-System erst nach stabiler Kernarchitektur

## Zusammenarbeit

- [ ] gemeinsame Arbeitsbereiche
- [ ] kollaborative Bearbeitung
- [ ] Aktivitätsfeed
- [ ] Teamrollen
- [ ] Organisationstemplates

## Enterprise

- [ ] PostgreSQL-Produktivbetrieb
- [ ] Multi-Worker-Betrieb
- [ ] Clusterbewusstsein
- [ ] verteilte Config-Invalidierung
- [ ] erweiterte Audits
- [ ] Policy Engine
- [ ] Mandantenverwaltung

## Ökosystem

- [ ] Plugin-Katalog
- [ ] Template-Repository
- [ ] gemeinsame Schema-Bibliotheken
- [ ] signierte Pakete
- [ ] Erweiterungsverwaltung

---

## Fortschrittsmodell

Arbeitspakete durchlaufen grundsätzlich folgende Zustände:

```text
Geplant

↓

In Bearbeitung

↓

Technisch umgesetzt

↓

Getestet

↓

Dokumentiert

↓

Abgeschlossen

```

Eine Implementierung gilt nicht allein deshalb als abgeschlossen, weil der Code vorhanden ist. Tests, Dokumentation, Sicherheitsprüfung und Integration gehören zum Abschluss.

---

## Verwandte Dokumentation

## Entwicklung

- [[Roadmap]]
- [[Coding Guidelines]]
- [[Release Process]]
- [[Testing]]

## Architektur

- [[Repository-Structure]]
- [[Extension-Points]]
- [[Manifest-System]]

## Konzepte

- [[Runtime Configuration]]
- [[Configuration Revisions]]
- [[Plugin-System]]
- [[Schema Versioning]]
- [[Dynamic-UI]]
- [[Prompt Inheritance]]

## Betrieb

- [[Development]]
- [[Intranet]]
- [[Internet]]

---

## Zusammenfassung

Kernschmied besitzt inzwischen eine funktionierende technische Basis mit Bootstrap, generischer Hierarchie, UI-Schema, Modell- und Tool-Registries, revisionsorientierter Konfiguration und einer funktionierenden SSE-Chatpipeline.

Der unmittelbar wichtigste nächste Entwicklungsschritt ist die vollständige schema-gesteuerte Konfigurationsoberfläche. Dazu gehören insbesondere die auswählbaren Modellprovider, die vom Provider abhängige Modellauswahl, die serverseitige Konsistenzprüfung und die atomare Speicherung zusammengehöriger Werte.

Danach folgen der vollständige `SchemaRenderer`, die bearbeitbare Hierarchie sowie das integrierte Wiki und Benutzerhandbuch.

Back to [[Home]].
