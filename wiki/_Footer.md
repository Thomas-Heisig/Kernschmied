---
## Navigation

← [[Home]] · [[Getting-Started]] · [[Architecture]] · [[Project-Principles]]
---

## Quick Links

📦 **Repository**  
<https://github.com/Thomas-Heisig/Kernschmied>

🐞 **Issue Tracker**  
<https://github.com/Thomas-Heisig/Kernschmied/issues>

📖 **Wiki Home**  
[[Home]]

---

## Documentation

This wiki is maintained together with the source code.

If you discover outdated or incorrect documentation, please create an issue or submit a pull request.

Documentation is considered part of the project and should evolve together with the implementation.

---

## Project Information

**Project:** Kernschmied

**Architecture:** Schema-Driven AI Platform

**Backend:** Python · FastAPI · Pydantic v2 · SQLAlchemy Async

**Frontend:** React · TypeScript · Vite · Tailwind CSS

**Default Database:** SQLite

**Future Database:** PostgreSQL

---

## Neuerungen

- Frontend: Interaktiver Kalender im Footer (Auswahl speicherbar, Copy-to-clipboard, Tastaturnavigation).
- Backend: Neuer API-Endpunkt `POST /api/v1/calendar/selection` zur Speicherung von Kalenderauswahlen (integration point).
- DB: Tabelle `calendar_selections` vorbereitet (ORM-Modell und SQL-Migration in `backend/migrations/001_create_calendar_selections.sql`).

Wenn du die Kalender-Integration aktivieren möchtest, implementiere die Persistenzlogik auf Serverseite oder nutze das bereitgestellte Modell/Migration.

---

## License

See the repository's **LICENSE** file for licensing information.

---

© 2026 Thomas Heisig · Kernschmied Project
