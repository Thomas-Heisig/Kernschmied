Plan: Normalize Markdown filenames to lowercase (controlled PR)

Goal
----
Rename repository Markdown files so that filenames are all lowercase, to avoid
case-sensitivity issues on CI and Linux.

Steps
-----
1. Run `scripts/normalize_doc_filenames.ps1` in dry-run to discover mappings.
2. Review the planned renames for conflicts (files mapping to same lowercase name).
3. Apply renames with `-Apply` to perform `git mv` where possible and commit.
4. Open PR from branch `feat/docs-lowercase` for review.

Notes
-----
- This process is destructive only in that file paths change; links should be
  checked and updated where necessary (we have `scripts/fix_doc_link_casing.py` to help).
- Perform this on a dedicated branch; do not apply directly to `master`.

Commands (Windows PowerShell):

```powershell
# Dry-run
.
\scripts\normalize_doc_filenames.ps1

# Apply (after review)
.
\scripts\normalize_doc_filenames.ps1 -Apply

# Push branch and open PR
git checkout -b feat/docs-lowercase
git push -u origin feat/docs-lowercase
```
