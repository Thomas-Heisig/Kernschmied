# Kernschmied Wiki-Popup Patch

Dieser Overlay-Patch ergänzt:

- einen Dokumentationsbutton im Header,
- ein modernes, durchsuchbares Dokumentations-Popup,
- eine kontrollierte Backend-API für registrierte Markdown-Dateien,
- ein Benutzerhandbuch unter `wiki/User-Manual`,
- einen lokalen Markdown-Renderer ohne zusätzliche npm-Abhängigkeiten.

## Installation

Die ZIP-Datei in einen temporären Ordner entpacken und aus PowerShell ausführen:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\apply-patch.ps1 -ProjectRoot "F:\Kernschmied"
```

Das Skript erstellt vor dem Überschreiben Sicherungskopien unter:

```text
F:\Kernschmied\.patch-backups\wiki-popup-<Zeitstempel>
```

## Danach prüfen

```powershell
cd F:\Kernschmied\backend
.\.venv\Scripts\python.exe -m compileall app\api\v1\documentation.py app\api\v1\router.py

cd F:\Kernschmied\frontend
npm run build
```

Anschließend Kernschmied neu starten und testen:

```text
http://localhost:8000/api/v1/documentation
http://localhost:5173
```

## Sicherheitsgrenze

Der Backend-Endpunkt akzeptiert nur feste Seiten-IDs aus `DOCUMENTATION_PAGES`. Beliebige Dateipfade und Directory Traversal sind nicht möglich.
