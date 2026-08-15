param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [bool]$Reload = $true,
    [bool]$ShowBackendLog = $true,
    [bool]$StartMailpit = $true
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"
$RuntimeDir = Join-Path $Root "artifacts\run"
$BackendPidFile = Join-Path $RuntimeDir "backend.pid"
$BackendLogViewerPidFile = Join-Path $RuntimeDir "backend-log-viewer.pid"
$MailpitComposeFile = Join-Path $Root "compose.mailpit.yml"

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

function Stop-ManagedProcessTree {
    param([string]$PidFile)

    if (-not (Test-Path $PidFile)) {
        return
    }

    $managedPid = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($managedPid -and ($managedPid -match '^\d+$')) {
        $managedProcess = Get-Process -Id ([int]$managedPid) -ErrorAction SilentlyContinue
        if ($managedProcess) {
            Write-Host "Stopping managed process tree (PID $managedPid)..."
            & taskkill.exe /PID $managedPid /T /F | Out-Null
        }
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

# Vor dem Start vorhandene Prozesse beenden und Fenster schließen
Write-Host "Überprüfe und stoppe Prozesse auf Backend-Port $BackendPort und Frontend-Port $FrontendPort (falls vorhanden)..."
Stop-ManagedProcessTree -PidFile $BackendLogViewerPidFile
Stop-ManagedProcessTree -PidFile $BackendPidFile
Stop-ProcessOnPort -Port $BackendPort
Stop-ProcessOnPort -Port $FrontendPort

if ($StartMailpit) {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($docker -and (Test-Path $MailpitComposeFile)) {
        Write-Host "Starte Mailpit für lokale Test-E-Mails..."
        & docker compose -f $MailpitComposeFile up -d mailpit
        if ($LASTEXITCODE -eq 0) {
            $env:EMAIL_DELIVERY_ENABLED = "true"
            $env:EMAIL_PROVIDER = "smtp"
            $env:SMTP_HOST = "127.0.0.1"
            $env:SMTP_PORT = "1025"
            $env:SMTP_STARTTLS = "false"
        } else {
            Write-Warning "Mailpit konnte nicht gestartet werden; E-Mail-Zustellung bleibt deaktiviert."
            $env:EMAIL_DELIVERY_ENABLED = "false"
        }
    } else {
        Write-Warning "Docker oder compose.mailpit.yml fehlt; E-Mail-Zustellung bleibt deaktiviert."
        $env:EMAIL_DELIVERY_ENABLED = "false"
    }
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
if (-not (Test-Path $RuntimeDir)) {
    New-Item -ItemType Directory -Path $RuntimeDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackendLog = Join-Path $LogDir ("backend-$timestamp.log")
$BackendErrorLog = Join-Path $LogDir ("backend-$timestamp.err.log")
$FrontendLog = Join-Path $LogDir ("frontend-$timestamp.log")

# Control reload flag for backend uvicorn
if ($Reload) {
    $reloadFlag = "--reload"
    Write-Host "Backend wird mit Reload gestartet."
} else {
    $reloadFlag = ""
    Write-Host "Backend wird OHNE Reload gestartet."
}

# Uvicorn direkt starten. Eine PowerShell-Pipeline um den Reload-Prozess kann
# unter Windows beim Austausch des Server-Kindprozesses die gesamte Pipeline
# beenden. Native Umleitung hält den WatchFiles-ReLoader am Leben.
$backendProcessArgs = @('-u', '-m', 'uvicorn', 'main:app')
if ($Reload) {
    $backendProcessArgs += @(
        '--reload'
        '--reload-dir', $Backend
        '--reload-delay', '0.5'
    )
}
$backendProcessArgs += @(
    '--host', '0.0.0.0'
    '--port', $BackendPort
    '--timeout-graceful-shutdown', '3'
)

$backendProcess = Start-Process `
    -FilePath $VenvPython `
    -ArgumentList $backendProcessArgs `
    -WorkingDirectory $Backend `
    -RedirectStandardOutput $BackendLog `
    -RedirectStandardError $BackendErrorLog `
    -PassThru

Set-Content -Path $BackendPidFile -Value $backendProcess.Id -Encoding ascii

if ($ShowBackendLog) {
    $backendLogViewerCommand = @"
`$Host.UI.RawUI.WindowTitle = 'Kernschmied Backend Log'
Write-Host 'Backend-Log: $BackendLog' -ForegroundColor Cyan
Write-Host 'Reload-/Fehlerlog: $BackendErrorLog' -ForegroundColor Cyan
Write-Host 'Dieses Fenster kann geschlossen werden, ohne das Backend zu beenden.' -ForegroundColor DarkGray
`$logJobs = @(
    Start-Job -ScriptBlock { param(`$Path) Get-Content -Path `$Path -Wait -Tail 100 } -ArgumentList '$BackendLog'
    Start-Job -ScriptBlock { param(`$Path) Get-Content -Path `$Path -Wait -Tail 100 } -ArgumentList '$BackendErrorLog'
)
try {
    Receive-Job -Job `$logJobs -Wait
} finally {
    `$logJobs | Stop-Job
    `$logJobs | Remove-Job -Force
}
"@

    $backendLogViewer = Start-Process `
        -FilePath 'powershell.exe' `
        -ArgumentList @('-NoProfile', '-NoExit', '-Command', $backendLogViewerCommand) `
        -WorkingDirectory $Backend `
        -WindowStyle Normal `
        -PassThru

    Set-Content -Path $BackendLogViewerPidFile -Value $backendLogViewer.Id -Encoding ascii
}

# Start frontend in a new external PowerShell window and redirect output to the log file
$frontendArgs = @(
    '-NoProfile'
    '-NoExit'
    '-Command'
    "& { Set-Location '$Frontend'; npx vite --host 0.0.0.0 --port $FrontendPort 2>&1 | ForEach-Object { `$_.ToString() } | Tee-Object -FilePath '$FrontendLog' }"
)
Start-Process -FilePath 'powershell.exe' -ArgumentList $frontendArgs -WorkingDirectory $Frontend -WindowStyle Normal

Write-Host "Logs:"
Write-Host "  Backend -> $BackendLog"
Write-Host "  Backend errors/reload -> $BackendErrorLog"
Write-Host "  Frontend -> $FrontendLog"
if ($ShowBackendLog) {
    Write-Host "  Live-Logfenster -> geöffnet (deaktivierbar mit -ShowBackendLog:`$false)"
}

Write-Host "Backend: http://localhost:$BackendPort"
Write-Host "Frontend: http://localhost:$FrontendPort"
Write-Host "API-Doku: http://localhost:$BackendPort/docs"
if ($StartMailpit -and $env:EMAIL_DELIVERY_ENABLED -eq "true") {
    Write-Host "Mailpit: http://localhost:8025"
}
