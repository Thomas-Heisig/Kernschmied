# Fehlerbehebung

## Dokumentation bleibt leer

Prüfe zuerst:

- `GET /api/v1/documentation`
- `GET /api/v1/documentation/pages/user-manual-overview`
- ob der Ordner `wiki/User-Manual` im Projekt vorhanden ist

## Chat antwortet nicht

Prüfe:

1. Ollama oder den gewählten Provider.
2. die registrierte logische Modell-ID.
3. den tatsächlichen Provider-Modellnamen.
4. die Backend-Konsole und die Request-ID.
5. SSE-Fehlerereignisse in den Browser-Entwicklertools.

## Einstellungen werden nicht gespeichert

Eine veraltete Config-Revision führt bewusst zu einem Konflikt. Lade die Einstellungen neu und wiederhole die Änderung auf Basis der aktuellen Revision.
