<#
Sync documentation/ export to GitHub Wiki repository.

This is a placeholder PowerShell wrapper that clones `Kernschmied.wiki.git`, copies files from the export build, commits and pushes.
Configure `$WikiRepo` and run manually.
#>

param(
    [string]$WikiRepo = "git@github.com:Thomas-Heisig/Kernschmied.wiki.git",
    [string]$BuildFolder = "artifacts/documentation-wiki-build"
)

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git not found in PATH"
    exit 2
}

$tmp = Join-Path $env:TEMP "kernschmied-wiki-clone"
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }

git clone $WikiRepo $tmp
Copy-Item -Path $BuildFolder\* -Destination $tmp -Recurse -Force
Push-Location $tmp
git add --all
git commit -m "Sync documentation from repository (automated)" -a
git push
Pop-Location
