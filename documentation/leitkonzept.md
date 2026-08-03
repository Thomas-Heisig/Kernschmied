Stand: 2026-08-03

# Kernschmied – Konsolidiertes Leitkonzept

Hinweis: Für das MVP gilt erwartungsgemäß die technische Knotentyp-ID `workspace`. In der deutschen UI wird dieser Knoten als „Bereich" angezeigt. Kurz:

"Bereich" bezeichnet fachlich den technischen Basisknotentyp `workspace`.

## 1. Grundsatz
Kernschmied bleibt vollständig fachneutral.

Der Kern kennt keine fest eingebauten Fachrichtungen wie:

- Firma
- Schule
- Verein
- Familie
- Handwerk
- Verwaltung
- Softwareentwicklung
Diese Bedeutungen entstehen ausschließlich durch:

- Prompts
- Ressourcenschemas
- Vorlagen
- Aliase
- Beziehungen
- Teilnehmer
- Berechtigungen
- Konfigurationen
Die technische Plattform bleibt unverändert.

```
Fachneutraler Kern
    ↓
Prompts
    ↓
Schemas
    ↓
Vorlagen und Aliase
    ↓
konkrete Nutzung
```

---

## 2. Chat als Intentions- und Kommunikationszentrum
Der Chat ist nicht zwingend die einzige Oberfläche.

Er ist jedoch die zentrale Ebene für:

- Absicht des Nutzers
- Kommunikation
- Interpretation
- Zusammenfassung
- Erläuterung
- Aktionsvorschläge
- Bestätigung kritischer Änderungen
- Ergebnisse
- Fehler
- Auditierbare Entscheidungen
Widgets sind ergänzende Arbeitsflächen.

```
Chat:
Was soll passieren und warum?

Widget:
Welche Daten müssen dafür übersichtlich dargestellt oder bearbeitet werden?

Backend:
Darf es passieren und wie wird es korrekt ausgeführt?
```
Damit wird der Chat nicht zum Engpass, bleibt aber das Zentrum der menschlichen Interaktion.

---

## 3. Widgets nicht vollständig auf Read-only beschränken
Die Forderung, Widgets grundsätzlich nur lesend oder auslösend zu gestalten, ist zu streng.

Bei großen Tabellen, Formularen oder Dateimengen wäre dies unpraktisch.

Widgets dürfen deshalb drei Interaktionsklassen besitzen.

## 3.1 Read-only
Nur Darstellung.

Beispiele:

- Statistik
- Vorschau
- Verlauf
- Status
- Zusammenfassung

## 3.2 Trigger-only
Eine Benutzeraktion erzeugt eine registrierte Aktion.

Beispiele:

- Ressource öffnen
- Chat auswählen
- Export anfordern
- neuen Unterchat beginnen

## 3.3 Structured-edit
Strukturierte Bearbeitung direkt im Widget.

Beispiele:

- Tabellenzeilen bearbeiten
- mehrere Elemente markieren
- Felder in einem Formular ändern
- Reihenfolge per Drag-and-drop ändern
- mehrere Dateien zuordnen
Structured-edit darf den Chat nicht umgehen.

Es gilt:

```
Widget sammelt Änderungen
    ↓
Backend validiert Änderungen
    ↓
bei kritischer Aktion erscheint eine Chat-Bestätigung
    ↓
Backend führt Änderung aus
    ↓
Chat protokolliert das Ergebnis
```
Nicht jede Änderung benötigt eine sichtbare Chatnachricht.

Beispielsweise darf das Sortieren eines persönlichen Widgets direkt gespeichert werden.

Kritische oder fachlich relevante Änderungen müssen dagegen im Chat sichtbar und nachvollziehbar sein.

---

## 4. Aktionsklassen statt pauschaler Bestätigung
Nicht jede Aktion darf denselben Ablauf besitzen.

Kernschmied benötigt Risikoklassen.

## Klasse A – lokal und reversibel
Beispiele:

- Widget verschieben
- Ansicht ändern
- Filter setzen
- Chat favorisieren
Ablauf:

```
direkt ausführen
```

## Klasse B – fachlich relevant, aber reversibel
Beispiele:

- Ressource bearbeiten
- Aufgabe zuordnen
- Termin ändern
- Chat verschieben
Ablauf:

```
validieren
→ ausführen
→ im Chat oder Activity Feed protokollieren
```

## Klasse C – extern wirksam oder schwer reversibel
Beispiele:

- Nachricht versenden
- Dokument extern freigeben
- Rechnung übertragen
- Daten löschen
- Teilnehmerberechtigung ändern
Ablauf:

```
Vorschau
→ ausdrückliche Bestätigung
→ ausführen
→ Audit-Log
→ sichtbares Ergebnis im Chat
```

## Klasse D – sicherheitskritisch
Beispiele:

- Rollenänderung
- Mandantenwechsel
- Secret-Konfiguration
- Sicherheitsrichtlinie ändern
Ablauf:

```
besondere Berechtigung
→ erneute Authentifizierung
→ Bestätigung
→ unveränderbares Audit-Log
```
Damit bleibt das System sicher, ohne den Nutzer bei jeder Kleinigkeit auszubremsen.

---

## 5. Fachneutralität und Nutzbarkeit
Ein fachneutraler Kern allein ist für normale Nutzer zu abstrakt.

Deshalb benötigt Kernschmied Konfigurationspakete.

Diese Pakete sind keine Fachmodule.

Sie bestehen aus Daten:

```
Paket
├── Prompt-Vorlagen
├── Ressourcenschemas
├── Widget-Konfigurationen
├── Aliasdefinitionen
├── Beispielhierarchie
├── Startnachrichten
├── Rollenprofile
└── optionale Integrationsvorschläge
```
Beispiele für mitgelieferte Pakete können sein:

```
Leeres System
Persönliche Organisation
Projektarbeit
Kommunikation
Dokumentenarbeit
```

Der Nutzer kann:

- ein leeres System starten
- ein Paket auswählen
- mehrere Pakete kombinieren
- ein Paket kopieren
- ein Paket vollständig verändern
- aus dem eigenen System ein neues Paket erzeugen
Die Fachlichkeit entsteht dadurch aus konfigurierbaren Startwerten und nicht aus hartcodierter Logik.

---

## 6. Geführte Ersteinrichtung
Die erste Einrichtung sollte als Chat mit unterstützenden Widgets erfolgen.

Beispiel:

```
Kernschmied:
Wie möchtest du dein System zunächst verwenden?

[Persönlich]
[Team]
[Organisation]
[Leeres System]
```
Danach:

```
Welche Themen möchtest du zunächst trennen?

[Arbeit]
[Privat]
[Projekte]
[Eigener Bereich]
```
Kernschmied erstellt daraus einen Vorschlag.

```
Vorgeschlagene Struktur:

Thomas
├── Arbeit
│   └── Allgemein
└── Privat
    └── Allgemein

[Übernehmen]
[Bearbeiten]
[Neu vorschlagen]
```
Die Einrichtung ist:

- prompt-gestützt
- schema-gesteuert
- jederzeit veränderbar
- nicht dauerhaft an eine Vorlage gebunden

---

## 7. Navigation
Vier normale Pulldowns reichen langfristig nicht aus.

Die Navigation sollte aus mehreren komplementären Elementen bestehen.

## Primäre Navigation
Generischer rekursiver Baum in der Sidebar.

## Globale Suche
Sucht nach:

- Knoten
- Chats
- Ressourcen
- Nachrichten
- Teilnehmern
- Dokumenten

## Breadcrumb

```
Thomas > Arbeit > Projekt A > Hauptchat
```
Jedes Segment öffnet eine kontextbezogene Auswahl der Geschwister und Unterknoten.

## Schnellwechsler
Tastatur- und Suchdialog:

```
Strg+K
```
Mögliche Ergebnisse:

```
Projekt öffnen
Chat öffnen
Ressource öffnen
Aktion ausführen
neuen Kontext erstellen
```

## Favoriten und zuletzt verwendet
Persönliche Schnellzugriffe.

## Pulldowns
Pulldowns bleiben sinnvoll für:

- schnellen Wechsel innerhalb einer Ebene
- Neuzuordnung
- Kontextbearbeitung
- Auswahl beim Erstellen eines Chats
Sie sind jedoch nicht die alleinige Navigation.

---

## 8. Prompt-Schichten
Die bisherige Prompt-Vererbung muss präziser getrennt werden.

```
1. Sicherheitsrichtlinien
2. Plattform-Systemprompt
3. Mandantenrichtlinien
4. Benutzerkontext
5. Bereichskontext
6. Projektkontext
7. Chatkontext
8. aktuelle Aufgabe
9. Nachrichten und externe Inhalte
```

## 8.1 Sicherheitsrichtlinien
Nicht über die normale Promptverwaltung editierbar.

Sie definieren:

- Sicherheitsgrenzen
- Datenschutzgrenzen
- Tool-Nutzung
- Geheimnisschutz
- Autorisierung
- externe Kommunikation
- Ausgabegrenzen

---

## 9. Prompt-Sicherheit
Ein einfacher Safety-Filter vor dem Systemprompt reicht nicht aus.

Kernschmied benötigt mehrere Schutzebenen.

```
Eingabeprüfung
    ↓
Kontextklassifikation
    ↓
Prompt-Zusammenstellung
    ↓
Tool- und Aktionsfreigabe
    ↓
Modellaufruf
    ↓
Ausgabeprüfung
    ↓
Aktionsvalidierung
```

---

## 10. Fachbegriffe durch Aliase und Konzepte
(gekürzt für Lesbarkeit; vollständiger Text in der originalen Leitkonzeptversion)

---

## 11. Kontextabhängige und lernende Aliase
(gekürzt)

---

## 12. Sichtbarkeit und externe Teilnehmer
(gekürzt)

---

## 13. Keine dynamische Redaktion nur zur Anzeigezeit
(gekürzt)

---

## 14. System-zu-System-Kommunikation
(gekürzt)

---

## 15. Transaktionen und externe Aktionen
(gekürzt)

---

## 16. Temporäre Chats
(gekürzt)

---

## 17. Multi-Tenancy
(gekürzt)

Hinweis: Für das lokale MVP wird ein Default-Tenant `local-default` empfohlen. Alle neuen relevanten Datensätze sollten jedoch bereits `tenant_id`-fähig entworfen werden.

---

## 18. Datenschutzprofile
(gekürzt)

---

## 19. Audit-Log und Aktivitätsverlauf
(gekürzt)

---

## 20. Kontextauflösung
(gekürzt)

---

## 21. Caching
(gekürzt)

---

## 22. Hierarchie-Skalierung
(gekürzt)

---

## 23. Sucharchitektur
(gekürzt)

---

## 24. Walking Skeleton
(gekürzt)

---

## 25. Überarbeitete Entwicklungsphasen
(gekürzt)

---

## 26. Verbindliches Zielbild
(gekürzt)

Das vollständige Leitkonzept ist die Referenz für Architekturentscheidungen; detaillierte Ausformungen und Tasks werden in `documentation/development/` abgelegt.
