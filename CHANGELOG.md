# Changelog

Alle wesentlichen Änderungen an Kernschmied werden in dieser Datei dokumentiert.

Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/). Das Projekt verwendet während der frühen Entwicklung eine an [Semantic Versioning](https://semver.org/lang/de/) angelehnte Versionierung.

## [Unreleased]

### Dokumentation

- Offene Aufgaben in `documentation/todo.md` zentralisiert und alte
  Parallelquellen entfernt.

### Hinzugefügt

- Benutzergebundene Postfächer versenden Willkommens-, Mention- und Testmails über eine fehlertolerante SMTP-Outbox; Mailpit steht als lokaler Testprovider bereit.
- `@Administrator` erzeugt eine direkte, als Administrator attribuierte KI-Auto-Antwort statt einer gewöhnlichen Benutzeranfrage.
- Nur das geschützte Administrator-Systemkonto löst diese Auto-Antwort aus; namentlich erwähnte menschliche Administratoren erhalten normale Mention- und Postfachbenachrichtigungen.
- Chatantworten können als persistente, farblich abgesetzte Nebenunterhaltung mit Elternbezug und Avatar dargestellt werden.
- Versandstatus, Benachrichtigungston, mehrfarbige Glocke sowie filter-, sortier-, archivier- und löschbares Postfach wurden ergänzt.
- Bootstrap-zentrierte Frontendarchitektur wird weiter konsolidiert.
- Schema-gesteuerte Ansichten über einen zentralen `SchemaRenderer` werden erweitert.
- Generische Komponenten- und Action-Registries werden vervollständigt.
- Modell- und Tool-Registries werden mit isolierter Fehlerbehandlung weiter integriert.
- Verträge für Hierarchie, UI-Schema, Modelle, Tools, Chat und Konfiguration werden vereinheitlicht.
- Strukturierte Fehlerantworten mit Request-ID werden weiter ausgebaut.

### Geändert

- KI-Ausgaben werden ausdrücklich attribuiert und durch einen serverseitigen Wahrheits- und Datenschutzrahmen geschützt; freigegebene Profildaten gelten niemals als Anweisungen.
- Pylance-Typfehler bei Mention-Defaults, Assistant-Metadaten und Session-Presence wurden beseitigt.
- Admin- und Selbstregistrierung melden ungültige Passwörter als konkrete Eingabefehler statt HTTP 500; die Browserformulare validieren die Passwortregeln vor dem Versand.
- Der ausgewählte Knotentyp `user` soll künftig über den zentralen `SchemaRenderer` dargestellt werden.
- Frontend-Einstieg und Providerstruktur wurden auf einen zentralen Anwendungseinstieg ausgerichtet.
- Bootstrap-, Registry- und Schema-Normalisierung werden schrittweise gehärtet.

### Behoben

- Persönliche JSON-Präferenzen einschließlich zusätzlicher KI-Antworten werden zuverlässig persistiert; Windows-Zeitzonen werden über `tzdata` aufgelöst.
- Chat-History-, Repository- und Nulladapterverträge sind für Elternnachrichten und Benutzerkontext synchronisiert.

## [0.1.0] - 2026-07-26

### Hinzugefügt

- FastAPI-Backend mit asynchronem SQLAlchemy-Zugriff.
- SQLite als lokale Standarddatenbank.
- Vorbereitung für PostgreSQL ohne grundlegenden Architekturwechsel.
- React-/TypeScript-/Vite-Frontend mit Tailwind CSS.
- Generische rekursive Hierarchieansicht.
- Grundlegender SSE-Chat.
- Bootstrap-Endpunkt als zentraler Einstiegspunkt der Anwendung.
- UI-Schema-Endpunkt und schema-gesteuerte Frontendgrundlagen.
- Modell-Registry und Tool-Registry.
- Modellprovider-Grundlagen, einschließlich Ollama-Vorbereitung.
- Datenbankbasierte Fachkonfiguration mit Revisionen.
- Administrierbare Konfigurationsendpunkte.
- Strukturierte Architektur für Entwicklung, Intranet und Internetbetrieb.
- PowerShell-Skripte zum gemeinsamen Starten und Stoppen von Backend und Frontend.

### Architektur

- `.env` ist auf Bootstrap-, Infrastruktur- und Sicherheitswerte begrenzt.
- Fachkonfiguration wird validiert und versioniert in der Datenbank gespeichert.
- Neue Modelle und Tools werden über Manifeste und Registries eingebunden.
- Dynamische Erkennung führt nicht automatisch zur Freigabe.
- Das Frontend verwendet feste Registries für Komponenten, Aktionen und Icons.
- Unbekannte dynamische Typen werden sicher abgelehnt oder sichtbar als nicht unterstützt dargestellt.

[Unreleased]: https://github.com/Thomas-Heisig/Kernschmied/compare/master...HEAD
[0.1.0]: https://github.com/Thomas-Heisig/Kernschmied/releases
