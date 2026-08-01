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

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackendLog = Join-Path $LogDir ("backend-$timestamp.log")
$FrontendLog = Join-Path $LogDir ("frontend-$timestamp.log")

# Start backend and frontend as background jobs and redirect stdout/stderr to log files
# Start backend in a new external PowerShell window and redirect output to the log file
# Build argument array to ensure a new external console window is created
$backendArgs = @(
    '-NoProfile'
    '-NoExit'
    '-Command'
    "& { Set-Location '$Backend'; & '$VenvPython' -u -m uvicorn main:app --reload --host 0.0.0.0 --port $BackendPort 2>&1 | Tee-Object -FilePath '$BackendLog' }"
)
Start-Process -FilePath 'powershell.exe' -ArgumentList $backendArgs -WorkingDirectory $Backend -WindowStyle Normal

# Start frontend in a new external PowerShell window and redirect output to the log file
$frontendArgs = @(
    '-NoProfile'
    '-NoExit'
    '-Command'
    "& { Set-Location '$Frontend'; npx vite --host 0.0.0.0 --port $FrontendPort 2>&1 | Tee-Object -FilePath '$FrontendLog' }"
)
Start-Process -FilePath 'powershell.exe' -ArgumentList $frontendArgs -WorkingDirectory $Frontend -WindowStyle Normal

Write-Host "Logs:"
Write-Host "  Backend -> $BackendLog"
Write-Host "  Frontend -> $FrontendLog"

Write-Host "Backend: http://localhost:$BackendPort"
Write-Host "Frontend: http://localhost:$FrontendPort"
Write-Host "API-Doku: http://localhost:$BackendPort/docs"
