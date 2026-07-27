# Zu Kernschmied beitragen

Vielen Dank für dein Interesse an Kernschmied.

Kernschmied ist eine modular aufgebaute, schema-gesteuerte Chat- und Assistenzplattform mit FastAPI im Backend und React/TypeScript im Frontend. Beiträge sollen die bestehenden Architekturgrenzen erhalten und Backend sowie Frontend gemeinsam lauffähig halten.

## Grundregeln

Beiträge müssen insbesondere folgende Prinzipien beachten:

- Dynamische Fachlogik, aber stabile und versionierte Verträge.
- Keine automatische Freigabe neu erkannter Modelle, Tools, Komponenten oder Aktionen.
- Jede Benutzeraktion wird serverseitig autorisiert.
- `.env` enthält ausschließlich Bootstrap-, Infrastruktur- und Sicherheitswerte.
- Fachliche Einstellungen werden validiert und versioniert in der Datenbank gespeichert.
- Das Frontend verwendet nur bekannte Komponenten aus einer festen Komponenten-Registry.
- Das Frontend verwendet nur bekannte Aktionen aus einer festen Action-Registry.
- Unbekannte Schema-, Komponenten- und Aktionstypen werden sicher abgelehnt oder sichtbar als nicht unterstützt dargestellt.
- Kein `eval()` und kein Laden beliebigen Python-Codes aus unkontrollierten Pfaden.
- Secrets dürfen weder im Quellcode noch in Fachkonfiguration, Logs, Tests oder Beispieldaten erscheinen.
- Neue Funktionen benötigen passende Tests und Dokumentation.

## Technische Voraussetzungen

- Python 3.12
- Node.js in einer mit dem Frontend kompatiblen LTS-Version
- npm
- Windows PowerShell für die vorhandenen Startskripte
- SQLite für die lokale Standardkonfiguration

PostgreSQL soll später ohne grundlegenden Architekturwechsel unterstützt werden. Neue Datenbanklogik muss deshalb möglichst datenbankneutral implementiert werden.

## Entwicklungsumgebung einrichten

Repository klonen:

```powershell
git clone https://github.com/Thomas-Heisig/Kernschmied.git
cd Kernschmied
```

Umgebungsdatei anlegen:

```powershell
Copy-Item .env.example .env
```

Backend vorbereiten:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ..
```

Frontend vorbereiten:

```powershell
cd frontend
npm install
cd ..
```

Gesamtsystem starten:

```powershell
.\start.ps1
```

## Vor einer Änderung

1. Prüfe bestehende Issues und Pull Requests.
2. Erstelle bei größeren Änderungen zunächst ein Issue.
3. Beschreibe bei Vertragsänderungen ausdrücklich:
   - betroffene API- oder Schema-Version,
   - Migrationsweg,
   - Rückwärtskompatibilität,
   - erforderliche Backend- und Frontend-Anpassungen.
4. Vermeide umfangreiche Refactorings zusammen mit fachlichen Änderungen, sofern diese nicht untrennbar verbunden sind.

## Branches und Commits

Verwende nach Möglichkeit kurze, aussagekräftige Branchnamen:

```text
feature/bootstrap-store
fix/hierarchy-openapi
refactor/model-registry
 docs/sse-contract
```

Empfohlene Commit-Präfixe:

```text
feat: neue Funktion
fix: Fehlerbehebung
refactor: interne Umstrukturierung
test: Tests ergänzen
docs: Dokumentation ändern
chore: Wartungsarbeit
security: Sicherheitsverbesserung
```

Beispiele:

```text
fix: correct hierarchy response model
feat: add bootstrap endpoint resolver
```

## Backend-Richtlinien

- Verwende Dependency Injection statt versteckter globaler Zustände.
- Validiere alle externen Daten an der Systemgrenze mit Pydantic v2.
- Öffentliche Verträge gehören in klar benannte Contract-Module.
- Verwende für stabile Verträge grundsätzlich `ConfigDict(extra="forbid")`, sofern Erweiterbarkeit nicht ausdrücklich vorgesehen ist.
- Trenne API-Verträge, Domainmodelle, Persistenzmodelle und Registry-Einträge.
- Verwende SQLAlchemy Async.
- Vermeide N+1-Abfragen.
- Berücksichtige SQLite und PostgreSQL.
- Nutze Alembic für Datenbankänderungen.
- Liefere strukturierte Fehler mit `code`, `message`, `details` und `request_id`.
- Gib keine internen Exceptions, Stacktraces oder Secrets an Clients aus.
- Behandle Modell- und Tool-IDs des Clients nur als Wünsche und autorisiere sie serverseitig erneut.

## Frontend-Richtlinien

- Verwende TypeScript ohne ungeprüfte Typumgehungen.
- Übernimm keine ungeprüften `unknown`-Werte in den Anwendungszustand.
- Lade den Bootstrap vor allen fachlichen Ressourcen.
- Beziehe fachliche Endpunkte aus `bootstrap.endpoints`.
- Verwende einen zentralen API-Client.
- Verwende einen generischen rekursiven Baum.
- Erstelle keine fachlich fest verdrahteten Komponenten wie `ProjectNode` oder `UserNode`, wenn die Ansicht schema-gesteuert darstellbar ist.
- Komponenten werden ausschließlich über die feste Komponenten-Registry aufgelöst.
- Aktionen werden ausschließlich über die feste Action-Registry ausgeführt.
- Verwende keine dynamischen Imports aus Backendwerten.
- Verwende kein `dangerouslySetInnerHTML` für dynamische Inhalte.
- Stelle unbekannte oder noch nicht implementierte Schemaelemente sichtbar und sicher dar.

## Verträge und Versionierung

Eine Änderung gilt als Vertragsänderung, wenn sie beispielsweise betrifft:

- JSON-Feldnamen oder Feldtypen,
- Pflicht- oder Optionalfelder,
- API-Endpunkte oder HTTP-Methoden,
- SSE-Ereignisse,
- Fehlercodes,
- Manifestformate,
- Komponenten- oder Aktionstypen,
- Hierarchie-, UI-Schema-, Modell-, Tool- oder Konfigurationsantworten.

Bei Vertragsänderungen müssen mindestens aktualisiert werden:

- Backend-Contract,
- Frontend-Contract und Laufzeitvalidierung,
- OpenAPI-Dokument,
- Tests,
- Dokumentation,
- `CHANGELOG.md`.

Parallele Alt- und Neuverträge sollen nicht dauerhaft bestehen bleiben.

## Tests und Qualitätsprüfung

Vor einem Pull Request sollen mindestens die für die Änderung relevanten Prüfungen erfolgreich sein.

Backend:

```powershell
cd backend
pytest
```

Frontend:

```powershell
cd frontend
npm run build
```

Sofern eingerichtet zusätzlich:

```powershell
npm run lint
npm run test
```

Prüfe außerdem:

- Backend und Frontend starten gemeinsam.
- OpenAPI entspricht den tatsächlich implementierten Routen.
- Keine Secrets oder lokalen Datenbankdateien wurden eingecheckt.
- Neue Fehlerpfade liefern strukturierte Fehlerantworten.
- Unbekannte dynamische Typen werden sicher behandelt.

## Pull Requests

Ein Pull Request sollte enthalten:

- eine klare Beschreibung des Problems,
- die umgesetzte Lösung,
- betroffene Verträge oder Revisionen,
- durchgeführte Tests,
- mögliche Risiken,
- Screenshots bei sichtbaren Frontendänderungen,
- Migrationshinweise bei Datenbank- oder Vertragsänderungen.

Kleine, thematisch geschlossene Pull Requests sind leichter prüfbar als große Sammeländerungen.

## Dokumentation

Aktualisiere bei relevanten Änderungen mindestens:

- `README.md`,
- `docs/todo.md`,
- API- und Vertragsdokumentation,
- `CHANGELOG.md`.

Dokumentation und tatsächliche Implementierung müssen denselben Projektstand beschreiben.

## Sicherheit

Sicherheitsprobleme sollen nicht als öffentliches Issue veröffentlicht werden. Verwende stattdessen den in `SECURITY.md` beschriebenen vertraulichen Meldeweg.

## Lizenz

Mit dem Einreichen eines Beitrags erklärst du dich damit einverstanden, dass dein Beitrag unter der Lizenz des Projekts veröffentlicht wird.
