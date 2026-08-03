Set-Location 'F:\Kernschmied'
Write-Host 'Fetching origin and pruning...'
git fetch --prune origin
$ts = (Get-Date -Format 'yyyyMMdd_HHmmss')
$remoteBranches = git for-each-ref --format='%(refname:short)' refs/remotes/origin | Where-Object {$_ -and ($_ -notmatch 'origin/HEAD') -and ($_ -ne 'origin/master')}
if (-not $remoteBranches) { Write-Host 'No remote branches to process'; exit 0 }
foreach ($r in $remoteBranches) {
  $branch = $r -replace '^origin/',''
  $tag = "backup/$branch-before-delete-$ts"
  Write-Host "Backing up $r as tag $tag"
  git tag $tag $r
  git push origin "refs/tags/$tag"
  Write-Host "Checking if $r is merged into master..."
  git merge-base --is-ancestor $r master
  if ($LASTEXITCODE -eq 0) {
    Write-Host "$r already merged into master — deleting remote+local"
    git push origin --delete $branch
    if ((git branch --list $branch) -ne '') { git branch -D $branch } else { Write-Host "No local branch $branch" }
  } else {
    Write-Host "$r not merged — attempting merge into master"
    git checkout master
    git pull --rebase origin master
    $mergeMsg = "Merge $r into master (automated)"
    git merge --no-ff $r -m $mergeMsg
    if ($LASTEXITCODE -ne 0) {
      Write-Host "Merge failed for $r; aborting merge and stopping. Show status:"
      git merge --abort
      git status --porcelain
      exit 2
    } else {
      git push origin master
      git push origin --delete $branch
      if ((git branch --list $branch) -ne '') { git branch -D $branch }
    }
  }
}
Write-Host 'ALL_DONE'
