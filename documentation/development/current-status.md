Stand: 2026-08-03

# Current Status (Kurzfassung)

- FastAPI Backend: startet lokal
- Frontend (Vite): startet lokal
- Alembic: Migrationen bis `0008` vorhanden für frische DBs; Entwicklungs-DB zeigt abweichende Revisionen und muss geprüft werden
- Persistente Hierarchie: Backend-CRUD vorhanden; Laufzeitintegration (Seeding + Chat-FK) teilweise blockiert
- Chat-Persistenz: Modelle und Repository vorhanden; Laufzeitpfad durch fehlenden persistenten Hierarchieknoten teilweise gestört

Bekannte Laufzeitfehler:

- Entwicklungsdatenbank mit Revision `0009_merge_branches` (nicht im Repo-Head)
- FK-Fehler beim Conversation-Insert wegen fehlendem Hierarchieknoten

Zu tun (Kurz):

- Alembic-Head dynamisch ermitteln und Entwicklungs-DB sichern
- Persistente Hierarchie seeden (idempotent)
- Chat-Repository an persistenten Hierarchiepfad anbinden
- SSE + History Deduplizierung prüfen
