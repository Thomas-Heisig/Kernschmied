Title: docs(iam): consolidate documentation cleanup, ADRs, and initial IAM artifacts

Summary
-------
This branch performs a set of documentation hygiene tasks and introduces initial IAM artifacts (ADR-0024 + supporting files).

Changes included
---------------
- Migrated and archived external website artifacts discovered under `documentation/generated` and `documentation/assets/attachments` to `archive/documentation-website-artifacts-2026-08-03`.
- Archived transitional documentation folders (`documentation/migrated`, `documentation/unknown`) to `archive/documentation-transitions-2026-08-03`.
- Moved `documentation/internal-work` into `documentation/development/internal`.
- Added ADR-0025 (Deployment Architecture) and updated `documentation/_Sidebar.md` and `documentation/manifest.json` to reflect ADRs.
- Added initial IAM artifacts:
  - `documentation/adr/adr-0024-identity-and-authorization.md`
  - `backend/app/schemas/iam_schema.sql` (initial registry schema)
  - `documentation/api/iam_openapi.yaml`
  - `backend/app/services/permission_evaluator.py` (minimal reference implementation)
  - `tests/test_permission_evaluator.py`
- Fixed Markdown link casing mismatches across `documentation/` (normalized link targets to real filenames).

Notes for reviewers
-------------------
- The website artifacts were archived rather than deleted to avoid accidental data loss; please verify the archive before permanent deletion.
- Prettier and markdownlint report formatting/style issues across many documentation files; these are *not* auto-fixed in this PR to keep changes reviewable. I can follow up with a dedicated PR that runs `prettier --write` and fixes markdownlint findings in smaller batches.
- The `PermissionEvaluator` is intentionally minimal and provided as a reference for further integration (policy engine, caching, audit hooks).

Recommended next steps
----------------------
1. Review and approve the archival of extraneous website files.
2. Merge this PR to publish ADRs and IAM starter artifacts.
3. Create a dedicated PR to run `prettier --write` and address markdownlint findings incrementally.
