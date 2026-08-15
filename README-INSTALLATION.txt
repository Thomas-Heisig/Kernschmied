Installation und Start

Diese Datei enthält eine kompakte Installationsanleitung. Eine ausführlichere Projektübersicht steht in `README.md`.

1) Repository klonen

```powershell
git clone https://github.com/Thomas-Heisig/Kernschmied.git
cd Kernschmied
```

2) Backend vorbereiten

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ..
```

3) Frontend vorbereiten

```powershell
cd frontend
npm install
cd ..
```

4) Gesamtsystem starten

```powershell
.\start.ps1
```

Das Backend startet standardmäßig mit WatchFiles-ReLoad. Änderungen an
Python-Dateien unter `backend` lösen automatisch einen Serverneustart aus.
Mit `-Reload:$false` kann dieses Verhalten deaktiviert werden.

Laufzeitdateien:

- `artifacts/run/backend.pid` – verwaltete Backend-Prozess-ID
- `artifacts/logs/backend-*.log` – Standardausgabe
- `artifacts/logs/backend-*.err.log` – Uvicorn-, WatchFiles- und Reloadmeldungen

`start.ps1` öffnet standardmäßig ein separates Fenster, das Anwendungs- und
Requestlogs sowie Uvicorn-, WatchFiles- und Reloadmeldungen live zusammenführt.
Dieses Fenster kann geschlossen werden, ohne das Backend zu beenden. Ohne
Logfenster starten:

```powershell
.\start.ps1 -ShowBackendLog:$false
```

Hinweis

- Verwende `.env.example` als Vorlage für `.env`.
- Lokale Entwicklung nutzt standardmäßig SQLite.
- Für umfangreiche Backend-Änderungen bitte Tests in `backend` ausführen (`pytest`).

