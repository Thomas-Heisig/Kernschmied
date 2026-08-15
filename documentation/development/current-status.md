Stand: 2026-08-15

# Current Status (Kurzfassung)

- FastAPI Backend: startet lokal
- Frontend (Vite): startet lokal
- Alembic: Repository und Entwicklungsdatenbank stehen auf `0024_add_user_hierarchy_quotas`
- Persistente Hierarchie: Backend-CRUD und kanonische Systemcontainer sind aktiv; reguläre Workspace-, Projekt- und Chat-Erstellung ist im Browser verifiziert
- Chat-Persistenz: Create, Read, History, Elternbezüge, FK-Fehlerfälle und dauerhafte Abschlussstatus sind durch Backendtests und einen Browser-Roundtrip verifiziert
- Chat-Verlaufsverwaltung: Berechtigte Eigentümer können den Verlauf leeren,
	einzelne persistierte Nachrichten löschen oder nach einem gewählten Stand
	kürzen; Backend und UI prüfen die effektive `delete`-Berechtigung
- Kontextbezogene Recents: System, Bereich, Projekt und Chat zeigen nur letzte
	Knoten, Projekte, Chats beziehungsweise Unterchats aus dem aktuell sichtbaren
	Hierarchieausschnitt
- Bereich/Projekt: Zusätzlich zu Recents zeigen beide Ebenen ihre vollständigen
	direkten Projekt-/Chat-Sammlungen im gemeinsamen Kartenaufbau des
	Benutzerarbeitsbereichs
- Unterchat-Kontext: Persistierte Benutzer- und Modellergebnisse übergeordneter Chats werden begrenzt und als nicht-instruktive Daten an die Generierung übergeben
- Benutzer-/Ausgabeaktionen: Eigene Benutzerprompts sowie berechtigungsbasierte Sidebar-Menüs sind aktiv; fertige KI-Ausgaben können kopiert, als Markdown gespeichert oder beantwortet werden
- Chatausgabe: Live-Chat und Historie rendern CommonMark/GFM sicher und
	einheitlich; gesendete Nachrichten sind im Lightmode kontrastreich, Roh-HTML
	bleibt gesperrt und Bild-/Audio-/Videoelemente besitzen explizite Renderer
- Chat-Attribution: Live-Chat, Historie und Chat-Widget zeigen den tatsächlichen
	Benutzer-Anzeigenamen oder `KI`; persistierte Benutzer-IDs werden dafür im
	History-Endpunkt serverseitig aufgelöst
- Benutzerknoten: Persönliches Dashboard mit Kontoaktionen, Kennzahlen,
	sichtbaren Bereichen und Projekten, letzten Chats, Kontingenten sowie
	funktionierenden Kalender-/Datei-Anbindungen ist aktiv
- Knoten-Design: System, Benutzer, Bereich, Projekt und Chat verwenden denselben
	responsiven Überblicksbaustein, eine kontrastreiche Neutral-/Salbeipalette und
	einheitliche Aktions-, Kennzahlen- und Widgetmuster
- Benutzeradministration: Bereichs-, Projekt- und Chatkontingente können je
	Benutzer auf Rollenstandard, ein festes Limit oder unbegrenzt gesetzt werden;
	API, Persistenz und Hierarchieerstellung verwenden dieselben effektiven Werte
- Frontend-Verifikation: 46 Vitest-Tests und Produktionsbuild erfolgreich; die
	neuen Chat-Aktionen sind im laufenden Browser ohne destruktiven Aufruf geprüft
- Backend-Verifikation: 149 Pytest-Tests erfolgreich; bekannte Warnungen
	beschränken sich auf AsyncMock- und Windows-Tempfile-Cleanup in Tests

Zu verifizierende Laufzeitrisiken:

- Der verifizierte Chat-History-Browser-Roundtrip muss noch als repository-eigener E2E-Test automatisiert werden.

Die zugehörigen Arbeiten werden ausschließlich in der
[zentralen TODO-Liste](../todo.md) gepflegt.
