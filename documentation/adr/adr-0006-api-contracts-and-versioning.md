# ADR-0006: API-Verträge und API-Versionierung

- **Status:** Angenommen – konsolidiert
- **Datum der ursprünglichen Entscheidung:** 2026-07-27
- **Letzte Überarbeitung:** 2026-08-03
- **Entscheidungsträger:** Kernschmied-Architekturteam
- **Ersetzt:** Keine
- **Ersetzt durch:** Keine
- **Verwandte Dokumente:**

  - `documentation/leitkonzept.md`
  - `documentation/architecture/contracts.md`
  - `documentation/architecture/contract-refactoring.md`
  - `documentation/architecture/schema-versioning.md`
  - `documentation/architecture/effective-context.md`
  - `documentation/architecture/decisions/ADR-0001-schema-driven-user-interface.md`
  - `documentation/architecture/decisions/ADR-0002-configuration-architecture-and-runtime-initialization.md`
  - `documentation/architecture/decisions/ADR-0003-registry-based-extension-architecture.md`
  - `documentation/architecture/decisions/ADR-0004-security-profiles-and-deployment-modes.md`
  - `documentation/architecture/decisions/ADR-0005-versioned-contracts-and-schema-evolution.md`

---

## 1. Entscheidung in Kurzform

Kernschmied verwendet eine **Contract-First-API-Architektur** mit expliziter URL-Versionierung für öffentliche HTTP-Schnittstellen.

Die öffentliche REST-API wird unter einem stabilen Hauptversionspräfix bereitgestellt:

```text
/api/v1
```

Innerhalb einer API-Hauptversion gelten stabile Transportverträge.

Kompatible Erweiterungen werden bevorzugt additiv eingeführt.

Inkompatible Änderungen benötigen:

- eine neue API-Hauptversion,
- eine neue konkrete Vertragsversion,
- einen dokumentierten Migrationspfad,
- eine kontrollierte Übergangsphase.

Die zentrale Regel lautet:

> APIs sind eigenständige Produkte.
> Jeder öffentliche Vertrag wird bewusst entworfen, versioniert, validiert, dokumentiert und getestet.

Die API-Version ersetzt nicht die Schemaversion einzelner Payloads.

Kernschmied unterscheidet ausdrücklich:

- API-Version,
- Payload-Schemaversion,
- Definitionversion,
- Manifestversion,
- Objekt-Revision,
- Registry-Revision.

---

# 2. Kontext

Kernschmied besteht aus mehreren Subsystemen, die sich teilweise unabhängig weiterentwickeln.

Dazu gehören:

- FastAPI-Backend,
- React-Frontend,
- Modellprovider,
- Toolprovider,
- administrative Oberflächen,
- Runtime-Registries,
- dynamische Definitionen,
- spätere Desktop-Clients,
- spätere Mobile-Clients,
- externe Integrationen,
- mögliche spätere Plugins.

Die Kommunikation erfolgt über explizite Verträge.

Beispiele:

- REST-Endpunkte,
- SSE-Streams,
- Bootstrap-Antworten,
- UI-Schemas,
- Hierarchieverträge,
- Konfigurationsverträge,
- Chatverträge,
- Modell- und Toolmetadaten,
- Registry-Verträge,
- Ressourcenverträge,
- Action-Verträge,
- Fehlerverträge.

Diese Systeme können unterschiedliche Releasezyklen besitzen.

Das Frontend kann beispielsweise älter sein als das Backend.

Eine externe Integration kann einen öffentlichen Endpunkt länger verwenden als die interne Webanwendung.

Deshalb müssen öffentliche Schnittstellen langfristig:

- stabil,
- nachvollziehbar,
- validierbar,
- dokumentiert,
- migrationsfähig

bleiben.

---

# 3. Problemstellung

Ohne klare API-Versionierungs- und Vertragsregeln können bereits kleine Backendänderungen bestehende Clients beschädigen.

Typische Beispiele:

- JSON-Feld umbenennen,
- Pflichtfeld ergänzen,
- Feld entfernen,
- `null` nicht mehr zulassen,
- Antwortstruktur verändern,
- Statuscode verändern,
- Fehlerformat verändern,
- Endpointsemantik verändern,
- Pagination ändern,
- Sortierreihenfolge ändern,
- SSE-Ereignis umbenennen,
- Enumwert entfernen,
- neue Validierung einführen.

Diese Probleme werden kritischer, sobald mehrere Clients und Integrationen existieren.

## 3.1 Implizite Verträge

Auch wenn ein Feld nicht ausdrücklich dokumentiert ist, kann ein Client davon abhängen.

Beispiel:

```json
{
  "items": []
}
```

Wird daraus später:

```json
{
  "results": []
}
```

entsteht ein Vertragsbruch.

## 3.2 Routerlokale Modelle

Wenn öffentliche Request- und Response-Modelle direkt in Routerdateien definiert werden, entstehen:

- Duplikate,
- uneinheitliche Benennungen,
- schwer auffindbare Verträge,
- unterschiedliche Fehlerformate.

## 3.3 Direkte Datenbankmodelle als API-Antwort

Werden SQLAlchemy-Modelle direkt serialisiert, können interne Felder unbeabsichtigt öffentlich werden.

Beispiele:

- interne IDs,
- Secretreferenzen,
- technische Statusfelder,
- Fremdschlüssel,
- Auditmetadaten.

## 3.4 Uneinheitliche Listenverträge

Verschiedene Endpunkte liefern möglicherweise:

```text
items
results
data
entries
```

oder unterschiedliche Pagination.

Das erschwert Frontend und Integrationen.

## 3.5 Uneinheitliche Fehler

Ein Endpunkt liefert:

```json
{
  "detail": "Not found"
}
```

ein anderer:

```json
{
  "code": "NOT_FOUND",
  "message": "..."
}
```

Dadurch müssen Clients mehrere Fehlerformate behandeln.

## 3.6 API- und Payload-Version werden vermischt

Ein Endpunkt unter `/api/v1` kann mehrere konkrete Payload-Verträge besitzen.

Die URL-Hauptversion allein beschreibt nicht jede Vertragsfamilie ausreichend.

## 3.7 Backendänderungen werden nicht automatisch erkannt

Ohne OpenAPI-Diff und Vertragstests können Breaking Changes unbemerkt in den Code gelangen.

---

# 4. Abgrenzung zur allgemeinen Schema-Versionierung

ADR-0005 beschreibt die allgemeine Entwicklung versionierter Verträge und gespeicherter Definitionen.

Diese ADR konkretisiert die öffentliche API-Schicht.

Sie behandelt insbesondere:

- HTTP-Endpunkte,
- URL-Versionierung,
- Requests,
- Responses,
- Fehler,
- Pagination,
- Statuscodes,
- OpenAPI,
- SSE als öffentlicher Transport,
- Deprecation öffentlicher Endpunkte.

Dabei gilt:

```text
API-Version
≠
Payload-Schemaversion
≠
Objekt-Revision
```

Beispiel:

```text
/api/v1/resources
```

kann einen Payload mit folgendem Feld liefern:

```json
{
  "schema_version": "1.1"
}
```

---

# 5. Aktueller Zustand – IST

Kernschmied besitzt bereits wichtige Grundlagen einer versionierten API.

## 5.1 Bereits vorhanden

- API-Präfix `/api/v1`,
- FastAPI und OpenAPI,
- Bootstrap-Endpunkt,
- UI-Schema-Endpunkt,
- Hierarchie-Endpunkte,
- Chat-SSE-Endpunkt,
- Modell- und Toolendpunkte,
- Config-Endpunkte,
- Health-Endpunkte,
- strukturierte Chatfehler,
- Pydantic-v2-Verträge,
- Request-ID-Grundlagen,
- Versionsinformationen im Bootstrap.

## 5.2 Teilweise implementiert

- zentralisierte öffentliche Contract-Module,
- einheitliche Listenverträge,
- einheitliche Mutationsantworten,
- konsistente Pagination,
- vollständige strukturierte Fehler,
- Request-ID in allen Antworten,
- OpenAPI-Diff-Prüfung,
- Frontend-Laufzeitvalidierung,
- endpointbasierte Capability Negotiation,
- Deprecation-Metadaten,
- gemeinsame Response-Envelopes.

## 5.3 Derzeitige Inkonsistenzen

- einzelne öffentliche Modelle liegen noch direkt in Routerdateien,
- einige Endpunkte verwenden noch FastAPI-Standardfehler,
- Listenantworten sind nicht überall einheitlich,
- Statuscodes und Mutationsantworten sind noch nicht vollständig harmonisiert,
- Request-ID ist noch nicht in allen Fehler- und Erfolgsantworten konsistent,
- Health-Endpunkte liegen teilweise außerhalb des `/api/v1`-Präfixes,
- Bootstrap-Endpointschlüssel und konkrete Routen sind noch nicht vollständig vereinheitlicht,
- Frontendcode verwendet teilweise feste Pfade statt Bootstrap-Endpointschlüssel,
- nicht alle Antworten werden im Frontend zur Laufzeit validiert,
- SSE verwendet teilweise Übergangs- oder Aliasereignisse.

---

# 6. Zielzustand – SOLL

Kernschmied soll eine konsistente, versionierte und dokumentierte öffentliche API besitzen.

```text
Client
  ↓
versionierter API-Endpunkt
  ↓
Request-Vertrag
  ↓
Authentifizierung und Autorisierung
  ↓
Anwendungsservice
  ↓
Domain und Persistenz
  ↓
Response-Vertrag
  ↓
OpenAPI und Laufzeitvalidierung
```

Jede öffentliche Route besitzt:

- stabile URL,
- dokumentierte HTTP-Methode,
- versionierten Request-Vertrag,
- versionierten Response-Vertrag,
- dokumentierte Statuscodes,
- strukturierte Fehler,
- Request-ID,
- Autorisierungsanforderungen,
- Tests.

---

# 7. Entscheidung

Kernschmied verwendet dauerhaft eine Contract-First-API-Architektur.

Die Entscheidung umfasst folgende verbindliche Punkte.

## 7.1 URL-Versionierung

Öffentliche REST-Endpunkte werden über ein Hauptversionspräfix versioniert.

```text
/api/v1
```

Eine spätere inkompatible API kann parallel bereitgestellt werden:

```text
/api/v1
/api/v2
```

## 7.2 Payload-Verträge bleiben separat versioniert

Jede zentrale Vertragsfamilie besitzt zusätzlich eine eigene Schemaversion.

## 7.3 Backend-Contract-Module sind die öffentliche Quelle

Router importieren öffentliche Pydantic-Modelle aus:

```text
backend/app/contracts/
```

## 7.4 OpenAPI beschreibt nur tatsächlich erreichbare Verträge

Zukunftsverträge werden nicht künstlich als bereits verfügbare API dokumentiert.

## 7.5 Frontend validiert jede Antwort

Kein API-Payload wird ungeprüft in den Store übernommen.

## 7.6 Breaking Changes werden bewusst behandelt

Inkompatible Änderungen benötigen:

- neue Version,
- Migrationsweg,
- Deprecation oder Parallelbetrieb,
- Tests,
- Dokumentation.

---

# 8. Architekturprinzip

Die ursprüngliche Aussage:

> APIs are products.

wird verbindlich präzisiert zu:

> Jede öffentliche API ist ein eigenständiger, versionierter Produktvertrag.
> Pfad, Methode, Request, Response, Statuscodes, Fehler und Semantik werden bewusst gepflegt und dürfen nicht beiläufig verändert werden.

---

# 9. Zielarchitektur

```text
Frontend / Client
        ↓
Endpoint Resolver
        ↓
REST API v1
        ↓
Request Validation
        ↓
Authentication
        ↓
Authorization
        ↓
Application Service
        ↓
Repository / Integration
        ↓
Public Response Model
        ↓
OpenAPI
        ↓
Frontend Runtime Validation
```

Für Streaming:

```text
Client
  ↓
SSE-Endpunkt
  ↓
versionierter Event-Envelope
  ↓
bekannte Eventtypen
  ↓
Frontend Event Registry
```

---

# 10. URL-Versionierung

Öffentliche Hauptendpunkte verwenden:

```text
/api/v1/...
```

Beispiele:

```text
/api/v1/bootstrap
/api/v1/hierarchy
/api/v1/chat/stream
/api/v1/chats
/api/v1/models
/api/v1/tools
/api/v1/config
/api/v1/resources
/api/v1/registries
```

## 10.1 Warum URL-Versionierung?

Sie ist:

- explizit,
- leicht zu dokumentieren,
- einfach zu debuggen,
- proxyfreundlich,
- OpenAPI-kompatibel,
- für Browser und externe Integrationen verständlich.

## 10.2 Was URL-Versionierung nicht löst

Sie ersetzt nicht:

- Payload-Schemaversionen,
- Eventversionierung,
- Definitionversionen,
- Revisionen,
- Capability Negotiation.

---

# 11. Alternative Versionierungsmechanismen

Untersucht wurden:

- HTTP-Header,
- Content Negotiation,
- Media Types,
- Queryparameter,
- ausschließlich Payload-Versionen.

Diese Mechanismen können später ergänzend verwendet werden.

Sie werden jedoch nicht als primäre API-Hauptversionierung eingesetzt.

---

# 12. Öffentliche Contract-Module

Öffentliche Verträge liegen zentral unter:

```text
backend/app/contracts/
```

Beispiele:

```text
bootstrap.py
hierarchy.py
chat.py
messages.py
config.py
resources.py
widgets.py
actions.py
registry.py
errors.py
events.py
```

Router dürfen kleine rein lokale Hilfsmodelle enthalten.

Öffentlich relevante Request- und Response-Verträge werden jedoch nicht dauerhaft in Routerdateien definiert.

---

# 13. Trennung von API-, Domain- und Persistenzmodellen

Kernschmied unterscheidet:

## 13.1 API-Modelle

Beschreiben öffentliche Requests und Responses.

## 13.2 Domainmodelle

Beschreiben interne fachneutrale Kernobjekte.

## 13.3 Persistenzmodelle

Beschreiben Datenbanktabellen.

Diese Modelle dürfen ähnlich aussehen, sind aber nicht automatisch identisch.

```text
SQLAlchemy Model
        ↓
Repository
        ↓
Domain Object
        ↓
Response Mapper
        ↓
Pydantic Response
```

Dadurch werden interne Felder nicht versehentlich veröffentlicht.

---

# 14. Request-Verträge

Öffentliche Mutationsanfragen verwenden strenge Pydantic-Modelle.

```python
ConfigDict(extra="forbid")
```

Anfragen validieren mindestens:

- Datentypen,
- Pflichtfelder,
- Längen,
- Wertebereiche,
- IDs,
- Enumwerte,
- Revisionen,
- Feldkombinationen.

Unbekannte Felder werden abgelehnt.

Dies verhindert:

- Tippfehler,
- wirkungslose Altparameter,
- uneindeutige Eingaben,
- unbeabsichtigte Felder.

---

# 15. Response-Verträge

Öffentliche Antworten werden ausschließlich über explizite Response-Modelle erzeugt.

Antwortmodelle verwenden ebenfalls kontrollierte Felder.

Keine internen Zusatzdaten dürfen durch automatische Serialisierung erscheinen.

Antworten enthalten je nach Vertrag:

- `schema_version`,
- Ressource oder `items`,
- Revision,
- Pagination,
- Request-ID,
- Status.

Nicht jeder Response benötigt denselben globalen Envelope.

Einheitlichkeit wird bevorzugt, aber unnötige Verschachtelung vermieden.

---

# 16. Einzelressourcen-Verträge

Ein konsistenter Leservertrag kann beispielsweise enthalten:

```json
{
  "schema_version": "1.0",
  "item": {
    "id": "resource_123",
    "revision": 4
  },
  "request_id": "request_123"
}
```

Alternativ kann die Ressource direkt zurückgegeben werden, sofern die Entscheidung je Vertragsfamilie einheitlich bleibt.

Für Kernschmied gilt:

> Eine Vertragsfamilie verwendet genau eine dokumentierte Antwortform.

---

# 17. Listenverträge

Listenantworten sollen langfristig einheitlich sein.

Empfohlener Vertrag:

```json
{
  "schema_version": "1.0",
  "items": [],
  "next_cursor": null,
  "total": null,
  "revision": 12,
  "request_id": "request_123"
}
```

Mögliche Felder:

- `items`,
- `next_cursor`,
- `total`,
- `revision`,
- `request_id`.

## 17.1 Cursor-Pagination

Cursor-Pagination wird für wachsende Datenmengen bevorzugt.

Geeignet für:

- Chats,
- Nachrichten,
- Ressourcen,
- Auditereignisse,
- Registry-Einträge.

## 17.2 Offset-Pagination

Kann für kleine administrative Listen zulässig sein.

Die gewählte Strategie wird pro Endpunkt dokumentiert.

## 17.3 Deterministische Sortierung

Jede paginierte Liste benötigt eine stabile Sortierung.

Beispiel:

```text
created_at DESC, id DESC
```

---

# 18. Mutationsverträge

Mutationsergebnisse verwenden eine stabile Statussemantik.

Mögliche Werte:

```text
created
updated
deleted
archived
restored
moved
reordered
activated
disabled
```

Beispiel:

```json
{
  "schema_version": "1.0",
  "status": "updated",
  "item_id": "node_123",
  "revision": 8,
  "request_id": "request_123"
}
```

Je nach Anwendungsfall darf zusätzlich die aktualisierte Ressource zurückgegeben werden.

---

# 19. Optimistic Locking

Konfliktanfällige Mutationen verwenden:

```json
{
  "expected_revision": 7
}
```

Stimmt die Revision nicht, antwortet das Backend mit:

```text
HTTP 409 Conflict
```

und einem strukturierten Fehlercode:

```text
REVISION_CONFLICT
```

Das Frontend darf Konflikte nicht still überschreiben.

---

# 20. HTTP-Methoden

Kernschmied verwendet HTTP-Methoden konsistent.

## GET

Lesen ohne fachliche Mutation.

## POST

Erstellen oder explizite Kommandos.

Beispiele:

```text
POST /resources
POST /entries/{id}/activate
```

## PUT

Vollständiger Ersatz einer Ressource, sofern unterstützt.

## PATCH

Partielle Aktualisierung.

## DELETE

Löschen oder Löschanforderung.

Bei Soft Delete muss das Verhalten dokumentiert sein.

---

# 21. Statuscodes

Empfohlene Grundregeln:

```text
200 OK
201 Created
202 Accepted
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
410 Gone
422 Unprocessable Content
429 Too Many Requests
500 Internal Server Error
503 Service Unavailable
```

## 21.1 401 und 403

- `401`: nicht authentifiziert,
- `403`: authentifiziert, aber nicht autorisiert.

## 21.2 409

Für:

- Revisionskonflikte,
- Eindeutigkeitskonflikte,
- ungültige Statusübergänge,
- Zielkonflikte.

## 21.3 422

Für strukturell oder fachlich ungültige Eingaben, sofern kein spezifischerer Status geeignet ist.

## 21.4 503

Für vorübergehend nicht verfügbare Pflichtdienste oder deaktivierte Laufzeitfähigkeiten.

---

# 22. Strukturierte Fehler

Jede öffentliche Fehlerantwort verwendet:

```json
{
  "code": "ERROR_CODE",
  "message": "Verständliche Beschreibung",
  "details": {},
  "request_id": "request_123"
}
```

## 22.1 `code`

Stabiler maschinenlesbarer Fehlercode.

## 22.2 `message`

Verständliche Beschreibung.

Clients dürfen ihre Logik nicht ausschließlich an den Nachrichtentext koppeln.

## 22.3 `details`

Strukturierte Zusatzinformationen ohne Secrets oder interne Stacktraces.

## 22.4 `request_id`

Ermöglicht Korrelation mit Logs.

---

# 23. Validierungsfehler

FastAPI- und Pydantic-Validierungsfehler werden in den einheitlichen Fehlervertrag übersetzt.

Beispiel:

```json
{
  "code": "REQUEST_VALIDATION_FAILED",
  "message": "Die Anfrage enthält ungültige Felder.",
  "details": {
    "issues": [
      {
        "path": ["body", "name"],
        "code": "string_too_short",
        "message": "Der Name darf nicht leer sein."
      }
    ]
  },
  "request_id": "request_123"
}
```

Interne Pydantic-Strukturen werden nicht ungefiltert öffentlich ausgegeben.

---

# 24. Request-ID

Jede Anfrage erhält eine Request-ID.

Die Request-ID wird:

- aus einem gültigen Clientheader übernommen oder neu erzeugt,
- in Logs verwendet,
- in `X-Request-ID` zurückgegeben,
- in Fehlerantworten ausgegeben,
- in SSE-Ereignissen berücksichtigt.

Ungeeignete oder zu lange Clientwerte werden nicht ungeprüft übernommen.

---

# 25. Endpoint-Auflösung

Das Frontend verwendet einen zentralen Endpoint Resolver.

Endpointpfade werden bevorzugt über Bootstrap-Schlüssel bereitgestellt.

Beispiel:

```json
{
  "endpoints": {
    "bootstrap": "/api/v1/bootstrap",
    "hierarchy": "/api/v1/hierarchy",
    "chat_stream": "/api/v1/chat/stream"
  }
}
```

Das Frontend soll keine fachlichen Pfade verteilt hart codieren.

## 25.1 Sicherheitsgrenze

Backendbereitgestellte Endpunkte dürfen nicht automatisch beliebige Fremd-Origins aktivieren.

Same-Origin ist Standard.

Externe Origins benötigen eine ausdrückliche technische Freigabe.

---

# 26. Bootstrap-Vertrag

Der Bootstrap-Endpunkt liefert:

- Anwendungsversion,
- API-Version,
- Vertragsversionen,
- Endpointschlüssel,
- Capabilities,
- Featureinformationen,
- Revisionsstände,
- Sicherheitsprofil in nicht sensitiver Form.

Beispiel:

```json
{
  "versions": {
    "api": "v1",
    "bootstrap": "1.1",
    "ui_schema": "1.0",
    "hierarchy": "1.0",
    "chat": "1.0",
    "config": "2.0"
  }
}
```

Das Frontend prüft diese Werte vor weiteren fachlichen Anfragen.

---

# 27. Contract Categories

Kernschmied besitzt mehrere unabhängig versionierte Vertragsfamilien.

| Vertragsfamilie   | Zweck                               |
| ----------------- | ----------------------------------- |
| API               | öffentliche HTTP-Hauptversion       |
| Bootstrap         | Startinformationen und Capabilities |
| UI-Schema         | schema-gesteuerte Oberfläche        |
| Hierarchie        | generische Baumstruktur             |
| Effective Context | wirksamer Laufzeitkontext           |
| Chat              | Chatrequests und Conversationdaten  |
| Events            | SSE-Transport und Ereignisse        |
| Config            | Laufzeitkonfiguration               |
| Model Registry    | Modell- und Providermetadaten       |
| Tool Registry     | Toolmetadaten                       |
| Resources         | dynamische Ressourcen               |
| Widgets           | Widgetdefinitionen und Instanzen    |
| Actions           | Aktionen und Ausführungsstatus      |
| Runtime Registry  | dynamische Definitionen             |

Diese Versionen entwickeln sich unabhängig.

---

# 28. SSE als öffentlicher API-Vertrag

SSE ist Teil der öffentlichen API.

Der Stream verwendet einen versionierten Envelope.

Beispiel:

```json
{
  "schema_version": "1.0",
  "event_id": "event_123",
  "event_type": "chat.token",
  "conversation_id": "chat_123",
  "sequence": 18,
  "timestamp": "2026-08-03T17:00:00+02:00",
  "request_id": "request_123",
  "payload": {}
}
```

## 28.1 Keine stillen Umbenennungen

Bestehende Eventarten werden nicht ohne Migrationspfad umbenannt.

## 28.2 Unbekannte Events

Unbekannte Eventarten:

- beenden den Stream nicht,
- lösen keine Aktion aus,
- können diagnostisch protokolliert werden.

## 28.3 Genau ein Abschlusszustand

Ein Stream endet fachlich mit genau einem Abschlussereignis:

- completed,
- failed,
- cancelled.

---

# 29. Streaming-Fehler

Fehler vor Streambeginn können als normale HTTP-Fehler ausgegeben werden.

Fehler nach Streambeginn werden als versionierte SSE-Fehlerereignisse gesendet.

Interne Exceptions und Stacktraces werden nicht öffentlich übertragen.

---

# 30. Binäre Daten und Dateiübertragung

JSON-Endpunkte werden nicht für beliebig große Binärdaten missbraucht.

Dateien verwenden kontrollierte Endpunkte mit:

- Content-Type,
- Größenlimit,
- Dateinamenvalidierung,
- Berechtigungsprüfung,
- Streaming,
- Malware- oder Typprüfung, soweit vorgesehen.

Metadaten bleiben versionierte JSON-Verträge.

---

# 31. Idempotenz

Nicht sicher wiederholbare Aktionen können einen Idempotency-Key unterstützen.

Beispiel:

```text
Idempotency-Key: ...
```

Geeignet für:

- Ressourcenerstellung,
- Integrationsaufrufe,
- externe Transaktionen,
- wiederholte Clientrequests.

Die konkrete Semantik wird pro Endpunkt dokumentiert.

---

# 32. Abbruch und Timeouts

API-Clients unterstützen `AbortSignal`.

Backendservices sollen Clientabbrüche, soweit technisch möglich, berücksichtigen.

Timeouts werden unterschieden in:

- Clienttimeout,
- Backendtimeout,
- Provider-Timeout,
- Tooltimeout,
- Integrationstimeout.

Fehlercodes bleiben unterscheidbar.

---

# 33. Authentifizierung und Autorisierung

Authentifizierung und Autorisierung sind Bestandteil jedes öffentlichen Endpunktvertrags.

Jede Route dokumentiert:

- ob Authentifizierung erforderlich ist,
- welche Berechtigung erforderlich ist,
- welche Objektprüfung erfolgt,
- welche Tenant-Grenze gilt.

Das Frontend darf angezeigte Aktionen filtern.

Die abschließende Entscheidung trifft immer das Backend.

---

# 34. Tenant-Isolation

Jede tenantgebundene Anfrage wird serverseitig auf den aktiven Tenant eingeschränkt.

Tenant-IDs aus Request-Bodies werden nicht ungeprüft als Autorität übernommen.

Der Tenant ergibt sich bevorzugt aus:

- authentifizierter Membership,
- sicherem Request-Kontext,
- explizit autorisiertem Tenantwechsel.

Mandantenübergreifende Zugriffe benötigen eigene Freigabeverträge.

---

# 35. CORS und Origins

CORS ist Teil der Sicherheits- und Deploymentkonfiguration.

API-Verträge dürfen nicht davon ausgehen, dass jede Origin zugelassen ist.

Im Internetprofil gelten restriktive CORS-Regeln.

Same-Origin bleibt der bevorzugte Betriebsmodus.

---

# 36. Deprecation

Veraltete Endpunkte oder Felder werden dokumentiert.

Ein Deprecation-Eintrag enthält:

- alten Vertrag,
- Ersatz,
- Migrationshinweis,
- Einführungsdatum,
- geplante Entfernung.

Optional können HTTP-Header verwendet werden:

```text
Deprecation
Sunset
Link
```

Diese werden erst eingeführt, wenn ihre Semantik zentral festgelegt und getestet ist.

---

# 37. Parallele API-Versionen

Bei einer späteren `/api/v2` können `/api/v1` und `/api/v2` zeitweise parallel bestehen.

Parallelbetrieb benötigt:

- getrennte Router,
- getrennte Contract-Module oder eindeutige Versionstypen,
- gemeinsame Service-Schicht,
- keine doppelte Fachlogik,
- definierte Abschaltfrist.

Versionierte Router dürfen nicht durch Copy-and-paste dauerhaft auseinanderlaufen.

---

# 38. OpenAPI

FastAPI erzeugt die OpenAPI-Spezifikation.

OpenAPI ist:

- maschinenlesbare Dokumentation,
- Grundlage für Diff-Prüfungen,
- mögliche Quelle generierter Transporttypen,
- nicht die einzige Laufzeitvalidierung.

OpenAPI muss widerspiegeln:

- reale Endpunkte,
- Requestmodelle,
- Responsemodelle,
- Statuscodes,
- Authentifizierung,
- Fehlerantworten.

---

# 39. OpenAPI-Diff

Öffentliche Änderungen werden gegen eine bekannte Referenz geprüft.

Breaking Changes umfassen beispielsweise:

- Endpunkt entfernt,
- Methode geändert,
- Pflichtfeld ergänzt,
- Feldtyp verändert,
- Responsecode entfernt,
- Responsemodell inkompatibel verändert.

Ein Breaking Change muss bewusst freigegeben werden.

---

# 40. Frontend-Laufzeitvalidierung

Das Frontend behandelt API-Daten zunächst als `unknown`.

Vor Store-Übernahme erfolgt Validierung.

Mindestens für:

- Bootstrap,
- Hierarchie,
- Effective Context,
- Config,
- Modelle,
- Tools,
- Chats,
- Nachrichten,
- Ressourcen,
- Widgets,
- Actions,
- SSE-Ereignisse,
- Fehlerantworten.

Ungültige Antworten werden nicht still übernommen.

---

# 41. Generierte Frontendtypen

Transporttypen können künftig teilweise aus OpenAPI generiert werden.

Dabei gilt:

- generierte Dateien werden nicht manuell geändert,
- UI-interne Typen bleiben separat,
- Runtime-Validatoren bleiben erforderlich,
- normalisierte Storemodelle bleiben unabhängig.

Codegenerierung ersetzt keine Architekturentscheidung.

---

# 42. API-Client

Kernschmied verwendet einen zentralen API-Client.

Dieser behandelt einheitlich:

- Basis-URL,
- Endpoint-Auflösung,
- Credentials,
- Header,
- Request-ID,
- JSON,
- 204- und 205-Antworten,
- Fehlerantworten,
- Timeouts,
- Abbruch,
- binäre Antworten.

SSE wird über einen eigenen Streamingpfad behandelt und nicht als normales JSON verarbeitet.

---

# 43. API-Service-Module

Empfohlene Frontendstruktur:

```text
frontend/src/api/
├── client.ts
├── endpoints.ts
├── bootstrap.ts
├── hierarchy.ts
├── context.ts
├── chat.ts
├── resources.ts
├── widgets.ts
├── actions.ts
├── models.ts
├── tools.ts
├── config.ts
└── documentation.ts
```

Komponenten führen keine freien `fetch`-Aufrufe zu fachlichen Endpunkten aus.

---

# 44. Sicherheitsinvarianten

1. Jeder öffentliche Endpunkt besitzt einen dokumentierten Vertrag.
2. Öffentliche Mutationsanfragen lehnen unbekannte Felder ab.
3. Öffentliche Antworten werden über explizite Response-Modelle erzeugt.
4. Datenbankmodelle werden nicht direkt als öffentliche Verträge verwendet.
5. Jede Mutation wird serverseitig autorisiert.
6. Tenant-Grenzen werden serverseitig durchgesetzt.
7. Fehlerantworten enthalten keine Stacktraces oder Secrets.
8. Request-IDs werden konsistent verwendet.
9. Unbekannte Actions werden nicht ausgeführt.
10. Unbekannte SSE-Events lösen keine Aktion aus.
11. Endpointschlüssel dürfen keine unkontrollierten Fremd-Origins aktivieren.
12. Breaking Changes erfolgen nicht innerhalb derselben API-Hauptversion ohne Übergangsvertrag.
13. OpenAPI muss dem Laufzeitverhalten entsprechen.
14. Frontenddaten werden vor Nutzung validiert.
15. API-Version und Payload-Version bleiben getrennt.

---

# 45. Positive Konsequenzen

## 45.1 Stabile Clients

Frontend und externe Integrationen können sich auf dokumentierte Verträge verlassen.

## 45.2 Bewusste Evolution

Breaking Changes werden früh erkannt.

## 45.3 Bessere Dokumentation

OpenAPI und Vertragsdokumente bilden die reale Schnittstelle ab.

## 45.4 Einheitliche Fehlerbehandlung

Clients benötigen keine Vielzahl unterschiedlicher Fehlerparser.

## 45.5 Bessere Testbarkeit

Request, Response, Fehler und Statuscodes können systematisch getestet werden.

## 45.6 Sichere Entkopplung

Backendinternas werden nicht unbeabsichtigt veröffentlicht.

## 45.7 Erweiterbarkeit

Neue Clients und Integrationen können auf denselben stabilen Verträgen aufbauen.

---

# 46. Negative Konsequenzen

## 46.1 Höherer Pflegeaufwand

Jede öffentliche Änderung benötigt Vertrags- und Dokumentationsarbeit.

## 46.2 Mehr Modelle

API-, Domain- und Persistenzmodelle können teilweise ähnliche Strukturen besitzen.

## 46.3 Migrationsaufwand

Breaking Changes benötigen Übergangsphasen oder Parallelversionen.

## 46.4 Zusätzliche Tests

Statuscodes, Fehler, OpenAPI und Clientvalidatoren erhöhen den Testumfang.

## 46.5 Langsamere spontane Änderungen

Ein öffentliches Feld kann nicht ohne Prüfung schnell umbenannt werden.

---

# 47. Verworfene Alternativen

## 47.1 Keine explizite API-Versionierung

### Vorteile

- kurze URLs,
- weniger sichtbare Versionsangaben.

### Nachteile

- unklare Kompatibilität,
- schwierige Migration,
- gefährliche stille Änderungen.

**Entscheidung:** Verworfen.

---

## 47.2 Ausschließlich Header-Versionierung

### Vorteile

- saubere URLs,
- flexible Content Negotiation.

### Nachteile

- schwerer zu debuggen,
- weniger sichtbar,
- aufwendiger für Browser und Reverse Proxies,
- komplexere OpenAPI-Darstellung.

**Entscheidung:** Als primäre Strategie verworfen.

---

## 47.3 Ausschließlich Queryparameter

Beispiel:

```text
/api/bootstrap?version=1
```

### Vorteile

- leicht nachrüstbar.

### Nachteile

- unklare Semantik,
- schlechte Cache- und Proxyeigenschaften,
- vermischt Ressource und Vertragsversion.

**Entscheidung:** Verworfen.

---

## 47.4 Direkte SQLAlchemy-Serialisierung

### Vorteile

- wenig Mappingcode,
- schnelle Entwicklung.

### Nachteile

- interne Felder werden öffentlich,
- enge Kopplung an Datenbankmodell,
- schlechte Versionierbarkeit,
- Sicherheitsrisiko.

**Entscheidung:** Verworfen.

---

## 47.5 Eine universelle Response-Hülle für alles

### Vorteile

- formal einheitlich.

### Nachteile

- unnötige Verschachtelung,
- unpassend für Streams und Binärdaten,
- schwächere OpenAPI-Lesbarkeit.

**Entscheidung:** Als zwingendes globales Muster verworfen.

Vertragsfamilien bleiben intern konsistent.

---

## 47.6 GraphQL als primäre API

### Vorteile

- flexible Abfragen,
- starkes Schema.

### Nachteile

- höhere Komplexität,
- zusätzlicher Betriebs- und Sicherheitsaufwand,
- SSE- und Command-Flows bleiben separat,
- für den aktuellen MVP nicht erforderlich.

**Entscheidung:** Nicht Teil der aktuellen Architektur.

---

# 48. Migrationsstrategie vom IST zum SOLL

## Phase 1 – API-Inventar

- alle öffentlichen Router erfassen,
- Methoden und Pfade dokumentieren,
- Request- und Response-Modelle erfassen,
- Router außerhalb des zentralen v1-Routers identifizieren.

## Phase 2 – Contracts zentralisieren

- Routermodelle nach `backend/app/contracts/` verschieben,
- kompatible Re-Exports,
- doppelte Typen entfernen.

## Phase 3 – Fehler vereinheitlichen

- zentrale Fehlerantwort,
- Exception Handler,
- FastAPI-Validierungsfehler,
- Request-ID.

## Phase 4 – Listen und Mutationen harmonisieren

- `items`,
- Pagination,
- Revision,
- Mutationsstatus,
- 409-Konflikte.

## Phase 5 – Frontend-API-Client

- zentrale Endpoints,
- Bootstrap-Auflösung,
- Laufzeitvalidierung,
- AbortSignal,
- strukturierte Fehler.

## Phase 6 – SSE konsolidieren

- gemeinsamer Envelope,
- Eventregistry,
- Request-ID,
- genau ein Abschlussereignis,
- unbekannte Eventtypen.

## Phase 7 – OpenAPI-Diff

- Referenzspezifikation,
- CI-Prüfung,
- Breaking-Change-Bericht.

## Phase 8 – Deprecation

- alte Pfade,
- alte Felder,
- Übergangsadapter,
- Entfernungsplan.

---

# 49. Abnahmekriterien

Die Entscheidung gilt als technisch umgesetzt, wenn:

- alle öffentlichen Endpunkte unter einer dokumentierten API-Version liegen oder bewusst als Infrastrukturendpunkte ausgenommen sind,
- öffentliche Request- und Response-Modelle zentral definiert sind,
- Router keine großen öffentlichen Vertragsmodelle mehr lokal enthalten,
- Mutationsanfragen unbekannte Felder ablehnen,
- Fehlerantworten einheitlich strukturiert sind,
- Request-ID in Headern und Fehlerantworten vorhanden ist,
- Listenverträge einheitlich dokumentiert sind,
- Pagination deterministisch ist,
- Revisionskonflikte `409` verwenden,
- Frontendantworten zur Laufzeit validiert werden,
- Bootstrap Endpointschlüssel bereitstellt,
- Frontend einen zentralen API-Client verwendet,
- SSE einen versionierten gemeinsamen Envelope besitzt,
- unbekannte Events den Stream nicht zerstören,
- OpenAPI dem Laufzeitverhalten entspricht,
- OpenAPI-Diffs in der Qualitätsprüfung berücksichtigt werden,
- Breaking Changes einen dokumentierten Migrationsweg besitzen.

---

# 50. Konkrete Auswirkungen auf Kernschmied

## Backend

Zielbereiche:

```text
backend/app/api/v1/
backend/app/contracts/
backend/app/errors/
backend/app/middleware/
backend/app/services/
backend/app/main.py
```

## Frontend

Zielbereiche:

```text
frontend/src/api/
frontend/src/contracts/
frontend/src/state/
frontend/src/registry/
frontend/src/components/
```

## Tests

Zielbereiche:

```text
backend/tests/api/
backend/tests/contracts/
backend/tests/openapi/
frontend/src/api/__tests__/
frontend/src/contracts/__tests__/
```

## Dokumentation

Zielbereiche:

```text
documentation/architecture/contracts.md
documentation/architecture/schema-versioning.md
documentation/contracts/examples/
documentation/development/release-checklist.md
```

---

# 51. Verbindliche Architekturregeln

1. Öffentliche HTTP-Schnittstellen verwenden ein explizites API-Hauptversionspräfix.
2. API-Version und Payload-Schemaversion bleiben getrennt.
3. Jede öffentliche Route besitzt dokumentierte Request- und Response-Verträge.
4. Öffentliche Verträge liegen zentral unter `backend/app/contracts/`.
5. Persistenzmodelle werden nicht direkt als API-Verträge verwendet.
6. Mutationsanfragen lehnen unbekannte Felder ab.
7. Backendantworten werden über explizite Response-Modelle erzeugt.
8. Fehler verwenden `code`, `message`, `details` und `request_id`.
9. Request-IDs werden in allen öffentlichen Pfaden konsistent verwendet.
10. Jede Mutation wird serverseitig autorisiert.
11. Tenant-Isolation wird serverseitig durchgesetzt.
12. Listenverträge verwenden stabile Feldnamen und deterministische Sortierung.
13. Konfliktanfällige Mutationen verwenden Revisionen.
14. Breaking Changes benötigen eine neue Version oder einen Übergangsvertrag.
15. Frontendantworten werden vor Store-Übernahme validiert.
16. Fachliche Endpunkte werden über den zentralen API-Client aufgerufen.
17. SSE ist ein versionierter öffentlicher Vertrag.
18. Unbekannte SSE-Events lösen keine unbekannte Aktion aus.
19. OpenAPI muss dem tatsächlichen Laufzeitverhalten entsprechen.
20. Öffentliche Vertragsänderungen werden über Tests und OpenAPI-Diff geprüft.

---

# 52. Endgültige Entscheidung

Kernschmied verwendet dauerhaft eine Contract-First-API-Architektur mit URL-basierter Hauptversionierung.

Das System kombiniert:

```text
versionierte API-Pfade
+
versionierte Payload-Verträge
+
zentrale Pydantic-Modelle
+
strukturierte Fehler
+
Request-IDs
+
deterministische Listen und Pagination
+
Optimistic Locking
+
versionierte SSE-Ereignisse
+
Frontend-Laufzeitvalidierung
+
OpenAPI-Diff-Prüfung
```

Dadurch können Backend, Frontend, spätere Clients und externe Integrationen unabhängig weiterentwickelt werden, ohne öffentliche Schnittstellen unkontrolliert zu verändern.

Kernschmied behandelt APIs damit als langfristige, testbare und bewusst gepflegte Produktverträge.
