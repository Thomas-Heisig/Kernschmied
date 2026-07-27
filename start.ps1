param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
    Write-Host ".env wurde aus .env.example erstellt. Bitte Secrets später ändern."
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Erstelle Python-Umgebung..."
    python -m venv (Join-Path $Backend ".venv")
}

Write-Host "Installiere Backend-Abhängigkeiten..."
& $VenvPython -m pip install -r (Join-Path $Backend "requirements.txt")

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Write-Host "Installiere Frontend-Abhängigkeiten..."
    Push-Location $Frontend
    npm install
    Pop-Location
}

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Backend'; & '$VenvPython' -m uvicorn main:app --reload --host 0.0.0.0 --port $BackendPort"
)

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Frontend'; npx vite --host 0.0.0.0 --port $FrontendPort"
)

Write-Host "Backend: http://localhost:$BackendPort"
Write-Host "Frontend: http://localhost:$FrontendPort"
Write-Host "API-Doku: http://localhost:$BackendPort/docs"
