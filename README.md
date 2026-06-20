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

## Installation & Setup

### Prerequisites

- **Python 3.10+** ([download](https://www.python.org/downloads/))
- **Git** ([download](https://git-scm.com/download/win))
- **~230 MB disk space** (130 MB if Python is already installed)

### Step 1: Clone the Repository

```powershell
git clone https://github.com/TanmayKamble004/AppSec-Final.git
cd AppSec-Final
```

### Step 2: Create a Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

You should see `(.venv)` in your terminal prompt after activation.

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs Flask, SQLAlchemy, Anthropic SDK, document parsing libraries, and all other dependencies (~120 MB).

### Step 4: Configure Environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set:
- **`APP_SECRET_KEY`** — Generate a random secret (required for session security)
  ```powershell
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Paste the output as `APP_SECRET_KEY` value.

- **`CLAUDE_API_KEY`** — (Optional) Set only if using AI code-fixer. Get from [console.anthropic.com](https://console.anthropic.com)
  - If not set, the app runs fine with pattern-based auto-fixer only. Set `ENABLE_AI_FIXER=0` to disable AI fixer.

- **Other settings** — Leave defaults unless you need a custom database path or port.

### Step 5: Run the Application

```powershell
python run.py
```

Open your browser to **`http://127.0.0.1:5000`** — you should see the login page.

### First-Time Setup

The database and runtime directories are created automatically on first startup:
- `instance/appsec.db` — SQLite database
- `scans/`, `uploads/`, `reports/`, `logs/` — runtime directories

There is no separate migration or init command needed.

### Verify Installation

1. Navigate to `http://127.0.0.1:5000`
2. Register a new account
3. Upload a test project ZIP or try document scanning
4. Run a scan and verify findings appear

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `python: command not found` | Python not installed or not in PATH. Reinstall and check "Add Python to PATH" |
| `ModuleNotFoundError: No module named 'flask'` | Activate venv: `.venv\Scripts\activate` and re-run `pip install -r requirements.txt` |
| Port 5000 already in use | Change port: `python run.py --port 5001` or kill the process using port 5000 |
| `.env` not loading | `run.py` reads environment variables, not the file. Export values: `$env:APP_SECRET_KEY="value"; python run.py` |

> **Note:** running via `python run.py` does **not** load `.env` automatically (the app reads real environment variables,
> not the file). Export environment variables before launching, or set them in your shell profile.

## Quick Start (Summary)

```powershell
git clone https://github.com/TanmayKamble004/AppSec-Final.git
cd AppSec-Final
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set APP_SECRET_KEY
python run.py            # http://127.0.0.1:5000
```

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
