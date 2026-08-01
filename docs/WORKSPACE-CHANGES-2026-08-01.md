Übersicht der Workspace-Änderungen (2026-08-01)

Kurzfassung:
- Backend: Kalender- und Event-Modelle, CRUD-APIs, Owner-Bindung und Auth-Integration hinzugefügt.
- Alembic: Async-SQLite URL-Konvertierung in `env.py` und Revision `0002_create_calendars_events` erstellt und angewendet.
- Storage: SQLAlchemy-Modelle für Calendars, Events und Selections; Index-Duplizate behandelt.
- Tests: Unit- und Integrationstests für Kalender/Events (pytest + TestClient) hinzugefügt und lokal ausgeführt.
- Frontend: Kleiner, typisierter Fetch-Client `frontend/src/api/calendarClient.ts` eingefügt und Footer an API angebunden.
- OpenAPI: Generierte TypeScript-Typen aus `docs/openapi-formatted.json` nach `frontend/src/api/openapi-types.ts` erstellt.
- Codegen: Versuch, vollständigen `typescript-fetch` Client mit `openapi-generator-cli` auszuführen; Umgebung benötigt Java (Blocker), daher JS-Only Typen generiert.

Wichtige Dateien / Orte:
- Backend API: `backend/app/api/v1/` (Calendars & Events)
- Migrations: `backend/migrations/` (Alembic `env.py` + revisions)
- Frontend Types: `frontend/src/api/openapi-types.ts`
- Frontend Client: `frontend/src/api/calendarClient.ts`

Hinweise:
- Java ist im aktuellen Environment nicht installiert; für ein vollständiges OpenAPI-Client-Generator-Lauf (`openapi-generator-cli`) wird Java benötigt.
- Tests und ein Produktions-Build (`npm --prefix frontend run build`) liefen lokal erfolgreich nach den Änderungen.

Wenn du möchtest, generiere ich jetzt einen JS-only fetch-Wrapper basierend auf den erzeugten Typen oder wir installieren Java und erzeugen den vollständigen Client mit `openapi-generator-cli`.
