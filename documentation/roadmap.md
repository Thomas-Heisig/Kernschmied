Stand: 2026-08-15

# Roadmap (Kurzfassung) – Kernschmied

Ziel: In klaren, testbaren Schritten von einem lokalen MVP zu einer produktionsnahen, modularen Intranet‑/KI‑Plattform.

Priorisierte Meilensteine (kurz):

- Meilenstein 1 – Konsolidierung (Kurzfristig, höchste Priorität)
  - Settings: Vollständige Migration auf Config‑v2 mit fachlichem Status je Key,
    kanonischer Runtime-Auflösung und einer gemeinsamen Definitionsquelle
  - Hierarchie: Frontend‑Bearbeitung (Create/Rename/Move/Delete + lokal konsistente Aktualisierung)
  - Repo‑Hygiene: entfernbare Root‑Artefakte verschieben/archivieren
  - Router/Services: modularisieren (configs.py in Services splitten)

- Meilenstein 2 – Persistenz & Verträge
  - Conversation/Message Persistenz + Migrationen
  - Serverseitige Validierung von Provider/Model‑Kombinationen (Registry-ID-Handoff und Default-Recovery umgesetzt)
  - Eindeutige, versionierte API‑Verträge (Bootstrap, Hierarchie, UI‑Schema, Config)

- Meilenstein 3 – Tool‑Pipeline
  - Tool Manifest → Registry → Execution → Audit → Chat‑Fortsetzung (ersten Tool durchgängig anbieten)

- Meilenstein 4 – Qualität & Betrieb
  - Tests: Vitest, React Testing Library, Backend‑Vertragstests
  - CI: GitHub Actions für Lint/Tests/OpenAPI‑Diff/Migrationsprüfung
  - Minimaler Intranet‑Security‑Scope (Auth/Session/Audit)
  - Lokale Start- und Seed-Warnungen bereinigt (abgeschlossen 2026-08-15)
  - Systemarbeitsbereich mit versionierter Betriebsübersicht und ausblendbaren Widget-Panels (abgeschlossen 2026-08-15)
  - Datenbank-Healthcheck über echten asynchronen `SELECT 1`-Probe (abgeschlossen 2026-08-15)
  - Zuverlässiger Windows-Backend-ReLoad mit verwaltetem Prozessbaum, nativer Logumleitung und separatem Live-Logfenster (abgeschlossen 2026-08-15)
  - Hybride Hierarchie-Sidebar mit Schnellzugriffen, Typfiltern, Favoriten, Status-Badges und Fokusmodus (abgeschlossen 2026-08-15)
  - Serverseitige Hierarchieprojektion: DEV-Admin sieht den Gesamtbaum, Benutzer nur eigenen Unterbaum sowie öffentliche, interne oder zugewiesene Knoten (abgeschlossen 2026-08-15)
  - Admin-Benutzerverwaltung, Profil-/Passwort-Selbstservice, dauerhafte Kontolöschung und DEV-Selbstregistrierung mit Gast-/Intern-/Admin-Stufen (abgeschlossen 2026-08-15)
  - Browser-Registrierungsformulare mit lokaler Passwortprüfung, zugänglichen Feldlabels und rollback-sicherem HTTP-422-Policyvertrag gehärtet (abgeschlossen 2026-08-15)
  - Minimaler DEV-Hierarchie-Seed und bereinigter Neustart nur mit Systemcontainern und Administrator (abgeschlossen 2026-08-15)
  - Sichtbare Selbstregistrierung und DEV-Login nach Abmeldung durch normalisierten Bootstrap-Vertrag (abgeschlossen 2026-08-15)
  - Benutzergebundene Invalidierung des Hierarchie-Caches bei Abmeldung, Registrierung und Kontowechsel (abgeschlossen 2026-08-15)
  - Profil- und Präferenz-Self-Service für angemeldete Gastkonten ohne globale Administrationsrechte (abgeschlossen 2026-08-15)
  - Persönlicher Benutzerarbeitsbereich mit kanonischen Profildaten, Self-Service-Aktionen und ausschließlich effektiv sichtbaren Bereichen (abgeschlossen 2026-08-15)
  - Robuste Sitzungsübersicht mit korrekter Session-Identität, UTC-Zeitstempeln und bereinigtem Dialog (abgeschlossen 2026-08-15)
  - Eigene Hierarchieerstellung mit rollenabhängigen, administrierbaren Bereichs-, Projekt- und Chatquoten sowie strikt privater Eigentümerschaft (abgeschlossen 2026-08-15)
  - Mention-/Presence-MVP mit getrennten Benutzeranfragen, hierarchiebegrenztem Autocomplete, Online-Liste, persönlichem Eingang und optionaler zusätzlicher KI-Antwort (abgeschlossen 2026-08-15)
  - Benutzergebundenes Postfach mit Mention-Zustellung, Statussynchronisierung, SMTP-Outbox, Mailpit-Testbetrieb und fehlertoleranten Willkommens-/Testmails (abgeschlossen 2026-08-15)
  - Direkte `@Administrator`-KI-Auto-Antwort mit persistierter Administrator-Attribution ohne gewöhnliche Benutzeranfrage (abgeschlossen 2026-08-15)
  - Trennung des geschützten Administrator-Autoresponders von namentlich erwähnten menschlichen Administratoren mit normaler Mention-/Postfachzustellung (abgeschlossen 2026-08-15)
  - Pylance-strikte Typisierung für Mention-Defaults, Assistant-JSON-Metadaten und Session-Presence-Persistenz (abgeschlossen 2026-08-15)
  - Kollaborationsausbau mit persistenter Nebenchat-Antwortstruktur, Avatar-/KI-Attribution, Versandstatus, optionalem Ton, mehrfarbiger Glocke und verwaltbarem Postfach (abgeschlossen 2026-08-15)
  - Serverseitiger KI-Wahrheits- und Datenschutzrahmen mit minimalem autorisiertem Benutzerkontext sowie persistenter Windows-Zeitzonen-/Präferenzunterstützung (abgeschlossen 2026-08-15)
  - Alembic-Head, idempotenter Seed mit kanonischen Systemcontainern und hierarchiegebundene Chat-History einschließlich Browser-Roundtrip verifiziert (abgeschlossen 2026-08-15)
  - Berechtigungsabhängige Prompt-, Konfigurations- und Werkzeugmenüs für eigene Chats und Unterchats wiederhergestellt (abgeschlossen 2026-08-15)
  - Persistierte Elternchat-Verläufe als begrenzter, nicht-instruktiver Kontext für Unterchats angebunden (abgeschlossen 2026-08-15)
  - Persönliche Benutzerprompts, strikt berechtigungsprojizierte Sidebar-Menüs und Ausgabeaktionen für Kopieren/Markdown-Download umgesetzt (abgeschlossen 2026-08-15)
  - Sicherer GFM-Chatrenderer mit kontrastreicher Lightmode-Ausgabe, einheitlicher
    Live-/Historienansicht und vorbereiteten Bild-, Audio- und Videokomponenten
    umgesetzt (abgeschlossen 2026-08-15)
  - Persönlicher Benutzer-Knoten als Dashboard mit sichtbaren Projekten,
    Recent-Chats, Kontoaktionen, Kontingenten und funktionierenden
    Kalender-/Datei-Widgets ausgebaut (abgeschlossen 2026-08-15)
  - Gemeinsames kontrastreiches Neutral-/Pastelldesign über System, Benutzer,
    Bereich, Projekt und Chat einschließlich einheitlicher Aktionen, Kennzahlen
    und Widget-Abschnitte abgeschlossen (abgeschlossen 2026-08-15)
  - Berechtigungsprojizierte letzte Knoten je Hierarchieebene sowie
    bestätigungspflichtiges Leeren, Einzellöschen und Fortsetzen ab einem
    persistenten Chatstand umgesetzt (abgeschlossen 2026-08-15)

Leitprinzipien (Kurz):

- Architektur vor Schnellfeatures
- Verträge (Backend↔Frontend) versionieren und testen
- keine dynamischen Imports oder eval aus Backenddaten
- keine Secrets in Config‑Antworten
- kleine, überprüfbare Commits und begleitende Tests

Die konkreten, priorisierten Arbeitspakete werden ausschließlich in der
[zentralen TODO-Liste](todo.md) gepflegt. Diese Roadmap enthält bewusst keine
zweite Aufgabenliste.

---

## Neues Leitkonzept: Fachneutraler Kern und Chat‑Zentrierte Interaktion

Das Leitkonzept ist in `documentation/leitkonzept.md` verschoben worden. Es bleibt die verbindliche Architekturgrundlage für weitere Entscheidungen.

Siehe: [Leitkonzept](leitkonzept.md)
