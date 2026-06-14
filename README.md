# AppSec Orchestrator — Unified Two-Engine Security Platform

AppSec Orchestrator is a Flask web app that combines **two security scan engines behind one login,
dashboard, findings view and reporting pipeline**:

| Engine | Scans | Produces |
|---|---|---|
| 🧑‍💻 **Code (AppSec)** | Uploaded source projects (ZIP or local path) | Vulnerability findings (secrets, SQL/command injection, dangerous functions, vulnerable deps) + **AI/pattern code fixes** |
| 📑 **Document (DeepSec)** | Uploaded documents (PDF, DOCX, XLSX, PPTX, ZIP, images) | Malware/threat findings (payloads, shellcode, embedded objects, IOCs) + threat intelligence + a **sanitized copy** |

Both engines write to the same `Scan → Finding → Report` model, distinguished by `Scan.scan_type`
(`"code"` | `"document"`). Document findings are analysis-only (`fixable=False`) and never run through the
code auto-fixer. This is the result of merging the standalone DeepSec document scanner into AppSec as a
service package — see [MERGE_STRATEGY.md](MERGE_STRATEGY.md) for the full plan and rationale.

## Quick start

```powershell
# 1. Create & activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies (AppSec + DeepSec document libs)
pip install -r requirements.txt

# 3. Configure
Copy-Item .env.example .env
#   set APP_SECRET_KEY; CLAUDE_API_KEY is optional (only the AI code-fixer needs it —
#   set ENABLE_AI_FIXER=0 to run without a key). The document engine needs no API key.

# 4. Run (dev server)
python run.py            # http://127.0.0.1:5000
```

The SQLite database (`instance/appsec.db`) and runtime directories (`scans/`, `reports/`, `uploads/`,
`logs/`) are created automatically on first startup. There is no separate build, migration or test step.

> **Note:** running via `python run.py` does **not** load `.env` (the app reads real environment variables,
> not the file). Set config via your shell environment, or export the values before launching.

## Using the two engines

**Code scan:** Projects → create a project (upload a ZIP or register a path) → Run Security Scan →
review findings → generate/apply AI or pattern fixes → download the fixed ZIP → export PDF/CSV report.

**Document scan:** Documents → Scan Document → upload a PDF/DOCX/XLSX/PPTX/ZIP/image. The file is scanned
synchronously and you are taken to the standard results view. A JSON report and a sanitized copy are saved
as downloadable report artifacts; PDF/CSV reports work over document scans too.

## Architecture at a glance

```
User → Project → Scan (scan_type: code | document) → Finding → (Fix, code only)
                                                            └→ Report (pdf | csv | json | sanitized)
```

- `app.py` — Flask application factory; one `before_request` guard handles rate limiting + CSRF.
- `backend/api/` — REST blueprints. `scans.py` (code) and `docscans.py` (document) are the two scan entry
  points; both write the same `Finding` rows. User isolation is enforced per-route via `owner_id`.
- `backend/services/scanner/` — JSON-rule-driven code scanner.
- `backend/services/docscan/` — DeepSec document engine; `adapter.py::scan_document()` maps DeepSec output
  onto AppSec's Finding contract (the one clean seam between the engines).
- `backend/services/fixer/`, `reporter/`, `risk/` — shared fix, report and CVSS/severity logic.
- `frontend/` — static HTML + vanilla JS; document upload at `document_scan.html`, results reuse
  `scan_detail.html`.

## Docs

- [FEATURES.md](FEATURES.md) — full feature list and API reference
- [QUICKSTART.md](QUICKSTART.md) — 5-minute setup
- [CLAUDE_SETUP.md](CLAUDE_SETUP.md) — configuring the optional AI code-fixer
- [MERGE_STRATEGY.md](MERGE_STRATEGY.md) — how the two engines were merged
- [docs/project_onboarding.md](docs/project_onboarding.md) — developer onboarding report

## Status

Both engines are functional and share the scan/finding/report pipeline. The shared multi-provider AI layer
(unifying the code-fixer and document AI summary) is a planned follow-up (Phase 4 of the merge); today the
AI code-fixer uses Claude directly and the document engine's analysis runs without requiring an API key.
