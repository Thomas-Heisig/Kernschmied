param(
    [switch]$Apply
)

$root = Join-Path (Get-Location) 'documentation'
Write-Output "Scanning documentation files under: $root"

$plan = @()

Get-ChildItem -Path $root -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($root.Length+1)
    $lower = $rel.ToLowerInvariant()
    if ($rel -ne $lower) {
        $src = $_.FullName
        $dst = Join-Path $root $lower
        $plan += [PSCustomObject]@{ Source = $src; Destination = $dst }
    }
}

if ($plan.Count -eq 0) {
    Write-Output "No files with uppercase letters found under documentation/."
    exit 0
}

Write-Output "Planned renames:"
$plan | ForEach-Object { Write-Output "  $($_.Source)  ->  $($_.Destination)" }

$conflicts = $plan | Group-Object -Property Destination | Where-Object { $_.Count -gt 1 }
if ($conflicts) {
    Write-Output "ERROR: Conflicts detected (multiple sources -> same destination):"
    $conflicts | ForEach-Object {
        Write-Output "Destination: $($_.Name)"
        $_.Group | ForEach-Object { Write-Output "  Source: $($_.Source)" }
    }
    exit 2
}

if (-not $Apply) {
    Write-Output "Dry-run complete. To apply these renames, run with -Apply."
    exit 0
}

Write-Output "Applying renames..."
foreach ($item in $plan) {
    $dstDir = Split-Path $item.Destination -Parent
    if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }
    git mv -f -- "$($item.Source)" "$($item.Destination)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Move-Item -Force -Path $item.Source -Destination $item.Destination
    }
}

git add -A
git commit -m "chore(docs): normalize documentation filenames to lowercase" -q
Write-Output "Renames applied and committed."
