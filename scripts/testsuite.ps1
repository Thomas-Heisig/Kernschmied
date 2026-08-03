<#

.SYNOPSIS
Führt die vollständige Kernschmied-Testsuite aus.

.DESCRIPTION
Formatiert, prüft und analysiert das Kernschmied-Projekt.

Die Testsuite erzeugt:

- ein vollständiges Textprotokoll,
- einen strukturierten JSON-Bericht,
- einen Bericht mit echten TODO-/FIXME-Hinweisen,
- einen automatisch generierten Arbeits-Prompt für ein lokales KI-Modell.

Der Arbeits-Prompt enthält:

- die fehlgeschlagenen Schritte,
- Warnungen,
- konkrete Werkzeugausgaben,
- Priorisierung,
- Regeln gegen Halluzinationen,
- Anweisungen für Diagnose und Reparatur.

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

.PARAMETER SkipFixes
Führt nur Prüfungen aus und verändert keine Dateien.

.PARAMETER InstallDependencies
Installiert Backend- und Frontend-Abhängigkeiten vor dem Lauf.

.PARAMETER AllowUnlockedNpmInstall
Erlaubt npm install, wenn keine package-lock.json vorhanden ist.

.PARAMETER FailOnTodo
Bewertet gefundene TODO-/FIXME-Hinweise als Fehler.

.PARAMETER FailFast
Bricht beim ersten echten Fehler ab.

.PARAMETER StrictPowerShell
Bewertet PSScriptAnalyzer-Warnungen als Fehler.

.PARAMETER StrictDocumentation
Bewertet Vale-Warnungen als Fehler.

.PARAMETER StrictNoTests
Bewertet Pytest-Exitcode 5 als Fehler.

.PARAMETER MaxPromptOutputLines
Maximale Anzahl Werkzeugausgabezeilen pro Schritt im Arbeits-Prompt.

.PARAMETER MaxFailureMessageLines
Maximale Anzahl Werkzeugausgabezeilen in einer Konsolen-Fehlermeldung.

.EXAMPLE
.\scripts\testsuite.ps1

.EXAMPLE
.\scripts\testsuite.ps1 -SkipFixes

.EXAMPLE
.\scripts\testsuite.ps1 -InstallDependencies

.EXAMPLE
.\scripts\testsuite.ps1 -FailFast -FailOnTodo -StrictPowerShell

.EXAMPLE
Get-Help .\scripts\testsuite.ps1 -Detailed
#>

[CmdletBinding()]
param(
    [switch]$SkipSecurity,
    [switch]$SkipTests,
    [switch]$SkipBuild,
    [switch]$SkipLinks,
    [switch]$SkipDocumentation,
    [switch]$SkipFixes,
    [switch]$InstallDependencies,
    [switch]$AllowUnlockedNpmInstall,
    [switch]$FailOnTodo,
    [switch]$FailFast,
    [switch]$StrictPowerShell,
    [switch]$StrictDocumentation,
    [switch]$StrictNoTests,

    [ValidateRange(20, 1000)]
    [int]$MaxPromptOutputLines = 120,

    [ValidateRange(0, 100)]
    [int]$MaxFailureMessageLines = 15
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Utf8Encoding = [System.Text.UTF8Encoding]::new($false)

[Console]::InputEncoding = $Utf8Encoding
[Console]::OutputEncoding = $Utf8Encoding
$OutputEncoding = $Utf8Encoding

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO = "0"

$env:NODE_OPTIONS = (
    @(
        $env:NODE_OPTIONS
        "--no-warnings"
    ) |
    Where-Object {
        -not [string]::IsNullOrWhiteSpace($_)
    }
) -join " "

if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

# Plattform-Flag robust bestimmen (funktioniert in PS Core und Windows PowerShell)
# Verwende eine eigene Variable, um keine automatische Variable zu überschreiben.
if (-not (Test-Path variable:IsWindowsPlatform)) {
    try {
        $existing = Get-Variable -Name IsWindows -ErrorAction SilentlyContinue
        if ($null -ne $existing) {
            $IsWindowsPlatform = [bool]$existing.Value
        }
        else {
            $IsWindowsPlatform = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)
        }
    }
    catch {
        $IsWindowsPlatform = $env:OS -eq 'Windows_NT'
    }
}

# ============================================================
# Laufzeit und Pfade
# ============================================================

$SuiteStartTime = Get-Date
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
$DocsDirectory = Join-Path $ProjectRoot "docs"

$ArtifactDirectory = Join-Path $ProjectRoot "artifacts\testsuite"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

$TranscriptFile = Join-Path `
    $ArtifactDirectory `
    "testsuite-$Timestamp.log"

$JsonReportFile = Join-Path `
    $ArtifactDirectory `
    "testsuite-$Timestamp.json"

$TodoReportFile = Join-Path `
    $ArtifactDirectory `
    "action-items-$Timestamp.txt"

$WorkPromptFile = Join-Path `
    $ArtifactDirectory `
    "work-prompt-$Timestamp.md"

$StepOutputDirectory = Join-Path `
    $ArtifactDirectory `
    "step-output-$Timestamp"

$WikiMarkdownConfigFile = Join-Path `
    $ArtifactDirectory `
    "wiki.markdownlint-cli2.jsonc"

$PipAuditReportFile = Join-Path `
    $ArtifactDirectory `
    "pip-audit-$Timestamp.json"

$BanditReportFile = Join-Path `
    $ArtifactDirectory `
    "bandit-$Timestamp.json"

New-Item `
    -ItemType Directory `
    -Path $ArtifactDirectory `
    -Force |
    Out-Null

New-Item `
    -ItemType Directory `
    -Path $StepOutputDirectory `
    -Force |
    Out-Null

$WikiMarkdownConfiguration = @'
{
  "config": {
    "default": true,
    "MD025": false,
    "MD036": false,
    "MD040": false
  },
  "ignores": [
    "**/node_modules/**",
    "**/artifacts/**",
    "**/.git/**"
  ]
}
'@

$WikiMarkdownConfiguration |
    Set-Content `
        -LiteralPath $WikiMarkdownConfigFile `
        -Encoding UTF8

Set-Location $ProjectRoot

# ------------------------------------------------------------
# Prüfe auf erforderliche CLI-Tools und frage nach Installation
# ------------------------------------------------------------
function Test-CommandExists {
    param(
        [Parameter(Mandatory)] [string]$CommandName
    )

    return (Get-Command $CommandName -ErrorAction SilentlyContinue) -ne $null
}

function Prompt-YesNo {
    param(
        [Parameter(Mandatory)] [string]$Message,
        [bool]$DefaultYes = $false,
        [int]$TimeoutSeconds = 5
    )

    $default = if ($DefaultYes) { 'Y' } else { 'N' }
    Write-Host "$Message [Y/n] (default: $default, timeout: ${TimeoutSeconds}s)"

    # Prefer non-blocking key read when available (console hosts). Fall back to Read-Host without timeout.
    try {
        $input = ''
        $endTime = (Get-Date).AddSeconds($TimeoutSeconds)
        while ((Get-Date) -lt $endTime) {
            if ([System.Console]::KeyAvailable) {
                $keyInfo = [System.Console]::ReadKey($true)
                $input = $keyInfo.KeyChar
                break
            }
            Start-Sleep -Milliseconds 100
        }

        if ([string]::IsNullOrWhiteSpace($input)) {
            return $DefaultYes
        }

        switch ($input.ToString().ToUpper()) {
            'Y' { return $true }
            'N' { return $false }
            default { return $DefaultYes }
        }
    }
    catch {
        # Fallback for hosts where Console.KeyAvailable is not supported (e.g. certain IDE hosts)
        $choice = Read-Host "$Message [Y/n] (default: $default)"
        if ([string]::IsNullOrWhiteSpace($choice)) { return $DefaultYes }
        switch ($choice.ToUpper()) {
            'Y' { return $true }
            'YES' { return $true }
            'N' { return $false }
            'NO' { return $false }
            default { return $DefaultYes }
        }
    }
}

function Ensure-RequiredTools {
    # Liste der Basis-Commands, die minimal erwartet werden
    $core = @(
        @{ Name='git'; Cmd='git' },
        @{ Name='python'; Cmd='python' },
        @{ Name='pip'; Cmd='pip' },
        @{ Name='node'; Cmd='node' },
        @{ Name='npm'; Cmd='npm' },
        @{ Name='npx'; Cmd='npx' }
    )

    $extra = @(
        @{ Name='tsc'; Cmd='tsc'; NpmPkg='typescript' },
        @{ Name='prettier'; Cmd='prettier'; NpmPkg='prettier' },
        @{ Name='markdownlint'; Cmd='markdownlint'; NpmPkg='markdownlint-cli2' },
        @{ Name='lychee'; Cmd='lychee'; NpmPkg='lychee' },
        @{ Name='ruff'; Cmd='ruff'; PipPkg='ruff' },
        @{ Name='bandit'; Cmd='bandit'; PipPkg='bandit' },
        @{ Name='pip-audit'; Cmd='pip-audit'; PipPkg='pip-audit' },
        @{ Name='mypy'; Cmd='mypy'; PipPkg='mypy' }
    )

    $missing = [System.Collections.Generic.List[object]]::new()

    foreach ($item in $core) {
        if (-not (Test-CommandExists $item.Cmd)) {
            $missing.Add($item)
        }
    }

    foreach ($item in $extra) {
        if (-not (Test-CommandExists $item.Cmd)) {
            $missing.Add($item)
        }
    }

    if ($missing.Count -eq 0) {
        Write-Host "Alle erforderlichen CLI-Tools sind installiert." -ForegroundColor Green
        return
    }

    Write-Host "Die folgenden benötigten Tools fehlen oder sind nicht im PATH:" -ForegroundColor Yellow
    foreach ($m in $missing) {
        Write-Host (" - {0}" -f $m.Name) -ForegroundColor Yellow
    }

    # Determine whether to perform non-interactive auto-install.
    $autoInstall = $false
    if ($PSBoundParameters.ContainsKey('InstallDependencies') -and $InstallDependencies) {
        $autoInstall = $true
    }

    if (-not $autoInstall) {
        if ($env:TESTSUITE_AUTO_INSTALL -eq '1') { $autoInstall = $true }
    }

    if (-not $autoInstall) {
        # Prompt with 5s timeout, default NO
        $userAccepted = Prompt-YesNo "Möchten Sie versuchen, die fehlenden Tools jetzt automatisch zu installieren?" $false 5
        if (-not $userAccepted) {
            Write-Host "Überspringe automatische Installation. Fortfahren mit der Testsuite..." -ForegroundColor DarkYellow
            return
        }
    }

    foreach ($m in $missing) {
        if ($m.PSObject.Properties.Name -contains 'NpmPkg') {
            if (-not (Test-CommandExists 'npm')) {
                Write-Host "npm nicht gefunden; überspringe Installation von $($m.NpmPkg)." -ForegroundColor Yellow
                continue
            }

            $cmd = "npm install -g $($m.NpmPkg)"
            Write-Host "Versuche Installation von $($m.NpmPkg) via npm (global): $cmd" -ForegroundColor Cyan
            try {
                # Use --no-fund and --no-audit to reduce interactive prompts from npm
                & npm install -g $($m.NpmPkg) --no-fund --no-audit 2>&1 | Write-Host
                Write-Host "Installation von $($m.NpmPkg) abgeschlossen." -ForegroundColor Green
            }
            catch {
                Write-Host "Fehler beim Installieren von $($m.NpmPkg) global: $_" -ForegroundColor Red
                # Fallback: try local install into frontend directory (if exists)
                if (Test-Path -LiteralPath $FrontendDirectory) {
                            # Try local install in project root first, then frontend
                            $localTargets = @($ProjectRoot, $FrontendDirectory) | Where-Object { Test-Path -LiteralPath $_ }

                            $installed = $false

                            foreach ($target in $localTargets) {
                                Write-Host "Versuche lokale Installation in $target..." -ForegroundColor Cyan
                                $attempt = 0
                                while ($attempt -lt 2 -and -not $installed) {
                                    try {
                                        $attempt++
                                        & npm install $($m.NpmPkg) --prefix $target --no-fund --no-audit 2>&1 | Write-Host
                                        $binPath = Join-Path $target 'node_modules\.bin'
                                        if (Test-Path -LiteralPath $binPath) {
                                            $env:PATH = "$binPath;$env:PATH"
                                            Write-Host "Lokale Installation erfolgreich; füge $binPath dem PATH hinzu." -ForegroundColor Green
                                        }
                                        else {
                                            Write-Host "Lokale Installation abgeschlossen, aber Bin-Verzeichnis nicht gefunden: $binPath" -ForegroundColor Yellow
                                        }
                                        $installed = $true
                                    }
                                    catch {
                                        Write-Host "Lokale Installation in $target fehlgeschlagen (Versuch $attempt): $_" -ForegroundColor Red
                                        Start-Sleep -Seconds 2
                                    }
                                }

                                if ($installed) { break }
                            }

                            if (-not $installed) {
                                Write-Host "Alle lokalen Installationsversuche fehlgeschlagen." -ForegroundColor Red
                                Write-Host "Sie können das Paket manuell installieren: npm install -g $($m.NpmPkg)" -ForegroundColor Yellow
                            }
                }
                else {
                    Write-Host "Frontend-Verzeichnis nicht gefunden; überspringe lokale Installation." -ForegroundColor Yellow
                    Write-Host "Sie können das Paket manuell installieren: npm install -g $($m.NpmPkg)" -ForegroundColor Yellow
                }
            }
        }
        else {
            if ($m.PSObject.Properties.Name -contains 'PipPkg') {
                if (-not (Test-CommandExists 'python')) {
                    Write-Host "Python nicht gefunden; überspringe Installation von $($m.PipPkg)." -ForegroundColor Yellow
                    continue
                }

                Write-Host "Versuche Installation von Python-Paket $($m.PipPkg) via pip (user): python -m pip install --user $($m.PipPkg)" -ForegroundColor Cyan
                try {
                    & python -m pip install --user --upgrade $($m.PipPkg) 2>&1 | Write-Host
                    Write-Host "Installation von $($m.PipPkg) abgeschlossen." -ForegroundColor Green
                }
                catch {
                    Write-Host "Fehler beim Installieren von $($m.PipPkg): $_" -ForegroundColor Red
                    Write-Host "Sie können das Paket manuell installieren: python -m pip install --user $($m.PipPkg)" -ForegroundColor Yellow
                }
            }
            else {
                switch ($m.Cmd) {
                    'pip' {
                        Write-Host "Versuche, pip zu aktualisieren..." -ForegroundColor Cyan
                        try { & python -m pip install --upgrade pip 2>&1 | Write-Host; Write-Host 'pip aktualisiert.' -ForegroundColor Green }
                        catch { Write-Host "pip-Aktualisierung fehlgeschlagen: $_" -ForegroundColor Red }
                    }
                    default {
                        Write-Host "Kein automatischer Installer für $($m.Name) hinterlegt. Bitte installieren Sie $($m.Name) manuell." -ForegroundColor Yellow
                    }
                }
            }
        }
    }

    Write-Host "Fertig mit Installationsversuchen. Bitte prüfen Sie PATH/Versionen und starten Sie die Testsuite ggf. erneut." -ForegroundColor Cyan
}

# Führe die Prüfung aus
Ensure-RequiredTools

# ============================================================
# Zustand
# ============================================================

$StepLog = [System.Collections.Generic.List[object]]::new()
$UnexpectedError = $null
$TranscriptStarted = $false

$CurrentCommandOutput = ""
$CurrentCommand = ""
$CurrentWorkingDirectory = ""

$SuiteState = [ordered]@{
    Name            = "Kernschmied Testsuite"
    ProjectRoot     = $ProjectRoot
    StartedAt       = $SuiteStartTime.ToString("o")
    FinishedAt      = $null
    DurationSeconds = $null
    Success         = $false
    PassedCount     = 0
    FailedCount     = 0
    WarningCount    = 0
    SkippedCount    = 0
    Parameters      = [ordered]@{
        SkipSecurity           = $SkipSecurity.IsPresent
        SkipTests              = $SkipTests.IsPresent
        SkipBuild              = $SkipBuild.IsPresent
        SkipLinks              = $SkipLinks.IsPresent
        SkipDocumentation      = $SkipDocumentation.IsPresent
        SkipFixes              = $SkipFixes.IsPresent
        InstallDependencies    = $InstallDependencies.IsPresent
        AllowUnlockedNpmInstall = $AllowUnlockedNpmInstall.IsPresent
        FailOnTodo             = $FailOnTodo.IsPresent
        FailFast               = $FailFast.IsPresent
        StrictPowerShell       = $StrictPowerShell.IsPresent
        StrictDocumentation    = $StrictDocumentation.IsPresent
        StrictNoTests          = $StrictNoTests.IsPresent
        MaxPromptOutputLines   = $MaxPromptOutputLines
        MaxFailureMessageLines = $MaxFailureMessageLines
    }
    Steps           = $StepLog
}

# ============================================================
# Ausgaben
# ============================================================

function Write-Section {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Title
    )

    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor DarkGray
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor DarkGray
}

function Write-CommandPreview {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string[]]$Arguments = @(),

        [string]$WorkingDirectory
    )

    if ($WorkingDirectory) {
        Write-Host (
            "Arbeitsverzeichnis: $WorkingDirectory"
        ) -ForegroundColor DarkGray
    }

    $RenderedArguments = foreach ($Argument in $Arguments) {
        if (
            $Argument.Contains(" ") -or
            $Argument.Contains("`t") -or
            $Argument.Contains("`n")
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

function ConvertTo-SafeFileName {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Value
    )

    $InvalidCharacters = [System.IO.Path]::GetInvalidFileNameChars()

    $Result = $Value

    foreach ($InvalidCharacter in $InvalidCharacters) {
        $Result = $Result.Replace(
            [string]$InvalidCharacter,
            "_"
        )
    }

    $Result = $Result -replace "\s+", "-"
    $Result = $Result -replace "-{2,}", "-"
    $Result = $Result.Trim("-", "_", ".")

    if ([string]::IsNullOrWhiteSpace($Result)) {
        return "step"
    }

    if ($Result.Length -gt 100) {
        return $Result.Substring(0, 100)
    }

    return $Result
}

function Get-TextPreview {
    [CmdletBinding()]
    param(
        [AllowEmptyString()]
        [string]$Text,

        [ValidateRange(1, 5000)]
        [int]$MaximumLines = 120
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return ""
    }

    $Lines = @(
        $Text -split "\r?\n"
    )

    if ($Lines.Count -le $MaximumLines) {
        return $Text.Trim()
    }

    $HeadLineCount = [Math]::Max(
        1,
        [Math]::Floor($MaximumLines * 0.65)
    )

    $TailLineCount = [Math]::Max(
        1,
        $MaximumLines - $HeadLineCount
    )

    $OmittedLineCount = (
        $Lines.Count -
        $HeadLineCount -
        $TailLineCount
    )

    $PreviewLines = @(
        $Lines |
            Select-Object -First $HeadLineCount

        ""

        (
            "... {0} Zeilen ausgelassen; vollständige Ausgabe " +
            "siehe separate Ausgabedatei ..."
        ) -f $OmittedLineCount

        ""

        $Lines |
            Select-Object -Last $TailLineCount
    )

    return (
        $PreviewLines -join [Environment]::NewLine
    ).Trim()
}

# ============================================================
# Hilfsfunktionen für Git und Bandit (korrigiert)
# ============================================================

function Invoke-Git {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    $gitArguments = @(
        "-c",
        "core.autocrlf=false",
        "-c",
        "core.safecrlf=false"
    ) + $Arguments

    & git @gitArguments
    return $LASTEXITCODE
}

function Get-BanditSummary {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ReportPath
    )

    if (-not (Test-Path -LiteralPath $ReportPath -PathType Leaf)) {
        return [PSCustomObject]@{
            Total  = 0
            High   = 0
            Medium = 0
            Low    = 0
            Items  = @()
        }
    }

    try {
        $report = Get-Content `
            -LiteralPath $ReportPath `
            -Raw `
            -Encoding UTF8 |
            ConvertFrom-Json
    }
    catch {
        throw "Bandit-Bericht ist ungültig: $ReportPath. $($_.Exception.Message)"
    }

    $results = @($report.results)

    $items = @(
        $results |
            Sort-Object `
                @{
                    Expression = {
                        switch ($_.issue_severity) {
                            "HIGH"   { 1 }
                            "MEDIUM" { 2 }
                            "LOW"    { 3 }
                            default  { 4 }
                        }
                    }
                },
                filename,
                line_number |
            Select-Object `
                issue_severity,
                issue_confidence,
                test_id,
                test_name,
                filename,
                line_number,
                issue_text
    )

    return [PSCustomObject]@{
        Total = $results.Count
        High = @(
            $results |
                Where-Object issue_severity -eq "HIGH"
        ).Count
        Medium = @(
            $results |
                Where-Object issue_severity -eq "MEDIUM"
        ).Count
        Low = @(
            $results |
                Where-Object issue_severity -eq "LOW"
        ).Count
        Items = $items
    }
}

# ============================================================
# Protokolleinträge
# ============================================================

function Save-StepOutput {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$StepName,

        [AllowEmptyString()]
        [string]$Output
    )

    if ([string]::IsNullOrWhiteSpace($Output)) {
        return ""
    }

    $SafeName = ConvertTo-SafeFileName $StepName

    if (-not (Test-Path -LiteralPath $StepOutputDirectory)) {
        try {
            New-Item -ItemType Directory -LiteralPath $StepOutputDirectory -Force | Out-Null
        }
        catch {
            Write-Host "Warnung: Konnte StepOutput-Verzeichnis nicht erstellen: $StepOutputDirectory" -ForegroundColor Yellow
        }
    }

    $ExistingFiles = @(
        Get-ChildItem `
            -LiteralPath $StepOutputDirectory `
            -Filter "$SafeName*.log" `
            -File `
            -ErrorAction SilentlyContinue
    )

    $Sequence = $ExistingFiles.Count + 1

    $OutputFile = Join-Path `
        $StepOutputDirectory `
        ("{0:D2}-{1}.log" -f $Sequence, $SafeName)

    try {
        $Output |
            Set-Content `
                -LiteralPath $OutputFile `
                -Encoding UTF8
    }
    catch {
        Write-Host "Fehler beim Schreiben der Schrittausgabe: $OutputFile" -ForegroundColor Yellow
        try { Write-Host $_ -ForegroundColor Yellow } catch { }
        $OutputFile = ""
    }

    return $OutputFile
}

function Add-StepLogEntry {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [ValidateSet(
            "Passed",
            "Failed",
            "Warning",
            "Skipped"
        )]
        [string]$Status,

        [Parameter(Mandatory)]
        [datetime]$StartTime,

        [Parameter(Mandatory)]
        [datetime]$EndTime,

        [string]$Message = "",

        [string]$Command = "",

        [string]$WorkingDirectory = "",

        [string]$Output = ""
    )

    $OutputFile = Save-StepOutput `
        -StepName $Name `
        -Output $Output

    $OutputPreview = Get-TextPreview `
        -Text $Output `
        -MaximumLines $MaxPromptOutputLines

    $StepLog.Add(
        [PSCustomObject]@{
            Name             = $Name
            Status           = $Status
            StartedAt        = $StartTime.ToString("o")
            FinishedAt       = $EndTime.ToString("o")
            DurationSeconds  = [Math]::Round(
                ($EndTime - $StartTime).TotalSeconds,
                3
            )
            Message          = $Message
            Command          = $Command
            WorkingDirectory = $WorkingDirectory
            OutputPreview    = $OutputPreview
            OutputFile       = $OutputFile
            OutputLineCount  = if ($Output) {
                @($Output -split "\r?\n").Count
            }
            else {
                0
            }
        }
    )
}

function New-StepResult {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet(
            "Passed",
            "Warning",
            "Skipped"
        )]
        [string]$Status,

        [string]$Message = ""
    )

    return [PSCustomObject]@{
        TestsuiteStatus  = $Status
        TestsuiteMessage = $Message
    }
}

function Invoke-TestsuiteStep {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [scriptblock]$Action,

        [switch]$WarningOnly
    )

    Write-Section $Name

    $StartTime = Get-Date
    $Status = "Passed"
    $Message = ""

    $script:CurrentCommandOutput = ""
    $script:CurrentCommand = ""
    $script:CurrentWorkingDirectory = ""

    try {
        $Result = & $Action

        if (
            $null -ne $Result -and
            $Result.PSObject.Properties.Name -contains
            "TestsuiteStatus"
        ) {
            $Status = $Result.TestsuiteStatus
            $Message = $Result.TestsuiteMessage
        }

        switch ($Status) {
            "Passed" {
                Write-Host ""
                Write-Host "[OK] $Name" -ForegroundColor Green
            }

            "Warning" {
                Write-Host ""
                Write-Host "[WARNUNG] $Name" -ForegroundColor Yellow

                if ($Message) {
                    Write-Host $Message -ForegroundColor DarkYellow
                }
            }

            "Skipped" {
                Write-Host ""
                Write-Host "[ÜBERSPRUNGEN] $Name" -ForegroundColor Yellow

                if ($Message) {
                    Write-Host $Message -ForegroundColor DarkYellow
                }
            }
        }
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
            -Message $Message `
            -Command $script:CurrentCommand `
            -WorkingDirectory $script:CurrentWorkingDirectory `
            -Output $script:CurrentCommandOutput
    }

    if (
        $Status -eq "Failed" -and
        $FailFast
    ) {
        throw "Testsuite wegen -FailFast abgebrochen: $Name"
    }

    return $Status
}

function Skip-TestsuiteStep {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [string]$Reason
    )

    Write-Section $Name
    Write-Host "[ÜBERSPRUNGEN] $Reason" -ForegroundColor Yellow

    $Now = Get-Date

    Add-StepLogEntry `
        -Name $Name `
        -Status "Skipped" `
        -StartTime $Now `
        -EndTime $Now `
        -Message $Reason
}

# ============================================================
# Prozesse
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
        [string]$Command,

        [string[]]$Arguments = @(),

        [string]$WorkingDirectory,

        [int[]]$AllowedExitCodes = @(0)
    )

    Assert-Executable $Command

    $PreviousLocation = Get-Location

    $EffectiveWorkingDirectory = if ($WorkingDirectory) {
        $WorkingDirectory
    }
    else {
        (Get-Location).Path
    }

    $RenderedCommand = (
        "$Command " + ($Arguments -join " ")
    ).Trim()

    if ($script:CurrentCommand) {
        $script:CurrentCommand += (
            [Environment]::NewLine +
            $RenderedCommand
        )
    }
    else {
        $script:CurrentCommand = $RenderedCommand
    }

    $script:CurrentWorkingDirectory = $EffectiveWorkingDirectory

    Write-CommandPreview `
        -Command $Command `
        -Arguments $Arguments `
        -WorkingDirectory $WorkingDirectory

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

        $CapturedOutput = @(
            & $Command @Arguments 2>&1 |
                ForEach-Object {
                    $Line = $_.ToString()
                    Write-Host $Line
                    $Line
                }
        )

        $ExitCode = $LASTEXITCODE

        if ($null -eq $ExitCode) {
            $ExitCode = 0
        }

        $CommandOutput = (
            $CapturedOutput -join [Environment]::NewLine
        ).Trim()

        $OutputSection = @(
            "COMMAND: $RenderedCommand"
            "WORKING DIRECTORY: $EffectiveWorkingDirectory"
            "EXIT CODE: $ExitCode"
            ""
            $CommandOutput
        ) -join [Environment]::NewLine

        if ($script:CurrentCommandOutput) {
            $script:CurrentCommandOutput += (
                [Environment]::NewLine +
                [Environment]::NewLine +
                ("-" * 78) +
                [Environment]::NewLine +
                $OutputSection
            )
        }
        else {
            $script:CurrentCommandOutput = $OutputSection
        }

        $Result = [PSCustomObject]@{
            Command          = $RenderedCommand
            WorkingDirectory = $EffectiveWorkingDirectory
            ExitCode         = $ExitCode
            Output           = $CommandOutput
        }

        if ($AllowedExitCodes -notcontains $ExitCode) {
            $ErrorMessage = (
                "Befehl '$Command' wurde mit Exitcode $ExitCode beendet."
            )

            if (
                $MaxFailureMessageLines -gt 0 -and
                $CapturedOutput.Count -gt 0 -and
                $CapturedOutput.Count -le $MaxFailureMessageLines
            ) {
                $ErrorMessage += (
                    [Environment]::NewLine +
                    [Environment]::NewLine +
                    ($CapturedOutput -join [Environment]::NewLine)
                )
            }
            elseif ($CapturedOutput.Count -gt 0) {
                $ErrorMessage += (
                    [Environment]::NewLine +
                    "Die vollständige Werkzeugausgabe wurde als " +
                    "separate Schrittausgabe gespeichert."
                )
            }

            throw $ErrorMessage
        }

        return $Result
    }
    finally {
        if ($WorkingDirectory) {
            Set-Location $PreviousLocation
        }
    }
}

function Invoke-Npx {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments,

        [string]$WorkingDirectory = $ProjectRoot,

        [int[]]$AllowedExitCodes = @(0)
    )

    return Invoke-External `
        -Command "npx" `
        -Arguments (@("--no-install") + $Arguments) `
        -WorkingDirectory $WorkingDirectory `
        -AllowedExitCodes $AllowedExitCodes
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

    $checkCommand = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec(sys.argv[1]) else 1)"

    if ($PSVersionTable.PSVersion.Major -ge 7) {
        & python -c $checkCommand $Module *> $null
    }
    else {
        & python -c $checkCommand $Module > $null 2>&1
    }

    return $LASTEXITCODE -eq 0
}

function Test-LocalNodeCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string]$WorkingDirectory = $ProjectRoot
    )
    # Consider global installations as valid as well
    if (Test-CommandExists $Command) {
        return $true
    }

    $ExecutableName = if ($IsWindowsPlatform) { "$Command.cmd" } else { $Command }

    $Candidates = @(
        (Join-Path $WorkingDirectory "node_modules\.bin\$ExecutableName"),
        (Join-Path $ProjectRoot "node_modules\.bin\$ExecutableName"),
        (Join-Path $FrontendDirectory "node_modules\.bin\$ExecutableName")
    )

    return @($Candidates | Where-Object { Test-Path -LiteralPath $_ }).Count -gt 0
}

# ============================================================
# Dateien
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
        ".vscode-test",
        "selfhtml"   # neu: schließt frontend/public/selfhtml aus
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
        [ValidateRange(1, 500)]
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
# NPM-Hilfsfunktionen
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
# Python-Abhängigkeiten
# ============================================================

function Get-BackendDependencySource {
    [CmdletBinding()]
    param()

    $Candidates = @(
        [PSCustomObject]@{
            Path = Join-Path $BackendDirectory "requirements.lock"
            Type = "requirements"
        },
        [PSCustomObject]@{
            Path = Join-Path $BackendDirectory "requirements.txt"
            Type = "requirements"
        },
        [PSCustomObject]@{
            Path = Join-Path $ProjectRoot "requirements.lock"
            Type = "requirements"
        },
        [PSCustomObject]@{
            Path = Join-Path $ProjectRoot "requirements.txt"
            Type = "requirements"
        },
        [PSCustomObject]@{
            Path = Join-Path $BackendDirectory "pyproject.toml"
            Type = "pyproject"
        },
        [PSCustomObject]@{
            Path = Join-Path $ProjectRoot "pyproject.toml"
            Type = "pyproject"
        }
    )

    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate.Path) {
            return $Candidate
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
            "Keine Python-Abhängigkeitsdatei gefunden."
        )
    }

    if ($DependencySource.Type -eq "requirements") {
        Invoke-External `
            -Command "python" `
            -Arguments @(
                "-m",
                "pip",
                "install",
                "-r",
                $DependencySource.Path
            ) |
            Out-Null

        return
    }

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
        -WorkingDirectory $PackageDirectory |
        Out-Null
}

# ============================================================
# Python-Dateivalidierung
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
                -Arguments $Arguments |
                Out-Null
        }
}

# ============================================================
# FastAPI-Einstieg erkennen
# ============================================================

function Get-FastApiImportTarget {
    [CmdletBinding()]
    param()

    $Candidates = @(
        [PSCustomObject]@{
            File             = Join-Path $BackendDirectory "main.py"
            WorkingDirectory = $BackendDirectory
            ImportStatement  = "from main import app"
        },
        [PSCustomObject]@{
            File             = Join-Path $BackendDirectory "app\main.py"
            WorkingDirectory = $BackendDirectory
            ImportStatement  = "from app.main import app"
        },
        [PSCustomObject]@{
            File             = Join-Path $BackendDirectory "app\api.py"
            WorkingDirectory = $BackendDirectory
            ImportStatement  = "from app.api import app"
        }
    )

    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate.File) {
            return $Candidate
        }
    }

    return $null
}

# ============================================================
# Aktionshinweise
# ============================================================

function Get-ActionItems {
    [CmdletBinding()]
    param()

    $Results = [System.Collections.Generic.List[object]]::new()

    $CodeFiles = @(
        Get-ProjectFiles @(
            ".py",
            ".pyi",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".css",
            ".scss",
            ".ps1"
        )
    ) |
    Where-Object {
        $_.FullName -ne $PSCommandPath
    }

    $CodePattern = (
        "(?i)(?:#|//|/\*|\*)\s*" +
        "(TODO|FIXME|HACK|XXX)\b"
    )

    foreach ($File in $CodeFiles) {
        $Matches = @(
            Select-String `
                -LiteralPath $File.FullName `
                -Pattern $CodePattern
        )

        foreach ($Match in $Matches) {
            $Results.Add(
                [PSCustomObject]@{
                    Type       = "CodeMarker"
                    Path       = $Match.Path
                    LineNumber = $Match.LineNumber
                    Text       = $Match.Line.Trim()
                }
            )
        }
    }

    $ExcludedMarkdownNames = @(
        "todo.md",
        "TODO.md"
    )

    $MarkdownFiles = @(
        Get-ProjectFiles @(
            ".md",
            ".mdx"
        )
    ) |
    Where-Object {
        $_.Name -notin $ExcludedMarkdownNames -and
        $_.FullName -notmatch
        "[\\/]Development[\\/]TODO\.md$" -and
        $_.FullName -notmatch
        "[\\/]CHANGELOG\.md$"
    }

    foreach ($File in $MarkdownFiles) {
        $Matches = @(
            Select-String `
                -LiteralPath $File.FullName `
                -Pattern "^\s*[-*]\s+\[\s\]\s+"
        )

        foreach ($Match in $Matches) {
            $Results.Add(
                [PSCustomObject]@{
                    Type       = "UncheckedTask"
                    Path       = $Match.Path
                    LineNumber = $Match.LineNumber
                    Text       = $Match.Line.Trim()
                }
            )
        }
    }

    return @($Results)
}

# ============================================================
# Berichte
# ============================================================

function Update-SuiteState {
    [CmdletBinding()]
    param()

    $SuiteEndTime = Get-Date

    $SuiteState.FinishedAt = $SuiteEndTime.ToString("o")
    $SuiteState.DurationSeconds = [Math]::Round(
        ($SuiteEndTime - $SuiteStartTime).TotalSeconds,
        3
    )

    $SuiteState.PassedCount = @(
        $StepLog |
        Where-Object Status -eq "Passed"
    ).Count

    $SuiteState.FailedCount = @(
        $StepLog |
        Where-Object Status -eq "Failed"
    ).Count

    $SuiteState.WarningCount = @(
        $StepLog |
        Where-Object Status -eq "Warning"
    ).Count

    $SuiteState.SkippedCount = @(
        $StepLog |
        Where-Object Status -eq "Skipped"
    ).Count

    $SuiteState.Success = (
        $SuiteState.FailedCount -eq 0 -and
        $null -eq $UnexpectedError
    )

    if ($UnexpectedError) {
        $SuiteState["UnexpectedError"] = $UnexpectedError
    }
}

function Save-JsonReport {
    [CmdletBinding()]
    param()

    Update-SuiteState

    $SuiteState |
        ConvertTo-Json -Depth 12 |
        Set-Content `
            -LiteralPath $JsonReportFile `
            -Encoding UTF8
}

function Save-WorkPrompt {
    [CmdletBinding()]
    param()

    $FailedSteps = @(
        $StepLog |
            Where-Object {
                $_.Status -eq "Failed"
            }
    )

    $WarningSteps = @(
        $StepLog |
            Where-Object {
                $_.Status -eq "Warning"
            }
    )

    $SkippedSteps = @(
        $StepLog |
            Where-Object {
                $_.Status -eq "Skipped"
            }
    )

    $PromptLines = [System.Collections.Generic.List[string]]::new()

    $PromptLines.Add(
        "# Arbeitsauftrag: Kernschmied-Testsuite analysieren und reparieren"
    )

    $PromptLines.Add("")

    $PromptLines.Add(
        "Du bist ein Senior Software Architect, Python-, TypeScript-, " +
        "PowerShell- und Build-System-Spezialist."
    )

    $PromptLines.Add("")
    $PromptLines.Add("## Ziel")
    $PromptLines.Add("")

    $PromptLines.Add(
        "Analysiere die folgenden Ergebnisse der Kernschmied-Testsuite. " +
        "Ermittle die tatsächlichen Ursachen und schlage konkrete, minimale " +
        "und überprüfbare Korrekturen vor."
    )

    $PromptLines.Add("")
    $PromptLines.Add("## Verbindliche Regeln")
    $PromptLines.Add("")

    $PromptLines.Add(
        "1. Erfinde keine Fehlermeldungen, Dateien, Funktionen oder Ursachen."
    )

    $PromptLines.Add(
        "2. Verwende ausschließlich die im Bericht enthaltenen Ausgaben."
    )

    $PromptLines.Add(
        "3. Wenn Informationen fehlen, nenne exakt den Diagnosebefehl, " +
        "der als Nächstes ausgeführt werden muss."
    )

    $PromptLines.Add(
        "4. Der Begriff 'placeholder' ist in Kernschmied ein legitimer " +
        "Fachbegriff und kein automatischer Hinweis auf unfertigen Code."
    )

    $PromptLines.Add(
        "5. Pytest-Exitcode 5 bedeutet, dass keine Tests gesammelt wurden."
    )

    $PromptLines.Add(
        "6. Unterscheide zwischen Quellcodefehler, Konfigurationsfehler, " +
        "fehlendem Werkzeug, fehlenden Tests, Warnung und Testsuite-Fehler."
    )

    $PromptLines.Add(
        "7. Ändere möglichst nur unmittelbar betroffene Dateien."
    )

    $PromptLines.Add(
        "8. Erzeuge keine Platzhalterimplementierungen."
    )

    $PromptLines.Add(
        "9. Gib für jede vorgeschlagene Änderung einen passenden " +
        "Verifikationsbefehl an."
    )

    $PromptLines.Add(
        "10. Sicherheitsprüfungen dürfen nicht einfach deaktiviert werden."
    )

    $PromptLines.Add("")
    $PromptLines.Add("## Priorisierung")
    $PromptLines.Add("")

    $PromptLines.Add("1. Fehler in der Testsuite selbst")
    $PromptLines.Add("2. Import- und Laufzeitfehler")
    $PromptLines.Add("3. Fehlgeschlagene Tests")
    $PromptLines.Add("4. Typfehler")
    $PromptLines.Add("5. Sicherheitsprobleme")
    $PromptLines.Add("6. Lint- und Formatierungsprobleme")
    $PromptLines.Add("7. Dokumentationsprobleme")

    $PromptLines.Add("")
    $PromptLines.Add("## Erwartetes Antwortformat")
    $PromptLines.Add("")

    $PromptLines.Add(
        "Erstelle für jeden fehlgeschlagenen oder relevanten Warnschritt:"
    )

    $PromptLines.Add("")
    $PromptLines.Add("- Kategorie")
    $PromptLines.Add("- betroffene Datei oder Komponente")
    $PromptLines.Add("- nachgewiesene Ursache")
    $PromptLines.Add("- fehlende Information")
    $PromptLines.Add("- nächster Diagnosebefehl")
    $PromptLines.Add("- konkrete Korrektur")
    $PromptLines.Add("- Verifikationsbefehl")
    $PromptLines.Add("- Risiko der Änderung")

    $PromptLines.Add("")
    $PromptLines.Add("## Projektinformationen")
    $PromptLines.Add("")

    $PromptLines.Add("- Projekt: Kernschmied")
    $PromptLines.Add("- Projektpfad: $ProjectRoot")
    $PromptLines.Add("- Testlauf: $($SuiteState.StartedAt)")
    $PromptLines.Add("- Fehlgeschlagen: $($FailedSteps.Count)")
    $PromptLines.Add("- Warnungen: $($WarningSteps.Count)")
    $PromptLines.Add("- Übersprungen: $($SkippedSteps.Count)")

    if ($FailedSteps.Count -gt 0) {
        $PromptLines.Add("")
        $PromptLines.Add("## Fehlgeschlagene Schritte")

        foreach ($Step in $FailedSteps) {
            $PromptLines.Add("")
            $PromptLines.Add("### $($Step.Name)")
            $PromptLines.Add("")

            if ($Step.Message) {
                $PromptLines.Add("- Meldung: $($Step.Message)")
            }
            else {
                $PromptLines.Add("- Meldung: Keine zusätzliche Meldung.")
            }

            if ($Step.Command) {
                $PromptLines.Add("- Befehl:")
                $PromptLines.Add("")
                $PromptLines.Add('```powershell')
                $PromptLines.Add([string]$Step.Command)
                $PromptLines.Add('```')
            }

            if ($Step.WorkingDirectory) {
                $PromptLines.Add(
                    "- Arbeitsverzeichnis: $($Step.WorkingDirectory)"
                )
            }

            if ($Step.OutputFile) {
                $PromptLines.Add(
                    "- Vollständige Ausgabe: $($Step.OutputFile)"
                )

                $PromptLines.Add(
                    "- Ausgabezeilen insgesamt: $($Step.OutputLineCount)"
                )
            }

            if ($Step.OutputPreview) {
                $PromptLines.Add("")
                $PromptLines.Add(
                    "Gekürzte Werkzeugausgabe, maximal " +
                    "$MaxPromptOutputLines Zeilen:"
                )
                $PromptLines.Add("")
                $PromptLines.Add('```text')
                $PromptLines.Add([string]$Step.OutputPreview)
                $PromptLines.Add('```')
            }
        }
    }
    else {
        $PromptLines.Add("")
        $PromptLines.Add("## Fehlgeschlagene Schritte")
        $PromptLines.Add("")
        $PromptLines.Add("Keine fehlgeschlagenen Schritte.")
    }

    if ($WarningSteps.Count -gt 0) {
        $PromptLines.Add("")
        $PromptLines.Add("## Warnungen")

        foreach ($Step in $WarningSteps) {
            $PromptLines.Add("")
            $PromptLines.Add("### $($Step.Name)")
            $PromptLines.Add("")

            if ($Step.Message) {
                $PromptLines.Add("- Meldung: $($Step.Message)")
            }
            else {
                $PromptLines.Add("- Meldung: Keine zusätzliche Meldung.")
            }

            if ($Step.Command) {
                $PromptLines.Add("- Befehl:")
                $PromptLines.Add("")
                $PromptLines.Add('```powershell')
                $PromptLines.Add([string]$Step.Command)
                $PromptLines.Add('```')
            }

            if ($Step.WorkingDirectory) {
                $PromptLines.Add(
                    "- Arbeitsverzeichnis: $($Step.WorkingDirectory)"
                )
            }

            if ($Step.OutputFile) {
                $PromptLines.Add(
                    "- Vollständige Ausgabe: $($Step.OutputFile)"
                )

                $PromptLines.Add(
                    "- Ausgabezeilen insgesamt: $($Step.OutputLineCount)"
                )
            }

            if ($Step.OutputPreview) {
                $PromptLines.Add("")
                $PromptLines.Add(
                    "Gekürzte Werkzeugausgabe, maximal " +
                    "$MaxPromptOutputLines Zeilen:"
                )
                $PromptLines.Add("")
                $PromptLines.Add('```text')
                $PromptLines.Add([string]$Step.OutputPreview)
                $PromptLines.Add('```')
            }
        }
    }
    else {
        $PromptLines.Add("")
        $PromptLines.Add("## Warnungen")
        $PromptLines.Add("")
        $PromptLines.Add("Keine Warnungen.")
    }

    $RelevantSkippedSteps = @(
        $SkippedSteps |
            Where-Object {
                $_.Name -notin @(
                    "PSScriptAnalyzer",
                    "Vale",
                    "Lychee-Linkprüfung"
                )
            }
    )

    $OptionalMissingTools = @(
        $SkippedSteps |
            Where-Object {
                $_.Name -in @(
                    "PSScriptAnalyzer",
                    "Vale",
                    "Lychee-Linkprüfung"
                )
            }
    )

    $PromptLines.Add("")
    $PromptLines.Add("## Übersprungene Prüfungen")
    $PromptLines.Add("")

    if ($RelevantSkippedSteps.Count -gt 0) {
        foreach ($Step in $RelevantSkippedSteps) {
            $Reason = if ($Step.Message) {
                [string]$Step.Message
            }
            else {
                "Kein Grund angegeben."
            }

            $PromptLines.Add(
                "- $($Step.Name): $Reason"
            )
        }
    }
    else {
        $PromptLines.Add(
            "Keine fachlich relevanten Prüfungen wurden übersprungen."
        )
    }

    if ($OptionalMissingTools.Count -gt 0) {
        $PromptLines.Add("")
        $PromptLines.Add("Optionale, nicht installierte Werkzeuge:")

        foreach ($Step in $OptionalMissingTools) {
            $PromptLines.Add("- $($Step.Name)")
        }
    }

    $PromptLines.Add("")
    $PromptLines.Add("## Abschlussauftrag")
    $PromptLines.Add("")

    $PromptLines.Add(
        "Beginne mit einer kurzen technischen Diagnose. " +
        "Behebe zuerst Fehler in der Testsuite selbst. " +
        "Arbeite danach die Projektfehler in Prioritätsreihenfolge ab. " +
        "Vermeide ungetestete großflächige Refactorings."
    )

    $PromptLines |
        Set-Content `
            -LiteralPath $WorkPromptFile `
            -Encoding UTF8
}

function Write-SuiteSummary {
    [CmdletBinding()]
    param()

    Write-Section "Zusammenfassung"

    Write-Host (
        "Erfolgreich:    {0}" -f
        $SuiteState.PassedCount
    ) -ForegroundColor Green

    Write-Host (
        "Fehlgeschlagen: {0}" -f
        $SuiteState.FailedCount
    ) -ForegroundColor Red

    Write-Host (
        "Warnungen:      {0}" -f
        $SuiteState.WarningCount
    ) -ForegroundColor Yellow

    Write-Host (
        "Übersprungen:   {0}" -f
        $SuiteState.SkippedCount
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
            "Passed" { "Green" }
            "Warning" { "Yellow" }
            "Skipped" { "Yellow" }
            "Failed" { "Red" }
        }

        $Marker = switch ($Status) {
            "Passed" { "OK" }
            "Warning" { "!" }
            "Skipped" { "--" }
            "Failed" { "X" }
        }

        Write-Host ""
        Write-Host "$Status-Schritte:" -ForegroundColor $Color

        foreach ($Entry in $Entries) {
            Write-Host (
                "  [{0}] {1} ({2:N2}s)" -f
                $Marker,
                $Entry.Name,
                $Entry.DurationSeconds
            ) -ForegroundColor $Color

            if ($Entry.Message) {
                Write-Host (
                    "       $($Entry.Message)"
                ) -ForegroundColor DarkGray
            }
        }
    }

    Write-Host ""
    Write-Host "Textprotokoll: $TranscriptFile"
    Write-Host "JSON-Bericht:  $JsonReportFile"
    Write-Host "Aktionsbericht: $TodoReportFile"
    Write-Host "Arbeits-Prompt: $WorkPromptFile"
    Write-Host (
        "Dauer:          {0:N2}s" -f
        $SuiteState.DurationSeconds
    )
}

# ============================================================
# Testsuite
# ============================================================

try {
    Start-Transcript `
        -Path $TranscriptFile `
        -Force |
        Out-Null

    $TranscriptStarted = $true

    Write-Host ""
    Write-Host "Kernschmied Testsuite" -ForegroundColor Magenta
    Write-Host "Projekt:        $ProjectRoot"
    Write-Host "Textprotokoll:  $TranscriptFile"
    Write-Host "JSON-Bericht:   $JsonReportFile"
    Write-Host "Arbeits-Prompt: $WorkPromptFile"
    Write-Host (
        "Start:          {0}" -f
        $SuiteStartTime.ToString("dd.MM.yyyy HH:mm:ss")
    )

    if ($SkipFixes) {
        Write-Host "Modus:          Nur prüfen" -ForegroundColor Yellow
    }
    else {
        Write-Host "Modus:          Korrigieren und prüfen"
    }

    # ========================================================
    # Voraussetzungen
    # ========================================================

    Invoke-TestsuiteStep `
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

            Invoke-External "python" @("--version") | Out-Null
            Invoke-External "node" @("--version") | Out-Null
            Invoke-External "npm" @("--version") | Out-Null
            Invoke-External "git" @("--version") | Out-Null

            Write-Host ""
            Write-Host ("PowerShell: {0}" -f $PSVersionTable.PSVersion)

            $pyCmd = Get-Command python -ErrorAction SilentlyContinue
            $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
            $npmCmd = Get-Command npm -ErrorAction SilentlyContinue

            Write-Host ("Python:     {0}" -f ($pyCmd.Source -or $pyCmd.Path -or $pyCmd.Name))
            Write-Host ("Node:       {0}" -f ($nodeCmd.Source -or $nodeCmd.Path -or $nodeCmd.Name))
            Write-Host ("NPM:        {0}" -f ($npmCmd.Source -or $npmCmd.Path -or $npmCmd.Name))
        } |
        Out-Null

    # ========================================================
    # Abhängigkeiten
    # ========================================================

    if ($InstallDependencies) {
        if (Test-Path -LiteralPath $BackendDirectory) {
            Invoke-TestsuiteStep `
                -Name "Backend-Abhängigkeiten installieren" `
                -Action {
                    Install-BackendDependencies
                } |
                Out-Null
        }

        $FrontendPackageJson = Join-Path `
            $FrontendDirectory `
            "package.json"

        $FrontendPackageLock = Join-Path `
            $FrontendDirectory `
            "package-lock.json"

        if (Test-Path -LiteralPath $FrontendPackageLock) {
            Invoke-TestsuiteStep `
                -Name "Frontend-Abhängigkeiten installieren" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "ci",
                            "--ignore-scripts"
                        ) `
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        elseif (
            (Test-Path -LiteralPath $FrontendPackageJson) -and
            $AllowUnlockedNpmInstall
        ) {
            Invoke-TestsuiteStep `
                -Name "Frontend-Abhängigkeiten ohne Lockdatei installieren" `
                -WarningOnly `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "install",
                            "--ignore-scripts"
                        ) `
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        elseif (Test-Path -LiteralPath $FrontendPackageJson) {
            Skip-TestsuiteStep `
                -Name "Frontend-Abhängigkeiten installieren" `
                -Reason (
                    "package-lock.json fehlt. Verwende ausdrücklich " +
                    "-AllowUnlockedNpmInstall."
                )
        }
    }

    # ========================================================
    # Ruff
    # ========================================================

    if (Test-Executable "ruff") {
        if (-not $SkipFixes) {
            Invoke-TestsuiteStep `
                -Name "Ruff: Python formatieren" `
                -Action {
                    Invoke-External "ruff" @(
                        "format",
                        "backend",
                        "scripts"
                    ) |
                    Out-Null
                } |
                Out-Null

            Invoke-TestsuiteStep `
                -Name "Ruff: sichere Auto-Fixes" `
                -Action {
                    Invoke-External "ruff" @(
                        "check",
                        "backend",
                        "scripts",
                        "--fix",
                        "--show-fixes"
                    ) |
                    Out-Null
                } |
                Out-Null
        }

        Invoke-TestsuiteStep `
            -Name "Ruff: Lint-Prüfung" `
            -Action {
                Invoke-External "ruff" @(
                    "check",
                    "backend",
                    "scripts",
                    "--output-format",
                    "concise"
                ) |
                Out-Null
            } |
            Out-Null

        Invoke-TestsuiteStep `
            -Name "Ruff: Formatprüfung" `
            -Action {
                Invoke-External "ruff" @(
                    "format",
                    "--check",
                    "backend",
                    "scripts"
                ) |
                Out-Null
            } |
            Out-Null
    }
    else {
        Skip-TestsuiteStep `
            -Name "Ruff" `
            -Reason "Ruff wurde nicht gefunden."
    }

    # ========================================================
    # Prettier
    # ========================================================

    if (Test-LocalNodeCommand "prettier") {
        # Alle von Prettier unterstützten Dateierweiterungen
        $PrettierExtensions = @(
            ".css",
            ".html",
            ".js",
            ".json",
            ".jsonc",
            ".jsx",
            ".md",
            ".mdx",
            ".scss",
            ".ts",
            ".tsx",
            ".yaml",
            ".yml"
        )

        # Sammle alle tatsächlich existierenden Dateien (unter Beachtung der Ausschlussliste)
        $PrettierFiles = @(
            Get-ProjectFiles -Extensions $PrettierExtensions
        )

        if ($PrettierFiles.Count -eq 0) {
            Skip-TestsuiteStep `
                -Name "Prettier" `
                -Reason "Keine von Prettier unterstützten Dateien gefunden."
        }
        else {
            Write-Host "Prettier formatiert $($PrettierFiles.Count) Dateien."

            if (-not $SkipFixes) {
                Invoke-TestsuiteStep `
                    -Name "Prettier: Projekt formatieren" `
                    -Action {
                        # Prettier in Batches aufrufen, um lange Befehlszeilen zu vermeiden
                        Invoke-FileBatch `
                            -Files $PrettierFiles `
                            -BatchSize 100 `
                            -Action {
                                param($Batch)

                                Invoke-Npx `
                                    -Arguments (
                                        @("prettier") +
                                        (@($Batch | ForEach-Object { $_.FullName })) +
                                        @("--write", "--ignore-unknown", "--log-level", "warn")
                                    ) |
                                    Out-Null
                            }
                    } |
                    Out-Null
            }

            Invoke-TestsuiteStep `
                -Name "Prettier: Formatierung prüfen" `
                -Action {
                    Invoke-FileBatch `
                        -Files $PrettierFiles `
                        -BatchSize 100 `
                        -Action {
                            param($Batch)

                            Invoke-Npx `
                                -Arguments (
                                    @("prettier") +
                                    (@($Batch | ForEach-Object { $_.FullName })) +
                                    @("--check", "--ignore-unknown", "--log-level", "warn")
                                ) |
                                Out-Null
                        }
                } |
                Out-Null
        }
    }
    else {
        Skip-TestsuiteStep `
            -Name "Prettier" `
            -Reason "Prettier ist nicht lokal installiert."
    }

    # ========================================================
    # Markdown
    # ========================================================

    $AllMarkdownFiles = @(
        Get-ProjectFiles @(
            ".md",
            ".mdx"
        )
    )

    $WikiMarkdownFiles = @(
        $AllMarkdownFiles |
            Where-Object {
                $_.FullName.StartsWith(
                    $WikiDirectory,
                    [System.StringComparison]::OrdinalIgnoreCase
                )
            }
    )

    $RepositoryMarkdownFiles = @(
        $AllMarkdownFiles |
            Where-Object {
                -not $_.FullName.StartsWith(
                    $WikiDirectory,
                    [System.StringComparison]::OrdinalIgnoreCase
                )
            }
    )

    if ($SkipDocumentation) {
        Skip-TestsuiteStep `
            -Name "Dokumentationsprüfungen" `
            -Reason "Durch -SkipDocumentation deaktiviert."
    }
    elseif ($AllMarkdownFiles.Count -eq 0) {
        Skip-TestsuiteStep `
            -Name "Markdownlint" `
            -Reason "Keine Markdown-Dateien gefunden."
    }
    elseif (Test-LocalNodeCommand "markdownlint-cli2") {
        if (
            -not $SkipFixes -and
            $RepositoryMarkdownFiles.Count -gt 0
        ) {
            Invoke-TestsuiteStep `
                -Name "Markdownlint: Repository Auto-Fix" `
                -Action {
                    Invoke-FileBatch `
                        -Files $RepositoryMarkdownFiles `
                        -BatchSize 25 `
                        -Action {
                            param($Batch)

                            Invoke-Npx `
                                -Arguments (
                                    @(
                                        "markdownlint-cli2",
                                        "--fix"
                                    ) + @(
                                        $Batch |
                                            ForEach-Object {
                                                $_.FullName
                                            }
                                    )
                                ) |
                                Out-Null
                        }
                } |
                Out-Null
        }

        if (
            -not $SkipFixes -and
            $WikiMarkdownFiles.Count -gt 0
        ) {
            Invoke-TestsuiteStep `
                -Name "Markdownlint: Wiki Auto-Fix" `
                -Action {
                    Invoke-FileBatch `
                        -Files $WikiMarkdownFiles `
                        -BatchSize 25 `
                        -Action {
                            param($Batch)

                            Invoke-Npx `
                                -Arguments (
                                    @(
                                        "markdownlint-cli2",
                                        "--config",
                                        $WikiMarkdownConfigFile,
                                        "--fix"
                                    ) + @(
                                        $Batch |
                                            ForEach-Object {
                                                $_.FullName
                                            }
                                    )
                                ) |
                                Out-Null
                        }
                } |
                Out-Null
        }

        if ($RepositoryMarkdownFiles.Count -gt 0) {
            Invoke-TestsuiteStep `
                -Name "Markdownlint: Repository prüfen" `
                -Action {
                    Invoke-FileBatch `
                        -Files $RepositoryMarkdownFiles `
                        -BatchSize 25 `
                        -Action {
                            param($Batch)

                            Invoke-Npx `
                                -Arguments (
                                    @(
                                        "markdownlint-cli2"
                                    ) + @(
                                        $Batch |
                                            ForEach-Object {
                                                $_.FullName
                                            }
                                    )
                                ) |
                                Out-Null
                        }
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "Markdownlint: Repository prüfen" `
                -Reason (
                    "Keine Markdown-Dateien außerhalb des Wikis gefunden."
                )
        }

        if ($WikiMarkdownFiles.Count -gt 0) {
            Invoke-TestsuiteStep `
                -Name "Markdownlint: Wiki prüfen" `
                -Action {
                    Invoke-FileBatch `
                        -Files $WikiMarkdownFiles `
                        -BatchSize 25 `
                        -Action {
                            param($Batch)

                            Invoke-Npx `
                                -Arguments (
                                    @(
                                        "markdownlint-cli2",
                                        "--config",
                                        $WikiMarkdownConfigFile
                                    ) + @(
                                        $Batch |
                                            ForEach-Object {
                                                $_.FullName
                                            }
                                    )
                                ) |
                                Out-Null
                        }
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "Markdownlint: Wiki prüfen" `
                -Reason "Keine Wiki-Markdown-Dateien gefunden."
        }
    }
    else {
        Skip-TestsuiteStep `
            -Name "Markdownlint" `
            -Reason "markdownlint-cli2 ist nicht lokal installiert."
    }

    if (-not $SkipDocumentation) {
        if ($SkipLinks) {
            Skip-TestsuiteStep `
                -Name "Lychee-Linkprüfung" `
                -Reason "Durch -SkipLinks deaktiviert."
        }
        elseif (Test-Executable "lychee") {
            Invoke-TestsuiteStep `
                -Name "Lychee: Links prüfen" `
                -Action {
                    # Call lychee once for all files to simplify output handling
                    $Files = $AllMarkdownFiles | ForEach-Object { $_.FullName }

                    if ($Files.Count -eq 0) {
                        return New-StepResult -Status "Passed" -Message "Keine Markdown-Dateien zum Prüfen."
                    }

                    $args = @("--no-progress") + $Files

                    $LycheeResult = Invoke-External `
                        -Command "lychee" `
                        -Arguments $args `
                        -AllowedExitCodes @(0,2)

                    # If lychee returned non-zero, check if errors are only localhost/connection refused
                    if ($LycheeResult.ExitCode -ne 0) {
                        $output = $LycheeResult.Output -join [Environment]::NewLine

                        if ($output -match "Connection refused" -or $output -match "localhost") {
                            return New-StepResult `
                                -Status "Warning" `
                                -Message "Lychee meldete Verbindungsfehler für lokale URLs (z.B. http://localhost). Diese werden als Hinweis behandelt. Volle Ausgabe ist in der Schrittausgabe gespeichert."
                        }

                        throw "Lychee-Linkprüfung hat Fehler gemeldet. Siehe Ausgabe.";
                    }

                    return New-StepResult -Status "Passed"
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "Lychee-Linkprüfung" `
                -Reason "Lychee wurde nicht gefunden."
        }

        $ValeConfigExists = @(
            @(
                ".vale.ini",
                "vale.ini",
                ".vale.yaml",
                ".vale.yml"
            ) |
                ForEach-Object {
                    Join-Path $ProjectRoot $_
                } |
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
                    Invoke-External `
                        -Command "vale" `
                        -Arguments @(
                            $WikiDirectory
                        ) |
                        Out-Null
                }
            }

            if (-not $StrictDocumentation) {
                $ValeParameters.WarningOnly = $true
            }

            Invoke-TestsuiteStep @ValeParameters |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "Vale" `
                -Reason (
                    "Vale oder Vale-Konfiguration wurde nicht gefunden."
                )
        }
    }

    # ========================================================
    # Documentation: run repository-provided helper scripts
    # These are lightweight checks that are expected to be idempotent
    # and safe to run as part of the testsuite. They respect the
    # -SkipDocumentation flag.
    # ========================================================

    if (-not $SkipDocumentation) {
        Invoke-TestsuiteStep `
            -Name "Validate Documentation (script)" `
            -Action {
                $r = Invoke-External `
                    -Command "python" `
                    -Arguments @("scripts/documentation/validate_documentation.py") `
                    -AllowedExitCodes @(0)

                if ($r.ExitCode -ne 0) {
                    throw "validate_documentation.py returned non-zero exit code: $($r.ExitCode)"
                }

                return New-StepResult -Status "Passed"
            } |
            Out-Null

        Invoke-TestsuiteStep `
            -Name "Check Documentation Links (script)" `
            -Action {
                # allow link-checker to report problems as warnings instead of failing the whole suite
                $r = Invoke-External `
                    -Command "python" `
                    -Arguments @("scripts/documentation/check_documentation_links.py") `
                    -AllowedExitCodes @(0,1)

                if ($r.ExitCode -eq 1) {
                    return New-StepResult -Status "Warning" -Message "Linkprüfung meldete Probleme; siehe Schrittausgabe."
                }

                return New-StepResult -Status "Passed"
            } |
            Out-Null

        Invoke-TestsuiteStep `
            -Name "Export GitHub Wiki" `
            -Action {
                $r = Invoke-External `
                    -Command "python" `
                    -Arguments @("scripts/documentation/export_github_wiki.py") `
                    -AllowedExitCodes @(0)

                if ($r.ExitCode -ne 0) {
                    throw "export_github_wiki.py returned non-zero exit code: $($r.ExitCode)"
                }

                return New-StepResult -Status "Passed"
            } |
            Out-Null
    }

    # ========================================================
    # JSON
    # ========================================================

    $JsonFiles = @(
        Get-ProjectFiles @(".json")
    )

    Invoke-TestsuiteStep `
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
    # TOML
    # ========================================================

    $TomlFiles = @(
        Get-ProjectFiles @(".toml")
    )

    Invoke-TestsuiteStep `
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
    # YAML
    # ========================================================

    $YamlFiles = @(
        Get-ProjectFiles @(
            ".yaml",
            ".yml"
        )
    )

    if (Test-PythonModule "yaml") {
        Invoke-TestsuiteStep `
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
        Skip-TestsuiteStep `
            -Name "YAML-Validierung" `
            -Reason "PyYAML ist nicht installiert."
    }

    # ========================================================
    # Backend-Kompilierung
    # ========================================================

    if (Test-Path -LiteralPath $BackendDirectory) {
        Invoke-TestsuiteStep `
            -Name "Python: Backend kompilieren" `
            -Action {
                Invoke-External "python" @(
                    "-m",
                    "compileall",
                    "-q",
                    $BackendDirectory
                ) |
                Out-Null
            } |
            Out-Null
    }
    else {
        Skip-TestsuiteStep `
            -Name "Python-Kompilierung" `
            -Reason "Backend-Verzeichnis wurde nicht gefunden."
    }

    # ========================================================
    # FastAPI/OpenAPI
    # ========================================================

    $FastApiTarget = Get-FastApiImportTarget

    if ($null -ne $FastApiTarget) {
        Invoke-TestsuiteStep `
            -Name "FastAPI-Import und OpenAPI prüfen" `
            -Action {
                $Code = @"
$($FastApiTarget.ImportStatement)

schema = app.openapi()

assert isinstance(schema, dict)
assert schema.get("openapi")
assert schema.get("info")
assert isinstance(schema.get("paths"), dict)

print("OpenAPI:", schema["openapi"])
print("Titel:", schema["info"].get("title"))
print("Pfade:", len(schema["paths"]))
"@

                Invoke-External `
                    -Command "python" `
                    -Arguments @(
                        "-c",
                        $Code
                    ) `
                    -WorkingDirectory $FastApiTarget.WorkingDirectory |
                    Out-Null
            } |
            Out-Null
    }
    else {
        Skip-TestsuiteStep `
            -Name "FastAPI/OpenAPI" `
            -Reason (
                "Kein unterstützter FastAPI-Einstiegspunkt gefunden."
            )
    }

    # ========================================================
    # Mypy
    # ========================================================

    if (Test-PythonModule "mypy") {
        Invoke-TestsuiteStep `
            -Name "Mypy: Typprüfung" `
            -Action {
                Invoke-External "python" @(
                    "-m",
                    "mypy",
                    "backend",
                    "--show-error-codes",
                    "--pretty"
                ) |
                Out-Null
            } |
            Out-Null
    }
    else {
        Skip-TestsuiteStep `
            -Name "Mypy" `
            -Reason "Mypy ist nicht installiert."
    }

    # ========================================================
    # Pip
    # ========================================================

    Invoke-TestsuiteStep `
        -Name "Pip: Abhängigkeiten prüfen" `
        -Action {
            Invoke-External "python" @(
                "-m",
                "pip",
                "check"
            ) |
            Out-Null
        } |
        Out-Null

    # ========================================================
    # Sicherheit (korrigiert)
    # ========================================================

    if ($SkipSecurity) {
        Skip-TestsuiteStep `
            -Name "Python-Sicherheitsprüfungen" `
            -Reason "Durch -SkipSecurity deaktiviert."
    }
    else {
        if (Test-PythonModule "pip_audit") {
            Invoke-TestsuiteStep `
                -Name "Pip-Audit: Schwachstellen prüfen" `
                -WarningOnly `
                -Action {
                    $PipAuditResult = Invoke-External `
                        -Command "python" `
                        -Arguments @(
                            "-m",
                            "pip_audit",
                            "--progress-spinner",
                            "off",
                            "--format",
                            "json",
                            "--output",
                            $PipAuditReportFile
                        ) `
                        -AllowedExitCodes @(
                            0,
                            1
                        )

                    if ($PipAuditResult.ExitCode -eq 1) {
                        return New-StepResult `
                            -Status "Warning" `
                            -Message (
                                "Pip-Audit hat bekannte Schwachstellen gefunden. " +
                                "Bericht: $PipAuditReportFile"
                            )
                    }

                    return New-StepResult `
                        -Status "Passed" `
                        -Message (
                            "Keine bekannten Python-Schwachstellen gefunden."
                        )
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "Pip-Audit" `
                -Reason "pip-audit ist nicht installiert."
        }

        if (Test-PythonModule "bandit") {
            Invoke-TestsuiteStep `
                -Name "Bandit: Sicherheitsanalyse" `
                -Action {
                    # Nur relevante Quellpfade prüfen (nicht .venv, tests, etc.)
                    $banditScanPaths = @(
                        (Join-Path $BackendDirectory "app"),
                        (Join-Path $BackendDirectory "main.py"),
                        (Join-Path $BackendDirectory "tools")
                    )

                    $existingBanditScanPaths = @(
                        $banditScanPaths |
                            Where-Object {
                                Test-Path -LiteralPath $_
                            }
                    )

                    if ($existingBanditScanPaths.Count -eq 0) {
                        throw "Es wurden keine gültigen Bandit-Prüfpfade gefunden."
                    }

                    $banditArguments = @(
                        "-m",
                        "bandit",
                        "-f",
                        "json",
                        "-o",
                        $BanditReportFile
                    )

                    foreach ($scanPath in $existingBanditScanPaths) {
                        $banditArguments += "-r"
                        $banditArguments += $scanPath
                    }

                    $BanditResult = Invoke-External `
                        -Command "python" `
                        -Arguments $banditArguments `
                        -AllowedExitCodes @(0,1)

                    # Zusammenfassung erstellen und anzeigen
                    $banditSummary = Get-BanditSummary -ReportPath $BanditReportFile

                    Write-Host ""
                    Write-Host (
                        "Bandit: {0} Fundstellen – HIGH: {1}, MEDIUM: {2}, LOW: {3}" -f
                        $banditSummary.Total,
                        $banditSummary.High,
                        $banditSummary.Medium,
                        $banditSummary.Low
                    )

                    if ($banditSummary.Total -gt 0) {
                        $banditSummary.Items |
                            Select-Object -First 100 |
                            Format-Table -AutoSize -Wrap
                    }

                    if ($BanditResult.ExitCode -eq 1) {
                        throw (
                            "Bandit hat Sicherheitsprobleme gefunden. " +
                            "Bericht: $BanditReportFile"
                        )
                    }
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "Bandit" `
                -Reason "Bandit ist nicht installiert."
        }
    }

    # ========================================================
    # Pytest
    # ========================================================

    if ($SkipTests) {
        Skip-TestsuiteStep `
            -Name "Pytest" `
            -Reason "Durch -SkipTests deaktiviert."
    }
    elseif (Test-PythonModule "pytest") {
        Invoke-TestsuiteStep `
            -Name "Pytest: Backend-Tests" `
            -Action {
                $PytestResult = Invoke-External `
                    -Command "python" `
                    -Arguments @(
                        "-m",
                        "pytest",
                        "-ra",
                        "--strict-markers",
                        "--strict-config"
                    ) `
                    -AllowedExitCodes @(
                        0,
                        5
                    )

                if ($PytestResult.ExitCode -eq 5) {
                    if ($StrictNoTests) {
                        throw (
                            "Pytest hat keine Tests gesammelt. " +
                            "Durch -StrictNoTests wird dies als Fehler bewertet."
                        )
                    }

                    return New-StepResult `
                        -Status "Warning" `
                        -Message (
                            "Pytest hat keine Tests gesammelt. " +
                            "Exitcode 5 ist kein Testfehler, zeigt aber, " +
                            "dass aktuell keine ausführbaren Tests vorhanden sind."
                        )
                }

                return New-StepResult `
                    -Status "Passed"
            } |
            Out-Null
    }
    else {
        Skip-TestsuiteStep `
            -Name "Pytest" `
            -Reason "Pytest ist nicht installiert."
    }

    # ========================================================
    # Frontend
    # ========================================================

    $FrontendPackageJson = Join-Path `
        $FrontendDirectory `
        "package.json"

    if (Test-Path -LiteralPath $FrontendPackageJson) {
        $FrontendScripts = @(
            Get-NpmScripts $FrontendPackageJson
        )

        if ($SkipFixes) {
            Skip-TestsuiteStep `
                -Name "ESLint: Auto-Fix" `
                -Reason "Durch -SkipFixes deaktiviert."
        }
        elseif (Test-NpmScript $FrontendScripts "lint:fix") {
            Invoke-TestsuiteStep `
                -Name "ESLint: Auto-Fix" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "lint:fix"
                        ) `
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        elseif (Test-NpmScript $FrontendScripts "lint") {
            Invoke-TestsuiteStep `
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
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "ESLint: Auto-Fix" `
                -Reason "Kein lint- oder lint:fix-Skript vorhanden."
        }

        if (Test-NpmScript $FrontendScripts "lint") {
            Invoke-TestsuiteStep `
                -Name "ESLint: Abschlussprüfung" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "lint"
                        ) `
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "ESLint-Prüfung" `
                -Reason "Kein lint-Skript vorhanden."
        }

        if (Test-NpmScript $FrontendScripts "typecheck") {
            Invoke-TestsuiteStep `
                -Name "TypeScript: Typprüfung" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "typecheck"
                        ) `
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        elseif (
            Test-Path -LiteralPath (
                Join-Path $FrontendDirectory "tsconfig.json"
            )
        ) {
            Invoke-TestsuiteStep `
                -Name "TypeScript: Typprüfung" `
                -Action {
                    Invoke-Npx `
                        -Arguments @(
                            "tsc",
                            "--noEmit",
                            "--pretty",
                            "false"
                        ) `
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "TypeScript" `
                -Reason "Keine TypeScript-Konfiguration gefunden."
        }

        if ($SkipTests) {
            Skip-TestsuiteStep `
                -Name "Frontend-Tests" `
                -Reason "Durch -SkipTests deaktiviert."
        }
        elseif (Test-NpmScript $FrontendScripts "test:run") {
            Invoke-TestsuiteStep `
                -Name "Frontend: Tests" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "test:run"
                        ) `
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        elseif (Test-NpmScript $FrontendScripts "test") {
            Invoke-TestsuiteStep `
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
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "Frontend-Tests" `
                -Reason "Kein Frontend-Testskript vorhanden."
        }

        if ($SkipBuild) {
            Skip-TestsuiteStep `
                -Name "Frontend-Build" `
                -Reason "Durch -SkipBuild deaktiviert."
        }
        elseif (Test-NpmScript $FrontendScripts "build") {
            Invoke-TestsuiteStep `
                -Name "Frontend: Produktions-Build" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "run",
                            "build"
                        ) `
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
        else {
            Skip-TestsuiteStep `
                -Name "Frontend-Build" `
                -Reason "Kein build-Skript vorhanden."
        }

        if ($SkipSecurity) {
            Skip-TestsuiteStep `
                -Name "NPM Audit" `
                -Reason "Durch -SkipSecurity deaktiviert."
        }
        else {
            Invoke-TestsuiteStep `
                -Name "NPM Audit: Schwachstellen prüfen" `
                -Action {
                    Invoke-External `
                        -Command "npm" `
                        -Arguments @(
                            "audit",
                            "--audit-level=high"
                        ) `
                        -WorkingDirectory $FrontendDirectory |
                        Out-Null
                } |
                Out-Null
        }
    }
    else {
        Skip-TestsuiteStep `
            -Name "Frontend-Prüfungen" `
            -Reason "frontend\package.json wurde nicht gefunden."
    }

    # ========================================================
    # PowerShell
    # ========================================================

    $ScriptAnalyzerCommand = Get-Command `
        -Name "Invoke-ScriptAnalyzer" `
        -ErrorAction SilentlyContinue

    if ($null -ne $ScriptAnalyzerCommand) {
            $AnalyzerParameters = @{
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

                    $AnalyzerErrors = @($Results | Where-Object { $_.Severity -eq 'Error' })
                    $AnalyzerWarnings = @($Results | Where-Object { $_.Severity -eq 'Warning' })

                    if ($AnalyzerErrors.Count -gt 0) {
                        Write-Host "PSScriptAnalyzer: Fehler gefunden:" -ForegroundColor Red
                        $AnalyzerErrors |
                            Select-Object RuleName, Severity, ScriptName, Line, Message |
                            Format-Table -AutoSize |
                            Out-Host

                        if ($AnalyzerWarnings.Count -gt 0) {
                            Write-Host "PSScriptAnalyzer: Zusätzlich Warnungen:" -ForegroundColor Yellow
                            $AnalyzerWarnings |
                                Select-Object RuleName, Severity, ScriptName, Line, Message |
                                Format-Table -AutoSize |
                                Out-Host
                        }

                        throw (
                            "{0} PowerShell-Fehler und {1} Warnungen gefunden." -f $AnalyzerErrors.Count, $AnalyzerWarnings.Count
                        )
                    }

                    if ($AnalyzerWarnings.Count -gt 0) {
                        Write-Host "PSScriptAnalyzer: Warnungen gefunden:" -ForegroundColor Yellow
                        $AnalyzerWarnings |
                            Select-Object RuleName, Severity, ScriptName, Line, Message |
                            Format-Table -AutoSize |
                            Out-Host

                        return New-StepResult -Status "Warning" -Message ("{0} PowerShell-Warnungen gefunden." -f $AnalyzerWarnings.Count)
                    }

                    Write-Host "Keine PowerShell-Probleme gefunden."
                    return New-StepResult -Status "Passed"
                }
            }

        if (-not $StrictPowerShell) {
            $AnalyzerParameters.WarningOnly = $true
        }

        Invoke-TestsuiteStep @AnalyzerParameters |
            Out-Null
    }
    else {
        Skip-TestsuiteStep `
            -Name "PSScriptAnalyzer" `
            -Reason (
                "PSScriptAnalyzer ist nicht installiert. " +
                "Installation: Install-Module PSScriptAnalyzer " +
                "-Scope CurrentUser"
            )
    }

    # ========================================================
    # Aktionsbericht
    # ========================================================

    Invoke-TestsuiteStep `
        -Name "TODO- und FIXME-Bericht erstellen" `
        -Action {
            $ActionItems = @(
                Get-ActionItems
            )

            $ReportLines = [System.Collections.Generic.List[string]]::new()

            $ReportLines.Add("Kernschmied-Aktionsbericht")
            $ReportLines.Add(
                "Erstellt: $(Get-Date -Format 'dd.MM.yyyy HH:mm:ss')"
            )
            $ReportLines.Add(
                "Treffer: $($ActionItems.Count)"
            )
            $ReportLines.Add("")
            $ReportLines.Add(
                "Erfasst werden nur echte Code-Kommentarmarker " +
                "und offene Markdown-Checkboxen."
            )
            $ReportLines.Add(
                "Normale Placeholder-Felder, Typnamen und Dokumentation " +
                "werden nicht als TODO gewertet."
            )
            $ReportLines.Add("")

            foreach ($Item in $ActionItems) {
                $ReportLines.Add(
                    (
                        "[{0}] {1}:{2}: {3}" -f
                        $Item.Type,
                        $Item.Path,
                        $Item.LineNumber,
                        $Item.Text
                    )
                )
            }

            $ReportLines |
                Set-Content `
                    -LiteralPath $TodoReportFile `
                    -Encoding UTF8

            Write-Host "$($ActionItems.Count) Aktionshinweise gefunden."
            Write-Host "Bericht: $TodoReportFile"

            if (
                $FailOnTodo -and
                $ActionItems.Count -gt 0
            ) {
                throw (
                    "$($ActionItems.Count) offene Aktionshinweise gefunden."
                )
            }
        } |
        Out-Null

    # ========================================================
    # Git (korrigiert)
    # ========================================================

    Invoke-TestsuiteStep `
        -Name "Git: Arbeitsverzeichnis prüfen" `
        -Action {
            # Separater Bericht für Git-Status
            $gitStatusReportPath = Join-Path `
                $ArtifactDirectory `
                "git-status-$Timestamp.txt"

            # Status abrufen (ohne Zeilenendewarnungen)
            $gitStatusLines = @(
                & git -c core.autocrlf=false -c core.safecrlf=false status --short
            )
            $gitStatusExitCode = $LASTEXITCODE
            if ($gitStatusExitCode -ne 0) {
                throw "Der Git-Status konnte nicht ermittelt werden."
            }

            $gitStatusLines | Set-Content -LiteralPath $gitStatusReportPath -Encoding UTF8

            Write-Host "Geänderte Git-Einträge: $($gitStatusLines.Count)"
            if ($gitStatusLines.Count -gt 0) {
                $gitStatusLines | Select-Object -First 50 | ForEach-Object { Write-Host $_ }
                if ($gitStatusLines.Count -gt 50) {
                    Write-Host "... weitere $($gitStatusLines.Count - 50) Einträge stehen in $gitStatusReportPath"
                }
            } else {
                Write-Host "Das Git-Arbeitsverzeichnis ist sauber."
            }

            # Diff-Statistik (kurz)
            $diffStat = & git -c core.autocrlf=false -c core.safecrlf=false diff --shortstat
            if ($LASTEXITCODE -ne 0) {
                throw "Git-Diff-Statistik konnte nicht erzeugt werden."
            }
            if ([string]::IsNullOrWhiteSpace($diffStat)) {
                Write-Host "Keine nicht vorgemerkten Änderungen."
            } else {
                Write-Host "Nicht vorgemerkte Änderungen: $diffStat"
            }

            # Diff --check (nur für nicht vorgemerkte)
            $diffCheckOutput = & git -c core.autocrlf=false -c core.safecrlf=false diff --check 2>&1
            $diffCheckExit = $LASTEXITCODE

            if ($diffCheckExit -ne 0) {
                # If the only messages are line-ending warnings (LF/CRLF) or purely trailing whitespace, downgrade to warning
                $lines = $diffCheckOutput -split "\r?\n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }

                $nonLineEnding = @($lines | Where-Object { $_ -notmatch "LF will be replaced by CRLF" -and $_ -notmatch "CRLF will be replaced by LF" -and $_ -notmatch "trailing whitespace" })

                if ($nonLineEnding.Count -eq 0) {
                    Write-Host "Git diff --check meldet nur Zeilenendungs-Hinweise; als Warning behandelt." -ForegroundColor Yellow
                }
                else {
                    Write-Host $diffCheckOutput
                    throw "Git diff --check hat Probleme festgestellt."
                }
            }

            # Diff --cached --check (für vorgemerkte)
            & git -c core.autocrlf=false -c core.safecrlf=false diff --cached --check
            if ($LASTEXITCODE -ne 0) {
                throw "Git diff --cached --check hat Probleme festgestellt."
            }
        } |
        Out-Null
}
catch {
    $UnexpectedError = $_.Exception.Message

    Write-Host ""
    Write-Host (
        "Unerwarteter Testsuite-Fehler: $UnexpectedError"
    ) -ForegroundColor Red
}
finally {
    try {
        Update-SuiteState
        Save-JsonReport
        Save-WorkPrompt
        Write-SuiteSummary
    }
    catch {
        Write-Host (
            "Abschlussberichte konnten nicht vollständig erstellt werden: " +
            $_.Exception.Message
        ) -ForegroundColor Red
    }

    if ($TranscriptStarted) {
        try {
            Stop-Transcript | Out-Null
        }
        catch {
            # Aufräumfehler wird nicht weiter eskaliert.
        }
    }

    Set-Location $OriginalLocation
}

if (
    $SuiteState.FailedCount -gt 0 -or
    $null -ne $UnexpectedError
) {
    Write-Host ""
    Write-Host (
        "Die Kernschmied-Testsuite enthält Fehler."
    ) -ForegroundColor Red

    Write-Host (
        "Der Arbeits-Prompt für das lokale Modell wurde erstellt:"
    ) -ForegroundColor Yellow

    Write-Host $WorkPromptFile -ForegroundColor Yellow

    exit 1
}

Write-Host ""
Write-Host (
    "Alle ausgeführten Prüfungen waren erfolgreich."
) -ForegroundColor Green

Write-Host (
    "Arbeits-Prompt: $WorkPromptFile"
)

exit 0
