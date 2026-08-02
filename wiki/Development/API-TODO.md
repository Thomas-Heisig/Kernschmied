# TODO – API-Ausbau und Ressourcenverwaltung

**Stand: 02.08.2026**

## Statuslegende

* `[x]` umgesetzt
* `[-]` teilweise umgesetzt oder vorbereitet
* `[ ]` offen
* `[!]` muss geprüft oder bewusst entschieden werden
* `[~]` langfristig geplant

---

# Ziel

Die Kernschmied-API wird von einer technischen MVP-Schnittstelle zu einer konsistenten, ressourcenorientierten und versionierten Plattform-API ausgebaut.

Dabei gelten folgende Grundsätze:

* Neue Endpunkte werden nur zusammen mit stabilen Verträgen eingeführt.
* Jeder öffentliche Endpunkt besitzt ein dokumentiertes Response-Modell.
* Dynamische Erkennung bedeutet niemals automatische Aktivierung oder Freigabe.
* Jede Mutation wird serverseitig autorisiert.
* Secrets werden niemals im Klartext ausgegeben.
* Ressourcen besitzen eindeutige IDs, Revisionen und Schema-Versionen.
* Neue Router werden zentral registriert.
* Frontend und Backend verwenden denselben öffentlichen Vertrag.
* Keine leeren Placeholder-Endpunkte ohne Domainmodell und Service.
* Jede neue Ressource erhält Tests, OpenAPI-Dokumentation und Benutzer- oder Entwicklerdokumentation.
* Bestehende Funktionsketten werden abgeschlossen, bevor weitere große Subsysteme begonnen werden.

---

# 1. Bestehende API inventarisieren und konsolidieren

## 1.1 Aktuelle Endpunkte bestätigen

* [x] `GET /api/v1/health`
* [x] `GET /api/v1/bootstrap`
* [x] `GET /`
* [x] `GET /api/v1/settings/catalog`
* [x] `GET /api/v1/ui/schema`
* [x] Kalenderauswahl
* [x] Kalender-CRUD
* [x] Event-CRUD
* [x] Hierarchie laden
* [x] Hierarchieknoten erstellen
* [x] Hierarchieknoten aktualisieren
* [x] Hierarchieknoten verschieben
* [x] Hierarchie neu ordnen
* [x] Hierarchieknoten löschen
* [x] Dokumentationsübersicht
* [x] Dokumentationsseite laden
* [x] Modellprovider aus Modell-Registry auflisten
* [x] Modelle auflisten
* [x] Tools auflisten
* [x] Chatstream
* [-] Chatnachrichten einer Unterhaltung laden
* [x] Konfiguration auflisten
* [x] Konfiguration atomar aktualisieren
* [x] Einzelnen Konfigurationswert aktualisieren

## 1.2 Zentrale Routerregistrierung

* [ ] Alle öffentlichen v1-Router inventarisieren.
* [ ] Prüfen, welche Router außerhalb von `backend/app/api/v1/router.py` registriert werden.
* [ ] Kalender-, Dokumentations- und Settings-Router zentral registrieren.
* [ ] Doppelte Routerregistrierungen entfernen.
* [ ] Prefix und Tags ausschließlich zentral definieren.
* [ ] Sicherstellen, dass jede öffentliche Route in OpenAPI erscheint.
* [ ] Sicherstellen, dass keine interne Debugroute produktiv veröffentlicht wird.
* [ ] Router-Reihenfolge bei statischen und dynamischen Pfaden prüfen.
* [ ] `/providers` vor `/{provider_id}` registrieren.
* [ ] `/models/providers` vor `/{model_id}` registrieren.
* [ ] `/prompts/test-cases` vor `/{prompt_id}` registrieren.

### Zieldatei

```text
backend/app/api/v1/router.py
```

### Verifikation

```powershell
cd F:\Kernschmied\backend

python -c "
from main import app
schema = app.openapi()
for path in sorted(schema['paths']):
    print(path)
"
```

---

# 2. Gemeinsame API-Verträge

## 2.1 Listenverträge

* [ ] Einheitlichen Grundvertrag für Ressourcenlisten definieren.
* [ ] `schema_version` verpflichtend ausgeben.
* [ ] `revision` oder `registry_revision` eindeutig verwenden.
* [ ] `items` immer als Array ausgeben.
* [ ] Cursor-basierte Pagination vorbereiten.
* [ ] `next_cursor` standardmäßig `null` ausgeben.
* [ ] `request_id` einheitlich ausgeben.
* [ ] Filterparameter dokumentieren.
* [ ] Sortierung deterministisch festlegen.

### Zielstruktur

```json
{
  "schema_version": "1.0",
  "revision": 12,
  "items": [],
  "next_cursor": null,
  "request_id": "..."
}
```

## 2.2 Einzelressourcen

* [ ] Einheitliche Response-Struktur für Einzelressourcen definieren.
* [ ] Ressourcenrevision und globale Revision unterscheiden.
* [ ] `request_id` ergänzen.
* [ ] Soft-deleted oder archivierte Ressourcen eindeutig kennzeichnen.
* [ ] Unbekannte zusätzliche Felder ablehnen.

## 2.3 Mutationen

* [ ] Einheitlichen Mutationsvertrag definieren.
* [ ] Statuswerte festlegen:

  * `created`
  * `updated`
  * `deleted`
  * `archived`
  * `restored`
  * `moved`
  * `reordered`
* [ ] Neue Revision ausgeben.
* [ ] Geänderte Ressource oder ID ausgeben.
* [ ] `expected_revision` für konfliktanfällige Mutationen verwenden.
* [ ] Revisionskonflikte als `409` ausgeben.

### Zielstruktur

```json
{
  "schema_version": "1.0",
  "status": "updated",
  "revision": 13,
  "item": {},
  "request_id": "..."
}
```

## 2.4 Fehlerverträge

* [ ] Zentrales Fehler-Pydantic-Modell verwenden.
* [ ] Alle Fehler im Format `code`, `message`, `details`, `request_id` ausgeben.
* [ ] Keine internen Stacktraces öffentlich ausgeben.
* [ ] Fehlercodes pro Ressourcengruppe dokumentieren.
* [ ] FastAPI-Standardfehler vereinheitlichen.
* [ ] `X-Request-ID` immer als Header setzen.
* [ ] SSE-Fehler auf dasselbe fachliche Fehlerformat abbilden.

---

# 3. Bestehende Hierarchie-API vervollständigen

## 3.1 Response-Verträge

* [ ] `HierarchyMutationResponse` definieren.
* [ ] `HierarchyDeleteResponse` definieren.
* [ ] `HierarchyReorderResponse` definieren.
* [ ] Create-, Update- und Move-Antworten vereinheitlichen.
* [ ] Baumrevision und Knotenrevision getrennt ausgeben.
* [ ] `request_id` ergänzen.
* [ ] OpenAPI-Response-Schemas prüfen.

## 3.2 Frontend-Verträge

* [ ] `frontend/src/api/hierarchy.ts` von `unknown` auf konkrete Typen umstellen.
* [ ] Create-Response typisieren.
* [ ] Update-Response typisieren.
* [ ] Move-Response typisieren.
* [ ] Reorder-Response typisieren.
* [ ] Delete-Response typisieren.
* [ ] Laufzeitvalidierung vor Store-Übernahme ergänzen.
* [ ] Revisionskonflikte verständlich darstellen.

## 3.3 Hierarchie-Sicherheit

* [ ] Zyklen beim Verschieben sicher ablehnen.
* [ ] Verschieben in eigene Unterknoten ablehnen.
* [ ] Root-Knoten gegen unzulässiges Löschen schützen.
* [ ] Aktionen pro Benutzer serverseitig autorisieren.
* [ ] Sortierpositionen validieren.
* [ ] Gleichzeitige Änderungen per Revision absichern.
* [ ] Mutation auditieren.

---

# 4. Persistente Chats

**Priorität: kritisch**

## 4.1 Domainmodell

* [ ] `Conversation`-Modell definieren.
* [ ] `Message`-Modell definieren.
* [ ] Rollen festlegen:

  * `system`
  * `user`
  * `assistant`
  * `tool`
* [ ] Status festlegen:

  * aktiv
  * archiviert
  * gelöscht
* [ ] Hierarchieknoten-Zuordnung ergänzen.
* [ ] Modell-ID speichern.
* [ ] Tool-IDs beziehungsweise Toolaufrufe speichern.
* [ ] Nachrichtenreihenfolge deterministisch speichern.
* [ ] Erstellungs- und Änderungszeitpunkte timezone-aware speichern.
* [ ] Token- und Usage-Daten optional speichern.
* [ ] Metadaten validieren.
* [ ] Alembic-Migration erstellen.

## 4.2 Repository und Service

* [ ] `ChatRepository` als stabile Schnittstelle definieren.
* [ ] SQLAlchemy-Implementierung erstellen.
* [ ] In-Memory- oder Null-Repository nur für Tests verwenden.
* [ ] ChatService an persistentes Repository anbinden.
* [ ] Neue Unterhaltung atomar erstellen.
* [ ] Benutzer- und Assistentennachricht speichern.
* [ ] Toolaufrufe und Toolresultate speichern.
* [ ] Verlauf begrenzen und laden.
* [ ] Archivierung unterstützen.
* [ ] Soft Delete oder Hard Delete bewusst entscheiden.
* [ ] Zugriff serverseitig autorisieren.

## 4.3 Endpunkte

* [ ] `GET /api/v1/chats`
* [ ] `POST /api/v1/chats`
* [ ] `GET /api/v1/chats/{chat_id}`
* [ ] `PATCH /api/v1/chats/{chat_id}`
* [ ] `DELETE /api/v1/chats/{chat_id}`
* [ ] `GET /api/v1/chats/{chat_id}/messages`
* [ ] `POST /api/v1/chats/{chat_id}/messages`
* [ ] `POST /api/v1/chats/{chat_id}/archive`
* [ ] `POST /api/v1/chats/{chat_id}/restore`
* [ ] Cursor-Pagination für Chatlisten ergänzen.
* [ ] Suche nach Titel oder Inhalt später vorbereiten.

## 4.4 Frontend

* [ ] Chatliste anzeigen.
* [ ] Neue Unterhaltung erstellen.
* [ ] Bestehende Unterhaltung laden.
* [ ] Chat umbenennen.
* [ ] Chat archivieren.
* [ ] Chat löschen.
* [ ] Unterhaltung einem Hierarchieknoten zuordnen.
* [ ] Nach Neustart wieder öffnen.
* [ ] Chatstream mit persistierter Unterhaltung verbinden.
* [ ] Lade- und Fehlerzustände getrennt darstellen.
* [ ] Aktive Unterhaltung im Store speichern.

## 4.5 Tests

* [ ] Chat erstellen.
* [ ] Nachricht speichern.
* [ ] Nachrichtenreihenfolge prüfen.
* [ ] Unterhaltung laden.
* [ ] Fremden Chat ablehnen.
* [ ] Archivieren und Wiederherstellen.
* [ ] Löschen.
* [ ] Stream speichert Abschlussnachricht.
* [ ] Streamfehler erzeugt keine unvollständige Nachricht.
* [ ] Clientabbruch korrekt behandeln.

---

# 5. Prompt-Ressourcen

**Priorität: hoch**

## 5.1 Domainmodell

* [ ] Promptdefinition erstellen.
* [ ] Promptversion erstellen.
* [ ] Scope-Zuordnung definieren.
* [ ] Promptstatus definieren:

  * Entwurf
  * aktiv
  * archiviert
* [ ] Promptname und Beschreibung speichern.
* [ ] Inhalt versionieren.
* [ ] Variablen beziehungsweise Platzhalter dokumentieren.
* [ ] Autor und Änderungsgrund speichern.
* [ ] Aktivierungsrevision speichern.
* [ ] Alembic-Migration erstellen.

## 5.2 Endpunkte

* [ ] `GET /api/v1/prompts`
* [ ] `POST /api/v1/prompts`
* [ ] `GET /api/v1/prompts/{prompt_id}`
* [ ] `PATCH /api/v1/prompts/{prompt_id}`
* [ ] `DELETE /api/v1/prompts/{prompt_id}`
* [ ] `GET /api/v1/prompts/{prompt_id}/versions`
* [ ] `POST /api/v1/prompts/{prompt_id}/versions`
* [ ] `GET /api/v1/prompts/{prompt_id}/effective`
* [ ] `POST /api/v1/prompts/{prompt_id}/preview`
* [ ] `POST /api/v1/prompts/{prompt_id}/activate`
* [ ] `POST /api/v1/prompts/{prompt_id}/archive`

## 5.3 Prompt-Testfälle

* [ ] Domainmodell für Prompt-Testfälle definieren.
* [ ] Erst nach stabilem Prompt-CRUD implementieren.
* [ ] `GET /api/v1/prompts/test-cases`
* [ ] `POST /api/v1/prompts/test-cases`
* [ ] `PATCH /api/v1/prompts/test-cases/{test_case_id}`
* [ ] `DELETE /api/v1/prompts/test-cases/{test_case_id}`
* [ ] `POST /api/v1/prompts/{prompt_id}/test`

## 5.4 Prompt-Vererbung

* [ ] System-, Knoten-, Projekt-, Chat-, Benutzer- und Request-Scope unterstützen.
* [ ] Effektive Reihenfolge serverseitig auflösen.
* [ ] Merge-Ergebnis diagnostizierbar machen.
* [ ] Doppelte oder widersprüchliche Scope-Zuordnung behandeln.
* [ ] Effektiven Prompt im Frontend anzeigen.
* [ ] Keine Secrets in Promptvorschau ausgeben.

---

# 6. Administrative Provider-Ressourcen

**Priorität: hoch**

## 6.1 Begriffe trennen

* [x] `/models/providers` als aus Modellregistrierung abgeleitete Liste verwenden.
* [ ] `/providers` als administrative Providerressource definieren.
* [ ] Provider-ID und Provider-Typ eindeutig unterscheiden.
* [ ] Modellprovider und konkrete Providerinstanz unterscheiden.
* [ ] Keine Provider-Secrets über Modelllisten ausgeben.

## 6.2 Providervertrag

* [ ] `ProviderEntry`
* [ ] `ProviderListResponse`
* [ ] `ProviderDetailResponse`
* [ ] `ProviderUpdateRequest`
* [ ] `ProviderProbeResponse`
* [ ] Felder definieren:

  * ID
  * Name
  * Typ
  * aktiviert
  * konfiguriert
  * verfügbar
  * Fähigkeiten
  * Secret gesetzt
  * Revision
  * letzte Prüfung
  * Fehlermeldung ohne Secretdaten

## 6.3 Endpunkte

* [ ] `GET /api/v1/providers`
* [ ] `GET /api/v1/providers/{provider_id}`
* [ ] `PATCH /api/v1/providers/{provider_id}`
* [ ] `POST /api/v1/providers/{provider_id}/test`
* [ ] `GET /api/v1/providers/{provider_id}/models`
* [ ] `PUT /api/v1/providers/{provider_id}/secrets/{secret_key}`
* [ ] `DELETE /api/v1/providers/{provider_id}/secrets/{secret_key}`
* [ ] Provider aktivieren und deaktivieren.
* [ ] Provideränderungen revisionieren.
* [ ] Provideränderungen auditieren.

## 6.4 Sicherheitsregeln

* [ ] Secretwerte niemals zurückgeben.
* [ ] Nur `configured=true/false` ausgeben.
* [ ] Keine beliebigen Providerklassen aus API-Daten laden.
* [ ] Nur registrierte Provider-Typen zulassen.
* [ ] Base-URLs gegen Betriebsprofil und Allowlist prüfen.
* [ ] Timeouts und Limits serverseitig begrenzen.
* [ ] Provider-Probe rate-limitieren.

---

# 7. Modelldiagnose und Routing

## 7.1 Modelldiagnose

**Priorität: hoch**

* [ ] `GET /api/v1/diagnostics/models`
* [ ] `POST /api/v1/diagnostics/models/{model_id}/probe`
* [ ] Providerstatus anzeigen.
* [ ] Modellstatus anzeigen.
* [ ] letzte erfolgreiche Prüfung speichern.
* [ ] Latenz messen.
* [ ] Timeout erfassen.
* [ ] Fehlercode normalisieren.
* [ ] Keine Provider-Stacktraces ausgeben.
* [ ] Diagnosedaten zeitlich begrenzen.
* [ ] Probe nur für Berechtigte ausführen.
* [ ] Diagnose in Admin-UI anzeigen.

## 7.2 Modelldetail

* [ ] `GET /api/v1/models/{model_id}`
* [ ] Fähigkeiten anzeigen.
* [ ] Limits anzeigen.
* [ ] Providerzuordnung anzeigen.
* [ ] Aktivierungsstatus anzeigen.
* [ ] Verfügbarkeit anzeigen.
* [ ] Auswahlgrund oder Sperrgrund anzeigen.

## 7.3 Modellrouting

**Priorität: mittel**

* [ ] Domainmodell für Routingregeln definieren.
* [ ] Versionierung definieren.
* [ ] Prioritäten definieren.
* [ ] Fallbackmodell unterstützen.
* [ ] Capability-basierte Auswahl unterstützen.
* [ ] Hierarchie- und Scopebezug definieren.
* [ ] Kosten- und Latenzregeln später vorbereiten.
* [ ] `GET /api/v1/model-routing`
* [ ] `PUT /api/v1/model-routing`
* [ ] `POST /api/v1/model-routing/simulate`
* [ ] Routingentscheidung auditierbar machen.

---

# 8. Tools und Tool-Orchestrierung

## 8.1 Tooldetails

* [ ] `GET /api/v1/tools/{tool_id}`
* [ ] Toolmanifest frontendfähig ausgeben.
* [ ] Aktivierung, Verfügbarkeit und Auswählbarkeit unterscheiden.
* [ ] Eingabeschema ausgeben.
* [ ] Ausgabeschema ausgeben.
* [ ] Berechtigungen ausgeben.
* [ ] Bestätigungspflicht ausgeben.
* [ ] Interne Importpfade nicht ausgeben.

## 8.2 Tool-Simulationen

**Priorität: mittel**

* [ ] `POST /api/v1/tools/{tool_id}/simulate`
* [ ] Optional zusätzlich `GET /api/v1/tools/simulations`
* [ ] Dry-Run-Vertrag definieren.
* [ ] Eingabe validieren.
* [ ] Keine verändernde Aktion im Simulationsmodus erlauben.
* [ ] Simulationsergebnis normalisieren.
* [ ] Toolfehler isolieren.
* [ ] Simulationen protokollieren.
* [ ] Rate Limiting vorbereiten.

## 8.3 Toolausführung Ende-zu-Ende

* [ ] Modell-Tool-Call normalisieren.
* [ ] Tool-ID auflösen.
* [ ] Toolfreigabe prüfen.
* [ ] Benutzerberechtigung prüfen.
* [ ] Bestätigungspflicht prüfen.
* [ ] Eingabeschema validieren.
* [ ] Timeout setzen.
* [ ] Abbruch unterstützen.
* [ ] Tool ausführen.
* [ ] Ergebnis auf JSON-Werte begrenzen.
* [ ] Toolresultat speichern.
* [ ] Chatstream fortsetzen.
* [ ] Audit schreiben.
* [ ] Calculator als erstes vollständiges Tool anbinden.

---

# 9. Wissen und Gedächtnis

**Priorität: mittel**

## 9.1 Knowledge Entries

* [ ] Wissenseintrag-Domainmodell definieren.
* [ ] Versionierung definieren.
* [ ] Status definieren:

  * Entwurf
  * freigegeben
  * archiviert
* [ ] Quelle speichern.
* [ ] Titel und Inhalt speichern.
* [ ] Tags speichern.
* [ ] Hierarchieknoten zuordnen.
* [ ] Berechtigungen definieren.
* [ ] Metadaten validieren.
* [ ] Alembic-Migration erstellen.

## 9.2 Endpunkte

* [ ] `GET /api/v1/knowledge/entries`
* [ ] `POST /api/v1/knowledge/entries`
* [ ] `GET /api/v1/knowledge/entries/{entry_id}`
* [ ] `PATCH /api/v1/knowledge/entries/{entry_id}`
* [ ] `DELETE /api/v1/knowledge/entries/{entry_id}`
* [ ] `GET /api/v1/knowledge/entries/{entry_id}/versions`
* [ ] `POST /api/v1/knowledge/search`
* [ ] Suche zunächst ohne vollständiges RAG implementieren.
* [ ] Cursor-Pagination ergänzen.
* [ ] Objektbezogene Rechte berücksichtigen.

## 9.3 Knowledge Candidates

**Priorität: später**

* [ ] Lernkandidaten-Domainmodell definieren.
* [ ] Kandidaten niemals automatisch freigeben.
* [ ] Freigabeworkflow definieren.
* [ ] `GET /api/v1/knowledge/candidates`
* [ ] `POST /api/v1/knowledge/candidates/{candidate_id}/approve`
* [ ] `POST /api/v1/knowledge/candidates/{candidate_id}/reject`
* [ ] Freigaben auditieren.

---

# 10. Audit und Governance

**Priorität: hoch**

## 10.1 Auditmodell

* [ ] Audit-ID
* [ ] Zeitpunkt
* [ ] Benutzer beziehungsweise Actor
* [ ] Aktion
* [ ] Ressourcentyp
* [ ] Ressourcen-ID
* [ ] alte Revision
* [ ] neue Revision
* [ ] Request-ID
* [ ] Begründung
* [ ] sichere Änderungsmetadaten
* [ ] keine Secretwerte
* [ ] Unveränderlichkeit definieren
* [ ] Aufbewahrungskonzept vorbereiten

## 10.2 Endpunkte

* [ ] `GET /api/v1/audit`
* [ ] `GET /api/v1/audit/{audit_id}`
* [ ] `GET /api/v1/audit/resources/{resource_type}/{resource_id}`
* [ ] `GET /api/v1/diagnostics/audit`
* [ ] Filter nach Benutzer.
* [ ] Filter nach Aktion.
* [ ] Filter nach Ressource.
* [ ] Filter nach Zeitraum.
* [ ] Filter nach Request-ID.
* [ ] Cursor-Pagination.
* [ ] Keine Mutationsendpunkte für Auditdaten.

## 10.3 Bestehende Mutationen anbinden

* [ ] Configänderungen auditieren.
* [ ] Hierarchiemutationen auditieren.
* [ ] Provideränderungen auditieren.
* [ ] Promptänderungen auditieren.
* [ ] Toolfreigaben auditieren.
* [ ] Benutzer- und Rollenänderungen auditieren.
* [ ] Chatlöschung und Archivierung auditieren.

---

# 11. Benutzer, Rollen und Authentifizierung

**Nicht Teil des lokalen Development-MVP, aber erforderlich für Intranet**

## 11.1 Aktueller Benutzer

* [ ] `GET /api/v1/users/me`
* [ ] Benutzerprofil ausgeben.
* [ ] Rollen ausgeben.
* [ ] effektive Berechtigungen ausgeben.
* [ ] keine Sessiontokens ausgeben.
* [ ] Development-Identity klar kennzeichnen.

## 11.2 Benutzerverwaltung

* [ ] `GET /api/v1/users`
* [ ] `POST /api/v1/users`
* [ ] `GET /api/v1/users/{user_id}`
* [ ] `PATCH /api/v1/users/{user_id}`
* [ ] `DELETE /api/v1/users/{user_id}`
* [ ] Aktivieren und deaktivieren.
* [ ] Keine öffentliche Registrierung.
* [ ] Objektbezogene Sichtbarkeit beachten.

## 11.3 Rollenverwaltung

* [ ] `GET /api/v1/roles`
* [ ] `POST /api/v1/roles`
* [ ] `GET /api/v1/roles/{role_id}`
* [ ] `PATCH /api/v1/roles/{role_id}`
* [ ] `DELETE /api/v1/roles/{role_id}`
* [ ] Berechtigungen validieren.
* [ ] Systemrollen schützen.
* [ ] Änderungen auditieren.

## 11.4 Authentifizierung

* [ ] Authentifizierungsstrategie je Betriebsprofil festlegen.
* [ ] `POST /api/v1/auth/login`
* [ ] `POST /api/v1/auth/logout`
* [ ] `GET /api/v1/auth/session`
* [ ] Sessionrotation.
* [ ] sichere Cookies.
* [ ] CSRF-Schutz.
* [ ] Rate Limiting.
* [ ] Reverse-Proxy-Identität optional vorbereiten.
* [ ] OIDC später vorbereiten.
* [ ] Internetprofil darf `auth_mode=none` nicht akzeptieren.

---

# 12. Workflows

**Priorität: später**

## 12.1 Vorbedingungen

* [ ] Tool-Orchestrierung stabil.
* [ ] Audit stabil.
* [ ] Berechtigungen stabil.
* [ ] persistente Chats stabil.
* [ ] Promptversionierung stabil.
* [ ] keine automatische Ausführung unfreigegebener Aktionen.

## 12.2 Domainmodell

* [ ] Workflowdefinition
* [ ] Workflowversion
* [ ] Schritte
* [ ] Übergänge
* [ ] Eingabeschema
* [ ] Ausgabeschema
* [ ] Status
* [ ] Berechtigungen
* [ ] Bestätigungsschritte
* [ ] Fehlerstrategien
* [ ] Laufzeitinstanz

## 12.3 Endpunkte

* [ ] `GET /api/v1/workflows`
* [ ] `POST /api/v1/workflows`
* [ ] `GET /api/v1/workflows/{workflow_id}`
* [ ] `PATCH /api/v1/workflows/{workflow_id}`
* [ ] `DELETE /api/v1/workflows/{workflow_id}`
* [ ] `GET /api/v1/workflows/{workflow_id}/versions`
* [ ] `POST /api/v1/workflows/{workflow_id}/execute`
* [ ] `GET /api/v1/workflow-runs/{run_id}`
* [ ] `POST /api/v1/workflow-runs/{run_id}/cancel`

---

# 13. Artifacts und Ausgabeschemas

**Priorität: später**

## 13.1 Artifact-Schemas

* [ ] Schema-Domainmodell definieren.
* [ ] JSON-Schema validieren.
* [ ] Versionierung definieren.
* [ ] MIME-Typen definieren.
* [ ] erlaubte Renderer festlegen.
* [ ] `GET /api/v1/artifact-schemas`
* [ ] `POST /api/v1/artifact-schemas`
* [ ] `GET /api/v1/artifact-schemas/{schema_id}`
* [ ] `PATCH /api/v1/artifact-schemas/{schema_id}`
* [ ] `DELETE /api/v1/artifact-schemas/{schema_id}`

## 13.2 Artifacts

* [ ] Artifact-Domainmodell definieren.
* [ ] Besitzer und Hierarchieknoten speichern.
* [ ] Status und Version speichern.
* [ ] Speicherpfad nicht unkontrolliert öffentlich ausgeben.
* [ ] Inhalt oder Datei kontrolliert ausliefern.
* [ ] `GET /api/v1/artifacts`
* [ ] `POST /api/v1/artifacts`
* [ ] `GET /api/v1/artifacts/{artifact_id}`
* [ ] `PATCH /api/v1/artifacts/{artifact_id}`
* [ ] `DELETE /api/v1/artifacts/{artifact_id}`
* [ ] `GET /api/v1/artifacts/{artifact_id}/download`
* [ ] `GET /api/v1/artifacts/{artifact_id}/versions`
* [ ] Zugriff serverseitig autorisieren.

---

# 14. Connectoren

**Priorität: Zukunft**

## 14.1 Gemeinsamer Connectorvertrag

* [ ] Connector-ID
* [ ] Typ
* [ ] Name
* [ ] aktiviert
* [ ] konfiguriert
* [ ] verfügbar
* [ ] Fähigkeiten
* [ ] letzter Status
* [ ] Secretstatus
* [ ] Berechtigungen
* [ ] Revision

## 14.2 Allgemeine Endpunkte

* [ ] `GET /api/v1/connectors`
* [ ] `GET /api/v1/connectors/{connector_id}`
* [ ] `PATCH /api/v1/connectors/{connector_id}`
* [ ] `POST /api/v1/connectors/{connector_id}/test`

## 14.3 E-Mail

* [ ] `GET /api/v1/connectors/email`
* [ ] Postfächer listen.
* [ ] Nachrichten suchen.
* [ ] Nachricht lesen.
* [ ] Entwurf erstellen.
* [ ] Versand autorisieren.
* [ ] Anhänge kontrolliert behandeln.
* [ ] Audit ergänzen.

## 14.4 Kalender

* [ ] Bestehende Kalenderressourcen von Connector-Konten trennen.
* [ ] `GET /api/v1/connectors/calendar`
* [ ] Konten und Kalenderquellen listen.
* [ ] Synchronisierungsstatus anzeigen.
* [ ] Schreibberechtigungen getrennt behandeln.

## 14.5 Kontakte

* [ ] `GET /api/v1/connectors/contacts`
* [ ] Kontaktquellen listen.
* [ ] Kontakte suchen.
* [ ] personenbezogene Daten schützen.
* [ ] Mandanten- und Benutzergrenzen beachten.

## 14.6 Telefonie

* [ ] `GET /api/v1/connectors/telephony`
* [ ] SIP-Konten verwalten.
* [ ] keine Passwörter ausgeben.
* [ ] Anrufereignisse definieren.
* [ ] Einwilligung und Datenschutz prüfen.
* [ ] Telefonie nicht vor stabiler Authentifizierung aktivieren.

---

# 15. Editor-Registry

**Priorität: später**

* [ ] Unterschied zwischen UI-Komponenten und Editoren definieren.
* [ ] Editor-Registry nur aus fest registrierten Typen erzeugen.
* [ ] Keine dynamischen React-Imports zulassen.
* [ ] `GET /api/v1/ui/editors`
* [ ] Editor-ID
* [ ] unterstützte Datentypen
* [ ] unterstützte Schemas
* [ ] readonly-Unterstützung
* [ ] Validierungsfähigkeiten
* [ ] bekannte Komponentenreferenz
* [ ] nicht verfügbare Editoren sichtbar kennzeichnen.

---

# 16. Laufzeitdiagnose und Kosten

**Priorität: später**

## 16.1 Runtime

* [ ] `GET /api/v1/diagnostics/runtime`
* [ ] Laufzeit seit Start.
* [ ] Requestanzahl.
* [ ] Fehlerrate.
* [ ] Latenzverteilung.
* [ ] aktive Streams.
* [ ] Registryrevisionen.
* [ ] Configrevision.
* [ ] Datenbankstatus.
* [ ] keine sensiblen Systemdetails öffentlich ausgeben.

## 16.2 Kosten

* [ ] Usage-Daten zuverlässig speichern.
* [ ] Providerpreise versioniert konfigurieren.
* [ ] Kosten nie nur clientseitig berechnen.
* [ ] `GET /api/v1/diagnostics/costs`
* [ ] Filter nach Zeitraum.
* [ ] Filter nach Modell.
* [ ] Filter nach Provider.
* [ ] Filter nach Benutzer oder Projekt nur mit Berechtigung.
* [ ] lokale Modelle mit Kosten `0` oder Infrastrukturkosten getrennt behandeln.

---

# 17. Evaluations

**Priorität: Zukunft**

* [ ] Evaluation-Domainmodell definieren.
* [ ] Testsatz definieren.
* [ ] Modell- und Promptversion speichern.
* [ ] Metriken versionieren.
* [ ] manuelle und automatische Bewertung trennen.
* [ ] `GET /api/v1/evaluations`
* [ ] `POST /api/v1/evaluations`
* [ ] `GET /api/v1/evaluations/{evaluation_id}`
* [ ] `POST /api/v1/evaluations/{evaluation_id}/run`
* [ ] `GET /api/v1/evaluation-runs/{run_id}`
* [ ] reproduzierbare Parameter speichern.

---

# 18. Lernen und Optimierung

**Priorität: Zukunft**

## 18.1 Experiences

* [ ] Erfolgreiche und fehlgeschlagene Aufgaben strukturiert speichern.
* [ ] personenbezogene Daten minimieren.
* [ ] keine automatische Prompt- oder Configänderung.
* [ ] `GET /api/v1/learning/experiences`
* [ ] Filter nach Ergebnis und Ressource.
* [ ] Zugriff streng autorisieren.

## 18.2 Candidates

* [ ] Optimierungskandidat-Domainmodell definieren.
* [ ] Quelle und Begründung speichern.
* [ ] Status:

  * vorgeschlagen
  * geprüft
  * angenommen
  * abgelehnt
* [ ] `GET /api/v1/learning/candidates`
* [ ] `POST /api/v1/learning/candidates/{candidate_id}/approve`
* [ ] `POST /api/v1/learning/candidates/{candidate_id}/reject`
* [ ] niemals automatisch aktivieren.
* [ ] jede Entscheidung auditieren.

---

# 19. Settings-Katalog und Resource-Links

## 19.1 Katalogkonsistenz

* [ ] Jeden `resource_link` gegen die OpenAPI prüfen.
* [ ] `availability=available` nur für tatsächlich vorhandene Endpunkte verwenden.
* [ ] `availability=prepared` nur verwenden, wenn Domainmodell und Service vorhanden sind.
* [ ] `availability=planned` für reine Zukunftsfunktionen verwenden.
* [ ] Nicht vorhandene Endpunkte nicht anklickbar darstellen.
* [ ] Frontend soll geplante Ressourcen sichtbar als geplant kennzeichnen.
* [ ] Katalogeinträge mit erforderlichen Berechtigungen ergänzen.
* [ ] Resource-Link und HTTP-Methode getrennt modellieren.
* [ ] Keine fremden Origins zulassen.
* [ ] Resource-Links aus zentralem Bootstrap-Prefix erzeugen.

## 19.2 Abgleichstests

* [ ] Automatischen Test erstellen, der alle `available`-Links gegen OpenAPI prüft.
* [ ] Fehlende Route als Testfehler behandeln.
* [ ] Planned-Links nicht als Fehler behandeln.
* [ ] Prepared-Links als Warnung behandeln.
* [ ] Falsche HTTP-Methode erkennen.
* [ ] Doppelte Resource-Links erkennen.

---

# 20. Frontend-API-Schicht

## 20.1 Typisierte Clients

* [ ] `chatApi.ts`
* [ ] `chatsApi.ts`
* [ ] `promptsApi.ts`
* [ ] `providersApi.ts`
* [ ] `diagnosticsApi.ts`
* [ ] `knowledgeApi.ts`
* [ ] `auditApi.ts`
* [ ] `usersApi.ts`
* [ ] `authApi.ts`
* [ ] `workflowsApi.ts`
* [ ] `artifactsApi.ts`
* [ ] `connectorsApi.ts`

## 20.2 Regeln

* [ ] Einen zentralen API-Client verwenden.
* [ ] Endpunkte aus Bootstrap beziehen.
* [ ] Antworten vor Store-Übernahme validieren.
* [ ] `unknown` nicht dauerhaft weiterreichen.
* [ ] AbortSignal unterstützen.
* [ ] Request-ID auslesen.
* [ ] strukturierte Fehler verwenden.
* [ ] keine Secrets loggen.
* [ ] keine direkten `fetch()`-Aufrufe in UI-Komponenten.
* [ ] Retry nur bei eindeutig wiederholbaren Leseoperationen.

---

# 21. Berechtigungen

## 21.1 Ressourcenberechtigungen

* [ ] `chats:read`
* [ ] `chats:create`
* [ ] `chats:update`
* [ ] `chats:delete`
* [ ] `prompts:read`
* [ ] `prompts:write`
* [ ] `prompts:activate`
* [ ] `providers:read`
* [ ] `providers:write`
* [ ] `providers:secrets`
* [ ] `models:diagnose`
* [ ] `knowledge:read`
* [ ] `knowledge:write`
* [ ] `audit:read`
* [ ] `users:read`
* [ ] `users:write`
* [ ] `roles:write`
* [ ] `workflows:execute`
* [ ] `artifacts:read`
* [ ] `artifacts:write`

## 21.2 Regeln

* [ ] Berechtigungen zentral benennen.
* [ ] Keine Berechtigungsentscheidung im Frontend.
* [ ] Objektbezogene Rechte berücksichtigen.
* [ ] Listenantworten serverseitig filtern.
* [ ] Detailzugriffe separat prüfen.
* [ ] Mutationen separat prüfen.
* [ ] Secretberechtigungen getrennt prüfen.
* [ ] Fehler nicht unnötig Informationen über fremde Ressourcen preisgeben lassen.

---

# 22. Datenbank und Migrationen

* [ ] Für jede neue Ressource SQLAlchemy-Modelle erstellen.
* [ ] SQLite und PostgreSQL unterstützen.
* [ ] Alembic-Migrationen ergänzen.
* [ ] Upgrade testen.
* [ ] Downgrade testen.
* [ ] Fremdschlüssel definieren.
* [ ] Löschverhalten bewusst festlegen.
* [ ] Indizes für häufige Filter ergänzen.
* [ ] Revisionen atomar speichern.
* [ ] Zeitstempel timezone-aware speichern.
* [ ] JSON-Felder validieren.
* [ ] Keine Secrets in normalen Configtabellen speichern.
* [ ] Seed-Daten versionieren.
* [ ] Migrationen in CI prüfen.

---

# 23. Tests

## 23.1 Vertragstests

* [ ] OpenAPI enthält alle erwarteten Endpunkte.
* [ ] Settings-Katalog-Links stimmen mit OpenAPI überein.
* [ ] Jede öffentliche Antwort besitzt `schema_version`.
* [ ] Mutationen besitzen `revision`.
* [ ] Fehler besitzen `request_id`.
* [ ] Keine Secrets in Providerantworten.
* [ ] Keine internen Importpfade in Toolantworten.

## 23.2 Chats

* [ ] Chat-CRUD
* [ ] Nachrichten-CRUD
* [ ] Archivierung
* [ ] Wiederherstellung
* [ ] Berechtigungen
* [ ] Stream-Persistenz
* [ ] Abbruch
* [ ] Parallelität

## 23.3 Prompts

* [ ] Prompt-CRUD
* [ ] Versionierung
* [ ] Aktivierung
* [ ] effektive Vererbung
* [ ] Preview
* [ ] Revisionskonflikt

## 23.4 Provider und Modelle

* [ ] Providerliste
* [ ] Providerdetail
* [ ] Secretstatus
* [ ] Providerprobe
* [ ] Modellprobe
* [ ] Provider-/Modellabweichung
* [ ] Providerfehler ohne Secretdaten

## 23.5 Hierarchie

* [ ] Create
* [ ] Update
* [ ] Move
* [ ] Reorder
* [ ] Delete
* [ ] Zyklus
* [ ] Revision
* [ ] Berechtigung

## 23.6 Frontend

* [ ] API-Validatoren
* [ ] Chatliste
* [ ] Prompteditor
* [ ] Providerverwaltung
* [ ] Hierarchiemutationen
* [ ] Settings-Resource-Links
* [ ] Audit-Viewer
* [ ] unbekannte Ressourcen
* [ ] strukturierte Fehler

---

# 24. Dokumentation

* [ ] OpenAPI nach jeder Endpunktänderung aktualisieren.
* [ ] Wiki-Seite für Chatressourcen erstellen.
* [ ] Wiki-Seite für Prompts erstellen.
* [ ] Wiki-Seite für Provideradministration erstellen.
* [ ] Wiki-Seite für Modelldiagnose erstellen.
* [ ] Wiki-Seite für Knowledge Entries erstellen.
* [ ] Wiki-Seite für Audit erstellen.
* [ ] Berechtigungsmatrix dokumentieren.
* [ ] Fehlercodes dokumentieren.
* [ ] Pagination dokumentieren.
* [ ] Revisionskonflikte dokumentieren.
* [ ] Secretverwaltung dokumentieren.
* [ ] Resource-Link-Verhalten dokumentieren.
* [ ] Implementiert, vorbereitet und geplant klar unterscheiden.
* [ ] README-Endpunktübersicht mit OpenAPI synchronisieren.

---

# 25. Empfohlene Umsetzungsphasen

## Phase A – Bestehende Verträge fertigstellen

* [ ] Routerregistrierung vereinheitlichen.
* [ ] Hierarchie-Response-Verträge ergänzen.
* [ ] Frontend-Hierarchieantworten typisieren.
* [ ] bestehende Listen- und Mutationsverträge vereinheitlichen.
* [ ] Settings-Katalog automatisch gegen OpenAPI prüfen.

## Phase B – Persistente Chats

* [ ] Conversation- und Message-Domainmodell.
* [ ] Migration.
* [ ] Repository.
* [ ] Service.
* [ ] CRUD-Endpunkte.
* [ ] Frontend-Chatliste.
* [ ] Stream-Persistenz.
* [ ] Tests.

## Phase C – Prompts

* [ ] Prompt-Domainmodell.
* [ ] Versionen.
* [ ] CRUD.
* [ ] Scope-Zuordnung.
* [ ] Effective- und Preview-Endpunkte.
* [ ] Prompteditor.
* [ ] Tests.

## Phase D – Provider und Diagnose

* [ ] administrative Providerressource.
* [ ] Secretstatus und Secretänderung.
* [ ] Providertest.
* [ ] Modelldiagnose.
* [ ] Admin-UI.
* [ ] Tests.

## Phase E – Audit

* [ ] Auditmodell.
* [ ] Config-, Hierarchie-, Prompt- und Providerintegration.
* [ ] Leseendpunkte.
* [ ] Audit-Viewer.
* [ ] Tests.

## Phase F – Wissen

* [ ] Knowledge Entries.
* [ ] Versionierung.
* [ ] einfache Suche.
* [ ] Hierarchiezuordnung.
* [ ] Berechtigungen.
* [ ] Tests.

## Phase G – Intranet-Sicherheit

* [ ] Users.
* [ ] Roles.
* [ ] Sessions.
* [ ] Auth-Endpunkte.
* [ ] objektbezogene Berechtigungen.
* [ ] Audit.
* [ ] Sicherheitstests.

## Phase H – Spätere Erweiterungen

* [ ] Modellrouting.
* [ ] Tool-Simulation.
* [ ] Workflows.
* [ ] Artifacts.
* [ ] Connectoren.
* [ ] Editor-Registry.
* [ ] Runtime- und Kostenmetriken.
* [ ] Evaluations.
* [ ] Learning.

---

# 26. Unmittelbar nächste Arbeitspakete

## Priorität 1

* [ ] Zentrale Routerregistrierung bereinigen.
* [ ] Hierarchie-Mutationsantworten typisieren.
* [ ] `available`-Resource-Links gegen OpenAPI testen.

## Priorität 2

* [ ] Persistente Chatmodelle und Migration erstellen.
* [ ] Chat-CRUD-Endpunkte implementieren.
* [ ] Chatliste im Frontend anbinden.

## Priorität 3

* [ ] Prompt-Domainmodell und Promptversionen erstellen.
* [ ] Prompt-CRUD implementieren.
* [ ] Prompteditor vorbereiten.

## Priorität 4

* [ ] Administrative Providerressource implementieren.
* [ ] Secretstatus sicher abbilden.
* [ ] Provider- und Modellprobe implementieren.

## Priorität 5

* [ ] Auditmodell erstellen.
* [ ] Config- und Hierarchiemutationen anbinden.
* [ ] Audit-Leseendpunkte implementieren.

---

# 27. MVP-Abnahmekriterien für den API-Ausbau

Der erweiterte lokale MVP gilt als abgeschlossen, wenn:

* [ ] alle öffentlichen Router zentral registriert sind;
* [ ] alle vorhandenen Mutationen konkrete Response-Verträge besitzen;
* [ ] Settings-Katalog und OpenAPI konsistent sind;
* [ ] Chats und Nachrichten persistent sind;
* [ ] Chats vollständig erstellt, geladen, geändert, archiviert und gelöscht werden können;
* [ ] Promptressourcen versioniert verwaltet werden können;
* [ ] Provider administrativ sichtbar und testbar sind;
* [ ] Secrets niemals im Klartext ausgegeben werden;
* [ ] Modelldiagnose verfügbar ist;
* [ ] Hierarchieantworten im Frontend nicht mehr `unknown` sind;
* [ ] mindestens ein Tool vollständig Ende-zu-Ende funktioniert;
* [ ] Config-, Hierarchie-, Chat-, Prompt- und Provideränderungen auditierbar sind;
* [ ] alle neuen Endpunkte serverseitig autorisiert werden;
* [ ] Backend- und Frontendtests für die Kernressourcen vorhanden sind;
* [ ] OpenAPI, README, Wiki und Settings-Katalog denselben Stand wiedergeben.

---

# Zusammenfassung

Der nächste API-Ausbau sollte nicht aus einer großen Zahl isolierter `GET`-Endpunkte bestehen. Jede Ressource benötigt einen vollständigen vertikalen Schnitt:

```text
Domainmodell

↓

Datenbank und Migration

↓

Repository

↓

Service

↓

Autorisierung

↓

versionierter API-Vertrag

↓

Router

↓

Frontend-Client

↓

Benutzeroberfläche

↓

Tests und Dokumentation
```

Die wichtigste Reihenfolge lautet:

1. bestehende Verträge und Router konsolidieren,
2. persistente Chats,
3. Promptverwaltung,
4. Provideradministration und Modelldiagnose,
5. Audit,
6. Knowledge Entries,
7. Intranet-Benutzer und Authentifizierung,
8. Workflows, Artifacts, Connectoren und Lernen.

Back to [[TODO]].
