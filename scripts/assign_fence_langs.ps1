# Assign heuristic languages to code fences currently marked as ```text in wiki files
$root = Join-Path $PSScriptRoot '..' | Resolve-Path
$wikiPath = Join-Path $root 'wiki'
function Detect-Lang($snippet) {
    $s = $snippet.TrimStart() -replace '\r?\n',' ' -replace '\s+',' '
    $lower = $s.ToLower()
    if ($s -match '^[\s\`]*\{') { return 'json' }
    if ($s -match '^---\s*$') { return 'yaml' }
    if ($lower -match '\b(import\s+\w+|from\s+\w+|def\s+\w+|class\s+\w+|async\s+def|print\()') { return 'python' }
    if ($lower -match '\b(package.json|npm install|npm run|yarn|pnpm)') { return 'bash' }
    if ($lower -match '\b(get-childitem|set-location|write-output|powershell|\.ps1|activate.ps1)') { return 'powershell' }
    if ($s -match '<[a-zA-Z]') { return 'html' }
    if ($lower -match '\b(const\s+\w+|let\s+\w+|function\s+\w+|=>|import\s+React|tsx|jsx)') { if ($s -match '<[A-Za-z]') { return 'tsx' } else { return 'ts' } }
    if ($lower -match '\b(select\s+.+from|insert\s+into|update\s+.+set)') { return 'sql' }
    if ($lower -match '\b(hostname:|server:|environment:|version:)') { return 'yaml' }
    if ($s -match '^[\s\t]*#\!') { return 'bash' }
    return 'text'
}

Get-ChildItem -Path $wikiPath -Recurse -Filter *.md | ForEach-Object {
    $file = $_.FullName
    $content = Get-Content -Raw -Encoding UTF8 -ErrorAction Stop $file
    $out = ''
    $pos = 0
    $fence = [char]96 + [char]96 + [char]96
    $openToken = $fence + 'text'
    while ($pos -lt $content.Length) {
        $idx = $content.IndexOf($openToken, $pos, [System.StringComparison]::OrdinalIgnoreCase)
        if ($idx -lt 0) { $out += $content.Substring($pos); break }
        $out += $content.Substring($pos, $idx - $pos)
        $start = $idx
        $openLineEnd = $content.IndexOf([Environment]::NewLine, $start)
        if ($openLineEnd -lt 0) { $openLineEnd = $content.IndexOf([char]10, $start) }
        if ($openLineEnd -lt 0) { $openLineEnd = $start + 7 }
        $bodyStart = $openLineEnd + 2
        if ($bodyStart -lt 0) { $bodyStart = $start + 7 }
        $closeIdx = $content.IndexOf($fence, $bodyStart, [System.StringComparison]::Ordinal)
        if ($closeIdx -lt 0) { $out += $content.Substring($start); break }
        $body = $content.Substring($bodyStart, $closeIdx - $bodyStart)
        $lang = Detect-Lang($body)
        $out += (('```{0}' -f $lang) + [Environment]::NewLine)
        $out += $body
        $out += [Environment]::NewLine + '```'
        $pos = $closeIdx + 3
    }
    if ($out -ne $content) {
        Set-Content -Path $file -Value $out -Encoding UTF8 -ErrorAction Stop
        Write-Output ('Re-langged: ' + $file)
    }
}
