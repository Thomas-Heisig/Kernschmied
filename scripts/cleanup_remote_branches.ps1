Set-Location -LiteralPath 'F:\Kernschmied'

# List remote branches
$branches = git for-each-ref refs/remotes/origin --format='%(refname:short)'

foreach ($b in $branches) {
  if ($b -ne 'origin/master' -and $b -ne 'origin/HEAD') {
    $name = $b -replace '^origin/',''
    Write-Output "Deleting remote branch: $name"
    git push origin --delete $name
  }
}

Write-Output 'Remaining remote branches:'
git for-each-ref refs/remotes/origin --format='%(refname:short)'
