$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================="
Write-Host " Kernschmied Quality Pipeline"
Write-Host "========================================="
Write-Host ""

function Step($text) {
    Write-Host ""
    Write-Host "-----------------------------------------"
    Write-Host $text -ForegroundColor Cyan
    Write-Host "-----------------------------------------"
}

Step "1/9 Ruff Format"

ruff format .

Step "2/9 Ruff Auto Fix"

ruff check . --fix

Step "3/9 Black"

black .

Step "4/9 Prettier"

npx prettier . --write

Step "5/9 Markdown Auto Fix"

npx markdownlint-cli2 --fix

Step "6/9 Markdown Prüfung"

npx markdownlint-cli2

Step "7/9 Wiki Linkprüfung"

Get-ChildItem wiki -Recurse -Filter *.md |
ForEach-Object {
    npx markdown-link-check $_.FullName
}

Step "8/9 Python Compile"

python -m compileall backend

Step "9/9 Git Status"

git status

Write-Host ""
Write-Host "========================================="
Write-Host " Fertig."
Write-Host "=========================================" -ForegroundColor Green