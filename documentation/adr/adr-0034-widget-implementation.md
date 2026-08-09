# ADR-0034: Widget Implementation Details

- **Status:** Accepted
- **Date:** 2026-08-09
- **Decision Makers:** Kernschmied Architecture & Implementation Team

---

# Context

ADR-0011 defines the generic widget architecture and high-level principles. This ADR records the concrete, implementable decisions required to persist widget definitions, expose registry APIs, and provide a minimal frontend integration (non-invasive badges) for the first rollout.

# Problem

The architecture prescribes a registry and runtime assignments but does not prescribe:

- the persistent schema for registry entries,
- how widget instances are stored on hierarchy nodes,
- the API surface for managing registry entries and assignments,
- a minimal frontend integration pattern for visualizing assigned widgets without altering the chat UI.

# Decision

We adopt the following concrete implementation choices to satisfy ADR-0011 requirements while keeping the solution configurable and non-invasive.

## Persistence

- Table: `widget_registry`
  - `id` (string, 36) PK
  - `name` (string, 100) — technical widget identifier
  - `type` (string, 100, nullable) — optional kind/category
  - `metadata` (JSON, not null) — capability metadata, provider, UI hints
  - `default_config` (JSON, not null) — authoring-friendly defaults (e.g. `{ "default_widgets": [...] }`)
  - `created_at`, `updated_at` (tz-aware datetimes)

- Hierarchy nodes (existing `hierarchy_nodes` table) gain a JSON column `widget_assignments` (not null, default `[]`) that stores a list of widget instance objects. Each widget instance is a JSON object with at least a `name` key referencing a registry `name`, plus optional `config`, `icon`, `title`, `visible`, etc.

## API

- `GET /api/v1/widgets/` — list registry entries
- `POST /api/v1/widgets/` — create a registry entry
- `GET /api/v1/widgets/nodes/{node_id}/effective` — resolve effective widget instances for a node (see resolution rules)
- `POST /api/v1/widgets/nodes/{node_id}/assignments` — set widget assignments on a node (requires auth)

These initial endpoints are intentionally minimal; they are intended for administrative workflows and programmatic integration.

## Resolution semantics (first implementation)

Effective widget instances are resolved as follows (deterministic, simple):

1. Build ancestor chain from root -> node.
2. For each ancestor (root first):
   - If a `widget_registry` entry exists with `name == node.type`, include `default_config.default_widgets` (if present and a list).
   - Merge the node's `widget_assignments` (list) into the effective list. If an assignment has the same `name` as an earlier entry, it replaces it (override).
3. The resulting ordered list is returned to the client.

This behavior implements inheritance with extension and override without complex rule syntax. Future work may introduce explicit `extend`/`override` flags in registry entries or per-assignment properties.

## Frontend integration (non-invasive)

- Frontend must render widgets as optional, compact UI affordances by default (mini‑icons/badges). Widgets must not disrupt primary chat UI.
- A minimal `WidgetBadges` component will request `GET /api/v1/widgets/nodes/{node_id}/effective` and render small icons with tooltips. Full widget panels and editors are out of scope for the initial rollout and should be toggled by user action.

## Security & Authorization

- Only authenticated users may modify `widget_assignments`. Authorization checks must still be implemented to restrict `system` widgets or other sensitive widget types to administrators.

## Migration

- Add Alembic migration to create `widget_registry` table and `widget_assignments` column on `hierarchy_nodes` with default `[]`.

# Consequences

- Allows runtime configuration of widgets without frontend code changes for each new widget type.
- Simple resolution rules make behavior predictable and easy to test.
- Further refinements (widget layout engine, permissions per-widget, provider plugins) may require additional ADRs.

# Related ADRs

- ADR-0011: Generic Widget Architecture
- ADR-0003: Registry-Based Extension Architecture
- ADR-0014: Runtime Configuration Architecture

---

# Default Widget Catalog (initial seed)

The following catalog lists recommended standard widgets per hierarchy level. These entries are intended as a starting point for the registry and as examples for authoring `default_config` payloads.

## System (dev/admin)

- `system_health` — global system status
- `audit_log` — recent actions
- `registry_editor` — registry management

## User (personal)

- `favorites` — quick access
- `recent_chats` — recently used chats
- `personal_calendar` — personal events

## Area / Workspace

- `area_members` — members list
- `area_calendar` — shared events
- `resource_overview` — key resources

## Project

- `project_timeline` — milestones
- `task_list` — tasks
- `linked_resources` — linked documents

## Chat

- `chat_history` — core chat view (rendered centrally)
- `participants` — current participants
- `attachments` — files
- `smart_actions` — context actions

## Subchat

- `subchat_participants`
- `subchat_attachments`

## Example registry entry (JSON)

{
  "name": "project_timeline",
  "type": "timeline",
  "metadata": {
    "capabilities": ["read_only", "timeline"],
    "icon": "timeline",
    "description": "Project milestones and progress"
  },
  "default_config": {
    "default_widgets": [
      { "name": "project_timeline", "title": "Timeline", "icon": "timeline" }
    ]
  }
}

## Example node assignment (JSON stored in `hierarchy_nodes.widget_assignments`)

[
  { "name": "project_timeline", "config": { "range": "90d" }, "icon": "timeline" },
  { "name": "task_list", "config": { "filter": "open" }, "icon": "checklist" }
]

These seeds should be created as part of an initial data migration or via an admin UI.

---

# ADR-0034: Review & offene Punkte

Die ADR wurde überprüft und ist grundsätzlich solide. Im Folgenden sind ergänzende Punkte, offene Fragen und konkrete Vorschläge aufgeführt, die in der ADR aufgenommen wurden, damit die Implementierung komplett und repo‑konform wird. Offene Punkte sind mit "🔴 Noch nicht implementiert / nicht spezifiziert" markiert.

## ✅ Bereits in ADR definiert

| Bereich | Status |
|--------:|:------:|
| Persistenz: `widget_registry` Tabelle | ✅ Definiert |
| Persistenz: `widget_assignments` JSON-Spalte in `hierarchy_nodes` | ✅ Definiert |
| API: `GET /api/v1/widgets/` – Registry-Liste | ✅ Definiert |
| API: `POST /api/v1/widgets/` – Registry-Eintrag anlegen | ✅ Definiert |
| API: `GET /api/v1/widgets/nodes/{node_id}/effective` – effektive Widgets auflösen | ✅ Definiert |
| API: `POST /api/v1/widgets/nodes/{node_id}/assignments` – Zuweisungen setzen | ✅ Definiert |
| Auflösungslogik: Vererbung von Root → Node mit Override | ✅ Definiert |
| Frontend: minimale, nicht-invasive Badges | ✅ Definiert |
| Sicherheit: Authentifizierung für Änderungen | ✅ Definiert |
| Migration: Alembic für Tabelle + Spalte | ✅ Definiert |
| Standard-Widget-Katalog (initial) | ✅ Definiert |

## 🔴 Noch nicht implementiert / nicht spezifiziert

Nachfolgend die offenen Themen mit kurzen Vorschlägen zur Ergänzung der ADR und zur Implementierung.

1) Widget‑Layout & Positionierung (🔴)
- Offenes Thema: Regionen (`header`, `sidebar`, `footer`), Grid vs. Stack, responsive Verhalten.
- Vorschlag: `widget_assignments` um `layout`-Feld erweitern (Beispiel unten).

2) Widget‑Konfigurations‑UI (Frontend) (🔴)
- Offenes Thema: Editor, Drag&Drop, schema‑gesteuerte Formulare.
- Vorschlag: Admin‑UI mit dynamischen Formularen basierend auf `config_schema` im Registry‑Eintrag.

3) Feingranulare Widget‑Berechtigungen (🔴)
- Offenes Thema: Rollen, Knotentyp‑Filter, effektive Filterung.
- Vorschlag: Registry‑Feld `required_permissions`, Filterung im `effective`‑Resolver anhand `request.state.user.permissions`.

4) Widget‑Datenquellen & Data Fetching (🔴)
- Offenes Thema: zentrale DataProvider, Caching, Lade-/Fehlerzustände.
- Vorschlag: `data_source` im Registry, `WidgetDataService` im Frontend mit `useWidgetData` Hook.

5) Interaktionsmuster (read-only vs. interaktiv) (🔴)
- Offenes Thema: Trigger / strukturierte Editoren / Navigation.
- Vorschlag: Registry‑Feld `interaction_mode: "read_only" | "trigger" | "structured_edit"`.

6) Caching & Performance (🔴)
- Offenes Thema: Cache‑Key, Invalidation, TTL.
- Vorschlag: Cache mit Schlüsseln `user_id|node_id|registry_rev|assign_rev`, TTL 60s oder SSE‑Invalidate.

7) Versionierung & Migration (🔴)
- Offenes Thema: Registry‑Version, Assignment‑Compatibility.
- Vorschlag: `version` im Registry, `target_version` in Assignments, Migrationspfad/Upgrade‑Hilfen.

8) Drittanbieter‑Erweiterung / Plugin‑Modell (🔴)
- Offenes Thema: Laufzeitkomponenten, Sicherheitsmodell.
- Vorschlag: Manifeste in Registry, dynamisches Laden nur vorgeladener Komponenten; kein Raw‑Code aus DB.

9) Badges → Vollansicht UX (🔴)
- Offenes Thema: Flyout / Sidepanel / Modal Verhalten.
- Vorschlag: Klick auf Badge öffnet Flyout; optional Vollbild‑Ansicht.

10) Internationalisierung (i18n) (🔴)
- Offenes Thema: Mehrsprachige Titel/Beschreibungen.
- Vorschlag: `title_i18n` Objekt im Registry; Frontend wählt `navigator.language` oder Nutzer‑Präferenz.

11) Analytics & Telemetrie (🔴)
- Offenes Thema: Nutzung, Öffnungen, Aktionen.
- Vorschlag: Events `widget.opened`, `widget.action_triggered`, `widget.closed` in bestehendes Telemetrie‑Backend.

12) Vorschau / Canary / Testing (🔴)
- Offenes Thema: Preview und staged rollouts.
- Vorschlag: `status: "draft" | "active" | "deprecated"` im Registry; `GET /api/v1/widgets/preview` Endpoint.

## Beispiel‑Erweiterung für `widget_assignments` (Layout + Version + Permissions)

```json
{
  "name": "project_timeline",
  "config": { "range": "90d" },
  "layout": { "region": "sidebar", "order": 2, "width": "full" },
  "target_version": "1.0",
  "visible_to": ["role:member", "role:admin"]
}
```

## Priorisierung (kurz)
- 1️⃣ Layout & Positionierung (Mittel)
- 2️⃣ Konfigurations‑UI (Hoch)
- 3️⃣ Berechtigungen (Mittel)
- 4️⃣ DataFetching & Caching (Mittel)
- 5️⃣ Interaktions‑Muster (Mittel)
- restliche Punkte: mittel → gering

## Empfehlung für Umsetzungsschritte
1. Ergänze ADR‑Text (done).  
2. Migration für `widget_registry` + `widget_assignments` (done).  
3. Minimal API & Frontend Badges (done).  
4. Implementiere `required_permissions` im Registry + Filter im Resolver (Sprint‑Task).  
5. Implementiere Layout‑Feld + Frontend Flyout (Sprint‑Task).  
6. Implementiere Admin‑UI (Registry Editor) inkl. Preview (Backlog‑Epic).

---

Diese Ergänzungen wurden in `ADR-0034` aufgenommen, damit die Entscheidungsschrift vollständig und unmittelbar umsetzbar ist. Wenn du möchtest, übernehme ich die Implementierung der priorisierten Punkte (1 → Layout, 2 → Konfig‑UI, 3 → Berechtigungen). Schreibe kurz, welche Priorität du möchtest.
