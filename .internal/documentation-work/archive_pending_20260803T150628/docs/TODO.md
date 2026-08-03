# Kernschmied – Complete Development Overview (Harmonisierte Fassung)

**Stand: 02.08.2026**

---

## Zusammenfassung

Kernschmied besitzt inzwischen eine funktionierende technische Basis mit Bootstrap, generischer Hierarchie, UI-Schema, Modell- und Tool-Registries, revisionsorientierter Konfiguration und einer funktionierenden SSE-Chatpipeline.

Der unmittelbar wichtigste nächste Entwicklungsschritt ist die **Laufzeitintegration der Chat-Persistenz**, insbesondere die Behebung der Datenbank-Migrationsinkonsistenz und die konsistente Anbindung der persistenten Hierarchie als gemeinsame Quelle für API und Chat.

Danach folgen die vollständige schema-gesteuerte Konfigurationsoberfläche, der vollständige `SchemaRenderer`, die bearbeitbare Hierarchie im Frontend sowie das integrierte Wiki und Benutzerhandbuch.

---

## Statuslegende

- `[x]` umgesetzt und grundsätzlich funktionsfähig
- `[-]` begonnen oder teilweise umgesetzt
- `[ ]` offen
- `[!]` muss geprüft oder bewusst entschieden werden
- `[~]` langfristig geplant

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

## Konsistenzkorrektur – Wichtigste Korrekturen

| Bereich | Widerspruch | Korrektur |
|---------|-------------|-----------|
| **Chat-Persistenz** | Unter "Kritische Blocker" nur "Begonnen", später Domainmodell, Migration und Repository komplett offen. Tatsächlich existieren Modelle, Migrationen, Repository, History-Endpunkt und Tests. | Auf `[-] weitgehend implementiert, Laufzeitintegration blockiert` setzen. |
| **Chatpipeline funktioniert** | Mehrfach als vollständig funktionsfähig markiert. Der aktuelle echte Lauf scheitert beim Conversation-Insert mit FK-Fehler. | Chatgenerierung `[x]`, persistenter Laufzeitpfad `[!]` oder `[-]`. |
| **Alembic / Datenbank** | Im Dokument fehlt der akute Fehler `0009_merge_branches` in der bestehenden Entwicklungsdatenbank. | Als höchsten Blocker ergänzen. |
| **Hierarchie-CRUD** | Oben steht "Create, Update, Move, Reorder, Delete implementiert". Unter "Hierarchie bearbeiten" sind alle Punkte offen. | Backend-CRUD `[x]`; Frontend-Bedienung und Integration `[-]/[ ]`. |
| **Persistente Hierarchie** | `/hierarchy` gilt als funktionsfähig, aber aktuell stammt `chat-1` offenbar aus In-Memory-Daten und fehlt in `hierarchy_nodes`. | Separate Aufgabe "persistente Hierarchie als einzige Laufzeitquelle" ergänzen. |
| **Config atomar** | Oben steht "Konfiguration atomar aktualisieren", später sind Batch-Update, Transaktion, keine Teiländerung und Revision noch offen. | Einzelupdate `[x]`; echtes transaktionales Batch-Update `[ ]`. |
| **Provider-Auswahl** | `PROVIDER_SELECT` und Provider-API sind schon `[x]`, in "Empfohlene Arbeitspakete" sollen sie erneut ergänzt/implementiert werden. | Erledigte Schritte entfernen; nur Frontend-Anbindung und Validierung offen lassen. |
| **Hierarchie als Priorität** | Hierarchie-Bearbeitung steht als kritischer Blocker, obwohl Backend-CRUD bereits implementiert ist. | Umbenennen in "Frontend-Hierarchieeditor und persistente Hierarchieanbindung". |
| **Health-Endpunkte** | Unter bestehenden APIs steht `GET /api/v1/health`. Bootstrap nennt jedoch `/health/live` und `/health/ready`. | Tatsächliche Endpunkte einmalig und korrekt dokumentieren. |
| **Dokumentation** | "Dokumentationsübersicht und -seite laden" ist `[x]`; Wiki-Popup sagt, Backend-Patch müsse erst integriert werden. | API `[x]`, Frontend-Popup `[-]`, Handbuch `[ ]`. |
| **Tests** | "Backendtests bestehen" bleibt im MVP offen, obwohl zuletzt 16/16 bestanden. Gleichzeitig fehlen neue E2E-Tests. | Unit-Suite `[x]`; persistenter SSE-E2E-Test `[ ]`. |
| **Conversation-Modell** | Unter Chat-Persistenz komplett offen, obwohl `Chat` faktisch die Conversation repräsentiert. | Entweder in `Conversation` umbenennen oder dokumentieren: `Chat = Conversation`. |
| **Message-Modell** | Als offen gelistet, obwohl `Message` mit Sequenz, Status und UI-Kontext existiert. | `[x]`, offene Zusatzfelder separat nennen. |
| **Migration** | Als offen gelistet, obwohl Migrationen bis `0008` existieren. | `[x] für frische DB`, `[!] für bestehende Entwicklungs-DB`. |
| **ChatRepository** | Als offen gelistet, obwohl Implementierung und Tests vorhanden sind. | `[x]`, Laufzeitadapterintegration `[-]`. |
| **History-Endpunkt** | In API-Inventar `[-]`, in Persistenz-Endpunkten komplett `[ ]`. | `GET /api/v1/chats/{id}/messages` auf `[x]` oder `[-]` setzen. |
| **Frontend-History** | Nicht prominent als aktueller Restpunkt geführt. | Als zentrale offene Aufgabe der Chat-Persistenz ergänzen. |
| **Monitoring** | Health Live/Ready sind offen, obwohl Logs und Bootstrap zeigen, dass sie vorhanden sind. | Endpunkte `[x]`; tiefere Readiness-Prüfung gegebenenfalls `[ ]`. |

---

## Kritische Blocker (Korrigierte Reihenfolge)

| Priorität | Aufgabe | Richtiger Status |
|-----------|---------|------------------|
| 🔴 **1** | Entwicklungsdatenbank auf gültigen Alembic-Stand bringen | Blockiert Laufzeit |
| 🔴 **2** | Persistente Hierarchie als gemeinsame Quelle für API und Chat verwenden | Blockiert Conversation-Insert |
| 🔴 **3** | Persistenten SSE-Chat inklusive Neustart nachweisen | Teilweise umgesetzt |
| 🔴 **4** | Frontend-History laden und Duplikate vermeiden | Offen |
| 🟠 **5** | Settings-v2 vollständig abschließen | In Arbeit |
| 🟠 **6** | Frontend-Hierarchieeditor anbinden | In Arbeit |
| 🟡 **7** | SchemaRenderer vervollständigen | Teilweise umgesetzt |

---

## Aktueller Projektstand

### Bereits funktionsfähig

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
- [x] Der Chat erzeugt wieder vollständige Modellantworten (technisch).
- [x] Modellfehler wie ein nicht vorhandener Ollama-Modellname können diagnostiziert werden.
- [x] Generischer rekursiver Hierarchiebaum ist vorhanden.
- [x] Theme-Umschaltung ist vorhanden.
- [x] Einstellungsdialog ist vorhanden.
- [x] Umfangreiche Config-Definitions-Registry ist vorhanden.
- [x] Config-Definitionen enthalten JSON-Schema, UI-Metadaten, Scopes, Berechtigungen und Sicherheitsinformationen.
- [x] OpenAPI dokumentiert die wichtigsten aktuellen Endpunkte.
- [x] Backend und Frontend besitzen zentrale Registry- und Contract-Grundlagen.
- [x] Hierarchie-CRUD (Create, Update, Move, Reorder, Delete) ist **backend-seitig** implementiert.
- [x] `GET /api/v1/models/providers` implementiert.
- [x] Kalenderauswahl und Kalender-CRUD.
- [x] Event-CRUD.
- [x] Dokumentationsübersicht und -seite laden (API).
- [x] Konfiguration einzeln aktualisieren.
- [x] `Chat`- und `Message`-Modelle vorhanden.
- [x] `ChatRepository` und Tests vorhanden.
- [x] Alembic-Migrationen bis Revision `0008` vorhanden (für frische DB).
- [x] Backend-Unit-Tests (16/16 bestehend).
- [x] `GET /health/live` und `GET /health/ready` vorhanden.

### Aktuell in Bearbeitung / Blockiert

- [-] Settings-API um vollständige Config-Definitionsmetadaten erweitern.
- [-] Settings-Frontend vollständig schema-gesteuert rendern.
- [-] Provider- und davon abhängige Modellauswahl in den Settings (Frontend-Anbindung).
- [-] Provider-Modell-Kombination serverseitig validieren.
- [-] Atomare Speicherung zusammengehöriger Konfigurationsänderungen (Batch-Update).
- [-] Grundlegender SchemaRenderer implementiert; Typisierung, Feldbindung, Sichtbarkeit, Fehlergrenzen und Action-Kontext noch offen.
- [-] Komponenten-Registry vervollständigen.
- [-] Internes Wiki und Benutzerhandbuch als Popup integrieren (Frontend-Popup fehlt).
- [-] Hierarchieknoten im Frontend bearbeitbar machen (Frontend-Editor fehlt).
- [-] Dokumentation an den tatsächlichen Projektstand anpassen.
- [-] SettingsField mit dynamischen Optionen (Provider/Model-Abhängigkeiten) in Arbeit.
- [-] Config-Schema 2.0: Migration und Frontend-Verträge in Arbeit.
- [!] **Chat-Persistenz**: Implementierung vorhanden, aber Laufzeitintegration blockiert durch:
  - Bestehende Entwicklungsdatenbank mit veralteter Revision `0009_merge_branches`
  - Fehlender persistenter Hierarchieknoten `chat-1` in `hierarchy_nodes`
- [-] **Persistente Hierarchie**: Backend-CRUD vorhanden, aber In-Memory-Hierarchie wird noch parallel als Laufzeitwahrheit verwendet.

---

## Review: Konfigurations-Definitionsänderungen (Settings-v2-Migration)

### Entfernt / Ersetzt

- `general.default_language` — entfernt; verwende stattdessen `identity.default_language`.
- `models.default_model_id` — entfernt; die Codebasis verwendet `models.default_model` als reichhaltigere und bevorzugte Definition.

### Umbenannt

- `planning.quality_check` → `planning.quality_check_enabled` (Name an Katalog angepasst).

### Lokal (nicht in CONFIG_DEFINITIONS)

- `appearance.density` bleibt eine `LOCAL_PREFERENCE`-Einstellung und ist deshalb bewusst nicht in `CONFIG_DEFINITIONS` aufgenommen.

### Offene Review-Punkte

1. Platzhalter-Definitionen: Viele konservative, generische Platzhalter wurden hinzugefügt, um das Fehlen von Keys im Katalog zu vermeiden. Bitte prüfen und ersetzen mit präzisen `value_schema`, `default_value`, `ui`-Metadaten und `permissions` — insbesondere für Gruppen: `knowledge`, `models`, `planning`, `tools`, `security`, `learning`.

2. `models.default_model` vs. `models.default_model_id`: Stelle sicher, dass alle Services (Model-Registry, Provider-Integration, Bootstrapping) die neue Namenswahl verwenden.

3. CI-Check: Füge `scripts/check_settings_defs.py` als CI-Job hinzu, damit Katalog und `CONFIG_DEFINITIONS` nicht wieder auseinanderlaufen.

4. Frontend-Save-Validation: Implementiere eine clientseitige Vorabprüfung, die verhindert, dass unbekannte/undefinierte Keys an `PUT /api/v1/config` gesendet werden.

### Referenzen

- Datei: `backend/app/config/definitions.py`
- Katalog: `backend/app/services/settings_catalog.py`
- Checker: `scripts/check_settings_defs.py`

---

## 1. Kritische Aufgaben

### Phase 0 – Datenbank und Hierarchie konsolidieren (JETZT)

- [x] Fehler identifiziert: `no such column: hierarchy_nodes.type`
- [ ] Entwicklungsdatenbank auf gültigen Alembic-Stand bringen
- [ ] Migration `0008_add_type_to_hierarchy_nodes` prüfen/erstellen
- [ ] Persistente Hierarchie als gemeinsame Quelle für API und Chat verwenden
- [ ] In-Memory-Hierarchie durch persistente ersetzen
- [ ] Development-Seed idempotent erstellen
- [ ] `GET /api/v1/hierarchy` und `ChatRepository` nutzen dieselbe Datenquelle

### 1.1 Datenbank und Migrationen (Höchste Priorität)

- [!] Bestehende Entwicklungsdatenbank enthält veraltete Revision `0009_merge_branches`.
- [ ] Entwicklungsdatenbank sichern und mit gültigem Head `0008` neu erzeugen.
- [ ] Migrationen für neue Modelle (falls erforderlich) erstellen.
- [ ] SQLite und PostgreSQL unterstützen.
- [ ] Upgrade testen.
- [ ] Downgrade testen.
- [ ] Fremdschlüssel definieren.
- [ ] Löschverhalten bewusst festlegen.
- [ ] Indizes für häufige Filter ergänzen.
- [ ] Revisionen atomar speichern.
- [ ] Zeitstempel timezone-aware speichern.
- [ ] JSON-Felder validieren.
- [ ] Keine Secrets in normalen Configtabellen speichern.
- [ ] Seed-Daten versionieren.
- [ ] Migrationen in CI prüfen.

### 1.2 Persistente Hierarchie als einzige Laufzeitquelle

- [ ] In-Memory-Hierarchie nicht parallel zur persistenten Hierarchie als Laufzeitwahrheit verwenden.
- [ ] Development-Seed für `root`, `workspace-1`, `project-1`, `chat-1` idempotent persistieren.
- [ ] `/api/v1/hierarchy` und `ChatRepository` müssen dieselbe Datenquelle nutzen.
- [ ] Hierarchie-API auf dieselbe persistente Datenquelle wie Chat-Persistenz stellen.
- [ ] Prüfen, ob alle Hierarchie-Operationen tatsächlich auf der persistenten SQLAlchemy-Hierarchie arbeiten.
- [ ] Audit vollständig anbinden.
- [ ] Revisionskonflikte vollständig testen.
- [ ] Zyklus- und Kindtypprüfungen mit Tests absichern.

### 1.3 Chat-Persistenz – Realistischer Stand

#### Domainmodell

- [x] `Chat` als Conversation-Modell vorhanden.
- [x] `Message`-Modell vorhanden.
- [x] Rollen grundsätzlich unterstützt.
- [x] Zuordnung zum Hierarchieknoten vorhanden.
- [x] Deterministische Sequenznummer vorhanden.
- [x] Status `pending`, `complete`, `failed`, `cancelled` vorhanden.
- [x] Zeitstempel vorhanden.
- [x] UI-Kontext und Metadaten vorhanden.
- [x] Alembic-Migrationen bis Revision `0008` vorhanden.
- [!] Bestehende Entwicklungsdatenbank enthält veraltete Revision `0009_merge_branches`.
- [ ] Modell-ID explizit und strukturiert am Chat oder an Nachrichten speichern.
- [ ] Toolaufrufe und Toolresultate vollständig persistieren.
- [ ] Usage-Daten als eigener stabiler Vertrag speichern.

#### Repository und Service

- [x] `ChatRepository` vorhanden.
- [x] SQLAlchemy-Implementierung vorhanden.
- [x] Atomare Sequenzreservierung vorhanden.
- [x] Parallelität getestet.
- [x] Repository verwaltet kein eigenes Commit.
- [x] Statusübergänge getestet.
- [x] ChatService-Persistenztests vorhanden.
- [-] ChatService ist an den Laufzeitadapter angebunden.
- [!] Conversation-Erstellung scheitert derzeit bei fehlendem persistentem Hierarchieknoten.
- [ ] Client-Abbruch im echten SSE-Lauf nachweisen.
- [ ] Providerfehler im echten Persistenzpfad nachweisen.
- [ ] Toolereignisse speichern.
- [ ] Archivierung und Löschstrategie festlegen.

#### Endpunkte

- [-] `GET /api/v1/chats/{chat_id}/messages` vorhanden, API-Abdeckung vervollständigen.
- [ ] `GET /api/v1/chats`
- [ ] `POST /api/v1/chats`
- [ ] `GET /api/v1/chats/{chat_id}`
- [ ] `PATCH /api/v1/chats/{chat_id}`
- [ ] `DELETE /api/v1/chats/{chat_id}`
- [ ] Archivieren und Wiederherstellen.
- [ ] Cursor-Pagination der Chatliste.

#### Frontend

- [ ] Persistierten Verlauf beim Öffnen laden.
- [ ] SSE- und History-Nachrichten deduplizieren.
- [ ] Verlauf nach Reload wiederherstellen.
- [ ] Aktive Conversation speichern.
- [ ] Chatliste darstellen.
- [ ] Neue Conversation erstellen.
- [ ] Umbenennen, archivieren und löschen.

### 1.4 Config-API und Settings-Migration

#### Backend (Fortsetzung)

- [x] `ConfigDefinition` ist vorhanden.
- [x] Definitionen besitzen alle erforderlichen Metadaten.
- [x] Globale Config-Definition-Registry ist vorhanden.
- [x] Doppelte Definitionen werden erkannt.
- [x] Standardwerte werden gegen JSON-Schema validiert.
- [-] Öffentliche Config-API gibt derzeit noch nicht alle Definitionsmetadaten aus.
- [ ] `GET /api/v1/config` auf den erweiterten Config-Vertrag umstellen.
- [ ] Alle Metadaten öffentlich und nicht sensibel ausgeben (siehe vollständige Liste oben).
- [ ] Sensitive Werte niemals als Klartext ausgeben.
- [ ] Für Secrets nur `secret_configured` ausgeben.
- [ ] `expected_revision` bei Änderungen verbindlich oder bewusst optional festlegen.
- [ ] Revisionskonflikte mit strukturiertem HTTP-409-Fehler beantworten.
- [ ] Config-Revision atomar erhöhen.
- [ ] Änderungen in einer Datenbanktransaktion speichern.
- [ ] **Batch-Update für mehrere zusammengehörige Werte ergänzen** (Priorität).
- [ ] Fehlgeschlagene Validierung darf keine Teiländerung speichern.
- [ ] Audit-Log für jede erfolgreiche Config-Änderung schreiben.
- [ ] Secret-Werte nicht in Auditdaten aufnehmen.
- [ ] Auswirkungen auf Modell-, Tool- oder UI-Registry gezielt invalidieren.

#### Frontend (Fortsetzung)

- [x] `contracts/config.ts` ist vorhanden (teilweise).
- [x] `SettingsField.tsx` ist vorhanden (teilweise).
- [x] Einstellungswerte können bearbeitet und gespeichert werden.
- [ ] Frontend-Verträge auf den erweiterten Config-API-Vertrag bringen.
- [ ] `SettingsField` erhält den gesamten `ConfigEntry`.
- [ ] Eingabekomponente über `entry.ui.component` bestimmen.
- [ ] Werttyp nicht mehr ausschließlich über `typeof value` erraten.
- [ ] Unterstützte Komponenten: `text`, `textarea`, `password`, `number`, `checkbox`, `select`, `multi_select`, `tags`, `json`, `url`, `provider_select`, `model_select`, `tool_select`, `node_select`, `hidden`
- [ ] Unbekannte Komponenten über `UnsupportedSetting` darstellen.
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

### 1.5 Provider- und Modellauswahl (Frontend-Anbindung)

#### Bereits erledigt

- [x] `ConfigUIComponent.PROVIDER_SELECT` ergänzen.
- [x] `ConfigValueSource.PROVIDERS` ergänzen.
- [x] `ConfigDynamicOptions` um `depends_on` und `dependency_parameter` erweitert.
- [x] `models.default_provider` als Config-Definition ergänzt.
- [x] `models.default_model` von `models.default_provider` abhängig gemacht.
- [x] `ProviderEntry` und `ProviderListResponse` definiert.
- [x] `GET /api/v1/models/providers` implementiert.

#### Noch offen (Frontend)

- [ ] Provider-Auswahl aus `/api/v1/models/providers` laden.
- [ ] Modelloptionen über `/api/v1/models?provider=<provider>` laden.
- [ ] `depends_on` und `dependency_parameter` aus dem Backendvertrag verwenden.
- [ ] Ohne Provider keine Modellanfrage senden.
- [ ] Modellfeld sichtbar, aber deaktiviert darstellen.
- [ ] Bei Providerwechsel das Modell lokal auf `null` setzen.
- [ ] Laufende Modelllisten-Anfrage bei Providerwechsel abbrechen.
- [ ] Alte Antwort darf eine neuere Auswahl nicht überschreiben.
- [ ] Lade- und Fehlerzustände sichtbar darstellen.
- [ ] Nur erwartete API-Antwortstrukturen übernehmen.

#### Serverseitige Validierung (noch offen)

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

---

## 2. UI-Schema und SchemaRenderer

### 2.1 Öffentlicher Vertrag

- [x] `GET /api/v1/ui/schema` ist vorhanden.
- [x] Transportantwort enthält alle erforderlichen Felder.
- [-] `UISchemaDocument` ist vorhanden.
- [-] Schema-Normalisierung unterstützt unterschiedliche Eingabeformen teilweise.
- [ ] Transportantwort und fachliches Dokument klar trennen.
- [ ] `api_schema_version`, `ui_schema_version` und Dokumentversion eindeutig unterscheiden.
- [ ] `minimum_client_version` ergänzen oder bewusst verwerfen.
- [ ] Komponenten, Aktionen, Knotentypen und Formulare eindeutig strukturieren.
- [ ] Komponenten-IDs auf Eindeutigkeit prüfen.
- [ ] Rekursionstiefe begrenzen.
- [ ] Maximale Komponentenanzahl begrenzen.
- [ ] Ungültige Schemaeinträge mit verständlichen Fehlern ablehnen.

### 2.2 Komponenten-Registry

- [-] Feste Komponenten-Registry ist vorgesehen.
- [-] Registry-Grundlagen sind vorhanden.
- [ ] `componentRegistry.tsx` finalisieren.
- [ ] Bekannte Typen explizit registrieren (siehe vollständige Liste oben).
- [ ] Nicht implementierte bekannte Typen als "noch nicht verfügbar" darstellen.
- [ ] Unbekannte Typen als "nicht unterstützt" darstellen.
- [ ] Keine dynamischen React-Imports aus Backendwerten.
- [ ] Registryeinträge mit Prop-Validatoren verbinden.

### 2.3 SchemaRenderer

- [-] Datei `SchemaRenderer.tsx` ist vorhanden.
- [-] Grundlegender SchemaRenderer implementiert; Typisierung, Feldbindung, Sichtbarkeit, Fehlergrenzen und Action-Kontext noch offen.
- [ ] Vorgesehene Props stabilisieren.
- [ ] Sichtbarkeit prüfen.
- [ ] Aktivierungszustand prüfen.
- [ ] Rekursive Kinder rendern.
- [ ] Formwerte kontrolliert verwalten.
- [ ] Aktionen nur über feste Action-Registry ausführen.
- [ ] Fehlergrenze pro Einzelkomponente ergänzen.
- [ ] Unbekannte Komponente über `UnsupportedSchemaComponent` darstellen.
- [ ] Development-Debuganzeige ohne Secrets ermöglichen.
- [ ] Renderzyklen und unnötige Neuberechnungen vermeiden.
- [ ] `SelectedNodePlaceholder` schrittweise ersetzen.
- [ ] Knotentyp `user` über den SchemaRenderer darstellen.
- [ ] Weitere Knotentypen anschließend migrieren.

### 2.4 Action-Registry

- [-] Feste Action-Registry ist vorgesehen.
- [ ] Aktionstyp und Aktionsinstanz klar trennen.
- [ ] Folgende Felder stabilisieren: `id`, `type`, `label`, `icon`, `endpoint_key`, `method`, `required_permissions`, `confirmation_required`, `destructive`, `enabled`, `payload_schema`
- [ ] Direkte freie URLs möglichst durch `endpoint_key` ersetzen.
- [ ] Nur bekannte HTTP-Methoden zulassen.
- [ ] Endpunkte über Bootstrap auflösen.
- [ ] Backend-Schema darf keine neuen Handler registrieren.
- [ ] Unbekannte Aktionen sichtbar ablehnen.
- [ ] Destruktive Aktionen immer bestätigen.
- [ ] Jede Aktion serverseitig erneut autorisieren.

---

## 3. Bootstrap und Anwendungsladefluss

### 3.1 Backend

- [x] `GET /api/v1/bootstrap` ist vorhanden.
- [x] Bootstrap enthält alle erforderlichen Felder.
- [x] Bootstrap initialisiert zentrale Dienste.
- [x] Modell- und Tool-Registry sind eingebunden.
- [x] Development-Identity wird im Bootstrap-Kontext sichtbar.
- [ ] Bootstrap-Antwort abschließend als stabilen Vertrag bestätigen.
- [ ] Nur nicht sensible Sicherheitsinformationen ausgeben.
- [ ] Keine Tokens, Secrets oder Session-IDs ausgeben.
- [ ] Endpointpfade aus dem konfigurierten API-Präfix erzeugen.
- [ ] Optionale und fatale Bootstrapfehler klar klassifizieren.
- [ ] Teilinitialisierte Zustände bei Fehlern bereinigen.
- [ ] Shutdown für Registries und Provider vervollständigen.

### 3.2 Frontend

- [x] `AppProviders` ist vorhanden.
- [x] Anwendung startet zentral über `main.tsx`.
- [x] Root-Element wird geprüft.
- [ ] `contracts/bootstrap.ts` finalisieren.
- [ ] Bootstrap-Antwort zur Laufzeit validieren.
- [ ] Bootstrap vor allen fachlichen Ressourcen laden.
- [ ] Bootstrap im zentralen Anwendungskontext speichern.
- [ ] Fachliche Endpunkte aus `bootstrap.endpoints` verwenden.
- [ ] Versionsangaben aus `bootstrap.versions` verwenden.
- [ ] Capabilities und Features zentral auswerten.
- [ ] Bei ungültigem Bootstrap keine Folgeanfragen starten.
- [ ] Unbekannte Endpointschlüssel nicht automatisch aktivieren.

### 3.3 Endpoint-Auflösung

- [ ] API-Origin und API-Präfix eindeutig trennen.
- [ ] Bedeutung von `VITE_API_URL` dokumentieren.
- [ ] Zentralen Endpoint-Resolver implementieren.
- [ ] Relative und absolute interne Endpunkte kontrolliert unterstützen.
- [ ] Fremde Origins standardmäßig ablehnen.
- [ ] Same-Origin als Standard verwenden.
- [ ] Doppelte Pfadteile verhindern.
- [ ] Endpointschlüssel und HTTP-Methode getrennt behandeln.

---

## 4. Modell- und Tool-Registries

### 4.1 Modell-Registry

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
- [ ] Keine Python-Importpfade aus Manifesten ausführen.
- [ ] Providerdiagnose ergänzen.
- [ ] Health-Checks ergänzen.
- [ ] Laufzeitstatus aktuell halten.
- [ ] Logische Modell-ID und providerinternen Modellnamen klar dokumentieren.

### 4.2 Tool-Registry

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
- [ ] Bestätigungspflicht vollständig anbinden.
- [ ] Abbruch unterstützen.
- [ ] Toolresultate auf JSON-kompatible Werte begrenzen.

### 4.3 Frontend-Auswahl

- [-] Modell- und Toolinformationen können über API geladen werden.
- [ ] `ModelSelector` vollständig anbinden.
- [ ] Providerfilter integrieren.
- [ ] `ToolSelector` vollständig anbinden.
- [ ] Auswahl im zentralen State halten.
- [ ] Auswahl bei Registry-Revision validieren.
- [ ] Nicht mehr verfügbare Auswahl entfernen.
- [ ] Grund für nicht auswählbare Einträge anzeigen.
- [ ] Modell- und Toolauswahl an `ChatRequest` übergeben.

---

## 5. API-Client und Verträge

### 5.1 Zentraler API-Client

- [-] Zentraler API-Client ist vorhanden.
- [ ] Strukturierte Backendfehler zuverlässig erkennen.
- [ ] Fehlerklasse mit HTTP-Status, Fehlercode, Nachricht, Details, Request-ID.
- [ ] Request-ID aus Header und Body auslesen.
- [ ] Timeout und Abbruch unterscheiden.
- [ ] `AbortSignal` durchgängig unterstützen.
- [ ] `text/event-stream` nicht als JSON behandeln.
- [ ] Leere 204-/205-Antworten behandeln.
- [ ] Binäre Antworten vorbereiten.
- [ ] Datei-Uploads kontrolliert unterstützen.
- [ ] Credentials je Betriebsprofil setzen.

### 5.2 Typisierte API-Dienste

Zielstruktur:
```
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
- [ ] Statuscodes konsistent verwenden.
- [ ] Stacktraces nur serverseitig loggen.
- [ ] Keine internen oder sensitiven Details ausgeben.

---

## 7. Authentifizierung und Autorisierung

### 7.1 Aktueller Stand

- [x] Authentication-Context-Middleware ist vorhanden.
- [x] Development-Fallback ist vorhanden.
- [x] Development-Fallback ist nur im Development-Profil aktivierbar.
- [x] `request.state.user` und `request.state.principal` werden gesetzt.
- [x] `UserContext.id` wird von der Chatautorisierung erkannt.
- [x] Development-User besitzt administrative Berechtigungen.
- [x] Chat erfordert eine Benutzer-ID.

### 7.2 Offene Aufgaben

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

---

## 8. Betriebsprofile und Sicherheit

### Development

- [x] Vereinfachte lokale Identität ist möglich.
- [x] Development-Fallback kann konfiguriert werden.
- [ ] Development-spezifische Hinweise in UI und Logs ergänzen.
- [ ] Unsichere Development-Werte beim Wechsel in Intranet oder Internet ablehnen.

### Intranet

- [ ] Authentifizierung verpflichtend.
- [ ] Audit verpflichtend.
- [ ] Session- oder Reverse-Proxy-Modus unterstützen.
- [ ] Vertrauensgrenzen dokumentieren.
- [ ] CORS kontrollieren.
- [ ] Sichere Cookies konfigurieren.

### Internet

- [ ] HTTPS erzwingen.
- [ ] Sessionauthentifizierung erzwingen.
- [ ] Sichere Cookie-Einstellungen erzwingen.
- [ ] CSRF-Schutz ergänzen.
- [ ] Rate Limiting erzwingen.
- [ ] Strenge Sicherheitsuntergrenzen festlegen.
- [ ] Unsichere Konfiguration beim Start ablehnen.
- [ ] Security-Header ergänzen.
- [ ] Reverse-Proxy-Betrieb dokumentieren.

### Frontend-Sicherheit

- [ ] Keine Backendwerte ungefiltert als HTML rendern.
- [ ] `dangerouslySetInnerHTML` für dynamische Inhalte vermeiden.
- [ ] Markdown ohne eingebettetes HTML rendern.
- [ ] Icons nur aus fester Registry laden.
- [ ] Aktionen nur aus fester Registry ausführen.
- [ ] URLs und Farben validieren.
- [ ] Keine Secrets oder Tokens in Local Storage speichern.
- [ ] Uploads nach Typ, Größe und Kontext validieren.

---

## 9. Dokumentation und internes Wiki

### Wiki-Popup

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

### Benutzerhandbuch

Neue beziehungsweise zu vervollständigende Seiten:
```
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

### Entwicklerdokumentation

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

---

## 12. Store und Ladezustände

- [-] Anwendung besitzt zentrale Provider-Struktur.
- [-] Knotenauswahl ist vorhanden.
- [ ] Zentralen Zustand ergänzen: Bootstrap, UI-Schema, Hierarchie, Modelle, Provider, Tools, Config, Revisionen, ausgewählter Provider, ausgewähltes Modell, ausgewählte Tools, ausgewählter Knoten, expandierte Knoten, Ladezustände, Fehlerzustände
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

### 13.1 Bereits nachgewiesen

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
- [x] Chatpipeline funktioniert nach Korrektur des Modells und der Usage-Verarbeitung (technisch).
- [x] Backend-Unit-Tests (16/16 bestehend).

### 13.2 Backend-Vertragstests (Noch offen)

- [ ] Bootstrap gültig.
- [ ] Bootstrap enthält keine Secrets.
- [ ] Bootstrap bei optionalem Registryfehler.
- [ ] Hierarchievertrag gültig.
- [ ] Leere Hierarchie.
- [ ] Verschachtelte Hierarchie.
- [ ] Doppelte Knoten-ID.
- [ ] Zyklische Hierarchie.
- [ ] UI-Schema mit ungültigem Eintrag.
- [ ] UI-Schema mit unbekannter Komponente.
- [ ] Modellliste.
- [ ] Providerliste.
- [ ] Toolliste.
- [ ] Config-Update mit korrekter Revision.
- [ ] Config-Update mit Konflikt.
- [ ] Batch-Config-Update.
- [ ] Keine Teiländerung bei Validierungsfehler.
- [ ] Strukturierte Fehler für 404, 409, 422, 500 und 503.
- [ ] Request-ID im Header.
- [ ] Request-ID im Fehlerbody.
- [ ] OpenAPI referenziert korrekte Response-Modelle.

### 13.3 Provider- und Modelltests (Noch offen)

- [ ] Leere Providerliste.
- [ ] Deaktivierte Modelle ausblenden.
- [ ] `include_disabled=true`.
- [ ] Keine Secrets in Providerantwort.
- [ ] Gültiges Modellmanifest.
- [ ] Ungültiges Modellmanifest.
- [ ] Doppelte Modell-ID.
- [ ] Nicht erreichbarer Provider.
- [ ] Ollama-Modell nicht gefunden.
- [ ] Ollama-Timeout.
- [ ] Provider und Modell passen.
- [ ] Provider fehlt.
- [ ] Modell unbekannt.
- [ ] Provider stimmt nicht.
- [ ] Modell deaktiviert.
- [ ] Modell nicht verfügbar.
- [ ] Modell ohne Chatfähigkeit.
- [ ] `default_model=null`.
- [ ] Provider und Modell gemeinsam geändert.

### 13.4 Tooltests (Noch offen)

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

### 13.5 SSE-Tests (Noch offen)

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

### 13.6 Frontend-Unit-Tests (Noch offen)

- [ ] Bootstrap-Validator.
- [ ] Hierarchie-Validator.
- [ ] UI-Schema-Validator.
- [ ] Modell-Validator.
- [ ] Provider-Validator.
- [ ] Tool-Validator.
- [ ] Config-Validator.
- [ ] SSE-Parser.
- [ ] Endpoint-Resolver.
- [ ] ComponentRegistry lehnt unbekannte Komponente ab.
- [ ] ActionRegistry lehnt unbekannte Aktion ab.
- [ ] GenericTree mit deaktiviertem Knoten.
- [ ] SchemaRenderer mit unbekannter Komponente.
- [ ] SettingsField für alle bekannten Komponenten.
- [ ] ProviderSelect.
- [ ] ModelSelect mit Providerabhängigkeit.
- [ ] Providerwechsel setzt Modell zurück.
- [ ] Abgebrochene Anfrage ändert keinen State.

### 13.7 Integrationstests (Noch offen)

- [ ] Bootstrap wird zuerst geladen.
- [ ] App startet ohne optionale Registry degradiert.
- [ ] Root-Knoten wird dargestellt.
- [ ] Knotenauswahl öffnet schema-gesteuerte Ansicht.
- [ ] Provider werden geladen.
- [ ] Modellliste wird nach Provider gefiltert.
- [ ] Chat sendet Knoten-ID.
- [ ] Chat sendet Modell-ID.
- [ ] SSE wird inkrementell dargestellt.
- [ ] Config-Änderung löst gezielten Reload aus.
- [ ] Unbekannte Komponente wird sichtbar abgelehnt.
- [ ] Unbekannte Aktion wird nicht ausgeführt.
- [ ] Dokumentationsdialog lädt lokale Wiki-Seiten.
- [ ] Produktionsbuild ist erfolgreich.
- [ ] Backend und Frontend starten gemeinsam.
- [ ] Persistenten SSE-Chat inklusive Neustart nachweisen.
- [ ] Frontend-History laden und Duplikate vermeiden.

---

## 14. Performance und Monitoring

### Performance

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

### Monitoring

- [x] `GET /health/live`
- [x] `GET /health/ready`
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
- [-] Backend-Hierarchiemutationen sind vorhanden; der Frontend-Editor und die konsistente persistente Datenquelle fehlen noch.
- [-] Config-Änderungen erfolgen noch nicht vollständig atomar als Batch.
- [-] Provider- und Modellauswahl sind noch nicht vollständig gekoppelt.
- [-] OpenAPI-`JsonValue` ist für TypeScript-Generatoren wenig aussagekräftig.

- [ ] Öffentliche Verträge aus Routerdateien in klar benannte Schema- oder Contract-Module verschieben.
- [ ] Doppelte oder veraltete Typen entfernen.
- [ ] Übergangscode nach erfolgreicher Migration entfernen.
- [ ] `type: ignore` nur mit dokumentierter Begründung verwenden.
- [ ] Pylance-, Ruff-, MyPy- und Pytest-Warnungen schrittweise auf null bringen.

---

## 17. Empfohlene nächste Arbeitspakete (Korrigierte Reihenfolge)

### 🔴 Priorität 1 – Datenbank und Hierarchie (Blocker)

1. [ ] Entwicklungsdatenbank sichern und mit gültigem Head `0008` neu erzeugen.
2. [ ] Persistente Development-Hierarchie idempotent seeden (`root`, `workspace-1`, `project-1`, `chat-1`).
3. [ ] Hierarchie-API auf dieselbe persistente Datenquelle wie Chat-Persistenz stellen.
4. [ ] In-Memory-Hierarchie nicht parallel zur persistenten Hierarchie als Laufzeitwahrheit verwenden.

### 🟠 Priorität 2 – Chat-Persistenz Laufzeitintegration

5. [ ] Echten SSE-Chat speichern und History direkt danach prüfen.
6. [ ] Server neu starten und denselben Verlauf erneut laden.
7. [ ] Frontend-History anbinden und Duplikate vermeiden.
8. [ ] Client-Abbruch im echten SSE-Lauf nachweisen.
9. [ ] Providerfehler im echten Persistenzpfad nachweisen.

### 🟡 Priorität 3 – Settings-v2 abschließen

10. [ ] Config-API-Mapping um dynamische Optionsmetadaten erweitern.
11. [ ] TypeScript-Verträge erweitern.
12. [ ] `ProviderSelect` im Frontend anbinden.
13. [ ] abhängigen `ModelSelect` anbinden.
14. [ ] serverseitige Provider-Modell-Konsistenz prüfen.
15. [ ] atomaren Batch-Update implementieren.
16. [ ] Tests ergänzen.

### 🟢 Priorität 4 – Frontend-Hierarchieeditor

17. [ ] Kontextmenü im Baum.
18. [ ] Erstellen-Dialog.
19. [ ] Bearbeiten-Dialog.
20. [ ] Verschieben.
21. [ ] Löschen mit Bestätigung.
22. [ ] Lokaler Baum-Patch.
23. [ ] Fehler- und Konfliktdarstellung.

### 🔵 Priorität 5 – SchemaRenderer vervollständigen

24. [ ] ComponentRegistry finalisieren.
25. [ ] rekursiven Renderer implementieren.
26. [ ] bekannte Layoutkomponenten ergänzen.
27. [ ] bekannte Formularfelder ergänzen.
28. [ ] Action-Registry anbinden.
29. [ ] Knotentyp `user` migrieren.
30. [ ] Unit-Tests ergänzen.

### 🟣 Priorität 6 – Dokumentationsdialog

31. [ ] vorhandenen Patch mit aktuellem Code abgleichen.
32. [ ] Backend-Dokumentationsrouter integrieren.
33. [ ] Header-Button ergänzen.
34. [ ] Dialog anbinden.
35. [ ] Benutzerhandbuch vervollständigen.

---

## 18. MVP-Abnahmekriterien (Korrigiert)

Der aktuelle MVP gilt als konsistent, wenn:

- [x] Backend und Frontend lokal gemeinsam starten.
- [x] Bootstrap, UI-Schema, Hierarchie, Modelle, Tools und Config erreichbar sind.
- [x] Development-Identity funktioniert.
- [x] Chatpipeline erzeugt über einen registrierten Provider Antworten (technisch).
- [x] Provider-Streamereignisse werden normalisiert.
- [x] Usage-Daten verursachen keinen Serialisierungsfehler mehr.
- [x] Backend-Unit-Tests bestehen.
- [x] Health-Endpunkte sind vorhanden.
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
- [ ] Hierarchieknoten können sicher hinzugefügt, bearbeitet, verschoben und gelöscht werden (Backend: ja, Frontend: nein).
- [ ] Modell- und Toolauswahl werden an den Chat übertragen.
- [ ] SSE-Abschluss, Fehler und Abbruch werden sauber behandelt.
- [ ] Strukturierte Fehler inklusive Request-ID funktionieren.
- [ ] Betriebsprofile erzwingen ihre Sicherheitsuntergrenzen.
- [ ] Internes Wiki und Benutzerhandbuch sind aus dem Header erreichbar.
- [ ] Frontendtests bestehen.
- [ ] Produktionsbuild besteht.
- [ ] OpenAPI entspricht dem tatsächlichen Laufzeitverhalten.
- [ ] README, TODO, Roadmap und Wiki beschreiben denselben Projektstand.
- [ ] Persistenter SSE-Chat inklusive Neustart nachgewiesen.
- [ ] Frontend-History geladen und Duplikate vermieden.

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

### KI

- [ ] Multimodale Chats
- [ ] Bildverarbeitung
- [ ] Dokumentintelligenz
- [ ] Sprachsteuerung
- [ ] lokale STT-/TTS-Integration
- [ ] komplexe autonome Workflows
- [ ] Multi-Agenten-System erst nach stabiler Kernarchitektur

### Zusammenarbeit

- [ ] gemeinsame Arbeitsbereiche
- [ ] kollaborative Bearbeitung
- [ ] Aktivitätsfeed
- [ ] Teamrollen
- [ ] Organisationstemplates

### Enterprise

- [ ] PostgreSQL-Produktivbetrieb
- [ ] Multi-Worker-Betrieb
- [ ] Clusterbewusstsein
- [ ] verteilte Config-Invalidierung
- [ ] erweiterte Audits
- [ ] Policy Engine
- [ ] Mandantenverwaltung

### Ökosystem

- [ ] Plugin-Katalog
- [ ] Template-Repository
- [ ] gemeinsame Schema-Bibliotheken
- [ ] signierte Pakete
- [ ] Erweiterungsverwaltung

---

## 21. API-Ausbau und Ressourcenverwaltung

### 21.1 Bestehende API inventarisieren und konsolidieren

#### Aktuelle Endpunkte bestätigen

- [x] `GET /api/v1/health` (vermutlich veraltet, siehe Health-Endpunkte)
- [x] `GET /health/live`
- [x] `GET /health/ready`
- [x] `GET /api/v1/bootstrap`
- [x] `GET /`
- [x] `GET /api/v1/settings/catalog`
- [x] `GET /api/v1/ui/schema`
- [x] Kalenderauswahl
- [x] Kalender-CRUD
- [x] Event-CRUD
- [x] Hierarchie laden
- [x] Hierarchieknoten erstellen
- [x] Hierarchieknoten aktualisieren
- [x] Hierarchieknoten verschieben
- [x] Hierarchie neu ordnen
- [x] Hierarchieknoten löschen
- [x] Dokumentationsübersicht
- [x] Dokumentationsseite laden
- [x] Modellprovider aus Modell-Registry auflisten
- [x] Modelle auflisten
- [x] Tools auflisten
- [x] Chatstream
- [-] `GET /api/v1/chats/{chat_id}/messages` vorhanden, API-Abdeckung vervollständigen
- [x] Konfiguration auflisten
- [x] Konfiguration atomar aktualisieren (Einzelupdate)
- [x] Einzelnen Konfigurationswert aktualisieren

#### Zentrale Routerregistrierung

- [ ] Alle öffentlichen v1-Router inventarisieren.
- [ ] Prüfen, welche Router außerhalb von `backend/app/api/v1/router.py` registriert werden.
- [ ] Kalender-, Dokumentations- und Settings-Router zentral registrieren.
- [ ] Doppelte Routerregistrierungen entfernen.
- [ ] Prefix und Tags ausschließlich zentral definieren.
- [ ] Sicherstellen, dass jede öffentliche Route in OpenAPI erscheint.
- [ ] Router-Reihenfolge bei statischen und dynamischen Pfaden prüfen.
- [ ] `/providers` vor `/{provider_id}` registrieren.
- [ ] `/models/providers` vor `/{model_id}` registrieren.

### 21.2 Gemeinsame API-Verträge

#### Listenverträge

- [ ] Einheitlichen Grundvertrag für Ressourcenlisten definieren.
- [ ] `schema_version` verpflichtend ausgeben.
- [ ] `revision` oder `registry_revision` eindeutig verwenden.
- [ ] `items` immer als Array ausgeben.
- [ ] Cursor-basierte Pagination vorbereiten.
- [ ] `next_cursor` standardmäßig `null` ausgeben.
- [ ] `request_id` einheitlich ausgeben.
- [ ] Filterparameter dokumentieren.
- [ ] Sortierung deterministisch festlegen.

#### Einzelressourcen

- [ ] Einheitliche Response-Struktur für Einzelressourcen definieren.
- [ ] Ressourcenrevision und globale Revision unterscheiden.
- [ ] `request_id` ergänzen.
- [ ] Soft-deleted oder archivierte Ressourcen eindeutig kennzeichnen.
- [ ] Unbekannte zusätzliche Felder ablehnen.

#### Mutationen

- [ ] Einheitlichen Mutationsvertrag definieren.
- [ ] Statuswerte festlegen: `created`, `updated`, `deleted`, `archived`, `restored`, `moved`, `reordered`
- [ ] Neue Revision ausgeben.
- [ ] Geänderte Ressource oder ID ausgeben.
- [ ] `expected_revision` für konfliktanfällige Mutationen verwenden.
- [ ] Revisionskonflikte als `409` ausgeben.

---

## 22. Umsetzungsphasen (Korrigiert)

### Phase 0 – Datenbank und Hierarchie konsolidieren (JETZT)

- [ ] Entwicklungsdatenbank auf gültigen Alembic-Stand bringen.
- [ ] Persistente Hierarchie als gemeinsame Quelle für API und Chat verwenden.
- [ ] In-Memory-Hierarchie durch persistente ersetzen.
- [ ] Development-Seed idempotent erstellen.

### Phase 1 – Chat-Persistenz Laufzeitintegration

- [ ] Echten SSE-Chat inklusive Neustart nachweisen.
- [ ] Frontend-History laden und Duplikate vermeiden.
- [ ] Client-Abbruch und Providerfehler im echten Persistenzpfad testen.

### Phase 2 – Settings-v2 abschließen

- [ ] Config-API-Mapping um dynamische Optionsmetadaten erweitern.
- [ ] TypeScript-Verträge erweitern.
- [ ] ProviderSelect und ModelSelect im Frontend anbinden.
- [ ] Serverseitige Provider-Modell-Konsistenz prüfen.
- [ ] Atomaren Batch-Update implementieren.
- [ ] Tests ergänzen.

### Phase 3 – Frontend-Hierarchieeditor

- [ ] Kontextmenü, Dialoge, lokaler Baum-Patch.
- [ ] Fehler- und Konfliktdarstellung.

### Phase 4 – SchemaRenderer vervollständigen

- [ ] ComponentRegistry finalisieren.
- [ ] Rekursiven Renderer implementieren.
- [ ] Action-Registry anbinden.
- [ ] Knotentypen migrieren.

### Phase 5 – Dokumentationsdialog

- [ ] Backend-Dokumentationsrouter integrieren.
- [ ] Header-Button und Dialog anbinden.
- [ ] Benutzerhandbuch vervollständigen.

---

## 23. Nächste konkrete Aktionen (Korrigiert)

1. **Entwicklungsdatenbank sichern und mit gültigem Head `0008` neu erzeugen.**
2. **Persistente Development-Hierarchie idempotent seeden.**
3. **Hierarchie-API auf dieselbe persistente Datenquelle wie Chat-Persistenz stellen.**
4. **Echten SSE-Chat speichern und History direkt danach prüfen.**
5. **Server neu starten und denselben Verlauf erneut laden.**
6. **Frontend-History anbinden und Duplikate vermeiden.**
7. **Erst danach Settings-v2 fortsetzen.**
8. **Frontend-Hierarchieeditor anbinden.**
9. **SchemaRenderer vervollständigen.**
10. **CI-Check für Settings-Definitionen ergänzen.**

---

## 24. Verwandte Dokumentation

### Entwicklung
- [[Roadmap]]
- [[Coding Guidelines]]
- [[Release Process]]
- [[Testing]]

### Architektur
- [[Repository-Structure]]
- [[Extension-Points]]
- [[Manifest-System]]

### Konzepte
- [[Runtime Configuration]]
- [[Configuration Revisions]]
- [[Plugin-System]]
- [[Schema Versioning]]
- [[Dynamic-UI]]
- [[Prompt Inheritance]]

### Betrieb
- [[Development]]
- [[Intranet]]
- [[Internet]]

---

**Empfehlung:** Die dringendste Aufgabe ist die Behebung der Datenbank-Migrationsinkonsistenz und die konsistente Anbindung der persistenten Hierarchie. Erst danach sollten Settings-v2 und die weiteren Themen fortgesetzt werden.