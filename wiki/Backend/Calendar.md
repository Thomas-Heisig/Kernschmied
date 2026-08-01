# Kalender (Calendar) API

Diese Seite dokumentiert die Calendar-API des Backends und erklärt die wichtigsten Endpunkte, Datentypen und Beispielaufrufe sowie die Nutzung des TypeScript-Clients im Frontend.

## Übersicht

Die Calendar-API bietet CRUD-Funktionalität für Kalender und deren Events sowie eine kleine Integration für Datumsauswahl-Persistenz. Die API ist unter dem Prefix `/api/v1` registriert. Der relevante Router ist unter `/api/v1/calendars` verfügbar.

Auth: Die Endpunkte erwarten einen authentifizierten Benutzer. In der Entwicklung liefert die `AuthenticationContextMiddleware` einen Development-Fallback-User.

## Hauptendpunkte

- `GET /api/v1/calendars` — listet die Kalender des angemeldeten Benutzers (Response: `CalendarOut[]`).
- `POST /api/v1/calendars` — legt einen neuen Kalender an (Body: `CalendarCreate`, Response: `CalendarOut`).
- `GET /api/v1/calendars/{calendar_id}` — liefert Details zu einem Kalender.
- `PATCH /api/v1/calendars/{calendar_id}` — aktualisiert einen Kalender.
- `DELETE /api/v1/calendars/{calendar_id}` — löscht einen Kalender.

- `GET /api/v1/calendars/{calendar_id}/events` — listet Events (optional mit `time_min` / `time_max`).
- `POST /api/v1/calendars/{calendar_id}/events` — legt ein Event an (Body: `EventCreate`).
- `GET /api/v1/calendars/{calendar_id}/events/{event_id}` — Details zu einem Event.
- `PATCH /api/v1/calendars/{calendar_id}/events/{event_id}` — Event aktualisieren.
- `DELETE /api/v1/calendars/{calendar_id}/events/{event_id}` — Event löschen.

## Datentypen (Kurz)

- `CalendarCreate`: { name, color?, description? }
- `CalendarOut`: { id, name, color?, description?, owner_id, created_at, updated_at }
- `EventCreate`: { title, description?, start, end, all_day? }
- `EventOut`: { id, calendar_id, title, description?, start, end, all_day, created_at, updated_at }

Die genauen JSON-Formate sind im OpenAPI-Schema (`/openapi.json`) enthalten.

## Beispiele

Curl: Kalender anlegen

```bash
curl -X POST -H "Content-Type: application/json" -d '{"name":"Meine Termine"}' \
  http://localhost:8000/api/v1/calendars
```

Event anlegen

```bash
curl -X POST -H "Content-Type: application/json" -d '{"title":"Meeting","start":"2026-08-01T10:00:00Z","end":"2026-08-01T11:00:00Z"}' \
  http://localhost:8000/api/v1/calendars/<CAL_ID>/events
```

## TypeScript-Client (Frontend)

Im Frontend liegt ein generierter TypeScript-Client unter `frontend/src/api/calendarClient.ts` und die zugehörigen Typen unter `frontend/src/types/api.generated.ts`.

Beispielnutzung:

```ts
import { calendarClient } from "../api/calendarClient";

async function demo() {
  const calendars = await calendarClient.listCalendars();
  const cal = await calendarClient.createCalendar({ name: "Team" });
  const ev = await calendarClient.createEvent(cal.id, {
    title: "Standup",
    start: new Date().toISOString(),
    end: new Date(Date.now() + 3600000).toISOString(),
  });
  console.log(calendars, cal, ev);
}
```

Der Client verwendet `fetch` und erwartet den Backend-Prefix `/api/v1` (kann bei Bedarf konfiguriert werden).

## Hinweise zur Entwicklung

- Tests: Es gibt Unit- und Integrationstests unter `backend/tests/` die die CRUD-Flows abdecken.
- Migrationen: Alembic-Migrationen sind unter `backend/migrations/` gespeichert. In der Dev-Umgebung kann `alembic upgrade head` verwendet werden. Für Produktionsdeploys empfiehlt sich, Migrationen vor dem Rollout geplant auszuführen.
- Authentifizierung: Die `AuthenticationContextMiddleware` setzt `request.state.user`; in produktiven Umgebungen sollte ein echter Identity-Provider die `authenticated_principal` setzen.

Wenn du möchtest, erweitere ich die Wiki-Seite um ein Architekturdiagramm oder detaillierte Feldbeschreibungen pro Typ.
