Set-Location -LiteralPath 'F:\Kernschmied'

$current = git rev-parse --abbrev-ref HEAD
Write-Output "Current branch: $current"

$locals = git for-each-ref refs/heads --format="%(refname:short)"

foreach ($b in $locals) {
  if ($b -ne $current -and $b -ne 'master') {
    Write-Output "Deleting local branch: $b"
    git branch -D $b
  }
}

Write-Output 'Remaining local branches:'
git branch --format='%(refname:short)'
