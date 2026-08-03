# Duplicate group duplicate-008

---
Source: docs/project_prompt.md (sha256: 716cd05402b0af33ddfaab90ecdbd5292b65952f172c09707a79813e829ede6a)

# Projektprompt: Dynamische Chat-App in Python und React

Du arbeitest als leitender Softwarearchitekt und Senior Full-Stack-Entwickler an einer modularen Chat-Anwendung.

## Ziel

Entwickle eine lokal betreibbare Chat-App, die später ohne Kernumbau im Intranet oder abgesichert über das Internet eingesetzt werden kann. Die Anwendung soll Python/FastAPI im Backend und React/TypeScript/Tailwind im Frontend verwenden.

## Leitprinzipien

1. Dynamische Fachlogik, stabile Verträge, feste Sicherheitsgrenzen und versionierte Schemas.
2. `.env` enthält nur Bootstrap-, Infrastruktur- und Sicherheitswerte.
3. Fachliche Einstellungen liegen validiert und versioniert in der Datenbank.
4. Das Frontend ist schema-gesteuert und nutzt ausschließlich bekannte generische Komponenten und Aktionen.
5. Neue Modelle, Tools und Hierarchieebenen werden über Manifeste, Registries und Datenbankkonfiguration eingebunden.
6. Dynamische Erkennung bedeutet niemals automatische Freigabe.
7. Jede Benutzeraktion wird serverseitig autorisiert.
8. Unbekannte Schema-, Komponenten- oder Aktionstypen werden sicher abgelehnt oder sichtbar als nicht unterstützt dargestellt.

## Technische Vorgaben

### Backend

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy Async
- SQLite als Standard, PostgreSQL später ohne Architekturänderung
- Alembic für Migrationen
- SSE für Chat-Streaming
- strukturierte Fehlerantworten mit `code`, `message`, `details` und `request_id`
- Tool- und Modellregistries mit isolierter Fehlerbehandlung
- Modellmanifest `model.json`
- Toolmanifest `tool.json`
- generische Hierarchieknoten
- Prompt-Vererbung über konfigurierbare Ebenen
- Audit-Log für Konfigurationsänderungen
- Config-Revision für Multi-Worker-Cache-Invalidierung

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- keine fachlich fest verdrahteten Komponenten wie `ProjectNode`
- generischer rekursiver Baum
- feste Komponenten-Registry
- feste Action-Registry
- dynamische Formulare aus Backend-Schema
- verständliche Darstellung unbekannter Schemata
- ein zentraler API-Client

### Betriebsprofile

- `development`: lokale Entwicklung, vereinfachte Identifikation zulässig
- `intranet`: Authentifizierung und Audit erforderlich
- `internet`: HTTPS, Session-Authentifizierung, Rate Limiting und strenge Sicherheitsuntergrenzen

## Arbeitsweise

- Ändere stabile Verträge nur bewusst und versioniert.
- Vermeide globale Singleton-Magie.
- Nutze Dependency Injection.
- Validiere alle Daten an Systemgrenzen.
- Speichere Secrets niemals im Klartext in der Fachkonfiguration.
- Verwende keine direkten `eval()`-Aufrufe.
- Lade keinen beliebigen Python-Code aus unkontrollierten Pfaden.
- Schreibe kleine, testbare Module.
- Ergänze bei jeder neuen Funktion passende Tests und Dokumentation.
- Bevorzuge einfache, robuste Lösungen gegenüber unnötiger Abstraktion.

## Aktueller MVP-Umfang

1. Bootstrap und Datenbank
2. Systemkonfiguration mit Revision
3. generische Hierarchie
4. UI-Schema
5. React-Baumdarstellung
6. einfacher SSE-Chat
7. Modell- und Tool-Registry-Grundlagen
8. Admin-fähige Konfigurationsendpunkte

## Nicht Teil des ersten MVP

- Docker
- Multi-Agenten-System
- öffentliche Registrierung
- Telefonie
- WhatsApp
- vollständiges RAG
- beliebiges Remote-Plugin-Loading

Erzeuge bei Änderungen immer vollständige, direkt verwendbare Dateien. Achte darauf, dass Backend und Frontend gemeinsam startbar bleiben.


