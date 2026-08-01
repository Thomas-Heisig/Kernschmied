# TODO (Priorisiert) – Kernschmied

Stand: 2026-08-01

Diese Datei listet sofort umsetzbare Arbeitspakete in priorisierter Reihenfolge. Ziel ist, Blocker für einen belastbaren lokalen MVP zu beseitigen.

Top‑Priorität (Blocker → zuerst bearbeiten)

- Settings‑Migration (Backend + Frontend)
  - Backend: `GET /api/v1/config` liefert vollständige, nicht‑sensitive Definitionsmetadaten (ConfigListResponse).
  - Frontend: `SettingsField` erhält `ConfigEntry` und rendert ausschließlich über `entry.ui.component`.
  - Tests: Backend‑Vertragstest für Config‑API; Frontend Story/Unit für `SettingsField`.

- Hierarchie‑Bearbeitung
  - Kontextmenü (Kebab) pro Knoten: Aktionen aus Action‑Registry anzeigen.
  - Modal‑Flows: Create / Rename / Edit / Delete mit serverseitiger Validierung und lokalem Baum‑Patch.
  - Tests: Mutationsintegrationstest, lokaler Baum‑Update‑Unit Test.

- Chat‑Persistenz (Basis)
  - DB‑Modelle: Conversation, Message (minimal), Alembic‑Migration vorbereiten.
  - API: Create/Read/List Conversations, Append Message, Load Messages (paginiert).
  - Frontend: Chatliste + Laden vorhandener Konversationen.

High‑Priority (Kurzfristig)

- Repo‑Hygiene
  - Root‑Artefakte prüfen und in `docs/archive/` oder `scripts/patches/` verschieben.
  - `LICENSE` prüfen (Konsistenz mit gewählter OS‑Lizenz).

- Modularisierung Backend
  - `backend/app/api/v1/configs.py` schrittweise in Services splitten (`services/config_*`).

- Provider/Model Validation
  - Serverseitige Prüfungen für Provider/Model (Fehlercodes: `MODEL_NOT_REGISTERED`, `MODEL_PROVIDER_MISMATCH`, ...).

Medium (Mittelfristig)

- Tool‑Ende‑zu‑Ende (ein erstes Tool: Calculator)
- SchemaRenderer: Komponentenkatalog & Action‑Registry abschließen
- Tests: Vitest + RTL im Frontend initial einrichten

Low (Planung / später)

- Intranet‑Authentifizierung (Sessions, Rollen)
- CI: GitHub Actions für Lint/Tests/Migrations/OpenAPI‑Diff
- Skalierung & PostgreSQL Integration

Arbeitsweise und Regeln

- Kleine Commits, zu jedem Feature Begleittests.
- Änderungen an API‑Verträgen immer mit OpenAPI‑Diff und Testfall.
- Keine Geheimnisse in Config‑Antworten.

Nächste Aktion (von mir):

1. Ich kann sofort mit dem Frontend‑Settings‑Vertrag starten: `contracts/config.ts` und `SettingsField.tsx` prüfen und ein minimal typisiertes Interface anlegen — möchtest du, dass ich das jetzt implementiere?
