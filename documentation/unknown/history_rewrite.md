# Wichtige Mitteilung: Git-History wurde bereinigt

Datum: 2026-08-01

Kurzfassung

- Die Git-Historie des Repositories wurde bereinigt, um lokale SQLite-DB-Dateien
  (`backend/data/chat.db`, `backend/data/kernschmied.db`) aus der Historie zu entfernen.
- Diese Bereinigung wurde lokal durchgeführt und per Force-Push nach `origin/master`
  übertragen. Das ist eine destruktive Änderung der Remote-History.

Warum

- Die DB-Dateien gehören nicht ins Repository (sensitiv, lokal) und wurden
  versehentlich historisch aufgenommen. Sie sind jetzt aus der Commit-Historie
  entfernt.

Was du jetzt tun musst (wichtig)

1. Falls du lokale Änderungen oder nicht gepushte Branches hast: sichere sie (z. B. `git format-patch` oder temporäres Backup).
2. Aktualisiere deinen lokalen Haupt-Branch wie folgt (empfohlen):

```bash
git fetch origin
git checkout master
git reset --hard origin/master
git clean -fdx
git remote prune origin
```

1. Falls du lokale Feature-Branches hattest, die auf der alten History basieren,
   kannst du sie neu erstellen oder interaktiv auf `origin/master` rebasen.
   Falls das zu kompliziert ist, ist ein kompletter Neu-Klon sicher:

```bash
cd ..
git clone https://github.com/Thomas-Heisig/Kernschmied.git
```

1. Prüfe lokale Datei- und DB-Reste (z. B. `backend/data/`) und entferne sensible
   Dateien, falls vorhanden.

Hinweis

- Diese Operation überschreibt die Remote-History. Wenn du in den letzten Tagen
  an Branches gearbeitet hast, die nicht gepusht wurden, sichere sie vorher.
- Falls du Unterstützung beim Rebasen oder Wiederherstellen brauchst, antworte
  hier oder erstelle ein Ticket/PR; ich helfe beim sicheren Vorgehen.

Kontakt

- Verantwortlicher: Repository-Owner / Team
