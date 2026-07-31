[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot = "F:\Kernschmied"
)

$ErrorActionPreference = "Stop"

$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = Join-Path $ProjectRoot ".patch-backups\wiki-popup-$Timestamp"

$RelativeFiles = @(
    "backend\app\api\v1\documentation.py",
    "backend\app\api\v1\router.py",
    "frontend\src\api\documentation.ts",
    "frontend\src\contracts\documentation.ts",
    "frontend\src\components\documentation\DocumentationDialog.tsx",
    "frontend\src\components\documentation\MarkdownDocument.tsx",
    "frontend\src\components\documentation\index.ts",
    "frontend\src\components\layout\AppHeader.tsx",
    "frontend\src\components\layout\AppLayout.tsx",
    "frontend\src\app\AppShell.tsx",
    "frontend\src\app\AppWorkspace.tsx",
    "wiki\User-Manual\Overview.md",
    "wiki\User-Manual\Chat.md",
    "wiki\User-Manual\Hierarchy.md",
    "wiki\User-Manual\Settings.md",
    "wiki\User-Manual\Troubleshooting.md"
)

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Projektordner nicht gefunden: $ProjectRoot"
}

foreach ($RelativeFile in $RelativeFiles) {
    $Source = Join-Path $PatchRoot $RelativeFile
    $Destination = Join-Path $ProjectRoot $RelativeFile

    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Patch-Datei fehlt: $Source"
    }

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $Backup = Join-Path $BackupRoot $RelativeFile
        $BackupDirectory = Split-Path -Parent $Backup
        New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
        Copy-Item -LiteralPath $Destination -Destination $Backup -Force
    }

    $DestinationDirectory = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Force

    Write-Host "Installiert: $RelativeFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "Patch erfolgreich installiert." -ForegroundColor Cyan
Write-Host "Sicherungen: $BackupRoot"
Write-Host "Danach Backend und Frontend neu starten."
