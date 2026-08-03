# ADR-0001: Schema-gesteuerte Benutzeroberfläche einführen

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
  * `documentation/architecture/effective-context.md`
  * `documentation/architecture/dynamic-definitions.md`

---

## 1. Entscheidung in Kurzform

Kernschmied verwendet eine **schema-gesteuerte Benutzeroberfläche**.

Das Backend stellt versionierte, validierte und autorisierte Definitionen für:

* Ansichten
* Layouts
* Formulare
* Felder
* Widgets
* Aktionen
* Sichtbarkeit
* Datenbindungen
* Navigation
* unterstützte Knotendarstellungen

bereit.

Das Frontend rendert diese Definitionen ausschließlich mit:

* bekannten Komponenten,
* einer festen Komponenten-Registry,
* einer festen Action-Registry,
* validierten Laufzeitverträgen,
* kontrollierten API-Endpunkten.

Das Backend darf keine beliebigen React-Komponenten, JavaScript-Funktionen, Importpfade oder ausführbaren Codestrukturen an das Frontend übertragen.

Die zentrale Regel lautet:

> Das Backend beschreibt die beabsichtigte Darstellung und die erlaubten Interaktionen.
> Das Frontend entscheidet, wie bekannte und freigegebene Typen sicher dargestellt werden.

---

# 2. Kontext

Kernschmied soll keine fest verdrahtete Fachanwendung werden.

Das System soll langfristig unterschiedliche Nutzungskontexte unterstützen, ohne dass der technische Kern für jede neue Richtung umgebaut werden muss.

Dazu gehören unter anderem:

* unterschiedliche Betriebsprofile,
* konfigurierbare Hierarchien,
* dynamische Ressourcentypen,
* konfigurierbare Prompts,
* registrierte Modelle,
* registrierte Tools,
* dynamische Widgets,
* registrierte Aktionen,
* geführte Workflows,
* Vorlagenpakete,
* Integrationen,
* spätere Plugin- und Erweiterungspunkte,
* Laufzeitkonfiguration,
* mehrmandantenfähige Strukturen,
* langfristige Wartbarkeit.

Die fachliche Bedeutung eines Bereichs entsteht nicht durch eine spezielle React-Komponente.

Beispiele wie:

* Firma,
* Schule,
* Verein,
* Familie,
* Handwerk,
* Projektarbeit,
* Dokumentenverwaltung

werden nicht als fest programmierte Frontendmodule behandelt.

Ihre Bedeutung entsteht durch:

* Prompts,
* Schemas,
* Ressourcen,
* Aliase,
* Konzepte,
* Widgets,
* Vorlagen,
* Berechtigungen,
* Teilnehmer,
* Beziehungen.

---

# 3. Problemstellung

Eine klassische React-Anwendung würde für viele fachliche Objekte eigene Seiten und Komponenten einführen.

Beispiele:

```text
CustomerPage
ProjectEditor
InvoiceForm
TeamManagement
UserAdministration
SettingsPage
ConstructionSiteView
SchoolClassEditor
```

Dieser Ansatz ist bei kleinen, statischen Anwendungen verständlich, widerspricht jedoch dem Ziel von Kernschmied.

## 3.1 Fachlogik gelangt in das Frontend

Bei spezialisierten Komponenten entstehen häufig Regeln wie:

```typescript
if (node.type === "project") {
  // spezielle Projektlogik
}
```

oder:

```typescript
if (resource.type === "offer") {
  // spezielles Angebotsformular
}
```

Dadurch entsteht:

* doppelte Logik in Backend und Frontend,
* uneinheitliche Validierung,
* schwer nachvollziehbare Berechtigungslogik,
* erhöhte Kopplung,
* wachsender Testaufwand.

## 3.2 Enge Kopplung

Eine Frontendfreigabe würde erforderlich, sobald:

* neue fachliche Typen eingeführt werden,
* Formulare verändert werden,
* Felder hinzukommen,
* Layouts geändert werden,
* Ressourcen neu kombiniert werden,
* neue Aktionen angeboten werden,
* Sichtbarkeitsregeln verändert werden.

## 3.3 Schlechte Erweiterbarkeit

Jede neue Nutzungsausrichtung würde typischerweise benötigen:

* neue Seiten,
* neue React-Komponenten,
* neue Routen,
* neue Formulare,
* neue Validierungen,
* neue Tests,
* neue Zustandslogik.

## 3.4 Hohe Wartungskosten

Mit zunehmender Größe entstehen:

* duplizierte Komponenten,
* unterschiedliche Fehlerbehandlung,
* uneinheitliche Darstellung,
* wachsende Frontendkomplexität,
* schwer kontrollierbare Abhängigkeiten.

## 3.5 Ungeeignete Grundlage für dynamische Erweiterungen

Dynamische Definitionen könnten ihre Wirkung nicht entfalten, wenn das Frontend für jeden neuen Typ erneut erweitert werden müsste.

Eine dynamisch angelegte Ressourcendefinition wäre beispielsweise nutzlos, wenn anschließend dennoch eine neue React-Seite programmiert werden müsste.

---

# 4. Abgrenzung: Chat-Zentrum und schema-gesteuerte UI

Kernschmied bleibt chat-zentriert.

Die schema-gesteuerte Oberfläche ersetzt den Chat nicht.

Die Rollen sind getrennt:

```text
Chat:
Absicht, Kommunikation, Erklärung, Bestätigung und Ergebnis

Widgets:
strukturierte Darstellung und effiziente Bearbeitung

Backend:
Validierung, Autorisierung, Persistenz und Ausführung

UI-Schema:
Beschreibung der unterstützten Darstellung und Interaktion
```

Der Chat ist das Intentions- und Kommunikationszentrum.

Widgets und schema-gesteuerte Ansichten unterstützen den Nutzer bei Aufgaben, für die strukturierte Oberflächen sinnvoller sind, beispielsweise:

* Tabellen,
* Formulare,
* Listen,
* Kalender,
* Dateiansichten,
* Massenbearbeitung,
* Hierarchiebearbeitung.

---

# 5. Aktueller Zustand – IST

Zum Zeitpunkt dieser Überarbeitung verfügt Kernschmied bereits über Teile einer schema-gesteuerten Architektur.

## 5.1 Bereits vorhanden

* ein UI-Schema-Endpunkt,
* eine generische rekursive Hierarchiedarstellung,
* Grundlagen einer Komponenten-Registry,
* Grundlagen einer Action-Registry,
* ein teilweise implementierter `SchemaRenderer`,
* ein `UnsupportedSchema`- beziehungsweise Fallback-Konzept,
* zentrale API-Grundlagen,
* versionierte Bootstrap- und UI-Verträge,
* dynamische Konfigurationsdefinitionen,
* UI-Metadaten für Einstellungen,
* ein generischer Chatbereich,
* feste Modell- und Tool-Registries.

## 5.2 Teilweise implementiert

* Schema-Normalisierung,
* Komponentenauflösung,
* dynamische Formularfelder,
* Sichtbarkeitsregeln,
* Action-Ausführung,
* Fehlergrenzen,
* dynamische Datenbindungen,
* schema-gesteuerte Knotenansichten,
* Laufzeitvalidierung im Frontend.

## 5.3 Derzeitige Inkonsistenzen

* einzelne Frontendbereiche enthalten noch spezialisierte oder direkte Darstellungslogik,
* der `SchemaRenderer` deckt noch nicht alle vorgesehenen Typen ab,
* manche API-Daten werden noch nicht konsequent zur Laufzeit validiert,
* UI-Schema, Widget-System und fachliche Ressourcenverträge sind noch nicht vollständig getrennt,
* Actiondefinitionen enthalten noch nicht alle Risikoklassen und Ausführungsregeln,
* dynamische Definitionen und technische Implementierungsregistries sind noch nicht vollständig voneinander getrennt,
* bestehende Verträge befinden sich teilweise noch direkt in Routerdateien,
* unbekannte Typen werden noch nicht in allen Pfaden einheitlich behandelt.

---

# 6. Zielzustand – SOLL

Kernschmied soll einen stabilen, versionierten und fachneutralen UI-Vertragsrahmen besitzen.

## 6.1 Schema-gesteuerte Ansichten

Das Backend kann Ansichten beschreiben durch:

* Layoutdefinitionen,
* Sektionen,
* Felder,
* Tabellen,
* Baumansichten,
* Detailansichten,
* Widgets,
* Aktionen,
* Sichtbarkeitsbedingungen,
* Aktivierungsbedingungen,
* Datenquellen,
* Metadaten.

## 6.2 Feste technische Registries

Das Frontend besitzt feste Registries für:

```text
UI-Komponenten
Widgets
Icons
Aktionen
Layouttypen
Formularfelder
Workflow-Darstellungen
```

Neue Konfigurationen dürfen nur bekannte Registry-Einträge referenzieren.

## 6.3 Dynamische Definitionen

Zur Laufzeit dürfen ergänzt werden:

* UI-Schemas,
* Ressourcenschemas,
* Widget-Instanzen,
* Widget-Zuordnungen,
* Layouts,
* Promptdefinitionen,
* Aliase,
* Konzepte,
* Knotentypdefinitionen,
* Workflows aus bekannten Schritten,
* Vorlagenpakete.

Zur Laufzeit dürfen nicht ergänzt werden:

* neue React-Komponenten,
* neue JavaScript-Funktionen,
* neue Python-Handler,
* unbekannte Action-Implementierungen,
* freie API-Ziele,
* beliebige Imports.

## 6.4 Laufzeitvalidierung

Jede öffentliche Backendantwort wird vor der Nutzung im Frontend validiert.

Ungültige Daten werden:

* nicht in den Store übernommen,
* als strukturierter Fehler behandelt,
* im Development-Profil diagnostizierbar gemacht,
* niemals stillschweigend ausgeführt.

## 6.5 Sichere unbekannte Typen

Unbekannte Typen führen nicht zu dynamischer Ausführung.

Stattdessen zeigt das Frontend einen kontrollierten Hinweis:

```text
Komponente nicht unterstützt

Typ: custom_editor
Version: 2.0
```

Dies gilt für:

* Komponenten,
* Widgets,
* Aktionen,
* Events,
* Knotentypdarstellungen,
* Workflow-Schritte.

---

# 7. Entscheidung

Kernschmied übernimmt eine **schema-gesteuerte UI-Architektur mit festen technischen Registries und dynamischen validierten Definitionen**.

Die Entscheidung besteht aus mehreren verbindlichen Teilen.

## 7.1 Das Backend beschreibt fachliche Darstellung

Das Backend stellt bereit:

* Schema,
* Datenbindung,
* erlaubte Aktionen,
* Sichtbarkeit,
* Berechtigungsanforderungen,
* Validierungsinformationen,
* Capability-Informationen.

## 7.2 Das Frontend kontrolliert die technische Darstellung

Das Frontend entscheidet:

* welche Komponenten implementiert sind,
* welche Props akzeptiert werden,
* welche Aktionen technisch unterstützt werden,
* welche unbekannten Typen abgelehnt werden,
* wie Fehler dargestellt werden,
* wie responsive Darstellung erfolgt,
* wie Barrierefreiheit umgesetzt wird.

## 7.3 Das Backend bleibt Autorität für Fachlichkeit und Sicherheit

Das Backend bleibt verantwortlich für:

* Berechtigungen,
* Autorisierung,
* Validierung,
* Fachregeln,
* Persistenz,
* Workflows,
* Mandantenisolation,
* Datenschutzprofile,
* Toolfreigaben,
* Aktionsrisiken,
* Auditierung.

## 7.4 Das Frontend bleibt Autorität für sichere Darstellung

Das Frontend bleibt verantwortlich für:

* Rendern bekannter Komponenten,
* lokale Eingabevalidierung,
* verständliche Fehlerdarstellung,
* Tastaturbedienung,
* Fokusmanagement,
* Responsive Design,
* Barrierefreiheit,
* kontrollierten UI-Zustand.

---

# 8. Architekturprinzip

Die frühere verkürzte Formulierung:

> Das Backend definiert, was gerendert wird.
> Das Frontend definiert, wie es gerendert wird.

wird präzisiert zu:

> Das Backend beschreibt über versionierte Verträge, welche fachliche Ansicht und welche Interaktionen beabsichtigt und erlaubt sind.
> Das Frontend rendert ausschließlich bekannte, registrierte und validierte Komponenten und Aktionen.

Eine Backenddefinition ist daher keine Anweisung zur freien Codeausführung.

---

# 9. Zielarchitektur

```text
Datenbank und Konfiguration
        ↓
dynamische Definitionen
        ↓
typspezifische Validierung
        ↓
Freigabe und Aktivierung
        ↓
Backend-Services
        ↓
versionierter UI-Vertrag
        ↓
REST / SSE
        ↓
Frontend-Laufzeitvalidierung
        ↓
Schema Renderer
        ↓
feste Component Registry
        ↓
bekannte React-Komponenten
```

Für Aktionen:

```text
UI-Komponente
        ↓
Action-ID
        ↓
feste Action Registry
        ↓
zentraler API-Client
        ↓
Backend-Autorisierung
        ↓
Service
        ↓
Persistenz / Integration
        ↓
Audit und Ergebnisereignis
```

---

# 10. Kernbausteine

## 10.1 UI-Schema

Das UI-Schema beschreibt ausschließlich Darstellung und Interaktionsabsicht.

Es darf enthalten:

* `schema_version`,
* `id`,
* `component_type`,
* `layout`,
* `children`,
* `bindings`,
* `visibility`,
* `enabled`,
* `actions`,
* `metadata`.

Es darf nicht enthalten:

* ausführbaren Code,
* freie JavaScript-Ausdrücke,
* freie Python-Ausdrücke,
* Importpfade,
* Shell-Kommandos,
* unkontrollierte HTML-Fragmente.

## 10.2 Schema Renderer

Der Schema Renderer:

* validiert beziehungsweise erhält validierte Schemas,
* löst bekannte Komponenten auf,
* rendert rekursiv,
* kontrolliert Rekursionstiefe,
* verwaltet Fehlergrenzen,
* stellt unbekannte Typen sicher dar,
* enthält keine Fachlogik.

## 10.3 Component Registry

Beispiel:

```text
"text"
    ↓
TextField

"textarea"
    ↓
TextAreaField

"resource_table"
    ↓
ResourceTableWidget
```

Die Registry ist technisch fest und wird nicht aus der Datenbank erweitert.

## 10.4 Action Registry

Eine UI-Aktion referenziert eine bekannte Action-ID.

Beispiel:

```text
Button
    ↓
resource.create
    ↓
registrierter Handler
    ↓
API-Client
    ↓
Backend
```

Das Schema registriert keine neuen Handler.

## 10.5 Widget-System

Widget-Typ und Widget-Instanz werden getrennt.

### Widget-Typ

Technisch registrierte React-Komponente.

### Widget-Instanz

Dynamische Konfiguration:

* Titel,
* Datenquelle,
* Filter,
* Sortierung,
* Layout,
* Zuordnung,
* unterstützte Aktionen.

## 10.6 Ressourcen-Schema

Ein dynamischer Ressourcentyp kann ein Formular- und Darstellungsschema liefern.

Das Frontend verwendet generische Komponenten, um daraus:

* Formulare,
* Tabellen,
* Detailansichten,
* Suchfilter

zu erstellen.

---

# 11. Widget-Interaktionsklassen

Widgets werden in drei Klassen eingeteilt.

## 11.1 `read_only`

Nur Darstellung.

Beispiele:

* Status,
* Statistik,
* Vorschau,
* Zusammenfassung.

## 11.2 `trigger_only`

Interaktionen lösen registrierte Aktionen aus.

Beispiele:

* Ressource öffnen,
* Export starten,
* Unterchat erstellen.

## 11.3 `structured_edit`

Das Widget erlaubt strukturierte Bearbeitung.

Beispiele:

* Tabellenbearbeitung,
* Formularbearbeitung,
* Mehrfachauswahl,
* Drag-and-drop-Reihenfolge.

Auch `structured_edit` arbeitet ausschließlich über:

* bekannte Mutationsverträge,
* Backendvalidierung,
* Backendautorisierung,
* Revisionsprüfung.

---

# 12. Action-Risikoklassen

Die UI berücksichtigt die Risikoklasse einer Aktion.

## Klasse A

Lokal und reversibel.

Beispiele:

* Widget verschieben,
* Filter ändern,
* Favorit setzen.

## Klasse B

Fachlich relevant, aber reversibel.

Beispiele:

* Ressource bearbeiten,
* Chat verschieben,
* Zuordnung ändern.

## Klasse C

Extern wirksam oder schwer reversibel.

Beispiele:

* Nachricht versenden,
* Dokument extern freigeben,
* Ressource löschen.

## Klasse D

Sicherheitskritisch.

Beispiele:

* Rollen ändern,
* Sicherheitsrichtlinie ändern,
* Mandantenzugriff verändern.

Das Frontend zeigt die erforderliche Bestätigung an.

Das Backend entscheidet abschließend, ob die Aktion ausgeführt werden darf.

---

# 13. Dynamische Erweiterbarkeit

## 13.1 Erlaubte dynamische Erweiterungen

Zur Laufzeit ergänzbar:

* Knotentypdefinitionen,
* Ressourcentypdefinitionen,
* Promptdefinitionen,
* Widget-Instanzen,
* Widget-Zuordnungen,
* Konzepte,
* Aliase,
* Workflows,
* UI-Schemas,
* Vorlagenpakete.

## 13.2 Nicht dynamisch ausführbar

Nicht aus Backenddaten ladbar:

* React-Komponenten,
* JavaScript-Code,
* Python-Code,
* Action-Handler,
* Tool-Handler,
* Workflow-Schrittimplementierungen,
* Integrations-Transporte.

## 13.3 Aktivierung

Eine dynamische Definition durchläuft:

```text
draft
→ validated
→ pending_approval
→ active
```

Erstellung oder Discovery bedeutet nicht Aktivierung.

---

# 14. UI-Vertragsbeispiel

```json
{
  "schema_version": "1.0",
  "id": "resource-note-form",
  "component_type": "form",
  "layout": {
    "type": "single_column"
  },
  "children": [
    {
      "component_type": "text",
      "binding": "title",
      "label": "Titel",
      "required": true
    },
    {
      "component_type": "textarea",
      "binding": "content",
      "label": "Inhalt",
      "required": true
    }
  ],
  "actions": [
    {
      "action_id": "resource.create",
      "label": "Speichern"
    }
  ]
}
```

Das Frontend prüft:

* Ist `form` bekannt?
* Ist `single_column` bekannt?
* Sind `text` und `textarea` bekannt?
* Ist `resource.create` registriert?
* Sind Bindings und Props gültig?
* Darf die Aktion im aktuellen Kontext angeboten werden?

---

# 15. Versionierung

Jeder öffentliche UI-Vertrag besitzt eine `schema_version`.

## Kompatible Änderung

Beispiele:

* optionales Feld,
* neue Metadaten,
* zusätzliche bekannte Action,
* zusätzliche optionale Komponente.

## Inkompatible Änderung

Beispiele:

* Feld entfernt,
* Feldtyp geändert,
* Semantik verändert,
* Pflichtfeld ergänzt,
* Komponentenstruktur grundlegend geändert.

Inkompatible Änderungen benötigen:

* neue Schemaversion,
* Migrationsweg,
* Tests,
* Dokumentation,
* gegebenenfalls Mindestclientversion.

---

# 16. Capability Negotiation

Das Bootstrap-Dokument teilt mit, welche UI-Fähigkeiten aktiv sind.

Beispiel:

```json
{
  "capabilities": {
    "schema_driven_ui": {
      "enabled": true,
      "version": "1.0",
      "features": [
        "forms",
        "recursive_layout",
        "widget_instances",
        "registered_actions"
      ]
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

Das Frontend darf nicht aus dem Vorhandensein eines Vertrags schließen, dass die Funktion aktiv ist.

---

# 17. Validierung

## Backend

Das Backend validiert:

* UI-Schema-Struktur,
* bekannte technische Referenzen,
* Berechtigungen,
* Datenbindungen,
* Ressourcenschemas,
* Action-IDs,
* Versionskompatibilität.

## Frontend

Das Frontend validiert:

* Transportstruktur,
* Schemaversion,
* Komponenten-IDs,
* Property-Typen,
* Action-Referenzen,
* Layoutstruktur,
* maximale Rekursion,
* unbekannte Typen.

## Mutationsanfragen

Unbekannte Felder werden standardmäßig abgelehnt.

## Antworten

Bekannte Felder werden validiert. Zusätzliche Felder können je Vertrag kontrolliert toleriert werden, ohne sie ungeprüft für Verhalten oder Ausführung zu verwenden.

---

# 18. Sicherheitsinvarianten

1. Das Backend-Schema kann keinen React-Code registrieren.
2. Das Backend-Schema kann keinen JavaScript-Code ausführen.
3. Das Backend-Schema kann keine freien API-Ziele festlegen.
4. Jede Aktion wird serverseitig autorisiert.
5. Unbekannte Komponenten werden nicht ausgeführt.
6. Unbekannte Aktionen werden nicht ausgeführt.
7. Dynamische Definitionen können Sicherheitsregeln nur einschränken, nicht lockern.
8. Prompts ersetzen keine UI- oder Datenvalidierung.
9. Das Frontend vertraut keiner API-Antwort ohne Laufzeitvalidierung.
10. Secrets werden nicht in UI-Schemas übertragen.
11. Freies HTML wird nicht ohne sichere Sanitization gerendert.
12. Backenddaten registrieren keine technischen Handler.

---

# 19. Positive Konsequenzen

## 19.1 Fachneutraler Kern

Neue fachliche Bedeutungen können über Konfiguration entstehen.

## 19.2 Geringere Frontendkopplung

Viele Änderungen an:

* Formularen,
* Layouts,
* Widgets,
* Feldern,
* Ressourcenschemas

benötigen keine neue spezialisierte React-Seite.

## 19.3 Wiederverwendbarkeit

Verbesserungen an generischen Komponenten wirken systemweit.

## 19.4 Stabilere Verträge

Backend und Frontend kommunizieren über explizite versionierte Modelle.

## 19.5 Dynamische Laufzeiterweiterung

Neue Definitionen und Instanzen können ohne Kernumbau ergänzt werden.

## 19.6 Sichere Erweiterbarkeit

Neue fachliche Definitionen führen nicht automatisch zur Ausführung unbekannten Codes.

## 19.7 Bessere Testbarkeit

Registries, Renderer und Verträge können systematisch getestet werden.

---

# 20. Negative Konsequenzen

## 20.1 Höhere Anfangskomplexität

Ein robuster Schema Renderer und stabile Registries erfordern mehr Vorarbeit.

## 20.2 Schemaqualität wird kritisch

Unklare oder zu generische Schemas können schwer wartbare Oberflächen erzeugen.

## 20.3 Generische Komponenten können überladen werden

Komponenten dürfen nicht durch zu viele Sonderfälle zu versteckten Fachanwendungen werden.

## 20.4 Backendverantwortung wächst

Das Backend muss:

* valide Schemas,
* verlässliche Metadaten,
* Actiondefinitionen,
* Berechtigungen,
* Datenbindungen

bereitstellen.

## 20.5 Debugging wird verteilt

Fehler können entstehen in:

* Definition,
* Backendvalidierung,
* Transport,
* Frontendvalidierung,
* Registry-Auflösung,
* Renderer,
* Komponente.

Deshalb sind strukturierte Diagnosen erforderlich.

## 20.6 Nicht jede Ansicht ist sinnvoll generisch

Einzelne technisch hoch spezialisierte Darstellungen können später eine neue kontrollierte Komponente benötigen.

Dies ist erlaubt, solange sie als fester technischer Registry-Eintrag eingeführt wird und nicht aus Backenddaten geladen wird.

---

# 21. Verworfene Alternativen

## 21.1 Ausschließlich spezialisierte React-Seiten

### Vorteile

* vertrautes Entwicklungsmodell,
* schnelle Umsetzung einzelner Masken,
* direktes Debugging.

### Nachteile

* enge Kopplung,
* geringe Laufzeitflexibilität,
* duplizierte Fachlogik,
* hoher Wartungsaufwand,
* widerspricht der Fachneutralität.

**Entscheidung:** Verworfen als grundlegende Architektur.

Spezialisierte technische Komponenten bleiben nur für begründete, registrierte Sonderdarstellungen zulässig.

---

## 21.2 Vollständiges Low-Code-System

### Vorteile

* visuelle Erstellung,
* schnelle Oberflächenkonfiguration.

### Nachteile

* hoher Eigenentwicklungsaufwand,
* Gefahr eines zweiten Produkts innerhalb des Produkts,
* unklare Sicherheitsgrenzen,
* komplexe Migrationen,
* potenzieller Vendor Lock-in bei Fremdlösungen.

**Entscheidung:** Verworfen.

Kernschmied verwendet begrenzte, versionierte Schemas statt eines freien Low-Code-Baukastens.

---

## 21.3 Runtime-JavaScript

Das Backend liefert JavaScript zur Erzeugung von Oberflächen oder Verhalten.

### Vorteile

* maximale Flexibilität,
* keine Frontendfreigabe für neue Logik.

### Nachteile

* Remote-Code-Ausführung,
* erhebliche Sicherheitsrisiken,
* schwer prüfbar,
* schlechte Wartbarkeit,
* unkontrollierbare Abhängigkeiten,
* widerspricht den Sicherheitsprinzipien.

**Entscheidung:** Vollständig verworfen.

---

## 21.4 Dynamische React-Imports

Komponentenpfade werden vom Backend geliefert.

### Vorteile

* scheinbar flexible Erweiterung.

### Nachteile

* Backenddaten kontrollieren ausführbaren Frontendcode,
* Build- und Laufzeitprobleme,
* unklare Vertrauensgrenzen,
* schlechte Fehlerisolierung.

**Entscheidung:** Vollständig verworfen.

---

## 21.5 Reine Chatoberfläche ohne strukturierte UI

### Vorteile

* sehr einheitliche Bedienung,
* geringe Anzahl klassischer Seiten.

### Nachteile

* ineffizient bei Tabellen,
* ungeeignet für Massenbearbeitung,
* ungeeignet für komplexe Formulare,
* schlechte Übersicht bei großen Datenmengen.

**Entscheidung:** Verworfen.

Der Chat bleibt Zentrum. Widgets und schema-gesteuerte Ansichten ergänzen ihn.

---

## 21.6 Backend liefert vollständiges HTML

### Vorteile

* einfache Darstellung im Browser,
* Backend kontrolliert das Layout.

### Nachteile

* XSS-Risiken,
* schwache React-Integration,
* schlechter State-Abgleich,
* eingeschränkte Interaktivität,
* unklare Verantwortlichkeiten.

**Entscheidung:** Verworfen.

---

# 22. Migrationsstrategie vom IST zum SOLL

## Phase 1 – Verträge inventarisieren

* bestehende UI-Schema-Verträge erfassen,
* Router-lokale Modelle identifizieren,
* Frontendtypen erfassen,
* bekannte Komponenten katalogisieren,
* bekannte Aktionen katalogisieren.

## Phase 2 – Öffentliche UI-Verträge zentralisieren

* Pydantic-Verträge in `backend/app/contracts/`,
* TypeScript-Verträge in `frontend/src/contracts/`,
* kompatible Re-Exports,
* OpenAPI prüfen.

## Phase 3 – Laufzeitvalidierung

* Bootstrap,
* UI-Schema,
* Hierarchie,
* Actions,
* Widgets,
* Events

vor Store-Übernahme validieren.

## Phase 4 – Component Registry finalisieren

* bekannte Typen explizit registrieren,
* Props validieren,
* unbekannte Typen sichtbar ablehnen,
* keine dynamischen Imports.

## Phase 5 – Schema Renderer vervollständigen

* rekursive Darstellung,
* Sichtbarkeit,
* Aktivierungszustände,
* Datenbindungen,
* Fehlergrenzen,
* maximale Tiefe,
* kontrollierte Formzustände.

## Phase 6 – Action Registry anbinden

* Action-ID,
* Risikoklasse,
* Bestätigungsregeln,
* API-Auflösung,
* Backendautorisierung,
* Fehlerdarstellung.

## Phase 7 – Widget-System trennen

* Widget-Typ,
* Widget-Instanz,
* Widget-Zuordnung,
* Widget-Layout,
* Interaktionsklasse.

## Phase 8 – Dynamische Ressourcenschemas

* erster Typ `note`,
* generisches Formular,
* generische Liste,
* generische Action,
* SSE-Invalidierung.

## Phase 9 – Weitere Knotendarstellungen migrieren

Beginnend mit:

1. `user`,
2. `workspace`,
3. `project`,
4. `chat`.

Der Chat selbst bleibt eine kontrollierte Kernkomponente und wird nicht vollständig durch beliebige Schemas ersetzt.

---

# 23. Abnahmekriterien

Die Entscheidung gilt als technisch umgesetzt, wenn:

* ein stabiler öffentlicher UI-Schema-Vertrag existiert,
* Backend und Frontend dieselbe Versionierungssemantik verwenden,
* jede Backendantwort vor Store-Übernahme validiert wird,
* unbekannte Komponenten sichtbar und sicher behandelt werden,
* unbekannte Aktionen nicht ausgeführt werden,
* keine dynamischen React-Imports existieren,
* keine fachlich spezialisierten Kernkomponenten erforderlich sind,
* der Schema Renderer rekursive bekannte Komponenten darstellen kann,
* Action Registry und zentraler API-Client angebunden sind,
* Widget-Typ und Widget-Instanz getrennt sind,
* dynamische Ressourcenschemas bekannte Komponenten verwenden,
* jede Mutation serverseitig autorisiert wird,
* UI-Schemas keine Secrets enthalten,
* Tests für bekannte und unbekannte Typen vorhanden sind,
* OpenAPI dem tatsächlichen Laufzeitvertrag entspricht.

---

# 24. Konkrete Auswirkungen auf Kernschmied

## Backend

Zielbereiche:

```text
backend/app/contracts/
backend/app/api/v1/ui.py
backend/app/services/
backend/app/config/
backend/app/registries/
```

## Frontend

Zielbereiche:

```text
frontend/src/contracts/
frontend/src/components/schema/
frontend/src/components/widgets/
frontend/src/registry/
frontend/src/api/
```

## Tests

Zielbereiche:

```text
backend/tests/contracts/
backend/tests/api/
frontend/src/contracts/__tests__/
frontend/src/components/schema/__tests__/
frontend/src/registry/__tests__/
```

---

# 25. Verbindliche Architekturregeln

1. Keine fachlich fest verdrahteten React-Seiten als Kernmodell.
2. Keine freie Codeausführung aus Backenddefinitionen.
3. Keine dynamischen React-Imports.
4. Keine direkte Action-Ausführung aus beliebigen Schemas.
5. Keine Backend-Autorisierung im Frontend nachbilden.
6. Jede öffentliche Definition ist versioniert.
7. Jede unbekannte Komponente wird sicher behandelt.
8. Jede unbekannte Aktion wird abgelehnt.
9. Jede Mutation wird serverseitig validiert und autorisiert.
10. UI-Schemas beschreiben Darstellung, nicht ausführbaren Code.
11. Widgets ergänzen den Chat, ersetzen ihn aber nicht als Intentionszentrum.
12. Neue technische Fähigkeiten benötigen einen kontrollierten Registry-Eintrag im Code.
13. Neue fachliche Definitionen dürfen zur Laufzeit konfiguriert werden.
14. Discovery oder Speicherung bedeutet niemals Aktivierung.
15. Frontend und Backend bleiben über stabile Verträge entkoppelt.

---

# 26. Endgültige Entscheidung

Kernschmied verwendet dauerhaft eine schema-gesteuerte UI-Architektur.

Das System kombiniert:

```text
dynamische fachliche Definitionen
+
versionierte Backendverträge
+
Frontend-Laufzeitvalidierung
+
feste Komponenten-Registry
+
feste Action-Registry
+
generische Widgets
+
serverseitige Autorisierung
```

Dadurch kann Kernschmied neue Nutzungskontexte, Ressourcen und Darstellungen aufnehmen, ohne zu einer Sammlung fest programmierter Fachanwendungen zu werden.

Gleichzeitig bleibt die technische Ausführung kontrolliert, testbar und sicher.
