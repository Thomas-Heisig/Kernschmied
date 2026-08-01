# Kernschmied — Agent README

This repository contains Kernschmied, a schema-driven chat application.

Quick facts for agents and automated workflows:

- Tech: Python 3.12 (FastAPI), React + TypeScript (Vite), Tailwind CSS.
- DB (local dev): SQLite under `backend/data/` (these files are ignored and
  removed from history).
- Run: set `PYTHONPATH=backend` and start backend and frontend as described in
  the project's documentation.

Agent guidelines:

- Respect the `PROJECT_PROMPT` principles placed in `.github/PROJECT_PROMPT.agent.md`.
- Make small, testable changes; add tests and docs for behavior changes.
- Do not attempt destructive operations on remotes without human approval
  (e.g. force-push history rewrites).

If you need more context, open `docs/PROJECT_PROMPT.md` or the `.github` prompt.
