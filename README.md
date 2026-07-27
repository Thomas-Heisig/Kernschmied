# Kernschmied

> Eine schema-gesteuerte, lokal betreibbare KI-Chat- und Assistenzplattform mit Python/FastAPI und React.
>
> Ziel ist eine modulare Architektur, die lokal, im Intranet und später auch sicher über das Internet betrieben werden kann – ohne grundlegende Architekturänderungen.

---

# Projektstatus

**Aktueller Stand:** MVP+ (Architekturgrundlagen vollständig, Funktionsumfang wird kontinuierlich erweitert)

Bereits umgesetzt sind unter anderem:

- generische Systemarchitektur
- schema-gesteuerte Benutzeroberfläche
- dynamische Modellverwaltung
- Tool-Registries
- konfigurierbare Hierarchie
- Streaming-Chat
- Administrationsoberfläche
- versionierte Konfiguration

---

# Architekturprinzipien

Das gesamte Projekt folgt einigen festen Grundregeln:

- Dynamische Fachlogik
- Stabile API-Verträge
- Versionierte Schemas
- Serverseitige Autorisierung
- Klare Sicherheitsgrenzen
- Dependency Injection
- Kleine, testbare Module
- Keine Geschäftslogik im Frontend

---

# Technologie-Stack

## Backend

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy Async
- SQLite
- PostgreSQL (vorbereitet)
- Alembic
- Server Sent Events (SSE)
- strukturierte Fehlerantworten
- Dependency Injection

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Schema Renderer
- Komponenten-Registry
- Action-Registry
- rekursive Baumdarstellung

---

# Projektstruktur

```
Kernschmied/

├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── config/
│   │   ├── contracts/
│   │   ├── core/
│   │   ├── models/
│   │   ├── registries/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── storage/
│   │   └── hierarchy/
│   └── migrations/
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── registry/
│   │   ├── renderer/
│   │   └── tree/
│
├── docs/
├── start.ps1
├── PROJECT_PROMPT.md
└── README.md
```

---

# Kernfunktionen

## Konfigurationssystem

Die Fachkonfiguration liegt vollständig in der Datenbank.

Unterstützt werden:

- Versionierung
- Revisionen
- Runtime-Konfiguration
- Validierung
- Auditfähigkeit
- Bootstrap über `.env`

---

## Hierarchie

Das System besitzt eine vollständig generische Hierarchie.

Beispiele:

- Organisation
- Projekte
- Benutzer
- Teams
- Chats
- Dokumente
- Wissensbereiche

Neue Knotentypen können ohne Änderungen am Frontend ergänzt werden.

---

## Schema-gesteuerte Oberfläche

Das Frontend kennt keine fachlichen Komponenten.

Stattdessen werden Ansichten über Schemas beschrieben.

Unterstützt werden unter anderem:

- Formulare
- Tabs
- Listen
- Detailansichten
- Karten
- Baumstrukturen
- Aktionsleisten

Unbekannte Komponenten werden kontrolliert dargestellt und nicht ausgeführt.

---

## Komponenten-Registry

Alle Frontend-Komponenten werden zentral registriert.

Neue Komponenten können ergänzt werden, ohne bestehende Ansichten anzupassen.

---

## Action-Registry

Auch Benutzeraktionen werden zentral registriert.

Dadurch bleibt die Oberfläche vollständig generisch.

---

## Modell-Registry

Das Backend besitzt eine dynamische Modellverwaltung.

Aktuell vorbereitet für beispielsweise:

- Ollama
- OpenAI
- Azure OpenAI
- lokale Modelle
- zukünftige Provider

Neue Modelle werden über Manifeste registriert.

---

## Tool-Registry

Auch Werkzeuge werden dynamisch geladen.

Werkzeuge besitzen:

- Manifest
- Konfiguration
- Berechtigungen
- Validierung
- Fehlerisolierung

---

## Streaming-Chat

Der Chat verwendet Server Sent Events (SSE).

Unterstützt werden:

- Streaming
- Token-Ausgabe
- Fehlerereignisse
- strukturierte Events

---

## Konfigurationsverwaltung

Alle Einstellungen besitzen:

- Schema
- Version
- Revision
- Validierung
- Änderungsverlauf

---

# Sicherheitsmodell

Das Projekt unterstützt drei Betriebsprofile.

## Development

- lokale Entwicklung
- vereinfachte Authentifizierung
- Debugging

## Intranet

- Benutzerverwaltung
- Audit
- Berechtigungen

## Internet

- HTTPS
- Sessionverwaltung
- Rate Limiting
- CSRF-Schutz
- sichere Cookies
- strenge Sicherheitsrichtlinien

---

# API

Das Backend stellt eine REST-API bereit.

Dokumentation:

```
http://localhost:8000/docs
```

OpenAPI:

```
http://localhost:8000/openapi.json
```

---

# Schnellstart

## Voraussetzungen

- Python 3.12
- Node.js 20+
- PowerShell

---

## Projekt starten

```powershell
.\start.ps1
```

Danach stehen zur Verfügung:

| Dienst | Adresse |
|---------|----------|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

---

# Backend manuell starten

```powershell
cd backend

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

uvicorn main:app --reload
```

---

# Frontend manuell starten

```powershell
cd frontend

npm install

npm run dev
```

---

# Entwicklungsprinzipien

Im gesamten Projekt gelten folgende Regeln:

- Keine Fachlogik im Frontend
- Keine dynamischen `eval()`-Aufrufe
- Keine unkontrollierten Python-Imports
- Alle Daten werden validiert
- Server autorisiert jede Aktion
- Stabile Verträge werden versioniert
- Konfiguration niemals hart codieren
- Secrets niemals in der Datenbank im Klartext speichern

---

# Roadmap

## Bereits umgesetzt

- FastAPI
- React
- TypeScript
- Tailwind
- SQLAlchemy Async
- SQLite
- Bootstrap-Konfiguration
- Systemkonfiguration
- Revisionssystem
- Schema-Renderer
- Komponenten-Registry
- Action-Registry
- generische Hierarchie
- Modell-Registry
- Tool-Registry
- Streaming-Chat
- Administrationsgrundlagen

---

## Geplant

- Authentifizierung
- Rollen- und Rechtesystem
- Dokumentenverwaltung
- Wissensdatenbank (RAG)
- Plugin-System
- Multi-Modell-Unterstützung
- Agenten
- Workflow-Engine
- PostgreSQL
- Mehrbenutzerbetrieb
- Hintergrundjobs
- Monitoring
- Vollständige Testabdeckung

---

# Lizenz

Dieses Projekt befindet sich aktuell in aktiver Entwicklung.

```

## Warum diese Version besser ist

Sie beschreibt den tatsächlichen Projektstand deutlich genauer. Gegenüber der bisherigen README werden insbesondere folgende inzwischen vorhandene Architekturbausteine dokumentiert:

- ✅ generische Hierarchie
- ✅ schema-gesteuerter Renderer
- ✅ Komponenten- und Action-Registry
- ✅ Modell-Registry
- ✅ Tool-Registry
- ✅ Revisionssystem
- ✅ Konfigurationsverwaltung
- ✅ Sicherheitsmodell mit Betriebsprofilen
- ✅ Projektstruktur
- ✅ Roadmap
- ✅ Architekturprinzipien
- ✅ Entwicklungsrichtlinien

Damit wirkt das Repository nicht mehr wie ein einfaches FastAPI/React-Template, sondern als das, was es inzwischen ist: das Fundament einer modularen, schema-gesteuerten KI-Plattform.