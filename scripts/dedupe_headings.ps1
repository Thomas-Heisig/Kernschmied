# Append numeric suffixes to duplicate headings within each file (for MD024)
$root = Join-Path $PSScriptRoot '..' | Resolve-Path
$wikiPath = Join-Path $root 'wiki'
Get-ChildItem -Path $wikiPath -Recurse -Filter *.md | ForEach-Object {
    $file = $_.FullName
    try { $content = Get-Content -Raw -Encoding UTF8 -ErrorAction Stop $file } catch { Write-Warning ("Failed reading {0}: {1}" -f $file, $_.Exception.Message); return }
    $lines = $content -split '\r?\n'
    $counts = @{}
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($line in $lines) {
        if ($line -match '^\s*(#{1,6})\s+(.*\S)\s*$') {
            $level = $matches[1].Length
            $text = $matches[2]
            $key = "$level|$text"
            if (-not $counts.ContainsKey($key)) { $counts[$key] = 0 }
            $counts[$key] = $counts[$key] + 1
            if ($counts[$key] -gt 1) {
                $suffix = " ($($counts[$key]))"
                $newLine = "$($matches[1]) $text$suffix"
                $out.Add($newLine)
                continue
            }
        }
        $out.Add($line)
    }
    $new = $out -join "`r`n"
    if ($new -ne $content) {
        try { Set-Content -Path $file -Value $new -Encoding UTF8 -ErrorAction Stop; Write-Output "Deduped: $file" } catch { Write-Warning ("Failed writing {0}: {1}" -f $file, $_.Exception.Message) }
    }
}
