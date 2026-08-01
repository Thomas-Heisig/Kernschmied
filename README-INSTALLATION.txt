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

Hinweis

- Verwende `.env.example` als Vorlage für `.env`.
- Lokale Entwicklung nutzt standardmäßig SQLite.
- Für umfangreiche Backend-Änderungen bitte Tests in `backend` ausführen (`pytest`).

