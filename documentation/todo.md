Stand: 2026-08-03

# Kernschmied – Development Overview (harmonisierte Kurzfassung)

Dieses Dokument ist als überblicksartiges Arbeitsdokument gedacht. Aktive Aufgaben werden künftig in `documentation/development/todo-now.md` gepflegt; das umfangreiche Backlog findet sich in `documentation/development/backlog.md`.

---

## Kurz: Neuer Dokumentstand

- Das verbindliche Leitkonzept befindet sich in `documentation/leitkonzept.md`.
- Diese Datei enthält die aktuelle Zusammenstellung von Status, Blockern und priorisierten Arbeiten.

Siehe: [Leitkonzept](leitkonzept.md)

---

## Empfehlungen (kurz)

- Relative Links in Dokumenten wurden korrigiert.
- `documentation/unknown/` ist veraltet; neue Dokumente liegen nun in `documentation/` und `documentation/development/`.
- Der Begriff "Bereich" wird im MVP als Anzeige für den technischen Knotentyp `workspace` verwendet.
- Alembic-Head muss dynamisch ermittelt werden; keine dauerhafte Fixierung auf `0008`.
- Seed-IDs wie `chat-1` dürfen nicht als permanente Architekturvertrags-IDs verwendet werden.

---

## Nächste, verbindliche Minimalaufgaben (Kurz)

1. Korrigierte Links und Dokumentstruktur verifizieren.
2. `Bereich` ≙ technischer `workspace` dokumentieren.
3. Alembic-Head dynamisch abfragen (`alembic heads` / `alembic current`) und Migrationstasks anpassen.
4. `documentation/development/todo-now.md` anlegen und max. 20 aktive Tasks aufnehmen.

---

## Wo sind die Details?

- Technische Status- und Blockerlisten: `documentation/development/current-status.md`
- Aktive Aufgaben (now): `documentation/development/todo-now.md`
- Backlog / Architekturideen: `documentation/development/backlog.md`
- Release-Checkliste: `documentation/development/release-checklist.md`
