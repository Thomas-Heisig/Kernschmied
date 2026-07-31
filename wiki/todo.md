# TODO – Kernschmied MVP-Verträge konsolidieren und Frontend/Backend integrieren

**Stand: 27.07.2026**

## Statuslegende

- `[x]` umgesetzt
- `[-]` begonnen oder teilweise umgesetzt
- `[ ]` offen
- `[!]` muss geprüft oder bewusst entschieden werden

---

# Ziel

Backend und Frontend werden auf gemeinsame, versionierte und eindeutig dokumentierte Verträge gebracht.

Dabei gelten folgende Grundsätze:

- Der Bootstrap ist der einzige feste fachliche Einstiegspunkt des Frontends.
- Fachliche API-Endpunkte werden aus `bootstrap.endpoints` bezogen.
- UI-Schema, Hierarchie, Modelle, Tools, Chat und Konfiguration besitzen klare Transportverträge.
- Dynamisch gelieferte Typen bedeuten niemals automatische Freigabe.
- Jede Mutation sowie jede Modell- und Toolnutzung wird serverseitig autorisiert.
- Unbekannte Komponenten, Aktionen, Modelle, Tools und Knotentypen werden sicher abgelehnt oder sichtbar als nicht unterstützt dargestellt.
- Vertragsänderungen erfolgen bewusst, versioniert und mit Tests.
- Es werden keine dauerhaften parallelen Alt- und Neuverträge gepflegt.
- Das Frontend enthält keine fachlich fest verdrahteten Knotendarstellungen.
- Schema-gesteuerte Ansichten werden ausschließlich über bekannte Komponenten und Aktionen gerendert.
- Backend und Frontend müssen nach jeder Änderung gemeinsam startbar bleiben.

---

# 1. Aktuelle Vertragsabweichungen dokumentieren

## 1.1 Hierarchie-Endpunkt

- [x] Prüfen, ob `GET /api/v1/hierarchy` im aktuellen OpenAPI-Dokument noch als `HealthResponse` beschrieben wird. - Ursache: veraltetes OpenAPI-Artefakt - Laufzeit- und OpenAPI-Prüfung als erledigt
- [x] Falls weiterhin fehlerhaft: falsche Routerfunktion, falsches `response_model`, falschen Import oder kopierten Health-Handler korrigieren. - Nicht erforderlich, da Endpunkt korrekt ist.
- [-] Hierarchie-Vertragsmodelle und Normalisierung sind teilweise vorhanden.
- [ ] Sicherstellen, dass der Endpunkt zur Laufzeit ausschließlich den vereinbarten Hierarchievertrag liefert.
- [ ] OpenAPI nach der Korrektur neu erzeugen und prüfen.
- [ ] Vertragstest ergänzen, der den Hierarchie-Endpunkt gegen das erwartete Response-Modell prüft.

## 1.2 UI-Schema

- [-] Backendseitige Normalisierung von Schema-Sammlungen wurde erweitert.
- [-] Listen- und Record-Darstellungen können teilweise normalisiert werden.
- [-] Frontendseitige schema-gesteuerte Darstellung wird schrittweise eingeführt.
- [-] Der zentrale `SchemaRenderer` ist als Zielarchitektur festgelegt und wird angebunden.
- [ ] Endgültig festlegen und dokumentieren, welcher öffentliche UI-Schema-Vertrag dauerhaft gilt.
- [ ] Den Unterschied zwischen Transportantwort und fachlichem UI-Schema-Dokument vollständig beseitigen.
- [ ] Keine zwei konkurrierenden dauerhaften Schemaformen pflegen.
- [ ] Transport-Wrapper und fachliches Dokument klar voneinander trennen.
- [ ] Alte Schemaformen nur in einem klar befristeten Normalisierungsschritt unterstützen.

## 1.3 Bootstrap

- [-] Bootstrap ist als zentraler Einstiegspunkt vorgesehen und wird aktuell konsolidiert.
- [-] Der Backend-Bootstrap wurde strukturell erweitert beziehungsweise überarbeitet.
- [-] Bootstrap-Schritte besitzen isolierte Fehlerbehandlung.
- [-] Modell-Registry, Tool-Registry, Datenbank und Config-Service werden über den Bootstrap initialisiert.
- [ ] Bootstrap im Frontend verbindlich als ersten fachlichen Request verwenden.
- [ ] Verhindern, dass Frontendmodule fachliche Endpunkte mehrfach hart codieren.
- [ ] `bootstrap.versions.*` als zentrale Quelle für Vertragsversionen verwenden.
- [ ] `ui_schema_version` aus der UI-Schema-Antwort nicht als globale Versionsquelle behandeln.
- [ ] Startfehler einzelner Registry- oder Konfigurationsschritte klar klassifizieren und testen.
- [ ] Sicherstellen, dass kein globaler Singleton-Zustand den Bootstrap umgeht.

## 1.4 Chat

- [-] Ein einfacher SSE-Chat-Endpunkt ist vorhanden.
- [-] Modellprovider und Streaming-Verträge wurden erweitert.
- [-] Ollama ist als Provider angebunden beziehungsweise vorbereitet.
- [ ] Frontend und Backend auf den vollständigen `ChatRequest` abstimmen.
- [ ] Neben `message` folgende Felder vollständig unterstützen:

  - `conversation_id`
  - `hierarchy_node_id`
  - `model_id`
  - `tool_ids`
  - `metadata`

- [ ] Serverseitig sicherstellen, dass Modell- und Tool-IDs nur Clientwünsche darstellen und erneut geprüft werden.
- [ ] Konversations-, Knoten-, Modell- und Toolkontext durchgehend in Streamereignissen berücksichtigen.
- [ ] Abbruch-, Fehler- und Abschlusszustände vollständig vereinheitlichen.

---

# 2. Gemeinsame Vertragsstruktur im Backend

## 2.1 Contract-Module konsolidieren

Zielstruktur:

```text
backend/app/contracts/
├── common.py
├── bootstrap.py
├── hierarchy.py
├── ui_schema.py
├── chat.py
├── model_backend.py
├── models.py
├── tools.py
├── config.py
└── errors.py
```

- [-] Ein Contract-Bereich ist vorhanden.
- [x] Gemeinsame Modellbackend-Verträge für Nachrichten, Generierungsanfragen, Modellinformationen, Fähigkeiten, Nutzung und Streamereignisse sind vorhanden.
- [-] Rekursive JSON-Werttypen sind teilweise zentral definiert.
- [ ] Bestehende Contract-Module vollständig inventarisieren.
- [ ] Überschneidungen zwischen `model_backend.py`, öffentlichen Modelllisten und Provider-internen Modellen prüfen.
- [ ] Bestehende Modelle wiederverwenden oder bewusst migrieren.
- [ ] Keine doppelten Pydantic-Modelle für denselben öffentlichen Vertrag führen.
- [ ] Öffentliche API-Modelle klar von internen Domain-, Registry- und Persistenzmodellen trennen.
- [x] Pydantic v2 als Grundlage verwenden.
- [ ] Für stabile öffentliche Verträge grundsätzlich `ConfigDict(extra="forbid")` einsetzen.
- [ ] Zusätzliche Felder nur gezielt dort zulassen, wo Erweiterbarkeit fachlich notwendig ist.
- [ ] Freie Daten ausschließlich über klar benannte Felder wie `metadata`, `config` oder JSON-Schema-Strukturen zulassen.
- [ ] Keine Python-Klassen, Importpfade, Callables oder unkontrollierten Dateisystempfade öffentlich ausgeben.
- [-] Schema-Normalisierung lehnt ungültige Strukturen bereits teilweise mit verständlichen Fehlern ab.
- [ ] Schema-Versionen zentral und eindeutig definieren.
- [ ] Versionskonstanten nicht an mehreren Stellen duplizieren.

## 2.2 Namenskonventionen

- [ ] Einheitlich festlegen:

  - Transport-Wrapper enden auf `Response`
  - Fachliche Dokumente enden auf `Document`, `Tree`, `Manifest` oder einen anderen eindeutigen Fachnamen
  - Einzelobjekte enden auf `Entry`, `Node`, `Definition`, `Descriptor` oder `Info`

- [ ] Keine gleichnamigen Modelle mit unterschiedlicher Struktur verwenden.
- [ ] Feldnamen im JSON-Vertrag explizit festlegen.
- [ ] Aliase nur verwenden, wenn sie dokumentiert und getestet sind.
- [ ] Provider-interne Typen nicht ungeprüft als öffentliche API-Verträge wiederverwenden.
- [ ] Registry-Deskriptoren von ausführbaren Registry-Einträgen trennen.

---

# 3. Bootstrap-Vertrag vollständig anbinden

## 3.1 Backend

- [-] `GET /api/v1/bootstrap` als zentraler Einstiegspunkt ist architektonisch vorgesehen.
- [-] Bootstrap besitzt klar getrennte Initialisierungsschritte.
- [-] Datenbank, Konfiguration, Modell-Registry und Tool-Registry werden eingebunden.
- [ ] `GET /api/v1/bootstrap` als stabilen und nicht sensiblen öffentlichen Vertrag bestätigen.
- [ ] Folgende Bereiche vollständig und konsistent liefern:

  - `application`
  - `environment`
  - `user`
  - `security`
  - `capabilities`
  - `features`
  - `versions`
  - `endpoints`
  - `revisions`
  - `config_revision`
  - `request_id`

- [ ] Prüfen, ob `application.environment` und oberes `environment` bewusst doppelt vorhanden sind.
- [ ] Falls die Dopplung keinen Zweck erfüllt, für die nächste Vertragsversion bereinigen.
- [ ] Nur frontendfähige und nicht sensible Sicherheitsinformationen liefern.
- [ ] Keine Tokens, Secrets, Session-IDs oder internen Authentifizierungsdetails ausgeben.
- [ ] Alle Endpointpfade aus dem tatsächlich konfigurierten API-Präfix erzeugen.
- [ ] `capabilities` ausschließlich als technische Verfügbarkeit behandeln.
- [ ] Berechtigungen weiterhin bei jedem Endpunkt serverseitig prüfen.
- [ ] Registry-Fehler im Bootstrap degradiert oder fatal nach klaren Regeln behandeln.
- [ ] Bootstrap-Antwort nicht von zufälliger Import- oder Initialisierungsreihenfolge abhängig machen.

## 3.2 Frontend

- [-] Zentrale Provider-Struktur über `AppProviders` ist vorhanden.
- [-] Der Frontend-Einstieg wurde auf einen eindeutigen `main.tsx`-Pfad konsolidiert.
- [x] Root-Element-Prüfung und React-Initialisierung sind zentralisiert.
- [ ] Vertrag `contracts/bootstrap.ts` erstellen oder finalisieren.
- [ ] Laufzeitvalidierung für `BootstrapResponse` ergänzen.
- [ ] Zentralen Bootstrap-Service erstellen.
- [ ] Bootstrap vor UI-Schema, Hierarchie, Modellen und Tools laden.
- [ ] Bootstrap im zentralen Store beziehungsweise Anwendungskontext speichern.
- [ ] Endpunkte ausschließlich aus `bootstrap.endpoints` verwenden.
- [ ] Vertragsversionen aus `bootstrap.versions` verwenden.
- [ ] Capabilities und Features zentral verfügbar machen.
- [ ] Benutzer- und Umgebungsinformationen zentral verfügbar machen.
- [ ] Fehler bei ungültigem Bootstrap sichtbar und strukturiert darstellen.
- [ ] Keine Folgeanfragen starten, wenn der Bootstrap-Vertrag ungültig ist.
- [ ] Nur bekannte Endpointschlüssel verwenden.
- [ ] Unbekannte zusätzliche Endpointschlüssel nicht automatisch aktivieren.
- [ ] Entwicklungsfallbacks klar von produktiven Endpointwerten trennen.

## 3.3 Basis-URL und Endpoint-Auflösung

- [ ] API-Basis-URL und Bootstrap-URL eindeutig trennen.
- [ ] Festlegen, ob `VITE_API_URL` auf `/api/v1` oder nur auf den Origin zeigt.
- [ ] Eine zentrale Funktion zur sicheren Endpoint-Auflösung erstellen.
- [ ] Absolute und relative Bootstrap-Endpunkte kontrolliert unterstützen.
- [ ] Fremde Origins standardmäßig ablehnen.
- [ ] Same-Origin als Standardsicherheitsgrenze verwenden.
- [ ] Abweichende Origins nur über feste Infrastrukturkonfiguration zulassen.
- [ ] Development-, Intranet- und Internetprofil berücksichtigen.
- [ ] Doppelte Pfadbestandteile wie `/api/v1/api/v1/...` verhindern.
- [ ] Endpointschlüssel und HTTP-Methode getrennt behandeln.

---

# 4. Hierarchie-Endpunkt versionieren und korrigieren

## 4.1 Öffentlicher Vertrag

Zielstruktur:

```json
{
  "schema_version": "1.0",
  "revision": 1,
  "root": {
    "id": "root",
    "type": "workspace",
    "name": "Kernschmied",
    "actions": [],
    "children": [],
    "parent_id": null,
    "sort_order": 0,
    "selectable": true,
    "disabled": false,
    "status": null,
    "metadata": {},
    "revision": 1
  },
  "request_id": "optional"
}
```

- [-] Generische Hierarchieknoten sind Bestandteil der Architektur.
- [-] Das Frontend besitzt eine rekursive generische Baumdarstellung.
- [-] Knotentypen sollen schema-gesteuert dargestellt werden.
- [ ] Entscheiden, ob `request_id` Bestandteil des Wrappers oder ausschließlich Response-Header ist.
- [ ] `HierarchyTreeResponse` als eindeutiges `response_model` verwenden.
- [ ] `schema_version` als Pflichtfeld definieren.
- [ ] `revision` als nichtnegative Ganzzahl validieren.
- [ ] `root` als Pflichtfeld definieren.
- [ ] `children` immer als Array ausgeben.
- [ ] `actions` immer als Array ausgeben.
- [ ] Optionalfelder unterstützen:

  - `parent_id`
  - `sort_order`
  - `selectable`
  - `disabled`
  - `status`
  - `metadata`
  - `revision`

- [ ] Zyklische Hierarchien im Service oder Mapper erkennen und ablehnen.
- [ ] Doppelte Knoten-IDs erkennen und ablehnen.
- [ ] Maximale sinnvolle Rekursionstiefe festlegen.
- [ ] Sortierung der Kindknoten deterministisch festlegen.
- [ ] Leere Hierarchie eindeutig behandeln.
- [ ] Entscheiden, ob immer ein technischer Root-Knoten existieren muss.

## 4.2 Datenbank und Service

- [-] Eine generische Hierarchiestruktur ist vorgesehen beziehungsweise teilweise implementiert.
- [ ] Domainmodell und API-Darstellung vollständig trennen.
- [ ] Hierarchie rekursiv oder iterativ ohne N+1-Abfragen laden.
- [ ] SQLite und PostgreSQL ohne Architekturwechsel unterstützen.
- [ ] Serverseitige Filterung nicht sichtbarer Knoten vornehmen.
- [ ] Aktionen pro Knoten für den aktuellen Benutzer berechnen.
- [ ] Keine nicht autorisierten Knoten oder Metadaten an den Client übertragen.
- [ ] Metadaten vor Ausgabe validieren.
- [ ] Knotenrevisionen und Baumrevision klar voneinander unterscheiden.
- [ ] Lösch- und Verschiebeoperationen gegen Zyklen und ungültige Eltern absichern.

## 4.3 Frontend

- [x] Rekursiver generischer Baum ist als Frontendgrundlage vorhanden.
- [-] Knotenauswahl ist vorhanden.
- [-] Ausgewählte Knotentypen werden schrittweise an den `SchemaRenderer` angebunden.
- [-] Für den Knotentyp `user` ist die schema-gesteuerte Ansicht über den zentralen `SchemaRenderer` vorgesehen.
- [ ] `contracts/hierarchy.ts` mit dem endgültigen Backendvertrag abgleichen.
- [ ] Wrapper-Felder eindeutig validieren.
- [ ] Optionales `request_id` ergänzen, falls Bestandteil des Vertrags.
- [ ] `GenericTree` für `disabled` und `selectable` korrekt erweitern.
- [ ] Deaktivierte Knoten nicht auswählbar machen.
- [ ] Nicht auswählbare Knoten weiterhin auf- und zuklappbar machen.
- [ ] Unbekannte Knotentypen mit einer sicheren Standarddarstellung sichtbar machen.
- [ ] Doppelte IDs oder zyklische Daten bei Laufzeitvalidierung ablehnen.
- [ ] Baumzustand bei Revisionswechsel sinnvoll erhalten oder bereinigen.
- [ ] Auswahl entfernen, wenn der ausgewählte Knoten nicht mehr vorhanden oder nicht mehr sichtbar ist.
- [ ] Expandierungszustand nur für weiterhin vorhandene Knoten übernehmen.

---

# 5. UI-Schema-Vertrag vereinheitlichen

## 5.1 Transporttrennung

Transportantwort:

```json
{
  "api_schema_version": "1.0",
  "ui_schema_version": "1.0",
  "config_revision": 1,
  "schema": {},
  "request_id": "optional"
}
```

Fachliches Dokument:

```json
{
  "schema_name": "kernschmied.default",
  "schema_version": "1.0",
  "minimum_client_version": "0.1.0",
  "components": [],
  "actions": [],
  "node_types": {},
  "forms": {},
  "root_component": null,
  "action_definitions": {},
  "revision": 1,
  "metadata": {}
}
```

- [-] Backend-Normalisierung unterstützt teilweise Listen und Records.
- [-] `id`-Werte können teilweise aus Registry-Schlüsseln abgeleitet werden.
- [-] Fehlerhafte Einträge werden bei der Normalisierung abgelehnt.
- [ ] Transporttrennung verbindlich übernehmen oder bewusst abweichend dokumentieren.
- [ ] `UISchemaResponse` und `UISchemaDocument` eindeutig definieren.
- [ ] Keine Komponentenliste gleichzeitig als Typnamenliste und Definitionsliste verwenden.
- [ ] Für jedes Feld eine eindeutige Bedeutung festlegen.
- [ ] `api_schema_version`, `ui_schema_version` und Dokument-`schema_version` klar unterscheiden.
- [ ] `minimum_client_version` clientseitig prüfen.

## 5.2 Komponentenvertrag

- [ ] Festlegen, ob Komponenten über `type` identifiziert werden.
- [ ] `kind` nicht parallel als konkurrierendes Feld verwenden.
- [ ] Frontend und Backend auf exakt einen Feldnamen bringen.
- [ ] Folgende Felder stabilisieren:

  - `id`
  - `type`
  - `title`
  - `description`
  - `props`
  - `children`
  - `visible`
  - `enabled`

- [ ] Nicht gleichzeitig widersprüchliche Felder wie `enabled` und `disabled` verwenden.
- [ ] Rekursive Kinder validieren.
- [ ] Komponenten-IDs innerhalb des Dokuments auf Eindeutigkeit prüfen.
- [ ] Unbekannte Komponententypen ausschließlich über `UnsupportedSchema` anzeigen.
- [ ] Unbekannte Komponententypen niemals dynamisch importieren oder ausführen.
- [ ] `props` erst nach erfolgreicher Typprüfung der bekannten Komponente interpretieren.
- [ ] Rekursionstiefe und maximale Komponentenanzahl begrenzen.

## 5.3 Aktionsvertrag

- [ ] Aktionstyp und konkrete Aktionsinstanz voneinander trennen.
- [ ] Einheitliche Identifikation über `id` und `type` festlegen.
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

- [ ] Direkte freie Endpoint-URLs möglichst durch bekannte `endpoint_key`-Werte ersetzen.
- [ ] Nur bekannte HTTP-Methoden zulassen.
- [ ] Endpointwerte sicher über den Bootstrap auflösen.
- [ ] Frontend darf Aktionen nur aus einer festen Action-Registry ausführen.
- [ ] Backend-Schema darf keine neuen Handler registrieren.
- [ ] Serverseitige Autorisierung für jede Aktion erneut durchführen.
- [ ] Destruktive Aktionen immer mit Bestätigung versehen.
- [ ] Unbekannte Aktionsarten sichtbar ablehnen.

## 5.4 Knotentypen

- [-] Knotentypen werden generisch behandelt.
- [-] Fachlich fest verdrahtete Komponenten wie `ProjectNode` sollen vermieden werden.
- [ ] `node_types` als `Record<string, NodeTypeDefinition>` definieren.
- [ ] Folgende Felder stabilisieren:

  - `label`
  - `icon`
  - `color`
  - `allowed_child_types`
  - `allowed_actions`
  - `description`
  - `creatable`
  - `renamable`
  - `deletable`
  - `create_form`
  - `edit_form`
  - `detail_component_id`
  - `metadata`

- [ ] `allowed_actions` ausdrücklich nur als UI-Hinweis dokumentieren.
- [ ] `allowed_child_types` ausdrücklich nur als UI-Hinweis dokumentieren.
- [ ] Unbekannte Icons durch ein festes Fallback ersetzen.
- [ ] Farben sicher validieren.
- [ ] Neue Knotentypen dürfen keine neue React-Komponente voraussetzen.
- [ ] Standarddarstellung für Knotentypen ohne spezifische Ansicht definieren.

## 5.5 Formulare

- [-] Dynamische Formulare sind Bestandteil der Zielarchitektur.
- [ ] `forms` als Record nach stabiler Formular-ID definieren.
- [ ] Folgende Felder vereinheitlichen:

  - `id`
  - `schema_version`
  - `title`
  - `description`
  - `schema`
  - `submit_action_id`
  - `submit_label`
  - `metadata`

- [ ] JSON-Schema-artige Formulare klar von komponentenbasierten Layouts trennen.
- [ ] Keine Mischform ohne dokumentierte Auswertungsregel verwenden.
- [ ] Unbekannte Feldtypen sichtbar als nicht unterstützt darstellen.
- [ ] Clientvalidierung nur als Bedienhilfe behandeln.
- [ ] Serverseitige Validierung bleibt maßgeblich.
- [ ] Sensible Felder und Secrets nicht über normale Fachkonfiguration ausgeben.
- [ ] Passwort- und Secretfelder nur über gesonderte, sichere Verwaltungsabläufe unterstützen.

## 5.6 Frontend-Komponenten-Registry

- [-] Eine feste Komponenten-Registry ist architektonisch vorgesehen.
- [-] Bekannte Komponenten werden schrittweise zentralisiert.
- [ ] `componentRegistry.tsx` finalisieren.
- [ ] Bekannte Komponenten explizit registrieren.
- [ ] Mindestens vorbereiten:

  - `tree`
  - `chat_view`
  - `message_list`
  - `chat_input`
  - `form`
  - `text`
  - `textarea`
  - `select`
  - `checkbox`
  - `toggle`
  - `table`
  - `card`
  - `button_group`
  - `icon`
  - `prompt_editor`
  - `model_selector`
  - `tool_selector`
  - `file_upload`
  - `unsupported`

- [ ] Nicht implementierte, aber bekannte Komponenten als noch nicht verfügbar darstellen.
- [ ] Unbekannte Komponenten über `UnsupportedSchema` anzeigen.
- [ ] Keine dynamischen React-Imports aus Backendwerten zulassen.
- [ ] Registryeinträge mit typspezifischen Prop-Validatoren verbinden.

## 5.7 SchemaRenderer

- [-] Zentraler `SchemaRenderer` ist als verbindlicher Renderer festgelegt.
- [-] Knotentypabhängige Platzhalter werden schrittweise durch schema-gesteuerte Ansichten ersetzt.
- [-] Der Knotentyp `user` soll über den zentralen `SchemaRenderer` dargestellt werden.
- [ ] Generischen rekursiven Renderer vollständig implementieren.
- [ ] Sichtbarkeit prüfen.
- [ ] Aktivierungszustand prüfen.
- [ ] Rekursive Kinder rendern.
- [ ] Komponenten-Props typspezifisch normalisieren.
- [ ] Fehlergrenze für fehlerhafte Einzelkomponenten ergänzen.
- [ ] Unbekannte Schemata dürfen nicht die gesamte App abstürzen lassen.
- [ ] Development-Debuganzeige ohne sensible Werte ermöglichen.
- [ ] `SelectedNodePlaceholder` vollständig durch schema-gesteuerte Ansichten ersetzen.
- [ ] Fehlende Schemaansichten verständlich anzeigen.
- [ ] Renderzyklen und unnötige Neuberechnungen vermeiden.

---

# 6. Zentralen API-Client und API-Dienste erweitern

## 6.1 Bestehenden Client härten

- [-] Ein zentraler API-Client ist als verbindliche Architekturvorgabe festgelegt.
- [ ] Bestehenden generischen `apiRequest` beibehalten und gezielt erweitern.
- [ ] Strukturierte Backendfehler zuverlässig erkennen.
- [ ] FastAPI-Standardfehler mit `detail` nur übergangsweise berücksichtigen.
- [ ] Abbruch- und Timeoutfehler unterscheidbar machen.
- [ ] Request-ID aus Body und Header auslesen.
- [ ] Keine sensitiven Requestdaten in Produktionslogs schreiben.
- [ ] Credentials je Betriebsprofil korrekt setzen.
- [ ] CSRF-Anforderungen für spätere Sessionauthentifizierung vorbereiten.
- [ ] `text/event-stream` nicht als JSON behandeln.
- [ ] Leere `204`- und `205`-Antworten korrekt behandeln.
- [ ] Binäre Antworten und spätere Datei-Uploads kontrolliert unterstützen.
- [ ] Einheitliche Fehlerklasse mit Status, Code, Details und Request-ID verwenden.

## 6.2 Typisierte API-Dienste

Zielstruktur:

```text
frontend/src/api/
├── client.ts
├── endpoints.ts
├── bootstrapApi.ts
├── schemaApi.ts
├── hierarchyApi.ts
├── modelApi.ts
├── toolApi.ts
├── chatApi.ts
└── configApi.ts
```

- [ ] Typisierte Funktionen erstellen oder finalisieren:

  - `loadBootstrap`
  - `loadUISchema`
  - `loadHierarchy`
  - `loadModels`
  - `loadTools`
  - `streamChat`
  - `loadConfig`
  - `updateConfig`

- [ ] Endpunkte über den Bootstrap-Kontext beziehen.
- [ ] Laufzeitvalidierung jeder API-Antwort vor Store-Übernahme durchführen.
- [ ] Keine ungeprüften `unknown`-Werte in den Store übernehmen.
- [ ] Endpoints und Versionen nicht in UI-Komponenten duplizieren.
- [ ] API-Dienste unabhängig von konkreten React-Komponenten halten.
- [ ] AbortSignal durchgängig unterstützen.

---

# 7. Modelle und Tools vollständig anbinden

## 7.1 Backend-Registries

- [x] Modell-Registry ist als eigener Bootstrap-Bestandteil vorhanden.
- [x] Tool-Registry ist als eigener Bootstrap-Bestandteil vorhanden.
- [x] Registries werden mit isolierter Fehlerbehandlung initialisiert.
- [-] Modellprovider besitzen gemeinsame Backendverträge.
- [-] Ollama-Provider ist vorhanden beziehungsweise wird vervollständigt.
- [ ] Manifestprüfung für `model.json` vollständig testen.
- [ ] Manifestprüfung für `tool.json` vollständig testen.
- [ ] Registryfehler dürfen nicht unkontrolliert den gesamten Prozess beenden.
- [ ] Duplikate, ungültige IDs und inkompatible Versionen klar ablehnen.
- [ ] Automatische Erkennung strikt von Freigabe und Aktivierung trennen.
- [ ] Keine beliebigen Python-Module aus unkontrollierten Pfaden laden.

## 7.2 Modellverträge

- [ ] `contracts/models.ts` erstellen oder finalisieren.
- [ ] Folgende Strukturen abbilden:

  - `ModelListResponse`
  - `ModelEntry`
  - `ModelCapability`
  - `ModelLimits`

- [ ] Laufzeitvalidierung ergänzen.
- [ ] `enabled`, `available`, `selectable` und `default` getrennt behandeln.
- [ ] Nur auswählbare und verfügbare Modelle normal anbieten.
- [ ] Deaktivierte Modelle nur in administrativen Ansichten anzeigen.
- [ ] Defaultmodell eindeutig bestimmen.
- [ ] Mehrere Defaultmodelle als Vertragsfehler behandeln oder deterministisch auflösen.
- [ ] Registry- und Config-Revision speichern.
- [ ] Providerdetails nur ausgeben, soweit sie für das Frontend erforderlich und nicht sensibel sind.

## 7.3 Toolverträge

- [ ] `contracts/tools.ts` erstellen oder finalisieren.
- [ ] Folgende Strukturen abbilden:

  - `ToolListResponse`
  - `ToolEntry`
  - `ToolCapabilities`
  - `ToolInputSchema`

- [ ] Laufzeitvalidierung ergänzen.
- [ ] `enabled`, `available` und `selectable` getrennt behandeln.
- [ ] `required_permissions` im UI nur als Hinweis verwenden.
- [ ] Serverseitige Berechtigungsprüfung bleibt verpflichtend.
- [ ] Tool-Eingabeschemata ausschließlich mit bekannten generischen Formularfeldern rendern.
- [ ] Unbekannte JSON-Schema-Schlüssel nicht ausführen.
- [ ] Registry- und Config-Revision speichern.
- [ ] Toolresultate auf JSON-kompatible Transportwerte begrenzen.

## 7.4 Frontend-Auswahl

- [ ] `ModelSelector` implementieren beziehungsweise anbinden.
- [ ] `ToolSelector` implementieren beziehungsweise anbinden.
- [ ] Auswahl im Store halten.
- [ ] Auswahl bei Registry-Revision validieren und bereinigen.
- [ ] Nicht mehr verfügbare Auswahl sichtbar entfernen.
- [ ] Modell- und Toolauswahl an `ChatRequest` übergeben.
- [ ] Keine Modell- oder Toolfreigabe aus der bloßen Listung ableiten.
- [ ] Grund für nicht auswählbare Modelle und Tools verständlich anzeigen.

---

# 8. Chat-Streaming vollständig und robust umsetzen

## 8.1 Verträge

- [-] Backendseitige Nachrichten-, Generierungs- und Streamtypen sind vorhanden.
- [-] Streamereignisse besitzen bereits gemeinsame Grundtypen.
- [ ] `contracts/chat.ts` im Frontend erstellen oder finalisieren.
- [ ] `ChatRequest` exakt nach dem öffentlichen Backendvertrag abbilden.
- [ ] SSE-Ereignisvertrag als öffentlichen, versionierten Vertrag dokumentieren.
- [ ] Ereignistypen verbindlich festlegen:

  - `start`
  - `token`
  - `message`
  - `usage`
  - `tool_call`
  - `tool_result`
  - `error`
  - `done`

- [ ] Für jedes Ereignis eine versionierte Payload definieren.
- [ ] Streamversion festlegen.
- [ ] Abschlussereignis eindeutig definieren.
- [ ] Fehlerereignisse im strukturierten Fehlerformat liefern.
- [ ] Providerinterne Ereignisse vor Ausgabe auf öffentliche Ereignistypen abbilden.

## 8.2 Backend

- [-] SSE-Endpunkt als MVP ist vorhanden.
- [ ] `Content-Type: text/event-stream` zuverlässig setzen.
- [ ] Proxy-Pufferung soweit möglich deaktivieren.
- [ ] Keepalive-Kommentare oder Heartbeats ergänzen.
- [ ] Clientabbruch erkennen.
- [ ] Modellgenerierung bei Abbruch stoppen, sofern unterstützt.
- [ ] Toolausführung bei Abbruch stoppen, sofern unterstützt.
- [ ] Request-ID im Streamkontext verfügbar machen.
- [ ] Fehler nach Streambeginn als SSE-Fehlerereignis senden.
- [ ] Keine internen Exceptions oder Secrets in Streamfehlern ausgeben.
- [ ] Providerfehler auf stabile öffentliche Fehlercodes abbilden.
- [ ] Doppelte Abschlussereignisse verhindern.

## 8.3 Frontend

- [ ] SSE-Parser in ein eigenes Modul auslagern.
- [ ] Mehrzeilige `data:`-Felder unterstützen.
- [ ] Kommentare und unbekannte SSE-Felder ignorieren.
- [ ] Ereignistypen strikt auswerten.
- [ ] Unbekannte Ereignistypen sicher ignorieren oder sichtbar protokollieren.
- [ ] `done` sauber verarbeiten.
- [ ] Streamfehler strukturiert darstellen.
- [ ] `conversation_id` aus Serverereignissen übernehmen, falls geliefert.
- [ ] `hierarchy_node_id` aus dem aktuell ausgewählten Knoten mitsenden.
- [ ] `model_id` und `tool_ids` mitsenden.
- [ ] Chatnachrichten bei Registry- oder Schemareloads erhalten.
- [ ] Leere Assistentenantworten eindeutig behandeln.
- [ ] Abbruchstatus von Fehlerstatus unterscheiden.
- [ ] Mehrfachsenden während eines laufenden Streams kontrollieren.
- [ ] Aktiven Stream beim Wechsel der Konversation bewusst fortführen oder abbrechen.

---

# 9. Store und Ladefluss erweitern

## 9.1 Store-Zustand

- [-] Zentrale Providerstruktur ist vorhanden.
- [-] Ausgewählter Knoten wird bereits im Frontend berücksichtigt.
- [ ] Store beziehungsweise Anwendungskontext um folgende Bereiche erweitern:

  - `bootstrap`
  - `schemaResponse`
  - `schema`
  - `hierarchyTree`
  - `models`
  - `tools`
  - `configRevision`
  - `uiSchemaRevision`
  - `hierarchyRevision`
  - `modelRegistryRevision`
  - `toolRegistryRevision`
  - `selectedModelId`
  - `selectedToolIds`
  - `selectedNodeId`
  - `expandedNodeIds`
  - getrennte Lade- und Fehlerzustände

- [ ] Nicht alle Teilfehler als vollständigen App-Absturz behandeln.
- [ ] Bootstrapfehler als fatal behandeln.
- [ ] Optionale Capability-Fehler als degradierte Funktion darstellen.
- [ ] Schema- und Hierarchiefehler klar unterscheiden.
- [ ] Modelle und Tools unabhängig nachladen können.
- [ ] Chat- und Navigationszustand von Konfigurationszustand trennen.

## 9.2 Initialer Ladeablauf

Zielablauf:

1. Bootstrap laden und validieren.
2. Capabilities und Vertragsversionen prüfen.
3. UI-Schema und Hierarchie parallel laden.
4. Modelle und Tools abhängig von Capabilities parallel laden.
5. Daten normalisieren und validieren.
6. Initiale Auswahl bestimmen.
7. Anwendung als bereit markieren.

- [ ] Race Conditions durch `AbortController` oder Requestgenerationen verhindern.
- [ ] Ältere Antworten dürfen neue Daten nicht überschreiben.
- [ ] Bei Reload gültige Altdaten möglichst erhalten.
- [ ] Teilweise erfolgreiche Reloads kontrolliert übernehmen.
- [ ] Root-Knoten nur auswählen, wenn er auswählbar ist.
- [ ] Andernfalls ersten auswählbaren Knoten deterministisch bestimmen.
- [ ] Fehlerzustände je Ressource separat darstellen.
- [ ] Initialisierung gegen React-StrictMode-Doppelausführung absichern.

## 9.3 Revisionen und Cache-Invalidierung

- [-] Config-Revision ist Bestandteil der Architektur.
- [-] Multi-Worker-Cache-Invalidierung ist als Anforderung festgelegt.
- [ ] Bootstrap-Revisionswerte speichern.
- [ ] UI-Schema-Revision speichern.
- [ ] Hierarchie-Revision speichern.
- [ ] Modell-Registry-Revision speichern.
- [ ] Tool-Registry-Revision speichern.
- [ ] Config-Revision speichern.
- [ ] Regeln definieren, welche Revision welche Daten invalidiert.
- [ ] Keine unnötigen Komplettreloads auslösen.
- [ ] Nach Konfigurationsänderungen nur betroffene Ressourcen neu laden.
- [ ] Multi-Worker-fähige Invalidierung im Backend vorbereiten.
- [ ] Optional `ETag` und `If-None-Match` dokumentieren.
- [ ] Polling nur einsetzen, wenn keine bessere Benachrichtigung vorhanden ist.
- [ ] Pollingintervall konfigurierbar und ressourcenschonend halten.
- [ ] Sichtbare UI während eines Hintergrundreloads nicht unnötig zurücksetzen.

---

# 10. Konfigurationsverwaltung

## 10.1 Backend

- [x] Fachliche Konfiguration ist für die Datenbank vorgesehen.
- [x] Config-Service ist Bestandteil des Bootstraps.
- [-] Revisionsbasierte Konfiguration ist vorhanden beziehungsweise im Aufbau.
- [ ] `GET /api/v1/config` vollständig typisieren.
- [ ] Sensitive Werte niemals ausgeben.
- [ ] Runtime-Editierbarkeit serverseitig prüfen.
- [ ] `expected_revision` verpflichtend oder bewusst optional festlegen.
- [ ] Bei Revisionskonflikt strukturierten `409`-Fehler liefern.
- [ ] Jede Änderung auditieren:

  - Benutzer
  - Zeitpunkt
  - Gruppe
  - Schlüssel
  - alte Revision
  - neue Revision
  - Begründung
  - Request-ID

- [ ] Secrets nicht in Auditdetails schreiben.
- [ ] Revision atomar erhöhen.
- [ ] Transaktionale Konsistenz sicherstellen.
- [ ] Nicht zur Laufzeit editierbare Werte mit stabilem Fehlercode ablehnen.
- [ ] Änderungen mit Auswirkungen auf Registries oder Sicherheit gezielt behandeln.

## 10.2 Frontend

- [ ] `contracts/config.ts` erstellen oder finalisieren.
- [ ] Config-Liste und Updateantwort validieren.
- [ ] Nur `editable=true` bearbeitbar anzeigen.
- [ ] `sensitive=true` niemals als Klartext anzeigen.
- [ ] `expected_revision` bei Updates mitsenden.
- [ ] Revisionskonflikte verständlich darstellen.
- [ ] Nach erfolgreichem Update betroffene Daten neu laden.
- [ ] Administrative Oberfläche nur bei Capability und Berechtigung anzeigen.
- [ ] UI-Sichtbarkeit nicht als Sicherheitsentscheidung behandeln.
- [ ] Geänderte und gespeicherte Werte klar unterscheiden.
- [ ] Ungespeicherte Änderungen vor Navigation schützen.

---

# 11. Strukturierte Fehlerantworten vereinheitlichen

Standardformat:

```json
{
  "code": "invalid_hierarchy",
  "message": "Die Hierarchie konnte nicht geladen werden.",
  "details": {},
  "request_id": "..."
}
```

- [-] Strukturierte Fehler mit `code`, `message`, `details` und `request_id` sind als Projektstandard festgelegt.
- [-] Registry- und Bootstrapfehler besitzen teilweise eigene Fehlerklassen.
- [ ] Zentrales Fehler-Pydantic-Modell definieren.
- [ ] Request-ID-Middleware ergänzen oder prüfen.
- [ ] Eingehende vertrauenswürdige Request-ID optional übernehmen oder neu erzeugen.
- [ ] `X-Request-ID` immer als Response-Header setzen.
- [ ] Request-ID auch in Fehlerantworten ausgeben.
- [ ] FastAPI-Validierungsfehler in das zentrale Format umwandeln.
- [ ] Starlette-HTTP-Fehler vereinheitlichen.
- [ ] Unbehandelte Exceptions zentral abfangen.
- [ ] Statuscodes sinnvoll erhalten:

  - `400` ungültige Anfrage
  - `401` nicht authentifiziert
  - `403` nicht autorisiert
  - `404` nicht gefunden
  - `409` Revisions- oder Zustandskonflikt
  - `422` fachliche oder strukturelle Validierung
  - `429` Rate Limit
  - `500` interner Fehler
  - `503` Dienst nicht verfügbar

- [ ] Interne Stacktraces nur serverseitig loggen.
- [ ] Keine sensitiven Details an Clients senden.
- [ ] Fehlercodes zentral dokumentieren.
- [ ] Frontend auf `code`, `message`, `details` und `request_id` ausrichten.
- [ ] Übergangskompatibilität für FastAPI-`detail` befristen.

---

# 12. Autorisierung und Sicherheitsgrenzen

## 12.1 Serverseitige Autorisierung

- [ ] Jede Benutzeraktion serverseitig autorisieren.
- [ ] Knotenaktionen nicht allein aus `actions` oder `allowed_actions` freigeben.
- [ ] Modellwahl serverseitig prüfen.
- [ ] Toolwahl serverseitig prüfen.
- [ ] Toolaufruf separat autorisieren.
- [ ] Konfigurationszugriff separat autorisieren.
- [ ] Administrative Endpunkte separat autorisieren.
- [ ] Objektbezogene Berechtigungen berücksichtigen.
- [ ] Unbekannte Aktionstypen mit `unsupported_action` ablehnen.
- [ ] Bekannte, aber nicht erlaubte Aktionen mit `forbidden_action` ablehnen.
- [ ] Nicht verfügbare Modelle und Tools mit stabilen Fehlercodes ablehnen.
- [ ] Keine Berechtigungsinformationen über Fehlermeldungen unnötig offenlegen.
- [ ] Autorisierungsentscheidung nicht in Registry- oder UI-Schema-Logik verstecken.

## 12.2 Betriebsprofile

- [x] Die Profile `development`, `intranet` und `internet` sind als Architekturvorgabe definiert.
- [ ] Developmentprofil mit vereinfachter Identifikation klar kennzeichnen.
- [ ] Intranetprofil mit Authentifizierung und Audit erzwingen.
- [ ] Internetprofil mit HTTPS, Sessionauthentifizierung, Rate Limiting und Sicherheitsuntergrenzen absichern.
- [ ] Sicherheitsuntergrenzen nicht durch Datenbankkonfiguration unterschreitbar machen.
- [ ] CORS nicht allein aus dynamischer Fachkonfiguration steuern.
- [ ] Cookies je Profil korrekt konfigurieren.
- [ ] CSRF-Schutz für Sessionauthentifizierung vorbereiten.
- [ ] Rate-Limit-Fehler im Standardformat ausgeben.
- [ ] Anwendung bei unsicherer Profilkonfiguration kontrolliert nicht starten lassen.

## 12.3 Frontend-Sicherheit

- [ ] Keine Backendwerte als ungefiltertes HTML rendern.
- [ ] Kein `dangerouslySetInnerHTML` für dynamische Inhalte verwenden.
- [ ] Keine Endpunkte oder Module aus beliebigen Backendstrings importieren.
- [ ] Icons ausschließlich aus fester Registry laden.
- [ ] Aktionen ausschließlich aus fester Registry ausführen.
- [ ] URL- und Farbwerte validieren.
- [ ] Development-Debugdaten auf sensible Inhalte prüfen.
- [ ] Keine Tokens oder Secrets im Local Storage speichern.
- [ ] Schema-Props nicht ungeprüft auf native DOM-Elemente verteilen.
- [ ] Dateiuploads gegen Typ, Größe und Zielkontext validieren.

---

# 13. Kompatibilität und Migration

- [ ] Prüfen, ob existierende Clients einen einzelnen Root-Knoten erwarten.
- [ ] Falls notwendig, kurzen und klar befristeten Kompatibilitätsmodus vorsehen.
- [ ] Kompatibilitätsmodus mit Abschaltdatum oder Versionsgrenze dokumentieren.
- [ ] Keine dauerhafte doppelte Antwortstruktur etablieren.
- [ ] Vertragsänderungen im Changelog dokumentieren.
- [ ] API-Version nur bewusst erhöhen.
- [ ] Schema-Version und API-Version getrennt behandeln.
- [ ] `minimum_client_version` im Frontend prüfen.
- [ ] Bei zu altem Frontend verständliche Fehlermeldung anzeigen.
- [ ] Bei neuerem, aber kompatiblem Schema unbekannte Elemente sicher darstellen.
- [ ] Migration bestehender Seed- und Datenbankdaten prüfen.
- [ ] Alembic-Migrationen für neue Revisionsfelder ergänzen.
- [ ] Rollback-Verhalten der Migrationen testen.
- [ ] Übergangsnormalisierung nach erfolgreicher Migration wieder entfernen.

---

# 14. Tests

## 14.1 Backend-Vertragstests

- [ ] Gültiger Bootstrap.
- [ ] Bootstrap ohne Secrets.
- [ ] Fehler eines optionalen Registry-Bootstrap-Schritts.
- [ ] Fehler eines fatalen Bootstrap-Schritts.
- [ ] Gültiger `HierarchyTreeResponse`.
- [ ] Leere Hierarchie.
- [ ] Mehrere verschachtelte Ebenen.
- [ ] Doppelte Knoten-ID.
- [ ] Zyklische Hierarchie.
- [ ] Negative Revision.
- [ ] Fehlende `schema_version`.
- [ ] `children` oder `actions` nicht als Array.
- [ ] Unbekannter Knotentyp.
- [ ] UI-Schema mit leeren `forms`.
- [ ] UI-Schema als Record-Eingabe.
- [ ] UI-Schema als Listeneingabe.
- [ ] UI-Schema mit ungültigem Registry-Eintrag.
- [ ] UI-Schema mit unbekannter Komponente.
- [ ] UI-Schema mit unbekannter Aktion.
- [ ] Doppelte Komponenten-ID.
- [ ] Ungültige HTTP-Methode in Aktion.
- [ ] `ModelListResponse` mit Defaultmodell.
- [ ] `ToolListResponse` mit Eingabeschema.
- [ ] `ChatRequest` mit allen optionalen Feldern.
- [ ] `ChatRequest` mit ungültiger UUID.
- [ ] Config-Update mit korrekter Revision.
- [ ] Config-Update mit Revisionskonflikt.
- [ ] Strukturierte Fehlerantwort für `404`.
- [ ] Strukturierte Fehlerantwort für `409`.
- [ ] Strukturierte Fehlerantwort für `422`.
- [ ] Strukturierte Fehlerantwort für `500`.
- [ ] `X-Request-ID` vorhanden.
- [ ] Request-ID im Fehlerbody vorhanden.
- [ ] OpenAPI enthält korrekte `response_model`-Referenzen.

## 14.2 Registry- und Providertests

- [ ] Gültiges Modellmanifest.
- [ ] Ungültiges Modellmanifest.
- [ ] Doppelte Modell-ID.
- [ ] Nicht verfügbarer Modellprovider.
- [ ] Gültiges Toolmanifest.
- [ ] Ungültiges Toolmanifest.
- [ ] Doppelte Tool-ID.
- [ ] Fehler eines Tools isoliert behandeln.
- [ ] Ollama-Konfiguration ohne Base-URL.
- [ ] Ollama-Modell nicht gefunden.
- [ ] Ollama-Timeout.
- [ ] Ollama-Stream wird korrekt normalisiert.
- [ ] Providerinterne Fehlerdetails werden nicht öffentlich ausgegeben.

## 14.3 Autorisierungstests

- [ ] Nicht authentifizierter Zugriff.
- [ ] Authentifiziert, aber nicht berechtigt.
- [ ] Berechtigter Zugriff.
- [ ] Knotenaktionen pro Benutzer gefiltert.
- [ ] Modell nicht freigegeben.
- [ ] Tool nicht freigegeben.
- [ ] Unbekannte Aktion.
- [ ] Administrative Konfiguration ohne Adminberechtigung.
- [ ] Audit-Eintrag nach erfolgreicher Konfigurationsänderung.
- [ ] Kein Audit-Eintrag mit Secret-Klartext.

## 14.4 SSE-Tests

- [ ] Korrekte Eventformatierung.
- [ ] Tokenstream.
- [ ] Mehrzeilige Daten.
- [ ] Fehler nach Streamstart.
- [ ] Done-Ereignis.
- [ ] Clientabbruch.
- [ ] Modellabbruch.
- [ ] Toolabbruch.
- [ ] Keepalive.
- [ ] Request-ID im Streamkontext.
- [ ] Keine internen Exceptiondetails im Stream.
- [ ] Genau ein Abschlussereignis.
- [ ] Unbekanntes Providereignis wird nicht ungeprüft weitergereicht.

## 14.5 Frontend-Unit-Tests

- [ ] Bootstrap-Validator.
- [ ] Hierarchie-Validator.
- [ ] UI-Schema-Validator.
- [ ] Modell-Validator.
- [ ] Tool-Validator.
- [ ] Config-Validator.
- [ ] SSE-Parser.
- [ ] Endpoint-Auflösung.
- [ ] Fremde Origin wird abgelehnt.
- [ ] ComponentRegistry lehnt unbekannte Komponenten ab.
- [ ] ActionRegistry lehnt unbekannte Aktionen ab.
- [ ] GenericTree mit deaktiviertem Knoten.
- [ ] GenericTree mit nicht auswählbarem Knoten.
- [ ] SchemaRenderer mit unbekannter Komponente.
- [ ] SchemaRenderer mit fehlerhafter Einzelkomponente.
- [ ] SchemaRenderer für Knotentyp `user`.
- [ ] ModelSelector.
- [ ] ToolSelector.
- [ ] Store-Reducer bei Revisionwechsel.
- [ ] Store bereinigt nicht mehr vorhandene Auswahl.
- [ ] Ältere Ladeantwort überschreibt neuere nicht.
- [-] Tests für grundlegende Projektauswahl und Baumdarstellung sind teilweise vorhanden beziehungsweise vorbereitet.

## 14.6 Integrationstests

- [ ] Bootstrap lädt erfolgreich.
- [ ] Danach werden UI-Schema und Hierarchie geladen.
- [ ] Modelle und Tools werden nur bei Capability geladen.
- [ ] App startet ohne Modell- oder Toolregistry degradiert.
- [ ] Root-Knoten wird korrekt dargestellt.
- [ ] Knotenauswahl öffnet die passende schema-gesteuerte Ansicht.
- [ ] Knotentyp `user` wird über den zentralen `SchemaRenderer` dargestellt.
- [ ] Chat sendet aktuelle Knoten-ID.
- [ ] Chat sendet Modell- und Toolauswahl.
- [ ] SSE-Antwort wird inkrementell dargestellt.
- [ ] Konfigurationsänderung löst gezielten Reload aus.
- [ ] Unbekannte Komponente wird sichtbar als nicht unterstützt dargestellt.
- [ ] Unbekannte Aktion wird nicht ausgeführt.
- [ ] Produktionsbuild erfolgreich.
- [ ] Backend und Frontend gemeinsam startbar.
- [ ] React-StrictMode verursacht keine doppelten dauerhaften Requests oder Streams.

---

# 15. Dokumentation

- [-] README wurde an den erweiterten Projektumfang angepasst.
- [x] Projektprompt liegt in `PROJECT_PROMPT.md`.
- [ ] Architekturübersicht mit tatsächlichen Modulpfaden aktualisieren.
- [ ] Bootstrap-Ablauf dokumentieren.
- [ ] Beispielantwort für `/api/v1/bootstrap` ergänzen.
- [ ] Beispielantwort für `/api/v1/ui/schema` ergänzen.
- [ ] Beispielantwort für `/api/v1/hierarchy` ergänzen.
- [ ] Beispielantwort für `/api/v1/models` ergänzen.
- [ ] Beispielantwort für `/api/v1/tools` ergänzen.
- [ ] `ChatRequest` vollständig dokumentieren.
- [ ] SSE-Ereignisse dokumentieren.
- [ ] Bedeutung aller Revisionen erklären.
- [ ] Unterschied zwischen API-Version und Schema-Version erklären.
- [ ] `minimum_client_version` erklären.
- [ ] Sicherheitsgrenze zwischen UI-Hinweis und Autorisierung erklären.
- [ ] Regeln für neue Komponenten festhalten.
- [ ] Regeln für neue Aktionen festhalten.
- [ ] Regeln für neue Knotentypen festhalten.
- [ ] Regeln für neue Modelle und Tools festhalten.
- [ ] Regeln für Provider und Manifeste festhalten.
- [ ] Migrationshinweis für alten Hierarchie-Endpunkt ergänzen.
- [ ] Fehlercodes dokumentieren.
- [ ] Betriebsprofile und Sicherheitsuntergrenzen dokumentieren.
- [ ] OpenAPI nach jeder Vertragsänderung aktualisieren und prüfen.
- [ ] README-Angaben nach Abschluss jeder Phase mit dem tatsächlichen Stand synchronisieren.

---

# 16. Bereinigung der Einstiegspunkte und Projektstruktur

## 16.1 Frontend-Einstieg

- [x] React-Anwendung wird über `main.tsx` gestartet.
- [x] `AppProviders` umschließt die Anwendung zentral.
- [x] Fehlendes Root-Element führt zu einem klaren Fehler.
- [ ] Sicherstellen, dass keine zweite konkurrierende Einstiegspunktdatei mit eigener Renderlogik existiert.
- [ ] Alte beziehungsweise doppelte Bootstrap- oder Providerinitialisierung entfernen.
- [ ] `StrictMode`-Verhalten in Datenlade- und Streamlogik berücksichtigen.
- [ ] Importreihenfolge und globale Styles konsistent halten.

## 16.2 Backend-Bootstrap

- [-] Bootstrap-Schritte besitzen eigene Fehlerklassen.
- [-] Initialisierung ist in klarere Schritte aufgeteilt.
- [-] Asynchrone und synchrone Initialisierungsrückgaben werden berücksichtigt.
- [ ] Bootstrap-Schritte vollständig dokumentieren.
- [ ] Reihenfolgeabhängigkeiten explizit machen.
- [ ] Cleanup beziehungsweise Shutdown für Registries und Provider ergänzen.
- [ ] Teilinitialisierte Zustände bei Fehlern sauber zurückrollen.
- [ ] Logging um `request_id` beziehungsweise Startkontext ergänzen.
- [ ] Bootstrap-Status nicht als veränderbaren globalen Singleton ablegen.

---

# 17. Empfohlene Umsetzungsreihenfolge

## Phase A – Aktuelle Verträge verifizieren und korrigieren

1. [!] Tatsächliches OpenAPI-Dokument und Laufzeitantworten inventarisieren.
2. [ ] Falschen `/hierarchy`-Handler beziehungsweise dessen `response_model` korrigieren.
3. [ ] Öffentliche Backend-Verträge inventarisieren.
4. [ ] Endgültigen Hierarchie-Vertrag festlegen.
5. [ ] Endgültigen UI-Schema-Vertrag festlegen.
6. [ ] Contract-Module konsolidieren.
7. [ ] Strukturierte Fehler vereinheitlichen.
8. [ ] OpenAPI neu erzeugen und prüfen.

## Phase B – Bootstrap-zentriertes Frontend

1. [-] Frontend-Einstieg und Providerstruktur konsolidieren.
2. [ ] Bootstrap-Vertrag im Frontend ergänzen.
3. [ ] Bootstrap zuerst laden.
4. [ ] Endpoint-Auflösung zentralisieren.
5. [ ] Store um Bootstrap, Capabilities, Versionen und Revisionen erweitern.
6. [ ] Hart codierte Fachendpunkte entfernen.
7. [ ] StrictMode-sichere Initialisierung gewährleisten.

## Phase C – Hierarchie und SchemaRenderer

1. [-] Generischen Baum weiterverwenden und vervollständigen.
2. [ ] Hierarchie-Endpunkt vollständig implementieren.
3. [ ] Hierarchie-Frontendvertrag abgleichen.
4. [-] UI-Schema-Normalisierung vervollständigen.
5. [ ] UI-Schema-Endpunkt vollständig implementieren.
6. [ ] Komponenten-Registry finalisieren.
7. [-] Zentralen `SchemaRenderer` vollständig anbinden.
8. [-] Knotentyp `user` auf schema-gesteuerte Darstellung umstellen.
9. [ ] Weitere Platzhalter schrittweise ersetzen.

## Phase D – Modelle, Tools und Chat

1. [-] Modell- und Tool-Registries stabilisieren.
2. [ ] Manifestvalidierung und Fehlerisolierung testen.
3. [ ] Modellverträge und `ModelSelector` ergänzen.
4. [ ] Toolverträge und `ToolSelector` ergänzen.
5. [ ] `ChatRequest` vollständig anbinden.
6. [ ] SSE-Vertrag stabilisieren.
7. [ ] Chatstream robust testen.

## Phase E – Konfiguration, Revisionen und Sicherheit

1. [ ] Config-Revisionen atomar anbinden.
2. [ ] Registry-Revisionen anbinden.
3. [ ] Zielgerichtete Cache-Invalidierung implementieren.
4. [ ] Autorisierung vollständig prüfen.
5. [ ] Audit-Logging prüfen.
6. [ ] Betriebsprofile absichern.
7. [ ] Request-ID und strukturierte Fehler vollständig integrieren.

## Phase F – Abschluss

1. [ ] Backend-Unit-Tests vervollständigen.
2. [ ] Frontend-Unit-Tests ergänzen.
3. [ ] Integrationstests ausführen.
4. [ ] `npm run build` erfolgreich ausführen.
5. [ ] Backendtests erfolgreich ausführen.
6. [ ] OpenAPI-Diff prüfen.
7. [-] README und Projektdokumentation aktualisieren.
8. [ ] Gemeinsamen Start über `start.ps1` prüfen.
9. [ ] MVP-Abnahmekriterien vollständig dokumentieren und abnehmen.

---

# 18. Unmittelbar nächste Arbeitspakete

## Priorität 1 – Bootstrap und öffentliche Verträge

- [ ] Aktuelle OpenAPI-Ausgabe sichern.
- [ ] Tatsächliche Response-Modelle von Bootstrap, Hierarchie und UI-Schema prüfen.
- [ ] `BootstrapResponse` finalisieren.
- [ ] `HierarchyTreeResponse` finalisieren.
- [ ] `UISchemaResponse` und `UISchemaDocument` finalisieren.
- [ ] Gemeinsame Versionskonstanten definieren.
- [ ] Strukturierte Fehlerantwort für diese Endpunkte vereinheitlichen.

## Priorität 2 – Frontend-Bootstrap

- [ ] Bootstrap-Validator erstellen.
- [ ] Bootstrap-Service erstellen.
- [ ] Zentralen Endpoint-Resolver erstellen.
- [ ] Bootstrap vor allen weiteren Ressourcen laden.
- [ ] Hart codierte Endpunkte entfernen.
- [ ] Fehlerzustand für ungültigen Bootstrap implementieren.

## Priorität 3 – SchemaRenderer

- [ ] `componentRegistry.tsx` finalisieren.
- [ ] `SchemaRenderer` rekursiv und fehlertolerant implementieren.
- [ ] `UnsupportedSchema` vervollständigen.
- [ ] Knotentyp `user` vollständig über den Renderer darstellen.
- [ ] Danach weitere Knotentypen ohne fachlich fest verdrahtete React-Komponenten migrieren.

## Priorität 4 – Tests und Nachweis

- [ ] OpenAPI-Vertragstest für `/hierarchy`.
- [ ] Bootstrap-Vertragstest.
- [ ] UI-Schema-Normalisierungstests.
- [ ] Frontend-Test für Bootstrap-Ladefolge.
- [ ] Frontend-Test für unbekannte Schema-Komponente.
- [ ] Gemeinsamen Entwicklungsstart prüfen.

---

# 19. MVP-Abnahmekriterien

Der MVP gilt für diesen Arbeitsschritt als konsistent, wenn:

- [ ] `/api/v1/bootstrap` einen validen, versionierten und nicht sensiblen Vertrag liefert.
- [ ] Das Frontend alle fachlichen Endpunkte aus dem Bootstrap bezieht.
- [ ] `/api/v1/hierarchy` keinen `HealthResponse` oder anderen falschen Vertrag mehr liefert.
- [ ] Hierarchie und UI-Schema jeweils genau einen klaren öffentlichen Vertrag besitzen.
- [ ] Transport-Wrapper und fachliche Dokumente eindeutig getrennt sind.
- [ ] Alle API-Antworten vor Store-Übernahme validiert werden.
- [ ] Unbekannte Komponenten und Aktionen sicher behandelt werden.
- [ ] Neue Knotentypen keine neue fachlich fest verdrahtete React-Komponente benötigen.
- [ ] Der zentrale `SchemaRenderer` ausgewählte Knotenansichten darstellen kann.
- [ ] Der Knotentyp `user` schema-gesteuert dargestellt wird.
- [ ] Modelle und Tools gelistet und auswählbar sind, ohne daraus eine Freigabe abzuleiten.
- [ ] Modell- und Tool-Registries Fehler isoliert behandeln.
- [ ] Der Chat Knoten-, Modell- und Toolkontext übertragen kann.
- [ ] SSE-Fehler, Abschluss und Abbrüche sauber behandelt werden.
- [ ] Konfigurationsänderungen revisionsgeschützt und auditierbar sind.
- [ ] Strukturierte Fehler inklusive Request-ID funktionieren.
- [ ] Sicherheitsuntergrenzen durch das Betriebsprofil erzwungen werden.
- [ ] Backend und Frontend gemeinsam starten.
- [ ] Backendtests und Frontendbuild erfolgreich sind.
- [ ] OpenAPI den tatsächlich implementierten Verträgen entspricht.
- [ ] README, TODO und Architekturdokumentation denselben Projektstand wiedergeben.
