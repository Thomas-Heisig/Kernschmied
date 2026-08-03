# ADR-0005: Versionierte Verträge und Schema-Evolution

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
  - `documentation/architecture/dynamic-definitions.md`
  - `documentation/architecture/effective-context.md`
  - `documentation/architecture/decisions/ADR-0001-schema-driven-user-interface.md`
  - `documentation/architecture/decisions/ADR-0002-configuration-architecture-and-runtime-initialization.md`
  - `documentation/architecture/decisions/ADR-0003-registry-based-extension-architecture.md`
  - `documentation/architecture/decisions/ADR-0004-security-profiles-and-deployment-modes.md`

---

## 1. Entscheidung in Kurzform

Kernschmied verwendet für alle öffentlichen und dauerhaft gespeicherten Verträge eine explizite Versionierungs- und Evolutionsstrategie.

Versioniert werden insbesondere:

- REST-Verträge,
- SSE-Ereignisse,
- Bootstrap-Verträge,
- UI-Schemas,
- Hierarchieverträge,
- Chat- und Nachrichtenverträge,
- Ressourcenschemas,
- Promptdefinitionen,
- Widgetdefinitionen,
- Actiondefinitionen,
- Workflowdefinitionen,
- Registry-Einträge,
- Modellmanifeste,
- Toolmanifeste,
- Konfigurationsdefinitionen,
- Vorlagenpakete,
- Integrationsverträge.

Die zentrale Regel lautet:

> Verträge dürfen sich weiterentwickeln, aber ihre Bedeutung darf sich nicht stillschweigend ändern.
> Kompatible Erweiterungen erfolgen additiv.
> Inkompatible Änderungen benötigen eine neue Vertragsversion und einen dokumentierten Migrationsweg.

Datenbankmigrationen, Vertragsversionen, Objekt-Revisionen und Implementierungsversionen werden ausdrücklich getrennt behandelt.

---

# 2. Kontext

Kernschmied ist eine dynamische und langfristig erweiterbare Plattform.

Das System verbindet:

- Python-Backend,
- React-Frontend,
- Datenbank,
- SSE-Streaming,
- Modellprovider,
- Tools,
- dynamische UI-Schemas,
- Runtime-Registries,
- Prompts,
- Ressourcen,
- Widgets,
- Actions,
- Workflows,
- Integrationen.

Diese Bestandteile entwickeln sich nicht immer gleichzeitig.

Beispiele:

- Das Backend kann bereits ein neues optionales Feld liefern.
- Ein älteres Frontend kennt dieses Feld noch nicht.
- Ein Ressourcentyp erhält eine neue Definitionversion.
- Bereits gespeicherte Ressourcen verwenden weiterhin die alte Version.
- Ein SSE-Ereignis erhält zusätzliche Metadaten.
- Eine Datenbankmigration verändert die Speicherung, ohne den öffentlichen Vertrag zu ändern.
- Eine neue Modellmanifestversion wird unterstützt, während alte Manifeste weiter lesbar bleiben.

Ohne klare Versionierungsregeln entstehen schnell:

- stille Vertragsbrüche,
- nicht reproduzierbare Fehler,
- inkompatible Frontend- und Backendstände,
- fehlerhafte Migrationen,
- unklare Rollbacks,
- Datenverlust,
- langfristig unwartbare Übergangslösungen.

---

# 3. Problemstellung

Verträge ändern sich im Laufe der Entwicklung.

Typische Änderungen sind:

- neue Felder,
- entfernte Felder,
- geänderte Feldtypen,
- neue Enumwerte,
- neue Eventarten,
- neue Ressourcenversionen,
- neue UI-Komponenten,
- geänderte Semantik,
- neue Pflichtfelder,
- veränderte Sicherheitsregeln.

Ohne definierte Strategie entstehen mehrere Probleme.

## 3.1 Stille Bedeutungsänderung

Ein Feld behält denselben Namen, erhält aber eine andere Bedeutung.

Beispiel:

```text
status = "active"
```

könnte zunächst bedeuten:

```text
in der Datenbank aktiviert
```

und später:

```text
validiert, freigegeben, initialisiert und betriebsbereit
```

Obwohl der Feldname gleich bleibt, wäre der Vertrag inkompatibel verändert.

## 3.2 Frontend und Backend laufen auseinander

Das Backend liefert neue oder geänderte Strukturen, während das Frontend ältere Annahmen verwendet.

Mögliche Folgen:

- Laufzeitfehler,
- falsche Darstellung,
- verlorene Daten,
- nicht ausgeführte Aktionen,
- inkonsistenter Store.

## 3.3 Persistierte Daten verlieren ihre Bedeutung

Dynamische Definitionen und Ressourcen können über Jahre gespeichert bleiben.

Wird deren Schema verändert, muss weiterhin erkennbar sein:

- gegen welche Definition sie erstellt wurden,
- welche Version gültig war,
- ob eine Migration erforderlich ist,
- ob alte und neue Version parallel unterstützt werden.

## 3.4 Datenbankmigration wird mit API-Versionierung verwechselt

Eine neue Alembic-Revision bedeutet nicht automatisch eine neue API-Version.

Umgekehrt kann ein öffentlicher Vertrag geändert werden, ohne dass sich das Datenbankschema ändert.

## 3.5 Unbegrenzte Übergangskompatibilität

Werden alte Felder und Aliasnamen unbegrenzt unterstützt, wächst der Übergangscode dauerhaft.

Dadurch entstehen:

- doppelte Modelle,
- widersprüchliche Felder,
- schwer entfernbare Sonderfälle,
- unklare öffentliche Verträge.

## 3.6 Unbekannte Typen führen zu unsicherem Verhalten

Ein unbekannter Event-, Action-, Komponenten- oder Workflow-Typ darf nicht automatisch verarbeitet werden.

---

# 4. Abgrenzung der Versionsbegriffe

Kernschmied unterscheidet mehrere unabhängige Versions- und Revisionsarten.

## 4.1 API-Version

Beispiel:

```text
/api/v1
```

Beschreibt die öffentliche Hauptversion der HTTP-Schnittstelle.

## 4.2 Vertrags- oder Schemaversion

Beispiel:

```json
{
  "schema_version": "1.0"
}
```

Beschreibt die Struktur und Semantik eines konkreten Vertrags.

## 4.3 Objekt-Revision

Beispiel:

```json
{
  "revision": 7
}
```

Beschreibt den aktuellen Änderungsstand eines konkreten Objekts.

## 4.4 Registry-Revision

Beschreibt den Änderungsstand einer Registry.

Beispiel:

```json
{
  "registry_revisions": {
    "resource_types": 12,
    "actions": 5
  }
}
```

## 4.5 Definitionversion

Beschreibt die semantische Version einer dynamischen Definition.

Beispiel:

```text
resource_type note
definition_version 2.0
```

## 4.6 Implementierungsversion

Beschreibt die Version eines technischen Providers, Tools oder Plugins.

## 4.7 Manifestversion

Beschreibt die Struktur eines `model.json`, `tool.json` oder Paketmanifests.

## 4.8 Datenbankrevision

Beschreibt eine Alembic-Migrationsrevision.

Diese Begriffe dürfen nicht austauschbar verwendet werden.

---

# 5. Aktueller Zustand – IST

Kernschmied besitzt bereits mehrere Grundlagen für versionierte Verträge.

## 5.1 Bereits vorhanden

- versioniertes API-Präfix,
- Versionsfelder im Bootstrap,
- UI-Schemaversion,
- Chat-Schemaversion,
- SSE-Envelope-Grundlagen,
- Config-Revision,
- Registry- und Manifestversionen als Architekturprinzip,
- Alembic-Migrationen,
- Pydantic-v2-Verträge,
- TypeScript-Verträge,
- strukturierte Fehlerantworten,
- OpenAPI-Generierung.

## 5.2 Teilweise implementiert

- einheitliche Benennung aller Versionsfelder,
- Laufzeitvalidierung im Frontend,
- OpenAPI-Diff-Prüfung,
- Mindestclientversion,
- Deprecation-Metadaten,
- parallele Unterstützung mehrerer Vertragsversionen,
- Definitionmigrationen,
- Registry-Revisionsausgabe,
- vollständige Eventversionierung,
- systematische Re-Exports verlegter Vertragstypen.

## 5.3 Derzeitige Inkonsistenzen

- `schema_version`, `api_version`, `ui_schema_version` und Manifestversionen sind noch nicht überall klar voneinander abgegrenzt,
- einzelne öffentliche Modelle liegen noch in Routerdateien,
- manche Verträge verwenden unterschiedliche Feldnamen für dieselbe Bedeutung,
- Frontendtypen werden teilweise noch ohne Laufzeitvalidierung verwendet,
- alte Aliasfelder und Übergangsevents sind teilweise noch vorhanden,
- nicht alle Enum-Erweiterungen sind auf Vorwärtskompatibilität geprüft,
- Datenbank- und Vertragsmigrationen werden in der Dokumentation teilweise vermischt,
- nicht alle gespeicherten dynamischen Definitionen tragen eine eindeutige Definitionversion.

---

# 6. Zielzustand – SOLL

Kernschmied soll eine durchgängige, nachvollziehbare Vertrags- und Schema-Evolutionsstrategie besitzen.

```text
Vertrag definieren
        ↓
Version festlegen
        ↓
Backend validieren
        ↓
Frontend spiegeln
        ↓
Laufzeitvalidator bereitstellen
        ↓
Kompatibilität testen
        ↓
OpenAPI prüfen
        ↓
Migration dokumentieren
        ↓
Vertrag aktivieren
```

Für gespeicherte Definitionen:

```text
Definition 1.0
        ↓
Instanzen auf 1.0
        ↓
Definition 2.0
        ↓
Kompatibilitätsprüfung
        ↓
optional Migration
        ↓
Instanzen auf 1.0 und 2.0 parallel
        ↓
kontrollierte Ablösung von 1.0
```

---

# 7. Entscheidung

Kernschmied verwendet dauerhaft versionierte Verträge und kontrollierte Schema-Evolution.

Die Entscheidung umfasst folgende verbindliche Punkte.

## 7.1 Jeder öffentliche Vertrag ist eindeutig identifizierbar

Ein Vertrag besitzt mindestens:

- einen stabilen Namen,
- eine Vertragsfamilie,
- eine Schemaversion,
- eine dokumentierte Semantik.

## 7.2 Inkompatible Änderungen sind nicht stillschweigend

Bei inkompatiblen Änderungen wird:

- die Hauptversion erhöht,
- ein Migrationspfad beschrieben,
- die Kompatibilität getestet,
- gegebenenfalls eine Übergangsphase eingeführt.

## 7.3 Additive Änderungen werden bevorzugt

Neue optionale Felder sind gegenüber Umbenennungen oder Bedeutungsänderungen zu bevorzugen.

## 7.4 Persistierte Objekte speichern ihre Definitionsversion

Ressourcen, Workflows, Prompts und andere dynamische Instanzen behalten den Bezug zu der Definition, unter der sie erstellt wurden.

## 7.5 Alte Versionen werden nur kontrolliert unterstützt

Kompatibilitätsadapter und Re-Exports erhalten:

- Einführungsdatum,
- Ablöseziel,
- geplante Entfernung.

## 7.6 Vertragsänderungen werden automatisiert geprüft

Mindestens über:

- Backendtests,
- Frontendvalidatoren,
- OpenAPI-Diff,
- Migrationsprüfungen,
- Integrations- und Vertragstests.

---

# 8. Architekturprinzip

Die ursprüngliche Aussage:

> Contracts must be versioned to support future evolution.

wird präzisiert zu:

> Jeder stabile öffentliche oder persistierte Vertrag entwickelt sich nur über explizite Versionen weiter.
> Additive Änderungen bleiben nach Möglichkeit kompatibel.
> Semantische oder strukturelle Brüche erfordern eine neue Hauptversion, Migration und dokumentierte Übergangsstrategie.

---

# 9. Versionsformat

Vertrags- und Definitionsversionen verwenden grundsätzlich:

```text
MAJOR.MINOR
```

Beispiele:

```text
1.0
1.1
2.0
```

## 9.1 Major-Version

Wird erhöht bei inkompatiblen Änderungen.

Beispiele:

- Feld entfernt,
- Feldtyp verändert,
- Bedeutung verändert,
- bisher optionales Feld wird verpflichtend,
- Objektstruktur grundlegend verändert,
- Enumwert erhält andere Semantik.

## 9.2 Minor-Version

Wird erhöht bei kompatiblen Erweiterungen.

Beispiele:

- neues optionales Feld,
- neue optionale Metadaten,
- neue unterstützte Capability,
- zusätzliche optionale Darstellungsinformation.

## 9.3 Patch-Version

Öffentliche Vertragsschemata verwenden standardmäßig keine Patch-Version.

Implementierungen und Pakete dürfen weiterhin semantische Versionen wie:

```text
1.2.3
```

verwenden.

---

# 10. API-Versionierung

Kernschmied verwendet ein versioniertes API-Präfix:

```text
/api/v1
```

Eine neue API-Hauptversion wird nur eingeführt, wenn ein größerer Teil der öffentlichen Schnittstelle inkompatibel geändert werden muss.

Nicht jede Vertragsänderung erfordert:

```text
/api/v2
```

Einzelne Vertragsfamilien können innerhalb von `/api/v1` unterschiedliche Schemaversionen besitzen, solange:

- das Verhalten eindeutig ist,
- der Client die Version prüfen kann,
- keine widersprüchliche Semantik entsteht.

---

# 11. Vertragsversion im Payload

Versionierte Verträge führen ein Feld wie:

```json
{
  "schema_version": "1.0"
}
```

Das Feld bezeichnet ausschließlich die Version des jeweiligen Payload-Vertrags.

Nicht geeignet:

```json
{
  "version": "1.0"
}
```

wenn unklar bleibt, ob damit gemeint ist:

- API-Version,
- Objektversion,
- Implementierungsversion,
- Definitionsversion,
- Manifestversion.

Spezifische Felder werden bevorzugt:

```text
api_version
schema_version
definition_version
manifest_version
implementation_version
```

---

# 12. Revisionen

Eine Revision ist keine Schemaversion.

## 12.1 Schemaversion

Beschreibt Struktur und Semantik.

## 12.2 Revision

Beschreibt den aktuellen Änderungsstand eines Objekts.

Beispiel:

```json
{
  "schema_version": "1.0",
  "revision": 14
}
```

Das bedeutet:

- Objektstruktur folgt Vertrag `1.0`,
- Objekt wurde bis Revision `14` verändert.

Revisionen werden verwendet für:

- Optimistic Locking,
- Konflikterkennung,
- Cache-Invalidierung,
- Audit,
- gezielte Neuladung.

---

# 13. Zeitstempel sind keine Revisionen

`updated_at` darf nicht als alleiniger Konfliktschutz verwendet werden.

Gründe:

- Zeitauflösung,
- Zeitzonen,
- Parallelität,
- Datenbankunterschiede,
- nicht deterministische Vergleiche.

Kernschmied verwendet explizite Revisionen.

Zeitstempel bleiben ergänzende Metadaten.

---

# 14. Kompatible Änderungen

Als grundsätzlich kompatibel gelten:

- neues optionales Feld,
- neues optionales verschachteltes Objekt,
- zusätzliche Metadaten,
- neue Capability, die explizit ausgehandelt wird,
- neuer Endpunkt,
- neues bekanntes SSE-Ereignis, wenn unbekannte Events sicher ignoriert werden,
- neue optionale Action,
- zusätzliche nicht verpflichtende Registry-Information.

Kompatibilität hängt zusätzlich vom Clientverhalten ab.

Ein neues optionales Feld ist nur kompatibel, wenn ältere Clients zusätzliche Felder tolerieren.

---

# 15. Inkompatible Änderungen

Als inkompatibel gelten insbesondere:

- Pflichtfeld hinzugefügt,
- Feld entfernt,
- Feld umbenannt,
- Feldtyp geändert,
- `null` nicht mehr erlaubt,
- Enumwert entfernt,
- Bedeutung eines bestehenden Werts geändert,
- Listenreihenfolge erhält neue Semantik,
- Fehlercode erhält andere Bedeutung,
- Eventpayload grundlegend geändert,
- Sicherheitsanforderung stillschweigend reduziert,
- Standardverhalten verändert bestehende Daten.

Inkompatible Änderungen benötigen eine neue Hauptversion oder eine explizite Übergangsstrategie.

---

# 16. Umbenennung von Feldern

Felder werden nicht direkt umbenannt.

Übergangsablauf:

```text
1. Neues Feld ergänzen.
2. Altes Feld als deprecated markieren.
3. Backend akzeptiert gegebenenfalls beide Felder.
4. Antwort liefert bevorzugt nur den neuen Vertrag.
5. Frontend migriert.
6. Nutzung des alten Felds wird gemessen oder protokolliert.
7. Altes Feld wird in neuer Hauptversion entfernt.
```

Zwei Felder dürfen nicht dauerhaft dieselbe Bedeutung parallel darstellen.

---

# 17. Enum-Evolution

Enumwerte sind Teil des öffentlichen Vertrags.

## 17.1 Neue Enumwerte

Neue Werte können ältere Clients brechen, wenn diese erschöpfende Fallunterscheidungen verwenden.

Daher gilt:

- Frontendvalidatoren dürfen bei sicherheitskritischen Enums unbekannte Werte ablehnen.
- Darstellungsbezogene Enums können einen kontrollierten Fallback besitzen.
- Unbekannte Werte dürfen niemals automatisch privilegiertes Verhalten auslösen.

Beispiel:

```text
Unbekannte Action-Risikoklasse
→ Aktion nicht ausführbar
```

Nicht:

```text
Unbekannte Risikoklasse
→ wie Klasse A behandeln
```

## 17.2 Entfernte Enumwerte

Benötigen Migration bestehender Daten und eine neue Hauptversion.

---

# 18. Unbekannte Felder

Kernschmied unterscheidet Requests und Responses.

## 18.1 Öffentliche Mutationsanfragen

Unbekannte Felder werden standardmäßig abgelehnt.

Pydantic:

```python
ConfigDict(extra="forbid")
```

Frontend-Requestschema:

```typescript
schema.strict();
```

Vorteile:

- Tippfehler werden erkannt,
- alte Clients senden keine wirkungslosen Felder,
- unerwartete Eingaben werden nicht stillschweigend ignoriert.

## 18.2 Öffentliche Backendantworten

Das Backend verwendet strenge Response-Modelle, damit keine internen Daten versehentlich serialisiert werden.

## 18.3 Frontend-Antwortvalidierung

Zusätzliche Felder können je Vertrag kontrolliert toleriert werden.

Sie dürfen jedoch nicht ungeprüft:

- Aktionen auslösen,
- Komponenten registrieren,
- Berechtigungen verändern,
- Sicherheitsentscheidungen steuern.

---

# 19. Unbekannte Typen

Unbekannte diskriminierte Typen werden abhängig von ihrer Wirkung behandelt.

## 19.1 Darstellungstyp

Beispiel:

```text
unbekannter Widget-Typ
```

Verhalten:

- als nicht unterstützt anzeigen,
- keine Ausführung,
- optional Diagnose protokollieren.

## 19.2 Ereignistyp

Verhalten:

- Stream bleibt aktiv,
- Event wird nicht verarbeitet,
- keine unbekannte Aktion auslösen.

## 19.3 Action-Typ

Verhalten:

- vollständig ablehnen,
- stabilen Fehlercode liefern.

## 19.4 Sicherheits- oder Berechtigungstyp

Verhalten:

- sicher ablehnen,
- niemals permissiven Fallback verwenden.

---

# 20. SSE-Ereignisse

SSE-Ereignisse besitzen einen gemeinsamen Envelope.

Beispiel:

```json
{
  "schema_version": "1.0",
  "event_id": "event_123",
  "event_type": "chat.message",
  "conversation_id": "chat_123",
  "sequence": 17,
  "timestamp": "2026-08-03T16:00:00+02:00",
  "request_id": "request_123",
  "payload": {}
}
```

## 20.1 Envelope-Version

Beschreibt die gemeinsame Transportstruktur.

## 20.2 Payload-Version

Komplexe Eventpayloads können zusätzlich eine eigene Version besitzen.

## 20.3 Reihenfolge

`sequence` ist keine Vertragsversion.

Sie beschreibt die Reihenfolge innerhalb eines Streams oder einer Conversation.

## 20.4 Kompatibilität

Neue Eventarten dürfen ältere Clients nicht zum Abbruch bringen.

Bestehende Eventarten dürfen nicht ohne Migrationspfad umbenannt werden.

---

# 21. UI-Schema-Evolution

UI-Schemas sind öffentliche Verträge.

Versioniert werden:

- Komponentenstruktur,
- Bindings,
- Layouts,
- Actions,
- Sichtbarkeitsregeln,
- Metadaten.

Eine neue Backenddefinition darf nur Komponenten referenzieren, die:

- vom Client unterstützt werden,
- über Capabilities angekündigt wurden,
- eine bekannte Prop-Struktur besitzen.

Unbekannte Komponenten werden sicher dargestellt.

---

# 22. Ressourcenschema-Evolution

Jede Ressource speichert mindestens:

```text
resource_type
definition_version
schema_version
revision
```

Eine neue Definition verändert bestehende Ressourcen nicht automatisch.

## 22.1 Kompatible Definitionänderung

Beispiele:

- optionales Feld,
- zusätzliche Anzeigeinformation,
- neuer Alias.

## 22.2 Inkompatible Definitionänderung

Beispiele:

- Pflichtfeld,
- Datentypänderung,
- Feldentfernung,
- neue Bedeutung.

Benötigt:

- neue Definitionversion,
- Migrationsstrategie,
- Instanzprüfung,
- gegebenenfalls parallele Versionen.

---

# 23. Promptversionierung

Prompts werden revisioniert und historisiert.

Ein Prompt besitzt:

- stabile ID,
- Prompttyp,
- Scope,
- Revision,
- Status,
- vorherige Revision,
- Aktivierungszeitpunkt,
- Autor.

Eine Promptänderung überschreibt nicht die historische Bedeutung bereits abgeschlossener Aktionen.

Für auditierbare Modellaufrufe sollte nachvollziehbar sein, welche effektive Promptrevision verwendet wurde.

Interne Sicherheitsprompts dürfen nicht vollständig an Clients ausgegeben werden.

---

# 24. Registry- und Definitionsversionierung

Registry-Einträge besitzen:

```text
registry_type
definition_key
definition_version
schema_version
revision
status
```

Dabei gilt:

- `schema_version` beschreibt den Registry-Eintrag,
- `definition_version` beschreibt die konkrete Definition,
- `revision` beschreibt deren aktuellen Änderungsstand.

Nicht aktive Definitionen werden im normalen Laufzeitpfad nicht verwendet.

---

# 25. Manifestversionierung

`model.json`, `tool.json` und Paketmanifeste besitzen eigene Manifestversionen.

Beispiel:

```json
{
  "manifest_version": "1.0"
}
```

Eine unbekannte Major-Version wird abgelehnt.

Eine neuere kompatible Minor-Version kann akzeptiert werden, wenn:

- unbekannte optionale Felder sicher ignoriert werden,
- Pflichtsemantik unverändert bleibt,
- die Capability-Unterstützung ausreicht.

Manifeste enthalten keinen frei ausführbaren Code.

---

# 26. Konfigurationsschema-Evolution

Konfigurationsdefinitionen besitzen:

- Schlüssel,
- Schemaversion,
- Wertschema,
- Default,
- Scope,
- UI-Metadaten,
- Sicherheitsklasse,
- Reload-Verhalten.

Ändert sich das Wertschema, müssen bestehende Werte geprüft werden.

Mögliche Strategien:

```text
keep
migrate
reset_to_default
disable_until_reviewed
```

Bestehende Werte werden nicht stillschweigend neu interpretiert.

---

# 27. Datenbankmigrationen

Alembic-Revisionen beschreiben die Entwicklung der Speicherung.

Sie sind unabhängig von öffentlichen Vertragsversionen.

Eine Datenbankmigration kann:

- rein intern sein,
- eine neue Spalte ergänzen,
- Indizes verändern,
- Daten transformieren,
- einen öffentlichen Vertrag vorbereiten.

Jede Migration muss prüfen:

- Upgrade,
- vorhandene Daten,
- Downgrade, soweit unterstützt,
- SQLite,
- spätere PostgreSQL-Kompatibilität,
- Fremdschlüssel,
- Indizes,
- zeitliche Reihenfolge.

Bereits veröffentlichte Migrationen werden nicht nachträglich stillschweigend verändert.

---

# 28. Datenmigration und Vertragsmigration

Beide können gemeinsam erforderlich sein.

Beispiel:

```text
ResourceDefinition 1.0
        ↓
neue Definition 2.0
        ↓
Datenmigration
        ↓
Vertragsmigration
        ↓
Frontend-Unterstützung
        ↓
Aktivierung
```

Die Reihenfolge muss dokumentiert werden.

Eine neue Vertragsversion darf nicht aktiviert werden, wenn die zugrunde liegenden Daten noch nicht kompatibel sind.

---

# 29. Mindestclientversion

Bootstrap kann künftig eine Mindestclientversion ausgeben.

Beispiel:

```json
{
  "minimum_client_version": "0.2.0"
}
```

Ein Client unterhalb dieser Version darf nicht versuchen, inkompatible Verträge zu verwenden.

Für den MVP kann dieses Feld optional bleiben.

Sobald eingesetzt, muss die Versionsvergleichslogik zentral und getestet sein.

---

# 30. Capability Negotiation

Version und Aktivierung sind getrennt.

Ein Vertrag kann im Code vorhanden sein, während die Fähigkeit deaktiviert ist.

Beispiel:

```json
{
  "capabilities": {
    "dynamic_resource_types": {
      "enabled": false,
      "version": "1.0",
      "reason": "not_implemented"
    }
  }
}
```

Das Frontend verwendet nur:

- unterstützte Vertragsversionen,
- aktivierte Capabilities,
- bekannte Features.

---

# 31. Deprecation

Veraltete Felder, Endpunkte oder Eventarten werden ausdrücklich markiert.

Eine Deprecation-Dokumentation enthält:

- betroffenen Vertrag,
- Ersatz,
- Einführungsdatum,
- geplante Entfernung,
- Migrationshinweis.

Beispiel:

```text
models.default_model_id
→ ersetzt durch models.default_model
```

Deprecation bedeutet:

- weiterhin unterstützt,
- nicht mehr für neue Implementierungen verwenden,
- Entfernung geplant.

---

# 32. Kompatibilitätsadapter

Adapter dürfen zeitlich begrenzt verwendet werden.

Beispiele:

- altes Feld auf neues Feld abbilden,
- altes Event normalisieren,
- alten Importpfad re-exportieren,
- alte Responseform transformieren.

Jeder Adapter benötigt:

- Test,
- Dokumentation,
- Telemetrie oder Auffindbarkeit,
- Entfernungsplan.

Adapter dürfen keine dauerhafte zweite Vertragsrealität erzeugen.

---

# 33. Re-Exports

Werden Python- oder TypeScript-Typen verschoben, können vorübergehend Re-Exports verwendet werden.

Beispiel:

```python
from app.contracts.hierarchy import HierarchyNodeRead

__all__ = ["HierarchyNodeRead"]
```

Dokumentiert werden:

- alter Pfad,
- neuer Pfad,
- Zeitpunkt,
- geplantes Entfernungsrelease.

---

# 34. OpenAPI

OpenAPI beschreibt die tatsächlich erreichbaren öffentlichen HTTP-Verträge.

Nicht jeder Zukunftsvertrag muss künstlich in OpenAPI erscheinen.

OpenAPI wird geprüft auf:

- neue Endpunkte,
- entfernte Endpunkte,
- geänderte Pflichtfelder,
- veränderte Typen,
- geänderte Statuscodes,
- geänderte Response-Modelle.

Ein OpenAPI-Diff ist Bestandteil der Qualitätsprüfung.

---

# 35. Frontend-Vertragsabbildung

Das Frontend unterscheidet:

- generierte Transporttypen,
- manuelle Runtime-Validatoren,
- normalisierte Storemodelle,
- UI-interne Typen.

Generierte Dateien werden nicht manuell geändert.

Runtime-Validatoren bleiben erforderlich, auch wenn Typen aus OpenAPI generiert werden.

---

# 36. Fehlervertrags-Evolution

Fehlerantworten behalten die stabile Grundstruktur:

```json
{
  "code": "ERROR_CODE",
  "message": "Beschreibung",
  "details": {},
  "request_id": "request_123"
}
```

Fehlercodes sind Teil des Vertrags.

Bestehende Codes erhalten keine neue, widersprüchliche Bedeutung.

Neue Details werden additiv ergänzt.

Clients dürfen nicht ausschließlich auf freie Nachrichtentexte reagieren.

---

# 37. Sicherheitsrelevante Vertragsänderungen

Sicherheitsverträge verwenden konservative Evolution.

Bei unbekannten oder inkompatiblen Werten gilt:

```text
deny by default
```

Dies betrifft insbesondere:

- Berechtigungen,
- Risikoklassen,
- Sichtbarkeit,
- Datenklassifikation,
- Tenant-Scope,
- externe Freigaben,
- Actionbestätigungen.

Eine neue Vertragsversion darf keine bestehende Sicherheitsgrenze stillschweigend lockern.

---

# 38. Tests

Jede Vertragsänderung benötigt passende Tests.

## 38.1 Backend

Mindestens:

- gültiges Beispiel,
- fehlendes Pflichtfeld,
- unbekanntes Requestfeld,
- ungültige Version,
- zusätzliche Responsefelder ausgeschlossen,
- Serialisierung,
- Deserialisierung,
- Enumwerte,
- Revisionen.

## 38.2 Frontend

Mindestens:

- gültige Antwort,
- ungültige Antwort,
- unbekannter Typ,
- unbekannter Enumwert,
- zusätzliche Felder,
- alte Vertragsversion,
- neue unterstützte Version,
- keine Store-Übernahme bei Fehler.

## 38.3 Integration

Mindestens:

- Backendpayload wird vom Frontendvalidator akzeptiert,
- OpenAPI entspricht dem Laufzeitverhalten,
- ältere kompatible Antwort funktioniert,
- inkompatible Antwort wird kontrolliert abgelehnt.

---

# 39. Vertragsbeispiele

Für zentrale Verträge werden versionierte Beispiele gepflegt.

Empfohlene Struktur:

```text
documentation/contracts/examples/
├── bootstrap/
│   └── v1.0.json
├── hierarchy/
│   └── v1.0.json
├── effective-context/
│   └── v1.0.json
├── events/
│   └── v1.0/
├── resources/
│   └── v1.0/
└── errors/
    └── v1.0.json
```

Diese Beispiele können in Tests verwendet werden.

---

# 40. Positive Konsequenzen

## 40.1 Kontrollierte Weiterentwicklung

Verträge können erweitert werden, ohne bestehende Clients unnötig zu brechen.

## 40.2 Nachvollziehbare Migrationen

Daten, Definitionen und Clients können koordiniert migriert werden.

## 40.3 Bessere Testbarkeit

Kompatibilität wird explizit geprüft.

## 40.4 Sicherere dynamische Definitionen

Jede persistierte Instanz behält ihre Definitionsversion.

## 40.5 Stabilere Integrationen

Externe Systeme können sich auf dokumentierte Verträge verlassen.

## 40.6 Bessere Fehlerdiagnose

Versionen und Revisionen machen Zustände reproduzierbar.

## 40.7 Kontrollierter Übergang

Deprecation und Adapter verhindern abrupte Brüche.

---

# 41. Negative Konsequenzen

## 41.1 Höherer Pflegeaufwand

Versionen, Migrationen und Kompatibilitätsphasen müssen dokumentiert werden.

## 41.2 Mehr Testfälle

Mehrere unterstützte Versionen erhöhen den Testumfang.

## 41.3 Übergangscode

Temporäre Adapter und Re-Exports erzeugen zusätzliche Komplexität.

## 41.4 Langsamere spontane Änderungen

Feldumbenennungen oder schnelle Strukturänderungen benötigen bewusste Planung.

## 41.5 Gefahr zu vieler Versionen

Werden zu viele Versionen gleichzeitig unterstützt, steigt die Wartungslast.

Daher müssen alte Versionen kontrolliert entfernt werden.

---

# 42. Verworfene Alternativen

## 42.1 Verträge ohne Versionsfeld

### Vorteile

- weniger Felder,
- einfacher Beginn.

### Nachteile

- keine eindeutige Interpretation,
- schlechte Migration,
- unklare Clientkompatibilität.

**Entscheidung:** Verworfen.

---

## 42.2 Nur API-Pfadversionierung

Beispiel:

```text
/api/v1
/api/v2
```

### Vorteile

- leicht sichtbar,
- bekanntes Muster.

### Nachteile

- zu grob für einzelne Vertragsfamilien,
- dynamische Definitionen bleiben unversioniert,
- jede kleinere Änderung könnte neue API-Version erfordern.

**Entscheidung:** Als alleinige Strategie verworfen.

---

## 42.3 Nur Datenbankrevisionen verwenden

### Vorteile

- vorhandener Alembic-Mechanismus.

### Nachteile

- beschreibt keine API-Semantik,
- beschreibt keine Frontendkompatibilität,
- nicht für SSE, UI-Schemas oder Manifeste geeignet.

**Entscheidung:** Verworfen.

---

## 42.4 Automatische Interpretation unbekannter Versionen

### Vorteile

- scheinbar hohe Vorwärtskompatibilität.

### Nachteile

- unsichere Annahmen,
- unvorhersehbares Verhalten,
- besonders gefährlich bei Aktionen und Berechtigungen.

**Entscheidung:** Verworfen.

---

## 42.5 Dauerhafte Unterstützung aller Altversionen

### Vorteile

- keine erzwungenen Clientmigrationen.

### Nachteile

- unbegrenzte Komplexität,
- Sicherheitsrisiken,
- wachsender Übergangscode,
- nicht wartbar.

**Entscheidung:** Verworfen.

---

## 42.6 Stille Datenmigration beim Lesen

### Vorteile

- geringe explizite Migrationsarbeit.

### Nachteile

- nicht reproduzierbar,
- unterschiedliche Datenstände,
- unerwartete Schreibzugriffe,
- schwieriger Rollback.

**Entscheidung:** Als allgemeines Modell verworfen.

Kontrollierte Lazy Migration kann später für ausdrücklich geeignete Fälle eingeführt werden.

---

# 43. Migrationsstrategie vom IST zum SOLL

## Phase 1 – Versionsinventar

- alle vorhandenen Versionsfelder erfassen,
- Bedeutung dokumentieren,
- doppelte oder unklare Felder identifizieren,
- Router-lokale Verträge erfassen,
- SSE-Eventversionen dokumentieren.

## Phase 2 – Begriffe vereinheitlichen

Verbindlich unterscheiden:

```text
api_version
schema_version
definition_version
manifest_version
implementation_version
revision
registry_revision
```

## Phase 3 – Basistypen zentralisieren

- SchemaVersion,
- Revision,
- Zeitstempel,
- opaque IDs,
- Request-ID.

## Phase 4 – Kernverträge stabilisieren

Reihenfolge:

1. Fehler,
2. Bootstrap,
3. Hierarchie,
4. Chat,
5. Nachrichten,
6. SSE,
7. Config.

## Phase 5 – Frontendvalidatoren

- jeden öffentlichen Payload validieren,
- unbekannte Typen sicher behandeln,
- Versionsprüfung ergänzen.

## Phase 6 – Dynamische Definitionen versionieren

- Ressourcentypen,
- Prompts,
- Widgets,
- Konzepte,
- Workflows,
- Knotentypen.

## Phase 7 – Deprecation-Verzeichnis

- alte Felder,
- alte Events,
- alte Importpfade,
- geplante Entfernung.

## Phase 8 – OpenAPI-Diff und CI

- Vertragsänderungen automatisch prüfen,
- Breaking Changes sichtbar machen,
- bewusste Freigabe verlangen.

---

# 44. Abnahmekriterien

Die Entscheidung gilt als technisch umgesetzt, wenn:

- alle öffentlichen Kernverträge eine eindeutige Schemaversion besitzen,
- Versionsbegriffe klar getrennt sind,
- Objekt- und Registry-Revisionen nicht mit Schemaversionen verwechselt werden,
- inkompatible Änderungen eine neue Hauptversion erhalten,
- gespeicherte dynamische Instanzen ihre Definitionversion behalten,
- Frontendantworten laufzeitvalidiert werden,
- unbekannte sicherheitsrelevante Typen abgelehnt werden,
- unbekannte darstellungsbezogene Typen kontrolliert dargestellt werden,
- SSE-Events versioniert und vorwärtskompatibel verarbeitet werden,
- OpenAPI-Diffs geprüft werden,
- Datenbankmigrationen separat dokumentiert sind,
- Deprecations einen Entfernungsplan besitzen,
- Re-Exports nur zeitlich begrenzt bestehen,
- Vertragsbeispiele und Tests vorhanden sind,
- Dokumentation und Code dieselbe Versionssemantik verwenden.

---

# 45. Konkrete Auswirkungen auf Kernschmied

## Backend

Zielbereiche:

```text
backend/app/contracts/
backend/app/api/
backend/app/config/
backend/app/registries/
backend/app/services/
backend/alembic/
```

## Frontend

Zielbereiche:

```text
frontend/src/contracts/
frontend/src/api/
frontend/src/registry/
frontend/src/state/
frontend/src/components/schema/
```

## Tests

Zielbereiche:

```text
backend/tests/contracts/
backend/tests/api/
backend/tests/migrations/
frontend/src/contracts/__tests__/
frontend/src/api/__tests__/
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

# 46. Verbindliche Architekturregeln

1. Jeder stabile öffentliche Vertrag besitzt eine eindeutige Schemaversion.
2. API-Version, Schemaversion, Definitionversion und Revision bleiben getrennt.
3. Inkompatible Änderungen erfolgen niemals stillschweigend.
4. Additive Änderungen werden bevorzugt.
5. Mutationsanfragen lehnen unbekannte Felder standardmäßig ab.
6. Backendantworten werden über strenge Response-Modelle erzeugt.
7. Frontendantworten werden vor Store-Übernahme validiert.
8. Unbekannte sicherheitsrelevante Typen werden abgelehnt.
9. Unbekannte Darstellungstypen werden sicher als nicht unterstützt angezeigt.
10. Persistierte Instanzen behalten ihre Definitionversion.
11. Neue Definitionversionen verändern bestehende Instanzen nicht automatisch.
12. Datenbankrevisionen ersetzen keine Vertragsversionierung.
13. Zeitstempel ersetzen keine Objekt-Revisionen.
14. Fehlercodes behalten ihre Semantik.
15. Bestehende Eventarten werden nicht ohne Migrationspfad umbenannt.
16. Deprecations besitzen Ersatz und Entfernungsplan.
17. Re-Exports sind zeitlich begrenzte Übergangslösungen.
18. OpenAPI-Diffs werden bei öffentlichen Änderungen geprüft.
19. Sicherheitsgrenzen können durch neue Vertragsversionen nicht stillschweigend gelockert werden.
20. Alte Versionen werden nur so lange unterstützt, wie ein dokumentierter Bedarf besteht.

---

# 47. Endgültige Entscheidung

Kernschmied verwendet dauerhaft versionierte Verträge und kontrollierte Schema-Evolution.

Das System kombiniert:

```text
versionierte API-Verträge
+
versionierte Payload-Schemas
+
Objekt- und Registry-Revisionen
+
versionierte dynamische Definitionen
+
Frontend-Laufzeitvalidierung
+
OpenAPI-Diff-Prüfung
+
Daten- und Vertragsmigrationen
+
Deprecation und kontrollierte Adapter
```

Dadurch können Backend, Frontend, gespeicherte Daten, dynamische Definitionen, Manifeste und Integrationen unabhängig, aber koordiniert weiterentwickelt werden.

Kernschmied bleibt damit langfristig erweiterbar, nachvollziehbar und migrationsfähig, ohne bestehende Verträge unkontrolliert zu brechen.
