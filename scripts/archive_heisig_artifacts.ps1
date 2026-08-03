$root = "F:\Kernschmied"
$archive = Join-Path $root "archive\documentation-website-artifacts-2026-08-03"

New-Item -ItemType Directory -Force -Path $archive | Out-Null

$generated = Join-Path $root "documentation\generated"
$attachments = Join-Path $root "documentation\assets\attachments"

if (Test-Path $generated) {
    $dest = Join-Path $archive "generated"
    Move-Item -Path $generated -Destination $dest -Force
}

if (Test-Path $attachments) {
    $destAttach = Join-Path $archive "attachments"
    New-Item -ItemType Directory -Force -Path $destAttach | Out-Null
    Get-ChildItem -Path $attachments -File |
        Where-Object { $_.Name -like "frontend_public_selfhtml_heisig-naturstein-modern_*" -or $_.Name -eq "frontend_public_favicon.png" } |
        ForEach-Object { Move-Item -Path $_.FullName -Destination $destAttach -Force }
}

git add -A
git commit -m "chore(docs): archive external website artifacts (heisig-naturstein)" -q

Write-Output "Archive complete: $archive"
