<#
.SYNOPSIS
Führt die vollständige Kernschmied-Qualitätspipeline aus.

.DESCRIPTION
Formatiert, korrigiert und prüft das Kernschmied-Projekt.

Die Pipeline umfasst unter anderem:

- Ruff
- Black-Kompatibilitätsprüfung
- Prettier
- Markdownlint
- Lychee
- Vale
- JSON-, TOML- und YAML-Validierung
- Python-Kompilierung
- FastAPI- und OpenAPI-Prüfung
- Mypy
- pip check
- pip-audit
- Bandit
- Pytest
- ESLint
- TypeScript
- Frontend-Tests
- Frontend-Build
- npm audit
- PSScriptAnalyzer
- TODO-/FIXME-Bericht
- Git-Status und Whitespace-Prüfung

Die Ergebnisse werden sowohl als Textprotokoll als auch als strukturierter
JSON-Bericht im Verzeichnis artifacts\quality gespeichert.

.PARAMETER SkipSecurity
Überspringt pip-audit, Bandit und npm audit.

.PARAMETER SkipTests
Überspringt Backend- und Frontend-Tests.

.PARAMETER SkipBuild
Überspringt den Frontend-Produktions-Build.

.PARAMETER SkipLinks
Überspringt die Lychee-Linkprüfung.

.PARAMETER SkipDocumentation
Überspringt Markdownlint, Lychee und Vale.

.PARAMETER InstallDependencies
Installiert Backend- und Frontend-Abhängigkeiten vor der Prüfung.

Backend-Abhängigkeiten werden bevorzugt aus einer vorhandenen Lock- oder
Requirements-Datei installiert.

Frontend-Abhängigkeiten werden mit npm ci installiert, sofern eine
package-lock.json vorhanden ist.

.PARAMETER AllowUnlockedNpmInstall
Erlaubt als ausdrücklichen Fallback ein npm install, wenn package.json
vorhanden ist, aber package-lock.json fehlt.

Ohne diesen Parameter wird die Installation aus Sicherheits- und
Reproduzierbarkeitsgründen abgebrochen beziehungsweise übersprungen.

.PARAMETER FailOnTodo
Bewertet gefundene TODO-, FIXME-, HACK-, XXX-, PLACEHOLDER- und
NOT-IMPLEMENTED-Hinweise als Fehler.

.PARAMETER FailFast
Bricht die Pipeline nach dem ersten fehlgeschlagenen Schritt ab.

.PARAMETER StrictPowerShell
Bewertet Warnungen und Fehler von PSScriptAnalyzer als Pipelinefehler.

Ohne diesen Parameter wird PSScriptAnalyzer nur als Warnung behandelt.

.PARAMETER StrictDocumentation
Bewertet Vale-Probleme als Pipelinefehler.

Ohne diesen Parameter wird Vale nur als Warnung behandelt.

.PARAMETER SkipFixes
Führt keine automatischen Änderungen durch.

Dabei werden unter anderem folgende mutierende Schritte übersprungen:

- ruff format
- ruff check --fix
- prettier --write
- markdownlint --fix
- eslint --fix

Die reinen Prüfungen werden weiterhin ausgeführt.

.EXAMPLE
.\scripts\quality-full.ps1

Führt die vollständige Pipeline mit automatischen Korrekturen aus.

.EXAMPLE
.\scripts\quality-full.ps1 -SkipSecurity -SkipLinks

Überspringt Sicherheits- und Linkprüfungen.

.EXAMPLE
.\scripts\quality-full.ps1 -InstallDependencies

Installiert zuerst die Backend- und Frontend-Abhängigkeiten.

.EXAMPLE
.\scripts\quality-full.ps1 -InstallDependencies -AllowUnlockedNpmInstall

Erlaubt npm install, wenn keine package-lock.json vorhanden ist.

.EXAMPLE
.\scripts\quality-full.ps1 -FailFast -FailOnTodo -StrictPowerShell

Führt einen strengen Qualitätslauf aus.

.EXAMPLE
.\scripts\quality-full.ps1 -SkipFixes

Führt nur nicht-mutierende Prüfungen aus.

.EXAMPLE
Get-Help .\scripts\quality-full.ps1 -Detailed
#>

# F:\Kernschmied\scripts\quality-full.ps1

[CmdletBinding()]
param(
    [switch]$SkipSecurity,
    [switch]$SkipTests,
    [switch]$SkipBuild,
    [switch]$SkipLinks,
    [switch]$SkipDocumentation,
    [switch]$InstallDependencies,
    [switch]$AllowUnlockedNpmInstall,
    [switch]$FailOnTodo,
    [switch]$FailFast,
    [switch]$StrictPowerShell,
    [switch]$StrictDocumentation,
    [switch]$SkipFixes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Native Programme werden zentral über ihren Exitcode ausgewertet.
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

# ============================================================
# Laufzeit und Projektpfade
# ============================================================

$PipelineStartTime = Get-Date
$OriginalLocation = Get-Location

$ScriptDirectory = [System.IO.Path]::GetFullPath(
    (Split-Path -Parent $MyInvocation.MyCommand.Path)
)

$ProjectRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $ScriptDirectory "..")
)

$BackendDirectory = Join-Path $ProjectRoot "backend"
$FrontendDirectory = Join-Path $ProjectRoot "frontend"
$WikiDirectory = Join-Path $ProjectRoot "wiki"

$ArtifactDirectory = Join-Path $ProjectRoot "artifacts\quality"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

$LogFile = Join-Path `
    $ArtifactDirectory `
    "quality-$Timestamp.log"

$JsonLogFile = Join-Path `
    $ArtifactDirectory `
    "quality-$Timestamp.json"

$TodoReport = Join-Path `
    $ArtifactDirectory `
    "todo-report-$Timestamp.txt"

New-Item `
    -ItemType Directory `
    -Path $ArtifactDirectory `
    -Force |
    Out-Null

Set-Location $ProjectRoot

# ============================================================
# Pipeline-Zustand
# ============================================================

$StepLog = [System.Collections.Generic.List[object]]::new()

$PipelineState = [ordered]@{
    Name            = "Kernschmied Quality Pipeline"
    ProjectRoot     = $ProjectRoot
    StartedAt       = $PipelineStartTime.ToString("o")
    FinishedAt      = $null
    DurationSeconds = $null
    Success         = $false
    PassedCount     = 0
    FailedCount     = 0
    SkippedCount    = 0
    WarningCount    = 0
    Parameters      = [ordered]@{
        SkipSecurity           = $SkipSecurity.IsPresent
        SkipTests              = $SkipTests.IsPresent
        SkipBuild              = $SkipBuild.IsPresent
        SkipLinks              = $SkipLinks.IsPresent
        SkipDocumentation      = $SkipDocumentation.IsPresent
        InstallDependencies    = $InstallDependencies.IsPresent
        AllowUnlockedNpmInstall = $AllowUnlockedNpmInstall.IsPresent
        FailOnTodo             = $FailOnTodo.IsPresent
        FailFast               = $FailFast.IsPresent
        StrictPowerShell       = $StrictPowerShell.IsPresent
        StrictDocumentation    = $StrictDocumentation.IsPresent
        SkipFixes              = $SkipFixes.IsPresent
    }
    Steps           = $StepLog
}

$TranscriptStarted = $false
$UnexpectedError = $null

# ============================================================
# Ausgabe
# ============================================================

function Write-Section {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$Title
    )

    Write-Host ""
    Write-Host ("=" * 76) -ForegroundColor DarkGray
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host ("=" * 76) -ForegroundColor DarkGray
}

function Write-CommandPreview {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string[]]$Arguments = @()
    )

    $RenderedArguments = foreach ($Argument in $Arguments) {
        if (
            $Argument.Contains(" ") -or
            $Argument.Contains("`t")
        ) {
            '"{0}"' -f $Argument.Replace('"', '\"')
        }
        else {
            $Argument
        }
    }

    $Preview = (
        "> {0} {1}" -f
        $Command,
        ($RenderedArguments -join " ")
    ).TrimEnd()

    Write-Host ""
    Write-Host $Preview -ForegroundColor DarkGray
}

# ============================================================
# Schrittprotokoll
# ============================================================

function Add-StepLogEntry {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [ValidateSet(
            "Passed",
            "Failed",
            "Skipped",
            "Warning"
        )]
        [string]$Status,

        [Parameter(Mandatory)]
        [datetime]$StartTime,

        [Parameter(Mandatory)]
        [datetime]$EndTime,

        [string]$Message = ""
    )

    $DurationSeconds = (
        $EndTime - $StartTime
    ).TotalSeconds

    $StepLog.Add(
        [PSCustomObject]@{
            Name            = $Name
            Status          = $Status
            StartedAt       = $StartTime.ToString("o")
            FinishedAt      = $EndTime.ToString("o")
            DurationSeconds = [Math]::Round(
                $DurationSeconds,
                3
            )
            Message         = $Message
        }
    )
}

function Invoke-QualityStep {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$Name,

        [Parameter(Mandatory)]
        [scriptblock]$Action,

        [switch]$WarningOnly
    )

    Write-Section $Name

    $StartTime = Get-Date
    $Status = "Passed"
    $Message = ""

    try {
        & $Action

        Write-Host ""
        Write-Host "[OK] $Name" -ForegroundColor Green
    }
    catch {
        $Message = $_.Exception.Message

        if ($WarningOnly) {
            $Status = "Warning"

            Write-Host ""
            Write-Host "[WARNUNG] $Name" -ForegroundColor Yellow
            Write-Host $Message -ForegroundColor DarkYellow
        }
        else {
            $Status = "Failed"

            Write-Host ""
            Write-Host "[FEHLER] $Name" -ForegroundColor Red
            Write-Host $Message -ForegroundColor DarkRed
        }
    }
    finally {
        $EndTime = Get-Date

        Add-StepLogEntry `
            -Name $Name `
            -Status $Status `
            -StartTime $StartTime `
            -EndTime $EndTime `
            -Message $Message
    }

    if (
        $Status -eq "Failed" -and
        $FailFast
    ) {
        throw "Pipeline wegen -FailFast abgebrochen: $Name"
    }

    return $Status
}

function Skip-QualityStep {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [string]$Reason
    )

    Write-Section $Name

    Write-Host (
        "[ÜBERSPRUNGEN] $Reason"
    ) -ForegroundColor Yellow

    $Now = Get-Date

    Add-StepLogEntry `
        -Name $Name `
        -Status "Skipped" `
        -StartTime $Now `
        -EndTime $Now `
        -Message $Reason
}

# ============================================================
# Programme und Prozesse
# ============================================================

function Test-Executable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    return $null -ne (
        Get-Command `
            -Name $Name `
            -ErrorAction SilentlyContinue
    )
}

function Assert-Executable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    if (-not (Test-Executable $Name)) {
        throw "Das Programm '$Name' wurde nicht gefunden."
    }
}

function Invoke-External {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$Command,

        [string[]]$Arguments = @(),

        [string]$WorkingDirectory
    )

    Assert-Executable $Command
    Write-CommandPreview $Command $Arguments

    $PreviousLocation = Get-Location

    try {
        if ($WorkingDirectory) {
            if (-not (Test-Path -LiteralPath $WorkingDirectory)) {
                throw (
                    "Arbeitsverzeichnis nicht gefunden: " +
                    $WorkingDirectory
                )
            }

            Set-Location $WorkingDirectory
        }

        & $Command @Arguments

        $ExitCode = $LASTEXITCODE

        if ($null -eq $ExitCode) {
            $ExitCode = 0
        }

        if ($ExitCode -ne 0) {
            throw (
                "Befehl '$Command' wurde mit Exitcode " +
                "$ExitCode beendet."
            )
        }
    }
    finally {
        if ($WorkingDirectory) {
            Set-Location $PreviousLocation
        }
    }
}

function Test-LocalNodeCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string]$WorkingDirectory = $ProjectRoot
    )

    $ExecutableName = if ($IsWindows) {
        "$Command.cmd"
    }
    else {
        $Command
    }

    $Candidates = @(
        (Join-Path `
            $WorkingDirectory `
            "node_modules\.bin\$ExecutableName"),

        (Join-Path `
            $ProjectRoot `
            "node_modules\.bin\$ExecutableName"),

        (Join-Path `
            $FrontendDirectory `
            "node_modules\.bin\$ExecutableName")
    )

    return @(
        $Candidates |
        Where-Object {
            Test-Path -LiteralPath $_
        }
    ).Count -gt 0
}

function Invoke-Npx {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments,

        [string]$WorkingDirectory = $ProjectRoot
    )

    Invoke-External `
        -Command "npx" `
        -Arguments (@("--no-install") + $Arguments) `
        -WorkingDirectory $WorkingDirectory
}

function Test-PythonModule {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidatePattern("^[A-Za-z0-9_.]+$")]
        [string]$Module
    )

    if (-not (Test-Executable "python")) {
        return $false
    }

    & python `
        -c `
        "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec(sys.argv[1]) else 1)" `
        $Module `
        *> $null

    return $LASTEXITCODE -eq 0
}

# ============================================================
# Dateien und Ausschlüsse
# ============================================================

function Test-IsExcludedPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$FullName
    )

    $RelativePath = [System.IO.Path]::GetRelativePath(
        $ProjectRoot,
        $FullName
    )

    $Segments = $RelativePath -split "[\\/]+"

    $ExcludedSegments = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::OrdinalIgnoreCase
    )

    @(
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        "coverage",
        "htmlcov",
        "artifacts",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
        ".idea",
        ".vscode-test"
    ) |
    ForEach-Object {
        [void]$ExcludedSegments.Add($_)
    }

    foreach ($Segment in $Segments) {
        if ($ExcludedSegments.Contains($Segment)) {
            return $true
        }

        if ($Segment -match "^\.venv-\d+$") {
            return $true
        }
    }

    return $false
}

function Get-ProjectFiles {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Extensions
    )

    $NormalizedExtensions = @(
        $Extensions |
        ForEach-Object {
            if ($_.StartsWith(".")) {
                $_.ToLowerInvariant()
            }
            else {
                ".$($_.ToLowerInvariant())"
            }
        }
    )

    return @(
        Get-ChildItem `
            -LiteralPath $ProjectRoot `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $NormalizedExtensions -contains
            $_.Extension.ToLowerInvariant() -and
            -not (Test-IsExcludedPath $_.FullName)
        }
    )
}

function Invoke-FileBatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [System.IO.FileInfo[]]$Files,

        [Parameter(Mandatory)]
        [ValidateRange(1, 1000)]
        [int]$BatchSize,

        [Parameter(Mandatory)]
        [scriptblock]$Action
    )

    if ($Files.Count -eq 0) {
        return
    }

    for (
        $StartIndex = 0;
        $StartIndex -lt $Files.Count;
        $StartIndex += $BatchSize
    ) {
        $EndIndex = [Math]::Min(
            $StartIndex + $BatchSize - 1,
            $Files.Count - 1
        )

        $Batch = @(
            $Files[$StartIndex..$EndIndex]
        )

        & $Action $Batch
    }
}

# ============================================================
# NPM
# ============================================================

function Get-NpmScripts {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$PackageJsonPath
    )

    if (-not (Test-Path -LiteralPath $PackageJsonPath)) {
        return @()
    }

    $PackageJson = Get-Content `
        -LiteralPath $PackageJsonPath `
        -Raw `
        -Encoding UTF8 |
        ConvertFrom-Json

    if ($null -eq $PackageJson.scripts) {
        return @()
    }

    return @(
        $PackageJson.scripts.PSObject.Properties.Name
    )
}

function Test-NpmScript {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Scripts,

        [Parameter(Mandatory)]
        [string]$Name
    )

    return $Scripts -contains $Name
}

# ============================================================
# Backend-Abhängigkeiten
# ============================================================

function Get-BackendDependencySource {
    [CmdletBinding()]
    param()

    $Candidates = @(
        @{
            Path = Join-Path $BackendDirectory "requirements.lock"
            Type = "requirements"
        },
        @{
            Path = Join-Path $BackendDirectory "requirements.txt"
            Type = "requirements"
        },
        @{
            Path = Join-Path $ProjectRoot "requirements.lock"
            Type = "requirements"
        },
        @{
            Path = Join-Path $ProjectRoot "requirements.txt"
            Type = "requirements"
        },
        @{
            Path = Join-Path $BackendDirectory "pyproject.toml"
            Type = "pyproject"
        },
        @{
            Path = Join-Path $ProjectRoot "pyproject.toml"
            Type = "pyproject"
        }
    )

    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate.Path) {
            return [PSCustomObject]@{
                Path = $Candidate.Path
                Type = $Candidate.Type
            }
        }
    }

    return $null
}

function Install-BackendDependencies {
    [CmdletBinding()]
    param()

    $DependencySource = Get-BackendDependencySource

    if ($null -eq $DependencySource) {
        throw (
            "Keine requirements.txt, requirements.lock oder " +
            "pyproject.toml für das Backend gefunden."
        )
    }

    switch ($DependencySource.Type) {
        "requirements" {
            Invoke-External `
                -Command "python" `
                -Arguments @(
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    $DependencySource.Path
                )
        }

        "pyproject" {
            $PackageDirectory = Split-Path `
                -Parent `
                $DependencySource.Path

            Invoke-External `
                -Command "python" `
                -Arguments @(
                    "-m",
                    "pip",
                    "install",
                    "-e",
                    "."
                ) `
                -WorkingDirectory $PackageDirectory
        }

        default {
            throw (
                "Unbekannter Abhängigkeitstyp: " +
                $DependencySource.Type
            )
        }
    }
}

# ============================================================
# Dateivalidierung
# ============================================================

function Invoke-PythonFileValidator {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [System.IO.FileInfo[]]$Files,

        [Parameter(Mandatory)]
        [string]$PythonCode,

        [int]$BatchSize = 50
    )

    if ($Files.Count -eq 0) {
        Write-Host "Keine passenden Dateien gefunden."
        return
    }

    Invoke-FileBatch `
        -Files $Files `
        -BatchSize $BatchSize `
        -Action {
            param($Batch)

            $Arguments = @(
                "-c",
                $PythonCode
            ) + @(
                $Batch |
                ForEach-Object {
                    $_.FullName
                }
            )

            Invoke-External `
                -Command "python" `
                -Arguments $Arguments
        }
}

# ============================================================
# Berichtserstellung
# ============================================================

function Save-PipelineReport {
    [CmdletBinding()]
    param()

    $PipelineEndTime = Get-Date

    $PipelineState.FinishedAt = $PipelineEndTime.ToString("o")

    $PipelineState.DurationSeconds = [Math]::Round(
        ($PipelineEndTime - $PipelineStartTime).TotalSeconds,
        3
    )

    $PipelineState.PassedCount = @(
        $StepLog |
        Where-Object Status -eq "Passed"
    ).Count

    $PipelineState.FailedCount = @(
        $StepLog |
        Where-Object Status -eq "Failed"
    ).Count

    $PipelineState.SkippedCount = @(
        $StepLog |
        Where-Object Status -eq "Skipped"
    ).Count

    $PipelineState.WarningCount = @(
        $StepLog |
        Where-Object Status -eq "Warning"
    ).Count

    $PipelineState.Success = (
        $PipelineState.FailedCount -eq 0 -and
        $null -eq $UnexpectedError
    )

    if ($UnexpectedError) {
        $PipelineState["UnexpectedError"] = $UnexpectedError
    }

    $PipelineState |
        ConvertTo-Json -Depth 10 |
        Set-Content `
            -LiteralPath $JsonLogFile `
            -Encoding UTF8
}

function Write-PipelineSummary {
    [CmdletBinding()]
    param()

    Write-Section "Zusammenfassung"

    Write-Host (
        "Erfolgreich:    {0}" -f
        $PipelineState.PassedCount
    ) -ForegroundColor Green

    Write-Host (
        "Fehlgeschlagen: {0}" -f
        $PipelineState.FailedCount
    ) -ForegroundColor Red

    Write-Host (
        "Warnungen:      {0}" -f
        $PipelineState.WarningCount
    ) -ForegroundColor Yellow

    Write-Host (
        "Übersprungen:   {0}" -f
        $PipelineState.SkippedCount
    ) -ForegroundColor Yellow

    foreach (
        $Status in @(
            "Passed",
            "Warning",
            "Skipped",
            "Failed"
        )
    ) {
        $Entries = @(
            $StepLog |
            Where-Object Status -eq $Status
        )

        if ($Entries.Count -eq 0) {
            continue
        }

        $Color = switch ($Status) {
            "Passed" {
                "Green"
            }

            "Warning" {
                "Yellow"
            }

            "Skipped" {
                "Yellow"
            }

            "Failed" {
                "Red"
            }
        }

        $Marker = switch ($Status) {
            "Passed" {
                "OK"
            }

            "Warning" {
                "!"
            }

            "Skipped" {
                "--"
            }

            "Failed" {
                "X"
            }
        }

        Write-Host ""
        Write-Host "$Status-Schritte:" -ForegroundColor $Color

        foreach ($Entry in $Entries) {
            $Line = (
                "  [{0}] {1} ({2:N2}s)" -f
                $Marker,
                $Entry.Name,
                $Entry.DurationSeconds
            )

            Write-Host $Line -ForegroundColor $Color

            if ($Entry.Message) {
                Write-Host (
                    "       $($Entry.Message)"
                ) -ForegroundColor DarkGray
            }
        }
    }

    Write-Host ""
    Write-Host "Textprotokoll: $LogFile"
    Write-Host "JSON-Bericht:  $JsonLogFile"
    Write-Host "TODO-Bericht:  $TodoReport"
    Write-Host (
        "Dauer:         {0:N2}s" -f
        $PipelineState.DurationSeconds
    )
}

# ============================================================
# Pipeline
# ============================================================

try {
    Start-Transcript `
        -Path $LogFile `
        -Force |
        Out-Null

    $TranscriptStarted = $true

    Write-Host ""
    Write-Host (
        "Kernschmied Quality Pipeline"
    ) -ForegroundColor Magenta

    Write-Host "Projekt:       $ProjectRoot"
    Write-Host "Protokoll:     $LogFile"
    Write-Host "JSON-Bericht:  $JsonLogFile"
    Write-Host (
        "Start:         {0}" -f
        $PipelineStartTime.ToString("dd.MM.yyyy HH:mm:ss")
    )

    if ($SkipFixes) {
        Write-Host (
            "Modus:         Nur prüfen, keine automatischen Fixes"
        ) -ForegroundColor Yellow
    }
    else {
        Write-Host "Modus:         Prüfen und automatisch korrigieren"
    }

    # ========================================================
    # 1. Grundvoraussetzungen
    # ========================================================

    Invoke-QualityStep `
        -Name "Grundvoraussetzungen prüfen" `
        -Action {
            $RequiredCommands = @(
                "python",
                "git",
                "node",
                "npm",
                "npx"
            )

            $MissingCommands = @(
                $RequiredCommands |
                Where-Object {
                    -not (Test-Executable $_)
                }
            )

            if ($MissingCommands.Count -gt 0) {
                throw (
                    "Fehlende Programme: " +
                    ($MissingCommands -join ", ")
                )
            }

            Invoke-External "python" @("--version")
            Invoke-External "node" @("--version")
            Invoke-External "npm" @("--version")
            Invoke-External "git" @("--version")

            Write-Host ""
            Write-Host "PowerShell: $($PSVersionTable.PSVersion)"
            Write-Host "Python:     $((Get-Command python).Source)"
            Write-Host "Node:       $((Get-Command node).Source)"
            Write-Host "NPM:        $((Get-Command npm).Source)"
        } |
        Out-Null

    # ========================================================
    # 2. Abhängigkeiten installieren
    # ========================================================

    if ($InstallDependencies) {
        if (Test-Path -LiteralPath $BackendDirectory) {
            Invoke-QualityStep `
                -Name "Backend-Abhängigkeiten installieren" `
                -Action {
                    Install-BackendDependencies
                } |
                Out-Null
        }
        else {
            Skip-QualityStep `
                -Name "Backend-Abhängigkeiten installieren" `
                -Reason "Backend-Verzeichnis wurde nicht gefunden."
        }

        $FrontendPackageJson = Join-Path `
            $FrontendDirectory `
            "package.json"

        $FrontendPackageLock = Join-Path `
            $FrontendDirectory `
            "package-lock.json"

        if (Test-Path -LiteralPath $FrontendPackageLock) {
            Invoke-QualityStep `
                -Name "Frontend-Abhängigkeiten installieren" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "ci",
                            "--ignore-scripts"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
        elseif (
            (Test-Path -LiteralPath $FrontendPackageJson) -and
            $AllowUnlockedNpmInstall
        ) {
            Invoke-QualityStep `
                -Name "Frontend-Abhängigkeiten ohne Lockdatei installieren" `
                -WarningOnly `
                -Action {
                    Write-Warning (
                        "Keine package-lock.json vorhanden. " +
                        "npm install kann die Abhängigkeitsauflösung " +
                        "und das Arbeitsverzeichnis verändern."
                    )

                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "install",
                            "--ignore-scripts"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
        elseif (Test-Path -LiteralPath $FrontendPackageJson) {
            Skip-QualityStep `
                -Name "Frontend-Abhängigkeiten installieren" `
                -Reason (
                    "package.json ist vorhanden, aber package-lock.json " +
                    "fehlt. Verwende bei Bedarf ausdrücklich " +
                    "-AllowUnlockedNpmInstall."
                )
        }
        else {
            Skip-QualityStep `
                -Name "Frontend-Abhängigkeiten installieren" `
                -Reason "Keine frontend\package.json vorhanden."
        }
    }

    # ========================================================
    # 3. Ruff
    # ========================================================

    if (Test-Executable "ruff") {
        if ($SkipFixes) {
            Skip-QualityStep `
                -Name "Ruff: Python formatieren" `
                -Reason "Durch -SkipFixes deaktiviert."

            Skip-QualityStep `
                -Name "Ruff: sichere Auto-Fixes" `
                -Reason "Durch -SkipFixes deaktiviert."
        }
        else {
            Invoke-QualityStep `
                -Name "Ruff: Python formatieren" `
                -Action {
                    Invoke-External "ruff" @(
                        "format",
                        "."
                    )
                } |
                Out-Null

            Invoke-QualityStep `
                -Name "Ruff: sichere Auto-Fixes" `
                -Action {
                    Invoke-External "ruff" @(
                        "check",
                        ".",
                        "--fix"
                    )
                } |
                Out-Null
        }
    }
    else {
        Skip-QualityStep `
            -Name "Ruff" `
            -Reason "Ruff wurde nicht gefunden."
    }

    # ========================================================
    # 4. Black-Kompatibilität
    # ========================================================

    if (Test-Executable "black") {
        Invoke-QualityStep `
            -Name "Black-Kompatibilität prüfen" `
            -WarningOnly `
            -Action {
                Invoke-External "black" @(
                    "--check",
                    "."
                )
            } |
            Out-Null
    }
    else {
        Skip-QualityStep `
            -Name "Black-Kompatibilität" `
            -Reason "Black wurde nicht gefunden."
    }

    # ========================================================
    # 5. Prettier
    # ========================================================

    if (Test-LocalNodeCommand "prettier") {
        if ($SkipFixes) {
            Skip-QualityStep `
                -Name "Prettier: Projekt formatieren" `
                -Reason "Durch -SkipFixes deaktiviert."
        }
        else {
            Invoke-QualityStep `
                -Name "Prettier: Projekt formatieren" `
                -Action {
                    Invoke-Npx @(
                        "prettier",
                        ".",
                        "--write"
                    )
                } |
                Out-Null
        }

        Invoke-QualityStep `
            -Name "Prettier: Formatierung prüfen" `
            -Action {
                Invoke-Npx @(
                    "prettier",
                    ".",
                    "--check"
                )
            } |
            Out-Null
    }
    else {
        Skip-QualityStep `
            -Name "Prettier" `
            -Reason (
                "Prettier ist nicht lokal installiert. " +
                "Installiere es beispielsweise mit: " +
                "npm install --save-dev prettier"
            )
    }

    # ========================================================
    # 6. Markdown und Wiki
    # ========================================================

    $MarkdownFiles = @(
        Get-ProjectFiles @(
            ".md",
            ".mdx"
        )
    )

    if ($SkipDocumentation) {
        Skip-QualityStep `
            -Name "Dokumentationsprüfung" `
            -Reason "Durch -SkipDocumentation deaktiviert."
    }
    elseif ($MarkdownFiles.Count -eq 0) {
        Skip-QualityStep `
            -Name "Markdownlint" `
            -Reason "Keine Markdown-Dateien gefunden."
    }
    else {
        if (Test-LocalNodeCommand "markdownlint-cli2") {
            if ($SkipFixes) {
                Skip-QualityStep `
                    -Name "Markdownlint: Auto-Fix" `
                    -Reason "Durch -SkipFixes deaktiviert."
            }
            else {
                Invoke-QualityStep `
                    -Name "Markdownlint: Auto-Fix" `
                    -Action {
                        Invoke-FileBatch `
                            -Files $MarkdownFiles `
                            -BatchSize 40 `
                            -Action {
                                param($Batch)

                                Invoke-Npx (
                                    @(
                                        "markdownlint-cli2",
                                        "--fix"
                                    ) + @(
                                        $Batch |
                                        ForEach-Object FullName
                                    )
                                )
                            }
                    } |
                    Out-Null
            }

            Invoke-QualityStep `
                -Name "Markdownlint: Abschlussprüfung" `
                -Action {
                    Invoke-FileBatch `
                        -Files $MarkdownFiles `
                        -BatchSize 40 `
                        -Action {
                            param($Batch)

                            Invoke-Npx (
                                @(
                                    "markdownlint-cli2"
                                ) + @(
                                    $Batch |
                                    ForEach-Object FullName
                                )
                            )
                        }
                } |
                Out-Null
        }
        else {
            Skip-QualityStep `
                -Name "Markdownlint" `
                -Reason (
                    "markdownlint-cli2 ist nicht lokal installiert. " +
                    "Installiere es beispielsweise mit: " +
                    "npm install --save-dev markdownlint-cli2"
                )
        }

        if ($SkipLinks) {
            Skip-QualityStep `
                -Name "Lychee-Linkprüfung" `
                -Reason "Durch -SkipLinks deaktiviert."
        }
        elseif (-not (Test-Executable "lychee")) {
            Skip-QualityStep `
                -Name "Lychee-Linkprüfung" `
                -Reason "Lychee wurde nicht gefunden."
        }
        else {
            Invoke-QualityStep `
                -Name "Lychee: Links prüfen" `
                -Action {
                    Invoke-FileBatch `
                        -Files $MarkdownFiles `
                        -BatchSize 30 `
                        -Action {
                            param($Batch)

                            Invoke-External `
                                -Command "lychee" `
                                -Arguments (
                                    @(
                                        "--no-progress"
                                    ) + @(
                                        $Batch |
                                        ForEach-Object FullName
                                    )
                                )
                        }
                } |
                Out-Null
        }

        $ValeConfigCandidates = @(
            ".vale.ini",
            "vale.ini",
            ".vale.yaml",
            ".vale.yml"
        ) |
        ForEach-Object {
            Join-Path $ProjectRoot $_
        }

        $ValeConfigExists = @(
            $ValeConfigCandidates |
            Where-Object {
                Test-Path -LiteralPath $_
            }
        ).Count -gt 0

        if (
            (Test-Executable "vale") -and
            $ValeConfigExists -and
            (Test-Path -LiteralPath $WikiDirectory)
        ) {
            $ValeParameters = @{
                Name   = "Vale: Dokumentationsstil prüfen"
                Action = {
                    Invoke-External "vale" @(
                        $WikiDirectory
                    )
                }
            }

            if (-not $StrictDocumentation) {
                $ValeParameters.WarningOnly = $true
            }

            Invoke-QualityStep @ValeParameters |
                Out-Null
        }
        else {
            Skip-QualityStep `
                -Name "Vale" `
                -Reason (
                    "Vale, Vale-Konfiguration oder Wiki-Verzeichnis " +
                    "wurde nicht gefunden."
                )
        }
    }

    # ========================================================
    # 7. JSON
    # ========================================================

    $JsonFiles = @(
        Get-ProjectFiles @(".json")
    )

    Invoke-QualityStep `
        -Name "JSON-Dateien validieren" `
        -Action {
            $Code = @'
import json
import pathlib
import sys

errors = []

for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)

    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            json.load(stream)
    except Exception as exc:
        errors.append(f"{path}: {exc}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)

print(f"{len(sys.argv) - 1} JSON-Dateien sind gültig.")
'@

            Invoke-PythonFileValidator `
                -Files $JsonFiles `
                -PythonCode $Code
        } |
        Out-Null

    # ========================================================
    # 8. TOML
    # ========================================================

    $TomlFiles = @(
        Get-ProjectFiles @(".toml")
    )

    Invoke-QualityStep `
        -Name "TOML-Dateien validieren" `
        -Action {
            $Code = @'
import pathlib
import sys
import tomllib

errors = []

for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)

    try:
        with path.open("rb") as stream:
            tomllib.load(stream)
    except Exception as exc:
        errors.append(f"{path}: {exc}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)

print(f"{len(sys.argv) - 1} TOML-Dateien sind gültig.")
'@

            Invoke-PythonFileValidator `
                -Files $TomlFiles `
                -PythonCode $Code
        } |
        Out-Null

    # ========================================================
    # 9. YAML
    # ========================================================

    $YamlFiles = @(
        Get-ProjectFiles @(
            ".yaml",
            ".yml"
        )
    )

    if (Test-PythonModule "yaml") {
        Invoke-QualityStep `
            -Name "YAML-Dateien validieren" `
            -Action {
                $Code = @'
import pathlib
import sys
import yaml

errors = []

for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)

    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            yaml.safe_load(stream)
    except Exception as exc:
        errors.append(f"{path}: {exc}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)

print(f"{len(sys.argv) - 1} YAML-Dateien sind gültig.")
'@

                Invoke-PythonFileValidator `
                    -Files $YamlFiles `
                    -PythonCode $Code
            } |
            Out-Null
    }
    else {
        Skip-QualityStep `
            -Name "YAML-Validierung" `
            -Reason "PyYAML ist nicht installiert."
    }

    # ========================================================
    # 10. Python-Kompilierung
    # ========================================================

    if (Test-Path -LiteralPath $BackendDirectory) {
        Invoke-QualityStep `
            -Name "Python: Backend kompilieren" `
            -Action {
                Invoke-External "python" @(
                    "-m",
                    "compileall",
                    "-q",
                    $BackendDirectory
                )
            } |
            Out-Null
    }
    else {
        Skip-QualityStep `
            -Name "Python-Kompilierung" `
            -Reason "Backend-Verzeichnis wurde nicht gefunden."
    }

    # ========================================================
    # 11. FastAPI und OpenAPI
    # ========================================================

    $BackendMain = Join-Path $BackendDirectory "main.py"

    if (Test-Path -LiteralPath $BackendMain) {
        Invoke-QualityStep `
            -Name "FastAPI-Import und OpenAPI prüfen" `
            -Action {
                $Code = @'
from main import app

schema = app.openapi()

assert isinstance(schema, dict)
assert schema.get("openapi")
assert schema.get("info")
assert isinstance(schema.get("paths"), dict)

print("OpenAPI:", schema["openapi"])
print("Titel:", schema["info"].get("title"))
print("Pfade:", len(schema["paths"]))
'@

                Invoke-External `
                    -Command "python" `
                    -Arguments @(
                        "-c",
                        $Code
                    ) `
                    -WorkingDirectory $BackendDirectory
            } |
            Out-Null
    }
    else {
        Skip-QualityStep `
            -Name "FastAPI/OpenAPI" `
            -Reason "backend\main.py wurde nicht gefunden."
    }

    # ========================================================
    # 12. Mypy
    # ========================================================

    if (Test-PythonModule "mypy") {
        Invoke-QualityStep `
            -Name "Mypy: Typprüfung" `
            -Action {
                Invoke-External "python" @(
                    "-m",
                    "mypy",
                    $BackendDirectory
                )
            } |
            Out-Null
    }
    else {
        Skip-QualityStep `
            -Name "Mypy" `
            -Reason "Mypy ist nicht installiert."
    }

    # ========================================================
    # 13. Pip check
    # ========================================================

    Invoke-QualityStep `
        -Name "Pip: Abhängigkeiten prüfen" `
        -Action {
            Invoke-External "python" @(
                "-m",
                "pip",
                "check"
            )
        } |
        Out-Null

    # ========================================================
    # 14. Sicherheit
    # ========================================================

    if ($SkipSecurity) {
        Skip-QualityStep `
            -Name "Python-Sicherheitsprüfungen" `
            -Reason "Durch -SkipSecurity deaktiviert."
    }
    else {
        if (Test-PythonModule "pip_audit") {
            Invoke-QualityStep `
                -Name "Pip-Audit: Schwachstellen prüfen" `
                -WarningOnly `
                -Action {
                    Invoke-External "python" @(
                        "-m",
                        "pip_audit",
                        "--progress-spinner",
                        "off"
                    )
                } |
                Out-Null
        }
        else {
            Skip-QualityStep `
                -Name "Pip-Audit" `
                -Reason "pip-audit ist nicht installiert."
        }

        if (Test-PythonModule "bandit") {
            Invoke-QualityStep `
                -Name "Bandit: Sicherheitsanalyse" `
                -Action {
                    $BanditArguments = @(
                        "-m",
                        "bandit",
                        "-r",
                        $BackendDirectory,
                        "-q"
                    )

                    $BanditExcludes = @(
                        (Join-Path $BackendDirectory "tests"),
                        (Join-Path $BackendDirectory "__pycache__")
                    ) |
                    Where-Object {
                        Test-Path -LiteralPath $_
                    }

                    if ($BanditExcludes.Count -gt 0) {
                        $BanditArguments += @(
                            "-x",
                            ($BanditExcludes -join ",")
                        )
                    }

                    Invoke-External `
                        -Command "python" `
                        -Arguments $BanditArguments
                } |
                Out-Null
        }
        else {
            Skip-QualityStep `
                -Name "Bandit" `
                -Reason "Bandit ist nicht installiert."
        }
    }

    # ========================================================
    # 15. Python-Tests
    # ========================================================

    if ($SkipTests) {
        Skip-QualityStep `
            -Name "Python-Tests" `
            -Reason "Durch -SkipTests deaktiviert."
    }
    elseif (Test-PythonModule "pytest") {
        Invoke-QualityStep `
            -Name "Pytest: Backend-Tests" `
            -Action {
                Invoke-External "python" @(
                    "-m",
                    "pytest",
                    "-ra",
                    "--strict-markers",
                    "--strict-config"
                )
            } |
            Out-Null
    }
    else {
        Skip-QualityStep `
            -Name "Pytest" `
            -Reason "Pytest ist nicht installiert."
    }

    # ========================================================
    # 16. Frontend
    # ========================================================

    $FrontendPackageJson = Join-Path `
        $FrontendDirectory `
        "package.json"

    if (Test-Path -LiteralPath $FrontendPackageJson) {
        $FrontendScripts = @(
            Get-NpmScripts $FrontendPackageJson
        )

        # ----------------------------------------------------
        # ESLint Auto-Fix
        # ----------------------------------------------------

        if ($SkipFixes) {
            Skip-QualityStep `
                -Name "ESLint: Auto-Fix" `
                -Reason "Durch -SkipFixes deaktiviert."
        }
        elseif (Test-NpmScript $FrontendScripts "lint:fix") {
            Invoke-QualityStep `
                -Name "ESLint: Auto-Fix" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "lint:fix"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
        elseif (Test-NpmScript $FrontendScripts "lint") {
            Invoke-QualityStep `
                -Name "ESLint: Auto-Fix" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "lint",
                            "--",
                            "--fix"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
        else {
            Skip-QualityStep `
                -Name "ESLint Auto-Fix" `
                -Reason "Kein lint- oder lint:fix-Skript vorhanden."
        }

        # ----------------------------------------------------
        # ESLint Prüfung
        # ----------------------------------------------------

        if (Test-NpmScript $FrontendScripts "lint") {
            Invoke-QualityStep `
                -Name "ESLint: Abschlussprüfung" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "lint"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
        else {
            Skip-QualityStep `
                -Name "ESLint-Prüfung" `
                -Reason "Kein lint-Skript vorhanden."
        }

        # ----------------------------------------------------
        # TypeScript
        # ----------------------------------------------------

        if (Test-NpmScript $FrontendScripts "typecheck") {
            Invoke-QualityStep `
                -Name "TypeScript: Typprüfung" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "typecheck"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
        elseif (
            Test-Path -LiteralPath (
                Join-Path $FrontendDirectory "tsconfig.json"
            )
        ) {
            if (Test-LocalNodeCommand `
                -Command "tsc" `
                -WorkingDirectory $FrontendDirectory
            ) {
                Invoke-QualityStep `
                    -Name "TypeScript: Typprüfung" `
                    -Action {
                        Invoke-Npx `
                            -Arguments @(
                                "tsc",
                                "--noEmit"
                            ) `
                            -WorkingDirectory $FrontendDirectory
                    } |
                    Out-Null
            }
            else {
                Skip-QualityStep `
                    -Name "TypeScript-Typprüfung" `
                    -Reason (
                        "TypeScript ist nicht lokal installiert und " +
                        "kein typecheck-Skript ist vorhanden."
                    )
            }
        }
        else {
            Skip-QualityStep `
                -Name "TypeScript-Typprüfung" `
                -Reason (
                    "Kein typecheck-Skript und keine " +
                    "tsconfig.json vorhanden."
                )
        }

        # ----------------------------------------------------
        # Frontend-Tests
        # ----------------------------------------------------

        if ($SkipTests) {
            Skip-QualityStep `
                -Name "Frontend-Tests" `
                -Reason "Durch -SkipTests deaktiviert."
        }
        elseif (Test-NpmScript $FrontendScripts "test:run") {
            Invoke-QualityStep `
                -Name "Frontend: Tests" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "test:run"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
        elseif (Test-NpmScript $FrontendScripts "test") {
            Invoke-QualityStep `
                -Name "Frontend: Tests" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "test",
                            "--",
                            "--run"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
        else {
            Skip-QualityStep `
                -Name "Frontend-Tests" `
                -Reason "Kein test- oder test:run-Skript vorhanden."
        }

        # ----------------------------------------------------
        # Frontend-Build
        # ----------------------------------------------------

        if ($SkipBuild) {
            Skip-QualityStep `
                -Name "Frontend-Build" `
                -Reason "Durch -SkipBuild deaktiviert."
        }
        elseif (Test-NpmScript $FrontendScripts "build") {
            Invoke-QualityStep `
                -Name "Frontend: Produktions-Build" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "build"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
        else {
            Skip-QualityStep `
                -Name "Frontend-Build" `
                -Reason "Kein build-Skript vorhanden."
        }

        # ----------------------------------------------------
        # NPM Audit
        # ----------------------------------------------------

        if ($SkipSecurity) {
            Skip-QualityStep `
                -Name "NPM Audit" `
                -Reason "Durch -SkipSecurity deaktiviert."
        }
        else {
            Invoke-QualityStep `
                -Name "NPM Audit: Schwachstellen prüfen" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "audit",
                            "--audit-level=high"
                        ) `
                        -WorkingDirectory $FrontendDirectory
                } |
                Out-Null
        }
    }
    else {
        Skip-QualityStep `
            -Name "Frontend-Prüfungen" `
            -Reason "frontend\package.json wurde nicht gefunden."
    }

    # ========================================================
    # 17. PSScriptAnalyzer
    # ========================================================

    if (
        Get-Module `
            -ListAvailable `
            -Name PSScriptAnalyzer
    ) {
        $PowerShellAnalyzerParameters = @{
            Name   = "PSScriptAnalyzer: PowerShell prüfen"
            Action = {
                $Results = @(
                    Invoke-ScriptAnalyzer `
                        -Path $ScriptDirectory `
                        -Recurse `
                        -Severity @(
                            "Error",
                            "Warning"
                        )
                )

                if ($Results.Count -gt 0) {
                    $Results |
                        Select-Object `
                            RuleName,
                            Severity,
                            ScriptName,
                            Line,
                            Message |
                        Format-Table `
                            -AutoSize |
                        Out-Host

                    throw (
                        "$($Results.Count) PowerShell-Probleme gefunden."
                    )
                }

                Write-Host (
                    "Keine PowerShell-Probleme gefunden."
                )
            }
        }

        if (-not $StrictPowerShell) {
            $PowerShellAnalyzerParameters.WarningOnly = $true
        }

        Invoke-QualityStep @PowerShellAnalyzerParameters |
            Out-Null
    }
    else {
        Skip-QualityStep `
            -Name "PSScriptAnalyzer" `
            -Reason (
                "PSScriptAnalyzer ist nicht installiert. " +
                "Installation: Install-Module PSScriptAnalyzer " +
                "-Scope CurrentUser"
            )
    }

    # ========================================================
    # 18. TODO-/FIXME-Bericht
    # ========================================================

    Invoke-QualityStep `
        -Name "TODO- und FIXME-Bericht erstellen" `
        -Action {
            $RelevantFiles = @(
                Get-ProjectFiles @(
                    ".py",
                    ".pyi",
                    ".ts",
                    ".tsx",
                    ".js",
                    ".jsx",
                    ".json",
                    ".css",
                    ".scss",
                    ".md",
                    ".mdx",
                    ".yaml",
                    ".yml",
                    ".toml",
                    ".ps1"
                )
            )

            $Matches = @(
                $RelevantFiles |
                Select-String `
                    -Pattern (
                        "TODO|FIXME|HACK|XXX|" +
                        "PLACEHOLDER|NOT IMPLEMENTED"
                    ) `
                    -CaseSensitive:$false
            )

            $ReportLines = [System.Collections.Generic.List[string]]::new()

            $ReportLines.Add(
                "Kernschmied TODO-/FIXME-Bericht"
            )

            $ReportLines.Add(
                "Erstellt: $(Get-Date -Format 'dd.MM.yyyy HH:mm:ss')"
            )

            $ReportLines.Add(
                "Treffer: $($Matches.Count)"
            )

            $ReportLines.Add("")

            foreach ($Match in $Matches) {
                $ReportLines.Add(
                    (
                        "{0}:{1}: {2}" -f
                        $Match.Path,
                        $Match.LineNumber,
                        $Match.Line.Trim()
                    )
                )
            }

            $ReportLines |
                Set-Content `
                    -LiteralPath $TodoReport `
                    -Encoding UTF8

            Write-Host "$($Matches.Count) Hinweise gefunden."
            Write-Host "Bericht: $TodoReport"

            if (
                $FailOnTodo -and
                $Matches.Count -gt 0
            ) {
                throw (
                    "$($Matches.Count) TODO-/FIXME-Hinweise gefunden."
                )
            }
        } |
        Out-Null

    # ========================================================
    # 19. Git
    # ========================================================

    Invoke-QualityStep `
        -Name "Git: Arbeitsverzeichnis prüfen" `
        -Action {
            Invoke-External "git" @(
                "status",
                "--short"
            )

            Write-Host ""

            Invoke-External "git" @(
                "diff",
                "--stat"
            )

            Write-Host ""

            Write-Host (
                "Prüfe nicht gestagte Änderungen auf Whitespace-Fehler."
            )

            Invoke-External "git" @(
                "diff",
                "--check"
            )

            Write-Host ""

            Write-Host (
                "Prüfe gestagte Änderungen auf Whitespace-Fehler."
            )

            Invoke-External "git" @(
                "diff",
                "--cached",
                "--check"
            )
        } |
        Out-Null

    # ========================================================
    # 20. Finale Ruff-Prüfung
    # ========================================================

    if (Test-Executable "ruff") {
        Invoke-QualityStep `
            -Name "Ruff: finale Prüfung" `
            -Action {
                Invoke-External "ruff" @(
                    "format",
                    "--check",
                    "."
                )

                Invoke-External "ruff" @(
                    "check",
                    "."
                )
            } |
            Out-Null
    }
}
catch {
    $UnexpectedError = $_.Exception.Message

    Write-Host ""
    Write-Host (
        "Unerwarteter Pipelinefehler: $UnexpectedError"
    ) -ForegroundColor Red
}
finally {
    try {
        Save-PipelineReport
        Write-PipelineSummary
    }
    catch {
        Write-Host (
            "Der Abschlussbericht konnte nicht vollständig " +
            "erstellt werden: $($_.Exception.Message)"
        ) -ForegroundColor Red
    }

    if ($TranscriptStarted) {
        try {
            Stop-Transcript | Out-Null
        }
        catch {
            # Kein weiterer Fehler während des Aufräumens.
        }
    }

    Set-Location $OriginalLocation
}

if (
    $PipelineState.FailedCount -gt 0 -or
    $null -ne $UnexpectedError
) {
    Write-Host ""
    Write-Host (
        "Die Qualitätsprüfung enthält Fehler."
    ) -ForegroundColor Red

    exit 1
}

Write-Host ""
Write-Host (
    "Alle ausgeführten Qualitätsprüfungen waren erfolgreich."
) -ForegroundColor Green

exit 0