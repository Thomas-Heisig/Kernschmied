# Changelog

Alle wesentlichen Änderungen an Kernschmied werden in dieser Datei dokumentiert.

Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/). Das Projekt verwendet während der frühen Entwicklung eine an [Semantic Versioning](https://semver.org/lang/de/) angelehnte Versionierung.

## [Unreleased]

### Hinzugefügt

- Bootstrap-zentrierte Frontendarchitektur wird weiter konsolidiert.
- Schema-gesteuerte Ansichten über einen zentralen `SchemaRenderer` werden erweitert.
- Generische Komponenten- und Action-Registries werden vervollständigt.
- Modell- und Tool-Registries werden mit isolierter Fehlerbehandlung weiter integriert.
- Verträge für Hierarchie, UI-Schema, Modelle, Tools, Chat und Konfiguration werden vereinheitlicht.
- Strukturierte Fehlerantworten mit Request-ID werden weiter ausgebaut.

### Geändert

- Der ausgewählte Knotentyp `user` soll künftig über den zentralen `SchemaRenderer` dargestellt werden.
- Frontend-Einstieg und Providerstruktur wurden auf einen zentralen Anwendungseinstieg ausgerichtet.
- Bootstrap-, Registry- und Schema-Normalisierung werden schrittweise gehärtet.

### Offen

- OpenAPI-Artefakte gegen die tatsächlich laufende FastAPI-Anwendung verifizieren und neu erzeugen.
- Hierarchie-Endpunkt vollständig gegen `HierarchyTreeResponse` prüfen.
- Bootstrap als einzigen festen fachlichen Einstiegspunkt im Frontend durchsetzen.
- Laufzeitvalidierung aller öffentlichen Frontendverträge vervollständigen.
- ChatRequest und SSE-Ereignisse vollständig vereinheitlichen.
- Autorisierung, Auditierung und Betriebsprofile vervollständigen.

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

[Unreleased]: https://github.com/Thomas-Heisig/Kernschmied/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Thomas-Heisig/Kernschmied/releases/tag/v0.1.0
