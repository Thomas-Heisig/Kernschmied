# Changelog

Alle wesentlichen Änderungen an Kernschmied werden in dieser Datei dokumentiert.

Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/). Das Projekt verwendet während der frühen Entwicklung eine an [Semantic Versioning](https://semver.org/lang/de/) angelehnte Versionierung.

## [Unreleased]

### Dokumentation

- Offene Aufgaben aus Entwicklungsstatus, Backlog, Konfigurationsreview und
  Quellcode-Markern in `documentation/todo.md` zusammengeführt; ersetzte
  TODO-Dateien entfernt und Roadmap sowie Status auf die zentrale Liste
  ausgerichtet.

### Hinzugefügt

- Persistente, von Chatnachrichten getrennte `@Benutzer`-Anfragen mit eigenem Statuslebenszyklus, atomarer Speicherung und serverseitig auf den aktiven Hierarchiepfad begrenzter Empfängerauswahl.
- Mention-Autocomplete im Chat, persönlicher Anfrageeingang mit Statusaktionen, Ungelesen-Badge im Header sowie eine Online-Liste im Kontextbereich auf Basis aktiver Sitzungen.
- Persönliche Einstellung für zusätzliche KI-Antworten bei Benutzeranfragen; für Administratoren ist sie standardmäßig aktiv, für andere Rollen optional und standardmäßig deaktiviert.
- Ein automatisch mit jedem Benutzer verbundenes Postfach mit stabiler interner Adresse, rückwirkender Versorgung bestehender Konten und Mentions sowie geschützten Listen-, Lese- und Archivierungsendpunkten.
- SMTP-Zustellung über die Postfach-Outbox mit Mailpit-Entwicklungsprofil, Willkommens- und Mention-Mails, persönlichem Testmail-Endpunkt sowie persistierten Erfolgs- und Fehlerzuständen; SMTP-Fehler rollen Benutzeranlage und interne Nachrichten nicht zurück.
- `@Administrator` erzwingt serverseitig eine direkte KI-Auto-Antwort mit sichtbarer und persistierter Administrator-Attribution, ohne eine gewöhnliche Benutzeranfrage im Administrator-Postfach anzulegen.
- Der Administrator-Autoresponder ist auf das geschützte Systemkonto begrenzt; namentlich erwähnte menschliche Administratoren wie `@Thomas-Heisig` erhalten bei deaktivierter Zusatz-KI eine normale Mention- und Postfachbenachrichtigung ohne Assistentenantwort.
- Rollenabhängige, serverseitig erzwungene Hierarchiequoten: Gäste erhalten standardmäßig einen Bereich, zwei Projekte und fünf Chats, interne Benutzer höhere administrierbare Grenzen und Administratoren unbegrenzte Nutzung.
- Persönliche Erstellen-Aktionen und eine Nutzungsanzeige für eigene Bereiche, Projekte und Chats; neu angelegte Gastinhalte bleiben privat und dem erstellenden Benutzer zugeordnet.
- Serverseitige Hierarchie-Sichtbarkeit für eigene, öffentliche, interne und explizit zugewiesene Knoten mit Schutz direkter Node-ID-Zugriffe.
- Admin-Benutzerverwaltung zum Anlegen, Bearbeiten, Aktivieren/Deaktivieren und Zurücksetzen von Passwörtern.
- Datenzugriffs- und Benutzerzuweisungsfelder im Hierarchie-Knoten-Editor.
- Nutzbarer DEV-Selbstregistrierungsflow mit automatischer Anmeldung und Rücknavigation zum Login.
- Dreistufiges Zugriffsmodell `Gast`, `Intern` und `Administrator` mit administrativer Hochstufung und dauerhaftem Löschen nicht geschützter Konten.
- Eigener Benutzerarbeitsbereich mit Profil-, Einstellungs-, Sitzungs- und Passwort-Self-Service sowie Navigation zu sichtbaren zugeordneten Bereichen.
- Persistierte Sidebar-Sektionen für Favoriten und zuletzt verwendete Hierarchieknoten sowie Typfilter für Chats, Projekte und Bereiche.
- Status- und Ungelesen-Badges, Fokusmodus, „Alle einklappen“ und fokussierte Sidebar-Komponententests.
- Versionierter `GET /api/v1/system/overview`-Vertrag für Betriebsprofil, Konfigurationsrevision, Dienstzustände und Registry-Zähler.
- Vollbreiter Systemarbeitsbereich mit ausblendbaren Widget-Panels für Übersicht, Knotendaten, Systemprompt und Systemwidgets.
- Manuelles Aktualisieren der Systemübersicht sowie Backend- und Frontend-Regressionstests.
- Bootstrap-zentrierte Frontendarchitektur wird weiter konsolidiert.
- Schema-gesteuerte Ansichten über einen zentralen `SchemaRenderer` werden erweitert.
- Generische Komponenten- und Action-Registries werden vervollständigt.
- Modell- und Tool-Registries werden mit isolierter Fehlerbehandlung weiter integriert.
- Verträge für Hierarchie, UI-Schema, Modelle, Tools, Chat und Konfiguration werden vereinheitlicht.
- Strukturierte Fehlerantworten mit Request-ID werden weiter ausgebaut.

### Geändert

- Strikte Pylance-Typgrenzen für Mention-Defaults, Assistant-Metadaten und asynchronen Sitzungszugriff bereinigt; das Session-Testdouble bildet den synchronen `AsyncSession.add()`-Vertrag nun korrekt ab.
- Admin-Benutzeranlage und Selbstregistrierung behandeln Passwort-Policyverletzungen als verständliche HTTP-422-Eingabefehler statt als internen Serverfehler; beide Browserformulare prüfen Mindestlänge und Benutzername vor dem Request und besitzen korrekt zugeordnete Feldlabels.
- Benutzeranfragen können ohne Modellaufruf abgeschlossen werden; der SSE-Stream bestätigt in diesem Fall ausschließlich die persistierte Anfrage und das Frontend zeigt keinen leeren Assistant-Platzhalter an.
- Der Kontextbereich zeigt Benutzeranfragen als Postfacheinträge einschließlich interner Adresse und transparentem E-Mail-Bereitschaftsstatus; Lesen und Archivieren synchronisieren den zugrunde liegenden Mention-Status.
- Das lokale Startskript startet Mailpit optional mit und weist dessen Weboberfläche unter `http://localhost:8025` aus.
- Der DEV-Seed erzeugt nur noch die kanonischen Systemcontainer und den geschützten Administrator; die veralteten Beispiel-Roots `workspace-root`, `project-root` und `chat-root` werden nicht mehr automatisch angelegt.
- Gäste sehen den eigenen Benutzerknoten, öffentliche und explizit zugewiesene Bereiche; interne Benutzer sehen zusätzlich als `internal` markierte Bereiche. Der technische Systembaum und fremde Benutzer bleiben ausschließlich administrativen Sitzungen vorbehalten.
- `CurrentUserResponse` liefert Rollen und Berechtigungen, und Public-/Intern-Bereiche verwenden einheitliche Zugriffspolicy-Metadaten.
- Hierarchieknoten trennen Auswahl und Expand-Steuerung, bieten zugängliche Favoritenaktionen und behalten passende Vorfahren bei aktiven Typfiltern sichtbar.
- Der Systemknoten erkennt `system`, `system_root` und `system-root` und verwendet unabhängig vom UI-Schema den gemeinsamen scrollbaren Workspace.
- Eigene Benutzerknoten verwenden einen fachlichen persönlichen Arbeitsbereich statt technischer Schema-, Prompt- und Rohdefinitionsansichten; Administratoren erhalten bei fremden Benutzerknoten ausschließlich den Einstieg in die Benutzerverwaltung.
- Frontend-Einstieg und Providerstruktur wurden auf einen zentralen Anwendungseinstieg ausgerichtet.
- Bootstrap-, Registry- und Schema-Normalisierung werden schrittweise gehärtet.
- Der Development-Seed vereinigt Metadaten alter Widget-Registry-Duplikate verlustfrei in kanonische Einträge.

### Behoben

- Die Sitzungsverwaltung normalisiert SQLite-Zeitstempel nach UTC, sortiert die aktuelle Sitzung zuerst und kennzeichnet anhand der tatsächlichen Session-ID genau eine Sitzung als aktuell; der Sitzungsdialog zeigt Überschrift und Schließen-Aktion nur einmal.
- Gäste und interne Benutzer können eigene Hierarchien erstellen, ohne dadurch fremde, öffentliche, interne oder lediglich zugewiesene Inhalte verändern zu dürfen; administrative Sidebar-Aktionen erscheinen ausschließlich bei vorhandener Admin-Freigabe.
- Gastkonten können ihre eigenen persönlichen Einstellungen und Profildaten lesen und ändern; `/users/me`-Routen erfordern nur eine aktive Anmeldung und kollidieren nicht mehr mit der administrativen `/{user_id}`-Route.
- `/auth/me` übernimmt kanonischen Benutzernamen, Anzeigenamen und optionale E-Mail aus dem persistierten Benutzerprofil; eine fehlende E-Mail erscheint im Frontend nicht mehr als Text `null`.
- Benutzerbezogene Hierarchien werden beim Abmelden aus dem Frontend-Cache entfernt und nach Registrierung oder Kontowechsel neu geladen; ein zuvor geladener Administratorbaum bleibt für Gastkonten nicht mehr sichtbar.
- Der Frontend-Bootstrap normalisiert Authentifizierungsflags und Endpunkte aus dem serverseitigen `snake_case`-Vertrag; nach dem Abmelden sind DEV-Login und Selbstregistrierung wieder sichtbar.
- Die lokale Entwicklungshierarchie wurde auf einen sauberen Ausgangszustand zurückgesetzt; verwaiste Benutzer-, Inhalts-, Chat- und Nachrichtendaten wurden entfernt.
- Benutzerlisten serialisieren optionale E-Mail-Adressen korrekt; DEV-Registrierungsflags berücksichtigen Enum-basierte Umgebungsprofile.
- Der Admin-Benutzer-PATCH-Endpunkt akzeptiert echte Teilupdates über `UserUpdateRequest`.
- Persistierte Rollen werden beim Session-Auflösen in den Auth-Principal geladen; Gastkonten erhalten minimalen Hierarchie-Lesezugriff statt impliziter Intern-Rechte.
- `start.ps1` hält den Uvicorn-WatchFiles-ReLoader bei Dateiänderungen am Leben, beendet alte Backend-Prozessbäume über eine PID-Datei und begrenzt blockierende Graceful-Shutdowns.
- `start.ps1` führt Anwendungs-, Request-, Uvicorn- und Reloadmeldungen wieder in einem separaten Live-Logfenster zusammen, ohne den Uvicorn-Prozess in eine Pipeline einzuschließen.
- Der Datenbankstatus prüft nun die veröffentlichte Session-Factory mit `SELECT 1`, statt das nicht vorhandene `app.state.db` zu prüfen; das Systemstatus-Widget liest den gemeinsamen verschachtelten Servicevertrag korrekt.
- Chat-Modellauflösung verwendet nun dieselbe `ModelRegistry` wie Bootstrap und Konfigurationsvalidierung.
- Veraltete persistierte Standardmodellwerte werden auf eine registrierte Kernschmied-Modell-ID zurückgesetzt und atomar migriert; Provider-Modellnamen bleiben auf den Ollama-Adapter begrenzt.
- Deprecated Widget-Einträge erzeugen keine Resolver-Mehrdeutigkeiten mehr.
- Der Kalender-Client vermeidet den unnötigen Redirect der Listenroute.
- Das Startskript stellt normale Uvicorn- und Vite-Ausgaben nicht mehr als PowerShell-`NativeCommandError` dar.
- Die synchrone Datenbankbereinigung importiert beim Interpreter-Shutdown keine bereits deaktivierten Module mehr.

## [0.1.0] - 2026-07-26

### Hinzugefügt

- FastAPI-Backend mit asynchronem SQLAlchemy-Zugriff.
- SQLite als lokale Standarddatenbank.
- Vorbereitung für PostgreSQL ohne grundlegenden Architekturwechsel.
- React-/TypeScript-/Vite-Frontend mit Tailwind CSS.
- Generische rekursive Hierarchieansicht.
- Grundlegender SSE-Chat.
- Bootstrap-Endpunkt als zentraler Einstiegspunkt der Anwendung.
- UI-Schema-Endpunkt und schema-gesteuerte Frontendgrundlagen.
- Modell-Registry und Tool-Registry.
- Modellprovider-Grundlagen, einschließlich Ollama-Vorbereitung.
- Datenbankbasierte Fachkonfiguration mit Revisionen.
- Administrierbare Konfigurationsendpunkte.
- Strukturierte Architektur für Entwicklung, Intranet und Internetbetrieb.
- PowerShell-Skripte zum gemeinsamen Starten und Stoppen von Backend und Frontend.

### Architektur

- `.env` ist auf Bootstrap-, Infrastruktur- und Sicherheitswerte begrenzt.
- Fachkonfiguration wird validiert und versioniert in der Datenbank gespeichert.
- Neue Modelle und Tools werden über Manifeste und Registries eingebunden.
- Dynamische Erkennung führt nicht automatisch zur Freigabe.
- Das Frontend verwendet feste Registries für Komponenten, Aktionen und Icons.
- Unbekannte dynamische Typen werden sicher abgelehnt oder sichtbar als nicht unterstützt dargestellt.

[Unreleased]: https://github.com/Thomas-Heisig/Kernschmied/compare/master...HEAD
[0.1.0]: https://github.com/Thomas-Heisig/Kernschmied/releases
