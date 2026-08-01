# Patch wiki markdown files: keep first H1, convert other H1 to H2, add default fence language
$root = Join-Path $PSScriptRoot '..' | Resolve-Path
$wikiPath = Join-Path $root 'wiki'
Get-ChildItem -Path $wikiPath -Recurse -Filter *.md | ForEach-Object {
    $file = $_.FullName
    try {
        $content = Get-Content -Raw -Encoding UTF8 -ErrorAction Stop $file
    } catch {
        Write-Warning ("Failed reading {0}: {1}" -f $file, $_.Exception.Message)
        return
    }
    $outLines = New-Object System.Collections.Generic.List[string]
    $firstH1Found = $false
    $inFence = $false
    foreach ($line in ($content -split '\r?\n')) {
        if ($line -match '^\s*```') {
            if (-not $inFence) {
                $inFence = $true
                if ($line -match '^```\S') { $outLines.Add($line) } else { $outLines.Add('```text') }
            } else {
                $inFence = $false
                $outLines.Add('```')
            }
            continue
        }
        if (-not $firstH1Found -and $line -match '^\s*#\s') {
            $firstH1Found = $true
            $outLines.Add($line)
            continue
        }
        if ($line -match '^\s*#\s') {
            $line2 = $line -replace '^(\s*)#\s','${1}## '
            $outLines.Add($line2)
            continue
        }
        $outLines.Add($line)
    }
    $out = $outLines -join "`r`n"
    try {
        Set-Content -Path $file -Value $out -Encoding UTF8 -ErrorAction Stop
        Write-Output "Patched: $file"
    } catch {
        Write-Warning ("Failed writing {0}: {1}" -f $file, $_.Exception.Message)
    }
}
