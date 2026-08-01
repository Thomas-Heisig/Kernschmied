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
# Prepare log directory and paths
$LogDir = Join-Path $Root "artifacts\logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$BackendLog = Join-Path $LogDir "backend.log"
$FrontendLog = Join-Path $LogDir "frontend.log"

# Start backend and frontend as background jobs and redirect stdout/stderr to log files
Start-Job -Name "Kernschmied-Backend" -ScriptBlock {
    param($backend, $venv, $port, $log)
    Set-Location $backend
    # Redirect all output (stdout+stderr) to the log file
    & $venv -m uvicorn main:app --reload --host 0.0.0.0 --port $port *>$log 2>&1
} -ArgumentList $Backend, $VenvPython, $BackendPort, $BackendLog

Start-Job -Name "Kernschmied-Frontend" -ScriptBlock {
    param($frontend, $port, $log)
    Set-Location $frontend
    # Redirect all output (stdout+stderr) to the log file
    npx vite --host 0.0.0.0 --port $port *>$log 2>&1
} -ArgumentList $Frontend, $FrontendPort, $FrontendLog

Write-Host "Logs:"
Write-Host "  Backend -> $BackendLog"
Write-Host "  Frontend -> $FrontendLog"

Write-Host "Backend: http://localhost:$BackendPort"
Write-Host "Frontend: http://localhost:$FrontendPort"
Write-Host "API-Doku: http://localhost:$BackendPort/docs"
