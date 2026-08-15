Stand: 2026-08-15

# Current Status (Kurzfassung)

- FastAPI Backend: startet lokal
- Frontend (Vite): startet lokal
- Alembic: Repository und Entwicklungsdatenbank stehen auf `0023_add_message_parent`
- Persistente Hierarchie: Backend-CRUD und kanonische Systemcontainer sind aktiv; reguläre Workspace-, Projekt- und Chat-Erstellung ist im Browser verifiziert
- Chat-Persistenz: Create, Read, History, Elternbezüge, FK-Fehlerfälle und dauerhafte Abschlussstatus sind durch Backendtests und einen Browser-Roundtrip verifiziert
- Chat-Verlaufsverwaltung: Berechtigte Eigentümer können den Verlauf leeren,
	einzelne persistierte Nachrichten löschen oder nach einem gewählten Stand
	kürzen; Backend und UI prüfen die effektive `delete`-Berechtigung
- Kontextbezogene Recents: System, Bereich, Projekt und Chat zeigen nur letzte
	Knoten, Projekte, Chats beziehungsweise Unterchats aus dem aktuell sichtbaren
	Hierarchieausschnitt
- Unterchat-Kontext: Persistierte Benutzer- und Modellergebnisse übergeordneter Chats werden begrenzt und als nicht-instruktive Daten an die Generierung übergeben
- Benutzer-/Ausgabeaktionen: Eigene Benutzerprompts sowie berechtigungsbasierte Sidebar-Menüs sind aktiv; fertige KI-Ausgaben können kopiert, als Markdown gespeichert oder beantwortet werden
- Chatausgabe: Live-Chat und Historie rendern CommonMark/GFM sicher und
	einheitlich; gesendete Nachrichten sind im Lightmode kontrastreich, Roh-HTML
	bleibt gesperrt und Bild-/Audio-/Videoelemente besitzen explizite Renderer
- Benutzerknoten: Persönliches Dashboard mit Kontoaktionen, Kennzahlen,
	sichtbaren Bereichen und Projekten, letzten Chats, Kontingenten sowie
	funktionierenden Kalender-/Datei-Anbindungen ist aktiv
- Knoten-Design: System, Benutzer, Bereich, Projekt und Chat verwenden denselben
	responsiven Überblicksbaustein, eine kontrastreiche Neutral-/Salbeipalette und
	einheitliche Aktions-, Kennzahlen- und Widgetmuster
- Frontend-Verifikation: 46 Vitest-Tests und Produktionsbuild erfolgreich; die
	neuen Chat-Aktionen sind im laufenden Browser ohne destruktiven Aufruf geprüft
- Backend-Verifikation: 146 Pytest-Tests erfolgreich; bekannte Warnungen
	beschränken sich auf AsyncMock- und Windows-Tempfile-Cleanup in Tests

Zu verifizierende Laufzeitrisiken:

- Der verifizierte Chat-History-Browser-Roundtrip muss noch als repository-eigener E2E-Test automatisiert werden.

Die zugehörigen Arbeiten werden ausschließlich in der
[zentralen TODO-Liste](../todo.md) gepflegt.
