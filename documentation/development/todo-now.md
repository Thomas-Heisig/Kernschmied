Stand: 2026-08-03

# TODO Now (aktive Aufgaben, priorisiert)

Maximal 20–30 Aufgaben; Ziel: fokussierte Iteration.

1. Alembic: `alembic heads` prüfen; Entwicklungs-DB sichern und ggf. neu erzeugen.  
2. Persistente Hierarchie: idempotentes Seeding für `root` → `workspace` → `project` → `chat`.  
3. Chat-Persistenz: Laufzeit-Conversation erstellen und FK-Probleme beheben.  
4. Frontend: History beim Öffnen laden und SSE+Deduplizierung testen.  
5. Config-API: `GET /api/v1/config` Vertrag erweitern (nur Metadaten, secrets masked).  
6. Settings-Frontend: Provider/Model Abhängigkeiten (model_select) an API anbinden.  
7. Widget: Ein generisches read-only Widget (Lese- und Update-Pfad vorbereiten).  
8. Context Resolver: einfache serverseitige Kontextauflösung implementieren (tenant, user, path, effective_revisions).  
9. Seed-IDs: Seed-Verifikation implementieren (suche via seed_key, erstelle idempotent).  
10. Dokumentation: Links prüfen; `documentation/unknown/` als veraltet kennzeichnen.

(Weitere Aufgaben werden in `documentation/development/backlog.md` einsortiert.)
