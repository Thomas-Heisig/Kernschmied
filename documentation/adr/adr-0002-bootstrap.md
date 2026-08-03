# ADR-0002: Konfigurationsarchitektur, Bootstrap und Laufzeitinitialisierung

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
  - `documentation/architecture/effective-context.md`
  - `documentation/architecture/dynamic-definitions.md`
  - `documentation/architecture/decisions/ADR-0001-schema-driven-user-interface.md`

---

## 1. Entscheidung in Kurzform

Kernschmied trennt Konfiguration verbindlich in mehrere klar abgegrenzte Schichten.

Die wichtigste Trennung lautet:

1. **Bootstrap-Konfiguration**
2. **Persistente Laufzeitkonfiguration**
3. **Dynamische Definitionen und Registries**
4. **Instanzen und Zuordnungen**
5. **Effektiver Laufzeitkontext**

Die `.env`-Datei enthält ausschließlich Werte, die erforderlich sind, um die Plattform sicher zu starten und ihre technische Infrastruktur zu initialisieren.

Fachliche und verhaltenssteuernde Einstellungen werden versioniert, validiert und revisioniert in der Datenbank gespeichert.

Die zentrale Regel lautet:

> Bootstrap-Konfiguration startet die Plattform.
> Laufzeitkonfiguration und dynamische Definitionen bestimmen ihr Verhalten.
> Der Effective Context bestimmt, was für einen konkreten Benutzer in einem konkreten Kontext tatsächlich gilt.

---

# 2. Kontext

Kernschmied ist als dynamische, fachneutrale Kommunikations- und Assistenzplattform konzipiert.

Die Plattform soll sich im laufenden Betrieb verändern können, ohne dass für jede fachliche Anpassung:

- eine `.env`-Datei geändert,
- die Anwendung neu gebaut,
- der Server neu gestartet,
- das Frontend neu veröffentlicht

werden muss.

Kernschmied unterstützt oder plant:

- unterschiedliche Betriebsprofile,
- persistente Laufzeitkonfiguration,
- dynamische Hierarchien,
- dynamische Ressourcentypen,
- konfigurierbare Prompts,
- Modell- und Tool-Registries,
- UI-Schemas,
- Widgets,
- Actions,
- Workflows,
- Integrationen,
- Vorlagenpakete,
- Mehrmandantenfähigkeit,
- revisionsbasierte Cache-Invalidierung.

Gleichzeitig muss der Startvorgang:

- sicher,
- deterministisch,
- nachvollziehbar,
- fehlertolerant,
- testbar

bleiben.

Daraus ergibt sich die zentrale Frage:

> Welche Werte müssen bereits beim Start verfügbar sein, und welche Werte dürfen oder sollen erst nach erfolgreicher Infrastrukturinitialisierung aus der Datenbank geladen werden?

---

# 3. Problemstellung

Viele Anwendungen beginnen mit einer überschaubaren `.env`-Datei.

Im Laufe der Zeit werden dort jedoch zunehmend Werte abgelegt wie:

- Firmenname,
- Branding,
- Modellwahl,
- Toolfreigaben,
- Prompttexte,
- Feature-Flags,
- Workflowregeln,
- UI-Einstellungen,
- Benutzerpräferenzen,
- Rollen,
- fachliche Standardwerte.

Dadurch entstehen mehrere Probleme.

## 3.1 Umgebungsvariablen werden zu Fachkonfiguration

Infrastrukturelle und fachliche Einstellungen vermischen sich.

Beispiel:

```text
DATABASE_URL=...
DEFAULT_MODEL=...
COMPANY_NAME=...
ENABLE_INVOICE_FEATURE=true
DEFAULT_PROMPT=...
```

Eine Änderung des Firmennamens oder eines Prompts würde dadurch einen Neustart oder sogar ein neues Deployment erfordern.

## 3.2 Große `.env`-Dateien werden unwartbar

Mit wachsendem Funktionsumfang entstehen:

- hunderte Einträge,
- redundante Werte,
- versteckte Abhängigkeiten,
- schwer nachvollziehbare Überschreibungen,
- unterschiedliche Stände zwischen Umgebungen.

## 3.3 Fehlende Typisierung

Umgebungsvariablen sind zunächst Strings.

Ohne zentrale Validierung entstehen Probleme bei:

- Zahlen,
- Booleans,
- Listen,
- URLs,
- Pfaden,
- Secrets,
- komplexen Konfigurationen.

## 3.4 Unterschiedliche Umgebungen driften auseinander

Manuell gepflegte `.env`-Dateien führen zu Abweichungen zwischen:

- Entwicklung,
- Intranet,
- Internet,
- Testsystemen,
- einzelnen Installationen.

## 3.5 Laufzeitänderungen werden verhindert

Eine fachliche Änderung erfordert möglicherweise:

```text
Datei ändern
→ Dienst stoppen
→ Anwendung neu starten
→ Zustand prüfen
```

Das widerspricht dem dynamischen Zielbild.

## 3.6 Sicherheitsgrenzen werden unklar

Werden Sicherheitsuntergrenzen und Fachkonfiguration vermischt, kann eine administrative Laufzeitänderung unbeabsichtigt sicherheitskritische Startparameter beeinflussen.

---

# 4. Abgrenzung: Konfiguration, Definition, Instanz und Zuordnung

Kernschmied unterscheidet vier verschiedene Konzepte.

## 4.1 Konfiguration

Steuert allgemeines Verhalten.

Beispiele:

- Standardmodell,
- Sprache,
- erlaubte Modelle,
- UI-Präferenzen,
- Aufbewahrungsdauer.

## 4.2 Definition

Beschreibt, was grundsätzlich existieren kann.

Beispiele:

- Ressourcentyp `note`,
- Knotentyp `collection`,
- Widget-Konfigurationstyp,
- semantisches Konzept,
- Workflowdefinition.

## 4.3 Instanz

Ist ein konkretes Objekt auf Grundlage einer Definition.

Beispiele:

- eine konkrete Notiz,
- ein konkreter Hierarchieknoten,
- eine konkrete Widget-Instanz,
- ein konkreter Workflowlauf.

## 4.4 Zuordnung

Legt fest, wo oder für wen etwas gilt.

Beispiele:

- Prompt gehört zu Knoten X,
- Widget wird im Projekt Y angezeigt,
- Ressource ist mit Chat Z verknüpft,
- Benutzer hat Rolle R in Tenant T.

Diese Ebenen dürfen nicht vermischt werden.

---

# 5. Aktueller Zustand – IST

Zum Zeitpunkt dieser Überarbeitung besitzt Kernschmied bereits wichtige Teile der vorgesehenen Konfigurationsarchitektur.

## 5.1 Bereits vorhanden

- Bootstrap-Endpunkt,
- zentrale Anwendungskonfiguration,
- `.env`-basierte Bootstrapwerte,
- unterschiedliche Betriebsprofile,
- persistente Systemkonfiguration,
- Config-Revision,
- Konfigurationsdefinitionen,
- UI-Metadaten für Einstellungen,
- serverseitige Validierungsgrundlagen,
- Settings-Katalog,
- zentrale Registries für Modelle und Tools,
- Bootstrap-Capabilities und Versionsinformationen.

## 5.2 Teilweise implementiert

- Config-v2-Migration,
- vollständige Definitionsmetadaten,
- revisionsgeschützte Updates,
- atomare Batch-Updates,
- gezielte Cache-Invalidierung,
- Frontend-Laufzeitvalidierung,
- Provider- und Modellabhängigkeiten,
- dynamische Optionsquellen,
- vollständige Capability Negotiation.

## 5.3 Derzeitige Inkonsistenzen

- einzelne fachliche Werte können noch über Bootstrap oder statische Defaults beeinflusst werden,
- nicht alle Konfigurationsänderungen werden atomar gespeichert,
- Registry-Revisionen sind noch nicht vollständig getrennt,
- Multi-Worker-Invalidierung ist noch nicht vollständig umgesetzt,
- Secrets und normale Konfiguration sind konzeptionell getrennt, aber noch nicht in allen Pfaden vollständig abgesichert,
- nicht alle Frontendwerte werden ausschließlich aus versionierten Backendverträgen bezogen,
- einige Defaults sind noch im Code verteilt,
- dynamische Definitionen besitzen noch keinen vollständigen Lifecycle.

---

# 6. Zielzustand – SOLL

Kernschmied soll eine klar geschichtete Konfigurationsarchitektur besitzen.

```text
Bootstrap-Konfiguration
        ↓
Infrastrukturinitialisierung
        ↓
Datenbankverbindung
        ↓
persistente Systemkonfiguration
        ↓
Runtime-Registries und Definitionen
        ↓
Instanzen und Zuordnungen
        ↓
Effective Context
        ↓
REST / SSE / Frontend
```

Jede Schicht besitzt:

- eigenen Zweck,
- eigene Verträge,
- eigene Validierung,
- eigene Revisionslogik,
- klare Sicherheitsgrenzen.

---

# 7. Entscheidung

Kernschmied verwendet dauerhaft eine mehrschichtige Konfigurationsarchitektur.

Die Entscheidung besteht aus mehreren verbindlichen Teilen.

## 7.1 Bootstrap bleibt minimal

Bootstrapwerte enthalten ausschließlich:

- technische Infrastruktur,
- Sicherheitsuntergrenzen,
- Startpfade,
- Verbindungsdaten,
- initiale Betriebsparameter.

## 7.2 Fachliches Verhalten liegt in der Datenbank

Fachliche Einstellungen werden:

- validiert,
- versioniert,
- revisioniert,
- auditierbar,
- zur Laufzeit änderbar

gespeichert.

## 7.3 Dynamische Definitionen besitzen eigenen Lifecycle

Definitionen werden nicht allein durch Speicherung aktiv.

Sie durchlaufen:

```text
draft
→ validated
→ pending_approval
→ active
```

## 7.4 Effective Context wird serverseitig berechnet

Das Frontend erhält nur die tatsächlich wirksamen, zulässigen und gefilterten Werte.

## 7.5 Sicherheitsgrenzen sind nicht über Laufzeitkonfiguration abschwächbar

Untergeordnete Konfiguration darf einschränken, aber keine technische Sicherheitsuntergrenze lockern.

---

# 8. Architekturprinzip

Die ursprüngliche Formulierung:

> Bootstrap configuration starts the platform.
> Runtime configuration defines platform behavior.

wird präzisiert zu:

> Bootstrap-Konfiguration initialisiert die technische Plattform und ihre Sicherheitsgrenzen.
> Persistente Laufzeitkonfiguration, Definitionen, Instanzen und Zuordnungen bestimmen das fachliche Verhalten.
> Der Effective Context berechnet daraus die für Benutzer und Situation tatsächlich wirksame Konfiguration.

---

# 9. Zielarchitektur

```text
.env / Prozessumgebung
        ↓
Bootstrap Settings
        ↓
Profil- und Sicherheitsprüfung
        ↓
Logging / Speicher / Datenbank / Netzwerk
        ↓
Datenbankverbindung
        ↓
Migrationen und Schema-Prüfung
        ↓
Systemkonfiguration
        ↓
Runtime Registries
        ↓
aktive Definitionen
        ↓
Instanzen und Zuordnungen
        ↓
Context Resolver
        ↓
Effective Context
        ↓
API / SSE / Frontend
```

---

# 10. Bootstrap-Konfiguration

Bootstrap-Konfiguration enthält nur Werte, die vor oder während der Infrastrukturinitialisierung erforderlich sind.

Typische Werte:

- Betriebsprofil,
- Datenbank-URL,
- Secret-Key,
- Verschlüsselungsschlüssel,
- Cookie-Sicherheitsparameter,
- HTTPS- und Proxy-Vertrauen,
- Host und Port,
- Logging-Level,
- Log-Ausgabeziel,
- Dateispeicherpfade,
- erlaubte Modell- und Tool-Verzeichnisse,
- temporäre Verzeichnisse,
- initialer Entwicklungsbenutzer,
- Migrationsverhalten,
- Startdiagnostik.

Bootstrapwerte:

- werden beim Start validiert,
- sind grundsätzlich restartpflichtig,
- werden nicht über normale Fach-API-Endpunkte verändert,
- werden nicht vollständig an das Frontend ausgegeben.

---

# 11. Nicht in `.env` zulässige Werte

Nicht in die Bootstrap-Konfiguration gehören:

- Firmenname,
- Benutzerprofile,
- Branding,
- Prompts,
- Modellwahl,
- Toolauswahl,
- Widget-Zuordnungen,
- Hierarchieknoten,
- Ressourcentypen,
- Workflowdefinitionen,
- fachliche Feature-Flags,
- Standardprojekte,
- fachliche Rollen,
- Chatkonfiguration,
- Vorlagenpakete.

Diese Werte gehören in persistente, versionierte Laufzeitkonfiguration oder dynamische Definitionen.

---

# 12. Runtime-Konfiguration

Runtime-Konfiguration beschreibt veränderbares Verhalten der Plattform.

Sie kann gelten für:

```text
System
Tenant
Benutzer
Hierarchieknoten
workspace
project
chat
Widget
Ressource
Workflow
Integration
Session
```

Typische Beispiele:

- Standardmodell,
- verfügbare Modelle,
- erlaubte Tools,
- Promptzuordnungen,
- UI-Präferenzen,
- Sprachpräferenzen,
- Widget-Layouts,
- Datenprofile,
- Aufbewahrungsregeln,
- Benachrichtigungsregeln,
- Suchoptionen,
- Actionfreigaben.

---

# 13. Konfigurationshierarchie

Konfiguration kann auf mehreren Ebenen definiert werden.

```text
System
→ Tenant
→ Benutzer
→ Hierarchiepfad
→ aktiver Knoten
→ Chat
→ Laufzeitrequest
```

Die effektive Konfiguration wird nicht durch einfaches Überschreiben bestimmt.

Jede Definition besitzt eine Merge-Strategie.

Mögliche Strategien:

```text
inherit
extend
replace
restrict
disable
```

Sicherheitsrelevante Werte verwenden immer die strengste Kombination.

---

# 14. Definition, Instanz und Zuordnung

## 14.1 Definition

```text
Es gibt einen Ressourcentyp `note`.
```

## 14.2 Instanz

```text
Diese konkrete Notiz existiert.
```

## 14.3 Zuordnung

```text
Diese Notiz ist mit Projekt X und Chat Y verknüpft.
```

Dasselbe Modell gilt für:

- Prompts,
- Widgets,
- Actions,
- Workflows,
- Integrationen,
- Knotentypen.

---

# 15. Runtime-Registries

Dynamische Definitionen werden in kontrollierten Runtime-Registries verwaltet.

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

Technische Implementierungsregistries bleiben fest:

```text
widget_types
action_handlers
tool_handlers
workflow_step_types
ui_component_types
integration_transports
```

Eine Datenbankdefinition kann keine neue technische Implementierung registrieren.

---

# 16. Discovery, Validierung und Aktivierung

Kernschmied unterscheidet strikt:

```text
Discovery
→ Import
→ Validierung
→ Review
→ Freigabe
→ Aktivierung
```

Es gilt:

> Discovery oder Speicherung bedeutet niemals Aktivierung.

Eine neu gefundene Definition darf nicht automatisch:

- im Frontend erscheinen,
- Aktionen anbieten,
- Ressourcen erzeugen,
- Prompts beeinflussen,
- Tools freigeben.

---

# 17. Effective Context

Der Effective Context ist das serverseitig berechnete Ergebnis aller relevanten Schichten.

Er berücksichtigt:

- Tenant,
- Benutzer,
- Rollen,
- aktiven Hierarchieknoten,
- Hierarchievorfahren,
- Promptbeiträge,
- Widget-Zuordnungen,
- Actionfreigaben,
- Datenprofil,
- Runtime-Konfiguration,
- Registry-Revisionen,
- Capabilities.

Beispiel:

```json
{
  "schema_version": "1.0",
  "tenant_id": "tenant_local",
  "user_id": "local-user",
  "active_node_id": "node_chat_1",
  "active_chat_id": "chat_1",
  "effective_revisions": {
    "config": 12,
    "permissions": 8,
    "prompts": 4,
    "hierarchy": 17
  },
  "registry_revisions": {
    "resource_types": 5,
    "widget_instances": 7,
    "concepts": 3
  },
  "available_action_ids": ["message.send", "resource.create"],
  "available_widget_ids": ["widget_notes"],
  "data_profile": "standard"
}
```

Nicht ausgegeben werden:

- Secrets,
- vollständige Sicherheitsprompts,
- interne Rollenauflösung,
- ungefilterte Policytexte,
- interne Modellrouting-Details.

---

# 18. Revisionen

## 18.1 Objekt-Revision

Jedes veränderbare Objekt besitzt eine monotone Revision.

Verwendung:

- Optimistic Locking,
- Konflikterkennung,
- Audit,
- Cache-Invalidierung.

## 18.2 Config-Revision

Die Config-Revision zeigt Änderungen an persistenter Systemkonfiguration an.

## 18.3 Registry-Revision

Jede Registry besitzt eine eigene Revision.

Beispiele:

```text
node_types
resource_types
widgets
actions
concepts
workflows
integrations
```

## 18.4 Hierarchie-Revision

Die Hierarchie besitzt einen eigenen Revisionsstand.

## 18.5 Berechtigungsrevision

Berechtigungen und Memberships besitzen einen eigenen Revisionsstand.

---

# 19. Cache-Invalidierung

Cache-Schlüssel enthalten relevante Revisionen.

Beispiel:

```text
tenant_id
user_id
active_node_id
config_revision
permission_revision
hierarchy_revision
registry_revision
```

Änderungsablauf:

```text
Konfiguration ändern
→ validieren
→ speichern
→ Revision erhöhen
→ Audit schreiben
→ Cache logisch ungültig
→ Ereignis senden
→ Frontend lädt betroffene Daten neu
```

Keine globalen Caches ohne Invalidierungsweg.

---

# 20. Capability Negotiation

Bootstrap liefert keine Annahmen, sondern explizite Fähigkeiten.

Beispiel:

```json
{
  "capabilities": {
    "runtime_configuration": {
      "enabled": true,
      "version": "2.0",
      "features": ["revision", "validation", "batch_update"]
    },
    "dynamic_resource_types": {
      "enabled": false,
      "version": "1.0",
      "features": [],
      "reason": "not_implemented"
    }
  }
}
```

Das Frontend darf aus vorhandenen Verträgen nicht schließen, dass eine Funktion aktiv ist.

---

# 21. Betriebsprofile

## 21.1 Development

Zulässig:

- vereinfachte lokale Identität,
- unsichere lokale HTTP-Verbindung,
- ausführliche Diagnosen,
- lokale Standardwerte.

Nicht zulässig:

- versehentliche Übernahme unsicherer Werte in produktive Profile.

## 21.2 Intranet

Erforderlich:

- Authentifizierung,
- Audit,
- sichere Session- oder Proxy-Identität,
- kontrollierte CORS-Regeln,
- sichere Secrets.

## 21.3 Internet

Erforderlich:

- HTTPS,
- sichere Sessions,
- CSRF-Schutz,
- Rate Limiting,
- sichere Cookies,
- Security Header,
- strenge Startup-Validierung.

Ein Profil kann Sicherheitsuntergrenzen verschärfen.

Runtime-Konfiguration darf sie nicht lockern.

---

# 22. Secrets

Secrets gehören nicht in normale Runtime-Konfiguration.

Dazu zählen:

- API-Schlüssel,
- Passwörter,
- Session-Schlüssel,
- OAuth-Secrets,
- private Schlüssel,
- Datenbankpasswörter.

Secrets werden:

- über Bootstrap,
- Secret Store,
- sichere Referenzen

bereitgestellt.

Runtime-Konfiguration darf nur referenzieren:

```text
secret_reference
secret_configured
```

Nicht ausgegeben werden:

- Secretwert,
- teilweise maskierter Originalwert,
- Secret in Auditdaten,
- Secret in API-Antworten.

---

# 23. Hot Reload

Nicht jede Änderung erfordert einen Neustart.

## 23.1 Ohne Neustart

Typische Laufzeitänderungen:

- Promptzuordnung,
- Widget-Layout,
- Standardmodell,
- aktive Ressourcentypdefinition,
- Alias,
- Konzept,
- Benutzerpräferenz,
- Hierarchieknoten,
- Datenprofil,
- Toolfreigabe.

## 23.2 Mit Neustart

Typische Bootstrapänderungen:

- Datenbankverbindung,
- Secret-Key,
- Speicherpfad,
- Netzwerkbindung,
- HTTPS-Konfiguration,
- importierte technische Verzeichnisse,
- Logging-Infrastruktur.

## 23.3 Bedingter Reload

Einige Änderungen erfordern:

- Registry-Neuladen,
- Provider-Neustart,
- Cache-Invalidierung,
- kontrollierten Service-Reload.

Die Änderungsklasse muss im Konfigurationsvertrag dokumentiert sein.

---

# 24. Konfigurationsdefinitionen

Jeder konfigurierbare Wert besitzt eine Definition.

Beispiel:

```text
group
key
value_schema
default_value
scope
ui
permissions
sensitivity
reload_behavior
revision_behavior
```

Eine Definition beschreibt:

- Datentyp,
- Validierung,
- Standardwert,
- zulässige Scopes,
- UI-Komponente,
- Berechtigungen,
- Sicherheitsklasse,
- Reload-Verhalten.

---

# 25. Konfigurationsänderungen

Jede Mutation muss:

- autorisiert,
- validiert,
- revisionsgeschützt,
- atomar,
- auditierbar

sein.

Request:

```json
{
  "expected_revision": 12,
  "changes": [
    {
      "group": "models",
      "key": "default_provider",
      "value": "ollama"
    },
    {
      "group": "models",
      "key": "default_model",
      "value": "qwen2.5:7b"
    }
  ]
}
```

Bei Validierungsfehlern darf keine Teiländerung gespeichert werden.

---

# 26. Atomare Batch-Updates

Zusammengehörige Werte müssen gemeinsam geändert werden können.

Beispiel:

```text
Provider
+
Modell
```

Ein Providerwechsel ohne gültiges Modell darf nicht zu einem inkonsistenten Zwischenzustand führen.

Ablauf:

```text
gesamten Request validieren
→ Abhängigkeiten prüfen
→ Berechtigungen prüfen
→ Transaktion starten
→ alle Werte speichern
→ Revision einmal erhöhen
→ Audit schreiben
→ commit
```

---

# 27. Rollback

Jede Konfigurationsänderung besitzt:

- vorherige Revision,
- neue Revision,
- Autor,
- Zeitstempel,
- Änderungsgrund,
- Diff oder sichere Änderungsreferenz.

Rollback erzeugt eine neue Revision.

Alte Daten werden nicht durch direktes Zurücksetzen überschrieben.

```text
Revision 5
→ Änderung
Revision 6
→ Rollback auf Inhalt von Revision 5
Revision 7
```

---

# 28. Migrationen

Konfigurationsschemata können sich verändern.

Dafür benötigt Kernschmied:

- Schemaversion,
- Migrationen,
- Kompatibilitätsprüfung,
- Default-Ergänzungen,
- Deprecation-Phasen,
- Tests.

Alte Werte dürfen nicht stillschweigend anders interpretiert werden.

---

# 29. Mehrmandantenfähigkeit

Jeder relevante Laufzeitwert besitzt einen klaren Scope.

Mögliche Scopes:

```text
system
tenant
user
hierarchy_node
chat
session
```

Ein Benutzer kann mehreren Tenants angehören.

```text
User
↔ Membership
↔ Tenant
```

Tenant-Grenzen werden in jeder Query berücksichtigt.

Mandantenübergreifende Konfiguration ist standardmäßig verboten.

---

# 30. Bootstrap-Endpunkt

Der Bootstrap-Endpunkt liefert ausschließlich nicht sensitive Informationen.

Mindestens:

- Anwendungsname,
- Version,
- Betriebsprofil,
- API-Version,
- Endpointschlüssel,
- Capabilities,
- Featureinformationen,
- Revisionsstände,
- Identitätsstatus,
- degradierte Funktionen.

Nicht enthalten:

- Secrets,
- Tokens,
- Session-IDs,
- interne Pfade,
- vollständige Sicherheitskonfiguration,
- Datenbankverbindungsdaten.

---

# 31. Startup-Ablauf

Empfohlener Ablauf:

```text
1. Prozessumgebung lesen
2. Bootstrapwerte validieren
3. Betriebsprofil prüfen
4. Logging initialisieren
5. Speicherpfade prüfen
6. Datenbankverbindung herstellen
7. Datenbankschema und Migration prüfen
8. Systemkonfiguration laden
9. Config-Revision laden
10. Registries initialisieren
11. Definitionen entdecken
12. aktive Definitionen laden
13. Capabilities bestimmen
14. Dienste initialisieren
15. Readiness aktivieren
```

Bei Fehlern wird unterschieden zwischen:

- fatal,
- degradierbar,
- optional.

---

# 32. Fataler Startup-Fehler

Fatal sind beispielsweise:

- ungültige Bootstrapwerte,
- fehlender Secret-Key im Internetprofil,
- nicht erreichbare Pflichtdatenbank,
- inkompatibles Datenbankschema,
- ungültige Sicherheitsuntergrenze,
- nicht lesbarer Pflichtspeicher.

Die Anwendung darf nicht als ready gelten.

---

# 33. Degradierter Startup-Zustand

Degradierbar können sein:

- optionaler Modellprovider nicht erreichbar,
- optionales Tool ungültig,
- optionale Integration deaktiviert,
- nicht benötigte Registry teilweise fehlerhaft.

Das System startet, markiert aber die Capability als deaktiviert oder degradiert.

---

# 34. Readiness und Liveness

## Liveness

Prüft nur, ob der Prozess lebt.

## Readiness

Prüft, ob die Anwendung fachlich verwendbar ist.

Readiness kann berücksichtigen:

- Datenbank,
- Migration,
- Konfiguration,
- Pflichtregistries,
- Sicherheitsprofil,
- zentrale Services.

Optionale Provider dürfen die gesamte Readiness nicht zwingend blockieren.

---

# 35. Sicherheitsinvarianten

1. `.env` enthält keine normale Fachkonfiguration.
2. Secrets werden nicht in Runtime-Konfiguration gespeichert.
3. Runtime-Konfiguration kann Sicherheitsuntergrenzen nicht lockern.
4. Nicht validierte Definitionen werden nicht aktiviert.
5. Discovery bedeutet nicht Aktivierung.
6. Jede Änderung wird serverseitig autorisiert.
7. Jede Mutation ist revisionsgeschützt.
8. Zusammengehörige Änderungen werden atomar gespeichert.
9. Keine Teiländerung bei Validierungsfehler.
10. Keine Secrets in API-Antworten.
11. Keine Secrets in Auditdetails.
12. Tenant-Grenzen werden serverseitig durchgesetzt.
13. Frontendwerte ersetzen keine Backendvalidierung.
14. Runtime-Konfiguration registriert keinen ausführbaren Code.
15. Unsichere Developmentwerte werden in Intranet und Internet abgelehnt.

---

# 36. Positive Konsequenzen

## 36.1 Klare Verantwortlichkeiten

Bootstrap und Laufzeitverhalten sind sauber getrennt.

## 36.2 Weniger Neustarts

Fachliche Änderungen können zur Laufzeit erfolgen.

## 36.3 Bessere Wartbarkeit

`.env` bleibt klein und verständlich.

## 36.4 Sichere Dynamik

Neue Definitionen können ergänzt werden, ohne ausführbaren Code zu laden.

## 36.5 Revisionsbasierte Aktualisierung

Frontend und Backend können gezielt auf Änderungen reagieren.

## 36.6 Bessere Mehrmandantenfähigkeit

Konfiguration besitzt klare Scopes.

## 36.7 Auditierbarkeit

Jede relevante Änderung bleibt nachvollziehbar.

---

# 37. Negative Konsequenzen

## 37.1 Höhere Architekturkomplexität

Mehrere Konfigurationsschichten müssen verstanden und gepflegt werden.

## 37.2 Context Resolver erforderlich

Effektive Werte können nicht immer direkt aus einer Tabelle gelesen werden.

## 37.3 Cache-Invalidierung wird notwendig

Mehrere Revisionen müssen korrekt ausgewertet werden.

## 37.4 Migrationen werden komplexer

Nicht nur Datenbanktabellen, sondern auch Konfigurationsdefinitionen und Werte benötigen Migrationen.

## 37.5 Administrative Oberfläche erforderlich

Laufzeitkonfiguration benötigt sichere Bearbeitungs- und Diagnosemöglichkeiten.

## 37.6 Debugging erfordert Transparenz

Es muss nachvollziehbar sein, warum ein bestimmter Wert effektiv gilt.

---

# 38. Verworfene Alternativen

## 38.1 Alles über `.env`

### Vorteile

- einfach zu starten,
- vertrautes Betriebsmodell.

### Nachteile

- Neustarts,
- fehlende Laufzeitflexibilität,
- schlechte Typisierung,
- hohe Drift,
- Secrets und Fachwerte vermischt.

**Entscheidung:** Verworfen.

---

## 38.2 Alles in der Datenbank

### Vorteile

- maximale Laufzeitflexibilität.

### Nachteile

- Anwendung kann ohne Datenbank nicht sicher starten,
- Bootstrap-Secrets fehlen,
- Infrastrukturparameter werden unklar,
- Startreihenfolge wird zirkulär.

**Entscheidung:** Verworfen.

---

## 38.3 Statische Konfigurationsdateien

Beispiele:

- YAML,
- JSON,
- TOML.

### Vorteile

- strukturierter als `.env`,
- versionierbar.

### Nachteile

- weiterhin restartpflichtig,
- schwierig pro Tenant oder Benutzer,
- Secrets und Fachwerte können vermischt werden,
- parallele Konfigurationsquellen.

**Entscheidung:** Nicht als primäre Laufzeitquelle.

Manifeste und Pakete dürfen weiterhin dateibasiert importiert werden.

---

## 38.4 Frontend verwaltet Konfiguration selbst

### Vorteile

- schnelle UI-Anpassung,
- lokale Präferenzen einfach speicherbar.

### Nachteile

- keine zentrale Autorisierung,
- inkonsistente Zustände,
- keine Mandantenkontrolle,
- schlechte Auditierbarkeit.

**Entscheidung:** Verworfen.

Lokale, rein visuelle Präferenzen dürfen kontrolliert lokal gespeichert werden.

---

## 38.5 Globale Singleton-Konfiguration

### Vorteile

- einfache Zugriffe,
- geringe Boilerplate.

### Nachteile

- schwer testbar,
- versteckte Abhängigkeiten,
- Probleme bei Multi-Tenancy,
- schwierige Invalidierung,
- ungeeignet für Multi-Worker.

**Entscheidung:** Verworfen.

Dependency Injection und explizite Services werden verwendet.

---

# 39. Migrationsstrategie vom IST zum SOLL

## Phase 1 – Konfigurationsbestand inventarisieren

- `.env`-Werte katalogisieren,
- fachliche Werte identifizieren,
- Sicherheitswerte identifizieren,
- Defaults im Code suchen,
- Frontend-Lokalwerte erfassen.

## Phase 2 – Bootstrapwerte reduzieren

- nur Infrastruktur,
- Secrets,
- Profile,
- Startpfade,
- Netzwerk,
- Logging.

## Phase 3 – Config-v2 abschließen

- vollständige Definitionsmetadaten,
- Schemavalidierung,
- Revisionsschutz,
- strukturierte Fehler,
- Secret-Metadaten.

## Phase 4 – Atomare Batch-Updates

- mehrere Werte gemeinsam validieren,
- Transaktionen,
- keine Teiländerung,
- einheitliche Revision.

## Phase 5 – Registry-Revisionen

- getrennte Revisionen für dynamische Definitionen,
- Capability-Ausgabe,
- Cache-Invalidierung.

## Phase 6 – Effective Context

- Scopes,
- Hierarchiepfad,
- Berechtigungen,
- Prompts,
- Widgets,
- Actions,
- Datenprofil.

## Phase 7 – Diagnose

- Herkunft eines Werts anzeigen,
- Revision anzeigen,
- Merge-Strategie anzeigen,
- keine Secrets offenlegen.

## Phase 8 – Multi-Worker-Invalidierung

- Datenbankrevision,
- Polling oder Notify,
- später PostgreSQL `LISTEN/NOTIFY` oder Redis.

---

# 40. Abnahmekriterien

Die Entscheidung gilt als technisch umgesetzt, wenn:

- `.env` nur Bootstrap-, Infrastruktur- und Sicherheitswerte enthält,
- fachliche Werte in der Datenbank liegen,
- Bootstrapwerte beim Start streng validiert werden,
- Runtime-Konfiguration versioniert ist,
- jede Mutation revisionsgeschützt ist,
- Batch-Updates atomar sind,
- Validierungsfehler keine Teiländerung speichern,
- Secrets nicht in normalen Configantworten erscheinen,
- Config-Änderungen auditierbar sind,
- Registry-Revisionen vorhanden sind,
- Effective Context serverseitig berechnet wird,
- Capability Negotiation funktioniert,
- Sicherheitsprofile ihre Untergrenzen erzwingen,
- unsichere Developmentwerte produktiv abgelehnt werden,
- Frontend nur validierte Konfiguration übernimmt,
- Cache-Invalidierung revisionsbasiert funktioniert,
- OpenAPI dem tatsächlichen Vertragsstand entspricht.

---

# 41. Konkrete Auswirkungen auf Kernschmied

## Backend

Zielbereiche:

```text
backend/app/config/
backend/app/contracts/config.py
backend/app/services/config_service.py
backend/app/services/context_service.py
backend/app/registries/
backend/app/bootstrap/
backend/app/api/v1/config.py
backend/app/api/v1/bootstrap.py
```

## Frontend

Zielbereiche:

```text
frontend/src/contracts/config.ts
frontend/src/contracts/bootstrap.ts
frontend/src/contracts/context.ts
frontend/src/api/config.ts
frontend/src/api/bootstrap.ts
frontend/src/components/settings/
frontend/src/state/
```

## Tests

Zielbereiche:

```text
backend/tests/config/
backend/tests/bootstrap/
backend/tests/context/
frontend/src/contracts/__tests__/
frontend/src/components/settings/__tests__/
```

---

# 42. Verbindliche Architekturregeln

1. `.env` enthält nur Bootstrap-, Infrastruktur- und Sicherheitswerte.
2. Fachliche Konfiguration liegt versioniert in der Datenbank.
3. Secrets liegen nicht in normaler Runtime-Konfiguration.
4. Bootstrap startet die Plattform, bestimmt aber nicht die Fachlichkeit.
5. Laufzeitkonfiguration besitzt klare Scopes.
6. Definition, Instanz und Zuordnung bleiben getrennt.
7. Discovery bedeutet niemals Aktivierung.
8. Jede Definition wird vor Aktivierung validiert.
9. Jede Mutation wird serverseitig autorisiert.
10. Jede konfliktanfällige Änderung verwendet Revisionen.
11. Zusammengehörige Änderungen werden atomar gespeichert.
12. Sicherheitsgrenzen können nur verschärft, nicht gelockert werden.
13. Effective Context wird ausschließlich serverseitig berechnet.
14. Frontendwerte ersetzen keine Backendvalidierung.
15. Keine globale Singleton-Magie.
16. Cache-Invalidierung erfolgt revisionsbasiert.
17. Bootstrap-Ausgaben enthalten keine Secrets.
18. Capabilities werden explizit ausgehandelt.
19. Tenant-Grenzen werden in jeder Query berücksichtigt.
20. Unsichere Konfiguration verhindert produktive Readiness.

---

# 43. Endgültige Entscheidung

Kernschmied verwendet dauerhaft eine mehrschichtige Konfigurationsarchitektur.

Das System kombiniert:

```text
minimale Bootstrap-Konfiguration
+
persistente Laufzeitkonfiguration
+
dynamische validierte Definitionen
+
Instanzen und Zuordnungen
+
Registry-Revisionen
+
serverseitigen Effective Context
+
revisionsbasierte Cache-Invalidierung
```

Dadurch bleibt Kernschmied:

- sicher startbar,
- dynamisch veränderbar,
- fachneutral,
- auditierbar,
- mandantenfähig,
- langfristig wartbar.

Die Plattform kann neue fachliche Strukturen und Verhaltensweisen aufnehmen, ohne dass Infrastrukturwerte, Secrets und Fachkonfiguration miteinander vermischt werden.
