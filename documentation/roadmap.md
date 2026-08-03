Stand: 2026-08-03

# Roadmap (Kurzfassung) – Kernschmied

Ziel: In klaren, testbaren Schritten von einem lokalen MVP zu einer produktionsnahen, modularen Intranet‑/KI‑Plattform.

Priorisierte Meilensteine (kurz):

- Meilenstein 1 – Konsolidierung (Kurzfristig, höchste Priorität)
  - Settings: Vollständige Migration auf Config‑v2 (Frontend & Backend)
  - Hierarchie: Frontend‑Bearbeitung (Create/Rename/Move/Delete + lokal konsistente Aktualisierung)
  - Repo‑Hygiene: entfernbare Root‑Artefakte verschieben/archivieren
  - Router/Services: modularisieren (configs.py in Services splitten)

- Meilenstein 2 – Persistenz & Verträge
  - Conversation/Message Persistenz + Migrationen
  - Serverseitige Validierung von Provider/Model‑Kombinationen
  - Eindeutige, versionierte API‑Verträge (Bootstrap, Hierarchie, UI‑Schema, Config)

- Meilenstein 3 – Tool‑Pipeline
  - Tool Manifest → Registry → Execution → Audit → Chat‑Fortsetzung (ersten Tool durchgängig anbieten)

- Meilenstein 4 – Qualität & Betrieb
  - Tests: Vitest, React Testing Library, Backend‑Vertragstests
  - CI: GitHub Actions für Lint/Tests/OpenAPI‑Diff/Migrationsprüfung
  - Minimaler Intranet‑Security‑Scope (Auth/Session/Audit)

Leitprinzipien (Kurz):

- Architektur vor Schnellfeatures
- Verträge (Backend↔Frontend) versionieren und testen
- keine dynamischen Imports oder eval aus Backenddaten
- keine Secrets in Config‑Antworten
- kleine, überprüfbare Commits und begleitende Tests

Nächste Schritte (konkret):

1. Sofort: `documentation/todo.md` anlegen/aktualisieren mit priorisierten Tasks und Blockern.  
2. Kurzfristig: Settings‑API erweitern (Definitionsmetadaten) und `SettingsField`‑Vertrag finalisieren.  
3. Kurzfristig: Frontend‑Hierarchie: Kebab‑Kontextmenu + Modal‑Flows an Mutationsendpunkte binden.  
4. Kurzfristig: Chat‑Persistenz‑Datenmodell (Conversations/Messages), Migration und API‑Endpunkte definieren.  

---

## Neues Leitkonzept: Fachneutraler Kern und Chat‑Zentrierte Interaktion

Das Leitkonzept ist in `documentation/leitkonzept.md` verschoben worden. Es bleibt die verbindliche Architekturgrundlage für weitere Entscheidungen.

Siehe: [Leitkonzept](leitkonzept.md)
