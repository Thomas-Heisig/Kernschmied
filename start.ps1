param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [bool]$Reload = $true
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

# Funktion: Stoppe Prozesse, die auf einem bestimmten Port lauschen
function Stop-ProcessOnPort {
    param([int]$Port)
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction Stop
        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    } catch {
        $pids = @()
    }

    if ($pids.Count -gt 0) {
        foreach ($procId in $pids) {
            try {
                $proc = Get-Process -Id $procId -ErrorAction Stop
                Write-Host "Stopping process $($proc.ProcessName) (PID $procId) listening on port $Port..."
                Stop-Process -Id $procId -Force -ErrorAction Stop
            } catch {
                Write-Host "Failed to stop PID $($procId): $($_)"
            }
        }
        Start-Sleep -Milliseconds 500
        return
    }

    # Fallback: parse netstat output if Get-NetTCPConnection didn't return anything
    $netstat = & netstat -ano | Select-String ":$Port\s+LISTENING" -ErrorAction SilentlyContinue
    foreach ($line in $netstat) {
        $parts = ($line -split '\s+') | Where-Object { $_ -ne '' }
        $procId = $parts[-1]
        if ($procId -and ($procId -match '^\d+$')) {
            try {
                $proc = Get-Process -Id $procId -ErrorAction Stop
                Write-Host "Stopping process $($proc.ProcessName) (PID $procId) listening on port $Port..."
                Stop-Process -Id $procId -Force -ErrorAction Stop
            } catch {
                Write-Host "Failed to stop PID $($procId) from netstat: $($_)"
            }
        }
    }
    Start-Sleep -Milliseconds 500
}

# Vor dem Start vorhandene Prozesse beenden und Fenster schließen
Write-Host "Überprüfe und stoppe Prozesse auf Backend-Port $BackendPort und Frontend-Port $FrontendPort (falls vorhanden)..."
Stop-ProcessOnPort -Port $BackendPort
Stop-ProcessOnPort -Port $FrontendPort

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

# Control reload flag for backend uvicorn
if ($Reload) {
    $reloadFlag = "--reload"
    Write-Host "Backend wird mit Reload gestartet."
} else {
    $reloadFlag = ""
    Write-Host "Backend wird OHNE Reload gestartet."
}

# Start backend and frontend as background jobs and redirect stdout/stderr to log files
# Start backend in a new external PowerShell window and redirect output to the log file
# Build argument array to ensure a new external console window is created
$backendArgs = @(
    '-NoProfile'
    '-NoExit'
    '-Command'
    "& { Set-Location '$Backend'; & '$VenvPython' -u -m uvicorn main:app $reloadFlag --host 0.0.0.0 --port $BackendPort 2>&1 | Tee-Object -FilePath '$BackendLog' }"
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
