# CLAUDE.md

# Merge Context
This repo is mid-merge with DeepSec (document malware scanner).
Follow MERGE_STRATEGY.md in this repo root for the full plan.

## Current Phase
Phase 2 complete — `docscan/adapter.py::scan_document(path)` built and unit-tested: maps DeepSec's
`{"type","value"}` output onto AppSec's Finding contract (category `"document"`, `fixable=False`),
returns `{"findings","files_scanned":1,"summary"}` with DeepSec intelligence folded into a nested
`summary["document"]` block. Reuses `risk_calculator.calculate_risk`. Not yet wired into the app.
Next: Phase 3 — `scan_type` column + `backend/api/docscans.py` route + upload UI.
Update this line as each phase completes.

## Key Rules

- The Finding dict contract is the one clean seam — never break it
- Do NOT route document findings through the code auto-fixer
- Do NOT modify instance/appsec.db directly — drop and recreate it
- fixable=False for all document findings from DeepSec
- sanitize_pdf() currently writes to relative `sanitized/pdf/` at repo root —
  Phase 3 must route sanitized output to `reports/<scan_id>/` instead
- Add `sanitized/` to .gitignore before committing any scan artifacts 

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```powershell
# Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env        # then edit APP_SECRET_KEY (+ CLAUDE_API_KEY if using AI fixer)

# Run (dev server, http://127.0.0.1:5000)
python run.py
```

There is **no test suite, linter, or build step** configured for this project. `python run.py` is the only entry point. The database (`instance/appsec.db`) and runtime directories (`scans/`, `reports/`, `uploads/`, `logs/`) are created automatically on first startup via `create_app()` — no migration or init command is needed.

## Critical: runtime data directories contain third-party code

`scans/`, `uploads/`, and `reports/` hold **user-uploaded projects that this tool scans** — arbitrary third-party source code, not part of this application. When searching or grepping the codebase, scope to `app.py`, `run.py`, and `backend/` to avoid matching unrelated code inside those directories. A repo-wide `find`/`grep` will surface files (including `test_*.py`) that belong to scanned projects, not to AppSec Orchestrator.

## Architecture

AppSec Orchestrator is a Flask app that scans uploaded codebases for security vulnerabilities and generates fixes. The data model flows in one direction:

```
User → Project → Scan → Finding → Fix
```

A user uploads a project (ZIP or local path), runs a **Scan** that produces **Findings**, and each Finding can generate a **Fix** that is previewed, applied to disk, and optionally rolled back.

### Request lifecycle and cross-cutting guards

`app.py::create_app()` is the application factory. All cross-cutting request handling lives in a single `@app.before_request` hook (`api_guards`):
- **Rate limiting** (`SimpleRateLimiter`, in-memory, 90 req/60s per IP) runs first on every request.
- **CSRF** is enforced only on `/api/` `POST`/`PATCH`/`DELETE` requests from authenticated users, using a constant-time compare against `session["csrf_token"]`. The auth endpoints (`register`/`login`/`logout`) are exempt. The token is minted at login and read by the frontend via `/api/auth/me`.

Per-route auth is `@login_required` (Flask-Login). User isolation is enforced **manually in every route** by filtering queries on `owner_id=current_user.id` (see the `owned_project`/`owned_scan` helpers repeated across `backend/api/`) — there is no global ownership middleware, so new endpoints must replicate this pattern.

### Scanning is synchronous

`POST /api/projects/<id>/scans` runs the **entire scan inside the request thread** (`backend/api/scans.py::start_scan`) — there is no background worker or queue. `scan_project()` walks the project tree, applies rules, and writes all findings before the HTTP response returns. This is why `MAX_SCAN_FILE_SIZE` (per-file, default 512 KB) and the ignored-directory list in `config.py` matter: they bound the synchronous work. Large projects block the response.

### Scanner: JSON-driven rule engine

Detection logic is **data, not code**. Rules live as JSON files under `backend/rules/{secrets,injection,dangerous_funcs,dependencies}/`. `RuleEngine` loads them and `pattern_matcher.py` applies their regexes per file. To add a new detection, add a JSON rule file — no Python change is needed unless a new matching primitive is required. `dependency_scanner.py` is the exception: it parses `requirements.txt` against `vulnerable_packages.json` rather than scanning source lines.

Findings are enriched with CVSS/severity in `backend/services/risk/` (`severity.py` maps CVSS → severity string; `risk_calculator.py` aggregates the scan summary stored as JSON in `Scan.summary_json`).

### Fixer: dual strategy with fallback

Fix generation (`POST /api/findings/<id>/fix-preview`) has two engines:
- **`ai_fixer.py`** — sends file context to the Claude API (`CLAUDE_MODEL` in config) for context-aware fixes. Gated by `ENABLE_AI_FIXER`; if the key/SDK is missing the app logs a warning at startup but still runs.
- **`auto_fixer.py`** — fast deterministic pattern fixes for specific rule IDs (e.g. `SEC001` hardcoded secret → `os.getenv()`, `FUNC001` `eval()` → `ast.literal_eval()`).

Applying a fix (`patch_applier.py`) is safety-wrapped: `backup_manager.py` copies the original into `scans/<id>/backup/` first, writes are atomic (`file_helpers.atomic_write_text`, temp file + rename), and `rollback.py` restores from the backup. The `Fix` row tracks `status` (proposed/applied/rolled_back) and timestamps for each transition.

### Frontend

Static HTML + vanilla JS (no framework, no build). Each page in `frontend/` has a matching `js/*.js`. `frontend/js/app.js` defines the global `App` object that every page depends on: `App.api()` wraps `fetch` and injects the CSRF token, `App.session()` resolves auth, `App.shell()` renders nav, `App.escape()` is the XSS guard for injected content. Page routes are served by the `pages` blueprint in `app.py` (note the URL→template mapping in the `PAGES` dict, e.g. `/fix-preview` → `fix_preview.html`).

## Configuration

All config is centralized in `backend/config.py` (single `Config` class, env-var driven). Key knobs: `APP_SECRET_KEY`, `CLAUDE_API_KEY` (or `ANTHROPIC_API_KEY`), `ENABLE_AI_FIXER`, `MAX_SCAN_FILE_SIZE`, `DATABASE_URL`. Leave `DATABASE_URL` unset unless using a non-SQLite database — config.py builds the correct absolute SQLite path automatically, and a relative override breaks startup on Windows.
