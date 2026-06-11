# AppSec Orchestrator — Developer Onboarding Report

> Generated: 2026-06-11 | Codebase: `appsec_final/`

---

## Table of Contents

1. [Purpose of the Application](#1-purpose-of-the-application)
2. [Technology Stack](#2-technology-stack)
3. [Folder Structure](#3-folder-structure)
4. [Frontend Architecture](#4-frontend-architecture)
5. [Backend Architecture](#5-backend-architecture)
6. [Database Architecture](#6-database-architecture)
7. [Authentication Flow](#7-authentication-flow)
8. [API Flow](#8-api-flow)
9. [Build and Deployment Process](#9-build-and-deployment-process)
10. [Key Dependencies](#10-key-dependencies)
11. [Security Concerns](#11-security-concerns)
12. [Missing Documentation](#12-missing-documentation)
13. [Main Entry Points](#13-main-entry-points)
14. [Important Configuration Files](#14-important-configuration-files)
15. [Environment Variables](#15-environment-variables)
16. [Potential Technical Debt](#16-potential-technical-debt)

---

## 1. Purpose of the Application

**AppSec Orchestrator** is a full-stack web application designed to automate application security scanning and remediation. It targets developers and security analysts who want to identify and fix security vulnerabilities in codebases without manual triage.

### Core Capabilities

| Capability | Description |
|---|---|
| Security Scanning | Scans source code for secrets, injection vulnerabilities, dangerous functions, and vulnerable dependencies |
| AI-Powered Fixing | Uses Claude 3.5 Sonnet (Anthropic API) to generate context-aware, intelligent code fixes |
| Pattern-Based Fixing | Fast rule-based fixes for common vulnerability patterns (e.g., `eval()` → `ast.literal_eval()`) |
| Reporting | Generates PDF and CSV reports summarizing findings and applied fixes |
| Fix Rollback | Creates backups before applying any fix; supports one-click rollback |
| Multi-user Support | User accounts with isolated project workspaces |
| Audit Logging | Every security action is recorded in a tamper-evident audit log |

### Who Uses It

- Security analysts reviewing codebases for vulnerabilities
- Developers wanting automated security feedback on their projects
- Teams running security audits that need exportable reports

---

## 2. Technology Stack

### Backend

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.x |
| Web Framework | Flask | >=3.0,<4.0 |
| ORM | Flask-SQLAlchemy | >=3.1,<4.0 |
| Authentication | Flask-Login | >=0.6,<1.0 |
| AI Integration | Anthropic SDK (Claude API) | >=0.7,<1.0 |
| PDF Generation | ReportLab | >=4.0,<5.0 |
| Password Hashing | werkzeug.security | (bundled with Flask) |
| Environment Config | python-dotenv | >=1.0,<2.0 |

### Frontend

| Layer | Technology |
|---|---|
| Markup | HTML5 static pages |
| Styling | CSS3 with custom properties (no framework) |
| Scripting | Vanilla JavaScript ES6+ |
| HTTP Client | Fetch API |

### Storage

| Type | Technology |
|---|---|
| Database | SQLite (default; configurable via DATABASE_URL) |
| Uploaded ZIPs | Local filesystem (`uploads/`) |
| Extracted Projects | Local filesystem (`scans/`) |
| Reports | Local filesystem (`reports/`) |

### Infrastructure

- No Docker, no containerization (bare Python process)
- No CI/CD pipeline configured
- No reverse proxy configuration included (Nginx/Apache)
- Single-server deployment model

---

## 3. Folder Structure

```
appsec_final/
├── app.py                          # Flask application factory
├── run.py                          # Development entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
│
├── backend/
│   ├── config.py                   # All configuration constants
│   ├── extensions.py               # Flask extensions (SQLAlchemy, LoginManager)
│   ├── models.py                   # SQLAlchemy ORM models
│   │
│   ├── api/                        # REST API blueprints (one file per resource)
│   │   ├── auth.py                 # /api/auth/*
│   │   ├── projects.py             # /api/projects/*
│   │   ├── scans.py                # /api/scans/*
│   │   ├── findings.py             # /api/findings/*
│   │   ├── fixes.py                # /api/fixes/*
│   │   ├── reports.py              # /api/reports/*
│   │   ├── dashboard.py            # /api/dashboard
│   │   └── users.py                # /api/users/*
│   │
│   ├── services/
│   │   ├── scanner/                # Vulnerability detection engine
│   │   │   ├── file_scanner.py     # File discovery + iteration
│   │   │   ├── rule_engine.py      # JSON rule loading + matching
│   │   │   ├── pattern_matcher.py  # Regex pattern detection
│   │   │   └── dependency_scanner.py # requirements.txt vulnerability check
│   │   │
│   │   ├── fixer/                  # Code remediation engine
│   │   │   ├── ai_fixer.py         # Claude API-based intelligent fixing
│   │   │   ├── auto_fixer.py       # Pattern-based fast fixes
│   │   │   ├── backup_manager.py   # Backup files before fix
│   │   │   ├── patch_applier.py    # Write fixed content to disk
│   │   │   ├── rollback.py         # Restore from backup
│   │   │   ├── diff_generator.py   # Generate unified diffs
│   │   │   └── zip_exporter.py     # Export fixed project as ZIP
│   │   │
│   │   ├── reporter/               # Report generation
│   │   │   ├── pdf_generator.py    # PDF reports (ReportLab)
│   │   │   ├── csv_exporter.py     # CSV data export
│   │   │   └── summary_stats.py    # Aggregate statistics
│   │   │
│   │   └── risk/                   # Risk scoring
│   │       ├── risk_calculator.py  # Overall risk metrics
│   │       ├── cvss_mapper.py      # CVSS scores by category
│   │       └── severity.py         # CVSS → severity string
│   │
│   ├── middlewares/
│   │   ├── auth_middleware.py      # Current user identity helper
│   │   ├── error_handler.py        # Global 404/500 handlers
│   │   └── rate_limit.py           # 90 req/60s per IP limiter
│   │
│   ├── rules/                      # Detection rules as JSON
│   │   ├── secrets/                # AWS keys, GitHub tokens, passwords
│   │   ├── injection/              # SQL, command, NoSQL injection
│   │   ├── dangerous_funcs/        # eval, exec, pickle
│   │   └── dependencies/           # Vulnerable package database
│   │
│   └── utils/
│       ├── validators.py           # Path + password validation
│       ├── file_helpers.py         # Safe file I/O utilities
│       ├── git_helpers.py          # Git utilities
│       ├── logger.py               # Rotating file logger
│       └── decorators.py           # Authorization decorator
│
├── frontend/
│   ├── *.html                      # 11 static HTML pages
│   ├── css/style.css               # Dark theme stylesheet
│   └── js/                         # One JS file per page + shared app.js
│
├── scans/                          # Runtime: extracted project files + backups
├── reports/                        # Runtime: PDF, CSV, and ZIP downloads
├── uploads/                        # Runtime: uploaded ZIP archives
├── instance/                       # Runtime: SQLite database (appsec.db)
├── logs/                           # Runtime: rotating log files
│
└── docs/                           # Project documentation
    ├── FEATURES.md
    ├── QUICKSTART.md
    ├── CLAUDE_SETUP.md
    └── UPGRADE_SUMMARY.md
```

---

## 4. Frontend Architecture

### Design Pattern

The frontend uses a **server-rendered static HTML + vanilla JS** pattern. There is no SPA framework (React, Vue, Angular). Each page is a self-contained HTML file that fetches data from the REST API on load.

### Pages

| File | Route | Auth Required | Purpose |
|---|---|---|---|
| index.html | `/` | No | Landing/splash page |
| login.html | `/login` | No | Login form |
| register.html | `/register` | No | Registration form |
| dashboard.html | `/dashboard` | Yes | Metrics, recent scans |
| projects.html | `/projects` | Yes | Project list + upload ZIP |
| project_detail.html | `/projects/<id>` | Yes | Single project + scans |
| findings.html | `/findings` | Yes | All findings with filtering |
| fix_preview.html | `/fix-preview` | Yes | Side-by-side diff viewer |
| scan_detail.html | `/scans/<id>` | Yes | Scan results |
| reports.html | `/reports` | Yes | Report generation + download |
| settings.html | `/settings` | Yes | User settings |

### Shared Infrastructure (`frontend/js/app.js`)

The global `App` object provides:

```javascript
App.api(path, options)   // Fetch wrapper — auto-injects CSRF token, handles 401
App.session()            // GET /api/auth/me — returns current user or redirects
App.shell(active)        // Renders sidebar navigation HTML
App.msg(text, type)      // Displays alert banner (#message element)
App.escape(v)            // HTML-escapes values (XSS prevention)
```

### Styling

- **Theme**: Dark (navy `#07131e` / `#0f2233`, green accent `#20d39b`)
- **Layout**: 230px fixed sidebar + flex main content area
- **No external CSS frameworks** — all custom CSS with CSS custom properties
- **Severity colors**: critical=red, high=orange, medium=yellow, low=blue, info=grey

### State Management

- **Stateless**: No client-side state store; all data is fetched from the API
- **Auth state**: Resolved on each page load via `/api/auth/me`
- **CSRF token**: Stored in `sessionStorage` after login; injected into all mutating requests

### JavaScript Files

| File | Responsibility |
|---|---|
| app.js | Global utilities, API client, navigation shell |
| auth.js | Login, register, logout flows |
| dashboard.js | Metric card population, recent scan list |
| projects.js | Project CRUD, ZIP upload via FormData |
| scans.js | Scan creation, status polling, findings display |
| findings.js | Findings list, severity filtering, status updates |
| fix_preview.js | Diff display, apply/rollback actions |
| reports.js | Report generation, download links |

---

## 5. Backend Architecture

### Application Factory (`app.py`)

The app uses the **Flask Application Factory** pattern:

```python
def create_app(config_override=None):
    app = Flask(__name__)
    # 1. Load config from backend/config.py
    # 2. Initialize extensions (SQLAlchemy, LoginManager)
    # 3. Register API blueprints (/api/auth, /api/projects, etc.)
    # 4. Register frontend routes (serve HTML files)
    # 5. Register error handlers
    # 6. Create database tables (db.create_all())
    # 7. Create runtime directories (scans/, reports/, uploads/, logs/)
    return app
```

### API Blueprint Structure

Each resource group is a separate Flask Blueprint:

```
Blueprint: auth_bp     → prefix /api/auth
Blueprint: projects_bp → prefix /api/projects
Blueprint: scans_bp    → prefix /api/scans and /api/projects/<id>/scans
Blueprint: findings_bp → prefix /api/findings
Blueprint: fixes_bp    → prefix /api/fixes and /api/findings/<id>/fix-*
Blueprint: reports_bp  → prefix /api/reports
Blueprint: dashboard_bp→ prefix /api/dashboard
Blueprint: users_bp    → prefix /api/users
```

### Service Layer

Business logic is isolated in `backend/services/`:

```
scanner/   → file discovery, rule loading, pattern matching, dependency scanning
fixer/     → AI fix generation, pattern fixes, backup, apply, rollback, diff, ZIP export
reporter/  → PDF/CSV generation, statistics
risk/      → CVSS scoring, severity classification
```

### Middleware Stack

Applied globally via `app.before_request`:

1. **Rate Limiter** (`rate_limit.py`): Blocks IPs exceeding 90 requests/60 seconds
2. **CSRF Check** (`app.py`): Validates `X-CSRF-Token` header on POST/PATCH/DELETE
3. **Auth Check** (per-route): `@login_required` decorator from Flask-Login

### Detection Rules

Rules live in `backend/rules/` as JSON files. Each rule has:

```json
{
  "id": "SEC001",
  "category": "secrets",
  "title": "Hardcoded Secret",
  "description": "...",
  "pattern": "regex pattern",
  "severity": "critical",
  "cvss_score": 9.1,
  "fixable": true,
  "recommendation": "..."
}
```

Rule categories: `secrets`, `injection`, `dangerous_functions`, `dependencies`

### CVSS / Severity Mapping

| CVSS Range | Severity |
|---|---|
| ≥ 9.0 | Critical |
| ≥ 7.0 | High |
| ≥ 4.0 | Medium |
| > 0 | Low |

Default category scores: secrets=9.1, injection=8.8, dangerous_functions=7.8, dependencies=7.0

---

## 6. Database Architecture

### Database Engine

- **SQLite** (default) — single file at `instance/appsec.db`
- Configurable to any SQLAlchemy-supported database via `DATABASE_URL`
- Schema created automatically on startup via `db.create_all()`

### Entity-Relationship Summary

```
User ──< Project ──< Scan ──< Finding ──< Fix
                         └──< Report
User ──< AuditLog
```

### Models

#### User
```
id, email (unique), name, password_hash, role, created_at
→ has many: projects, audit_logs
```

#### Project
```
id, name, description, path (filesystem path), owner_id (FK→User), created_at
→ belongs to: User
→ has many: scans
```

#### Scan
```
id, project_id (FK→Project), status (queued/running/completed/failed),
total_files, summary_json (JSON string), error, started_at, completed_at
→ belongs to: Project
→ has many: findings, reports
```

The `summary_json` field stores a JSON object:
```json
{ "total": 12, "critical": 2, "high": 4, "medium": 5, "low": 1, "max_cvss": 9.1 }
```

#### Finding
```
id, scan_id (FK→Scan), rule_id (e.g. "SEC001"), category, severity,
title, description, file_path, line_number, line_text (redacted for secrets),
recommendation, cvss_score, fixable, status (open/fixed/accepted/false_positive)
→ belongs to: Scan
→ has many: fixes
```

#### Fix
```
id, finding_id (FK→Finding), status (proposed/applied/rolled_back),
explanation, original_content, fixed_content, diff (unified diff),
backup_path, created_at, applied_at, rolled_back_at
→ belongs to: Finding
```

#### Report
```
id, scan_id (FK→Scan), format (pdf/csv), output_path, created_at
→ belongs to: Scan
```

#### AuditLog
```
id, user_id (FK→User), action, entity_type, entity_id, details, created_at
Actions: login, create, scan, apply_fix, rollback_fix, fix_all, download_fixed_project
```

---

## 7. Authentication Flow

### Registration

```
Client                              Server
  │                                   │
  ├─ POST /api/auth/register ─────────►
  │   { name, email, password }       │
  │                                   ├─ Validate fields (name, email, min 8-char password)
  │                                   ├─ Check email uniqueness
  │                                   ├─ generate_password_hash(password)
  │                                   ├─ INSERT User
  │                                   ├─ login_user(user) → sets Flask session cookie
  │                                   ├─ Generate CSRF token → store in session
  │                                   ├─ INSERT AuditLog (action=login)
  │◄──────────────────────────────────┤
  │   { user, csrf_token }            │
```

### Login

```
Client                              Server
  │                                   │
  ├─ POST /api/auth/login ────────────►
  │   { email, password }             │
  │                                   ├─ Lookup user by email (case-insensitive)
  │                                   ├─ check_password_hash(hash, password)
  │                                   ├─ login_user(user)
  │                                   ├─ Generate CSRF token → session['csrf_token']
  │                                   ├─ INSERT AuditLog (action=login)
  │◄──────────────────────────────────┤
  │   { user, csrf_token }            │
  │                                   │
  ├─ Store csrf_token in sessionStorage
```

### Subsequent Authenticated Requests

```
Client                              Server
  │                                   │
  ├─ GET /api/auth/me ────────────────►  (called on every page load)
  │   Cookie: session=...             │
  │◄──────────────────────────────────┤
  │   { user, csrf_token }            │
  │                                   │
  ├─ POST /api/projects (mutating) ───►
  │   Cookie: session=...             │
  │   X-CSRF-Token: <token>           ├─ Validate CSRF (secrets.compare_digest)
  │                                   ├─ Check login_required
  │                                   ├─ Verify project ownership
  │◄──────────────────────────────────┤
  │   { ...response }                 │
```

### Logout

```
Client                              Server
  │                                   │
  ├─ POST /api/auth/logout ───────────►
  │   X-CSRF-Token: <token>           │
  │                                   ├─ logout_user()
  │                                   ├─ session.clear()
  │◄──────────────────────────────────┤
  │   { message: "Logged out" }       │
  │                                   │
  ├─ Redirect to /login
```

---

## 8. API Flow

### Complete Endpoint Reference

| Method | Endpoint | Auth | CSRF | Description |
|---|---|---|---|---|
| POST | `/api/auth/register` | No | No | Create user account |
| POST | `/api/auth/login` | No | No | Authenticate user |
| POST | `/api/auth/logout` | Yes | Yes | End session |
| GET | `/api/auth/csrf` | No | — | Get CSRF token |
| GET | `/api/auth/me` | Yes | — | Current user + CSRF |
| GET | `/api/projects` | Yes | — | List user's projects |
| POST | `/api/projects` | Yes | Yes | Upload ZIP or register path |
| GET | `/api/projects/<id>` | Yes | — | Get single project |
| DELETE | `/api/projects/<id>` | Yes | Yes | Delete project |
| GET | `/api/projects/<id>/scans` | Yes | — | List project's scans |
| POST | `/api/projects/<id>/scans` | Yes | Yes | Start new scan |
| GET | `/api/scans/<id>` | Yes | — | Get scan + findings |
| GET | `/api/scans/<id>/download-fixed` | Yes | — | Download fixed ZIP |
| POST | `/api/scans/<id>/fix-all` | Yes | Yes | Apply all fixable findings |
| GET | `/api/findings` | Yes | — | List findings (filterable) |
| GET | `/api/findings/<id>` | Yes | — | Get single finding |
| PATCH | `/api/findings/<id>` | Yes | Yes | Update finding status |
| POST | `/api/findings/<id>/fix-preview` | Yes | Yes | Generate fix preview |
| GET | `/api/fixes/<id>` | Yes | — | Get fix details |
| POST | `/api/fixes/<id>/apply` | Yes | Yes | Apply fix to file |
| POST | `/api/fixes/<id>/rollback` | Yes | Yes | Restore from backup |
| GET | `/api/reports` | Yes | — | List reports |
| POST | `/api/reports/scans/<id>/<format>` | Yes | Yes | Generate PDF or CSV |
| GET | `/api/reports/<id>/download` | Yes | — | Download report file |
| GET | `/api/dashboard` | Yes | — | Aggregate metrics |
| GET | `/api/users/me` | Yes | — | Profile + audit log |
| GET | `/api/health` | No | — | Health check |

### Typical User Flow

```
1. Register → POST /api/auth/register
2. Upload project → POST /api/projects (multipart/form-data with ZIP)
3. Start scan → POST /api/projects/<id>/scans
4. Poll scan → GET /api/scans/<id> until status = "completed"
5. View findings → GET /api/findings?scan_id=<id>&severity=critical
6. Preview fix → POST /api/findings/<id>/fix-preview
7. Apply fix → POST /api/fixes/<id>/apply
8. (Optional) Rollback → POST /api/fixes/<id>/rollback
9. Generate report → POST /api/reports/scans/<id>/pdf
10. Download report → GET /api/reports/<id>/download
```

### Scanning Pipeline (Internal)

```
POST /api/projects/<id>/scans
    ↓
file_scanner.py → discovers files (respects SCAN_IGNORED_DIRS, ALLOWED_EXTENSIONS, size limit)
    ↓
rule_engine.py → loads JSON rules from backend/rules/
    ↓
pattern_matcher.py → applies regex patterns per file
    ↓
dependency_scanner.py → checks requirements.txt against vulnerable_packages.json
    ↓
risk_calculator.py → computes CVSS scores, severity distribution
    ↓
INSERT Scan (status=completed) + INSERT Findings
```

### Fix Pipeline (Internal)

```
POST /api/findings/<id>/fix-preview
    ↓
ai_fixer.py → sends code context to Claude 3.5 Sonnet API
    (fallback: auto_fixer.py for SEC001, FUNC001 patterns)
    ↓
diff_generator.py → compute unified diff
    ↓
INSERT Fix (status=proposed)
    ↓
POST /api/fixes/<id>/apply
    ↓
backup_manager.py → copies original file to scans/<id>/backup/
    ↓
patch_applier.py → atomic write (temp file + rename)
    ↓
UPDATE Fix (status=applied), UPDATE Finding (status=fixed)
```

---

## 9. Build and Deployment Process

### Development Setup

```bash
# 1. Clone repository
git clone <repo>
cd appsec_final

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env: set CLAUDE_API_KEY, APP_SECRET_KEY

# 5. Start development server
python run.py
# App available at http://127.0.0.1:5000
```

### What Happens on First Start

1. Flask reads `.env` via `python-dotenv`
2. `create_app()` initializes SQLAlchemy
3. `db.create_all()` creates all tables in `instance/appsec.db`
4. Runtime directories created: `scans/`, `reports/pdf/`, `reports/csv/`, `reports/downloads/`, `uploads/`, `logs/`
5. Flask dev server starts on port 5000

### Production Considerations

- **WSGI Server**: The app is Gunicorn-compatible (`app.py` exports `app = create_app()`)
- **Recommended**: `gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"`
- **Reverse Proxy**: Place Nginx/Apache in front for static files and TLS termination
- **Database**: Replace SQLite with PostgreSQL for multi-user production use
- **Secret Key**: Set `APP_SECRET_KEY` to a cryptographically random string
- **Debug Mode**: Set `FLASK_DEBUG=0` in production

### No CI/CD or Docker

There is currently **no Dockerfile, docker-compose.yml, or CI/CD pipeline** in the repository. Deployment is entirely manual.

---

## 10. Key Dependencies

| Package | Version | Purpose | Notes |
|---|---|---|---|
| Flask | >=3.0,<4.0 | Web framework | Application factory pattern |
| Flask-SQLAlchemy | >=3.1,<4.0 | ORM + DB | SQLite default |
| Flask-Login | >=0.6,<1.0 | Session management | Cookie-based sessions |
| python-dotenv | >=1.0,<2.0 | .env file loading | Required for API key config |
| reportlab | >=4.0,<5.0 | PDF generation | Used in pdf_generator.py |
| anthropic | >=0.7,<1.0 | Claude API client | Required for AI fixes |
| werkzeug | (Flask dep) | Password hashing, utilities | Part of Flask install |

All dependencies pinned to major version ranges. No pinned minor/patch versions, which can cause subtle breakage on `pip install`.

---

## 11. Security Concerns

### Implemented Security Controls

| Control | Implementation | Location |
|---|---|---|
| Password hashing | werkzeug `generate_password_hash` / `check_password_hash` | `backend/api/auth.py` |
| CSRF protection | Custom token via `secrets.token_hex(32)`, constant-time comparison | `app.py`, `app.js` |
| Rate limiting | 90 req/60s per IP (sliding window) | `backend/middlewares/rate_limit.py` |
| Path traversal prevention | ZIP extraction validated with `relative_to()` | `backend/api/projects.py` |
| SQL injection prevention | SQLAlchemy parameterized queries (ORM) | All DB access |
| XSS prevention | `App.escape()` HTML-escapes all dynamic content | `frontend/js/app.js` |
| Secret redaction | Secrets shown as `<redacted: possible secret>` in UI | `backend/api/findings.py` |
| User isolation | All queries filter by `owner_id = current_user.id` | All API routes |
| Audit logging | Every sensitive action recorded in `audit_logs` | `backend/api/*.py` |
| File size limit | Skip files > 512 KB during scanning | `backend/config.py` |

### Known Security Gaps and Risks

#### High Priority

1. **No HTTPS enforcement** — The application has no TLS configuration. Cookies and CSRF tokens travel in plaintext unless a reverse proxy adds TLS. The session cookie also lacks the `Secure` flag.

2. **SQLite in production** — SQLite does not support concurrent writes well. Under load, this causes database lock errors and potential data corruption.

3. **Uploaded ZIPs stored on disk long-term** — ZIP files in `uploads/` are never automatically purged. Maliciously crafted or large archives can accumulate and exhaust disk space.

4. **No Content Security Policy (CSP) header** — The application serves no CSP header, leaving it open to potential XSS escalation through third-party injections.

5. **Session cookie flags** — The Flask session cookie should set `HttpOnly`, `Secure`, and `SameSite=Strict`. Current config does not explicitly set all three.

#### Medium Priority

6. **Dependency rule database is static** — `backend/rules/dependencies/vulnerable_packages.json` is a hardcoded list. It will go stale and miss newly disclosed CVEs without a process to update it.

7. **AI fix quality not validated** — `ai_fixer.py` accepts the Claude API response as a valid fix with minimal validation (only checks it differs from original). A hallucinated or malformed fix could corrupt source files.

8. **No upload file type validation beyond extension** — ZIP uploads are validated by file extension. A maliciously renamed file could pass the check.

9. **Report files are world-readable on disk** — PDF/CSV reports are written to `reports/` with default filesystem permissions. Another process or user on the same server could read them.

10. **Rate limiter is in-memory only** — The rate limiter uses a `defaultdict` in process memory. It resets on server restart and does not work behind a load balancer.

#### Low Priority

11. **No password complexity enforcement beyond length** — Only `len(password) >= 8` is checked. No character class requirements.

12. **Email not verified on registration** — Users can register with any email address without verification.

13. **No account lockout after failed logins** — The rate limiter provides some protection, but there is no per-account lockout after repeated failed login attempts.

14. **Backup files stored in scan directory** — Backups in `scans/<id>/backup/` are never pruned. Long-running deployments accumulate large amounts of backup data.

---

## 12. Missing Documentation

| Gap | Impact |
|---|---|
| No API documentation (OpenAPI/Swagger) | New developers must read source code to understand request/response schemas |
| No production deployment guide | No instructions for Nginx, Gunicorn, or systemd setup |
| No Docker / containerization docs | Manual environment setup is error-prone |
| No database migration guide | `db.create_all()` only creates missing tables; schema changes require manual migration |
| No test suite | Zero automated tests — regressions are only caught manually |
| Rule format not documented | Adding new detection rules requires reading `rule_engine.py` to understand JSON schema |
| AI fixer prompt not documented | The Claude prompt template in `ai_fixer.py` is not explained anywhere |
| No architecture decision records (ADRs) | The rationale for design choices (vanilla JS, SQLite, no framework) is unknown |
| No changelog / release notes beyond UPGRADE_SUMMARY.md | Hard to track what changed between versions |
| `backend/utils/git_helpers.py` has no usage documentation | Purpose is unclear without reading source |

---

## 13. Main Entry Points

| File | Purpose |
|---|---|
| [run.py](../run.py) | **Start here for development** — launches Flask dev server on port 5000 |
| [app.py](../app.py) | Application factory — the WSGI entrypoint for production |
| [backend/config.py](../backend/config.py) | All configuration constants — first place to check for tunable values |
| [backend/models.py](../backend/models.py) | All database models — understand the data model here |
| [backend/api/](../backend/api/) | All API endpoints — one blueprint file per resource |
| [frontend/js/app.js](../frontend/js/app.js) | Frontend shared utilities — all pages depend on this |
| [backend/rules/](../backend/rules/) | Detection rule definitions — extend scanning here |

---

## 14. Important Configuration Files

| File | Description |
|---|---|
| [.env.example](../.env.example) | Template for all required environment variables — copy to `.env` |
| [backend/config.py](../backend/config.py) | Python config class — database URL, upload limits, scan settings, API keys |
| [requirements.txt](../requirements.txt) | Python package dependencies |
| [backend/rules/](../backend/rules/) | JSON rule files that define what vulnerabilities are detected |

### `backend/config.py` Key Constants

| Constant | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | env: `APP_SECRET_KEY` | Flask session signing key |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///./instance/appsec.db` | Database connection |
| `MAX_UPLOAD_SIZE` | 200 MB | Maximum ZIP upload size |
| `MAX_SCAN_FILE_SIZE` | 512 KB | Skip files larger than this during scanning |
| `SCAN_IGNORED_DIRS` | `.git`, `node_modules`, `.venv`, `__pycache__`, etc. | Directories excluded from scanning |
| `ALLOWED_EXTENSIONS` | `.py`, `.js`, `.ts`, `.php`, `.java`, `.sql`, ... (23 types) | File types scanned |
| `CLAUDE_MODEL` | `claude-3-5-sonnet-20241022` | Anthropic model for AI fixes |
| `ENABLE_AI_FIXER` | `1` | Set to `0` to disable AI and use pattern fixes only |

---

## 15. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `CLAUDE_API_KEY` | **Yes** (for AI fixes) | — | Anthropic API key (`sk-ant-...`) |
| `ANTHROPIC_API_KEY` | No | — | Alias for `CLAUDE_API_KEY` |
| `APP_SECRET_KEY` | **Yes** (production) | `dev-secret-change-in-production-xyz` | Flask session signing key |
| `FLASK_DEBUG` | No | `0` | Enable Flask debug mode (`1` = on) |
| `DATABASE_URL` | No | `sqlite:///./instance/appsec.db` | Database connection string |
| `MAX_SCAN_FILE_SIZE` | No | `524288` (512 KB) | Max bytes per scanned file |
| `ENABLE_AI_FIXER` | No | `1` | Set to `0` to disable Claude API calls |

### Setup

```bash
# Windows PowerShell
Copy-Item .env.example .env
# Edit .env and set values

# Minimum viable .env
APP_SECRET_KEY=<random 32+ char string>
CLAUDE_API_KEY=sk-ant-...
```

---

## 16. Potential Technical Debt

### Architecture

| Issue | Risk | Effort to Fix |
|---|---|---|
| No test suite whatsoever | High — regressions go undetected | High |
| SQLite as default database | Medium — not suitable for multi-user production | Medium |
| No database migrations (using `db.create_all()`) | High — schema changes break existing deployments | High |
| In-memory rate limiter resets on restart | Medium — burst attacks after crash/deploy | Low |
| No CI/CD pipeline | Medium — manual deployments are error-prone | Medium |
| No Docker / containerization | Medium — inconsistent environments | Medium |

### Code Quality

| Issue | Risk | Effort to Fix |
|---|---|---|
| `summary_json` stored as a text column | Low — harder to query/index than a proper JSON column | Low |
| Vulnerability rule database is static JSON | High — goes stale; no CVE feed integration | Medium |
| AI fix validation is minimal (only diff check) | Medium — malformed fixes could corrupt code | Medium |
| Uploaded ZIPs never auto-purged | Medium — disk exhaustion over time | Low |
| Backup files never pruned | Low — slow disk usage growth | Low |
| Password policy only enforces length ≥ 8 | Low — weak passwords accepted | Low |
| No email verification on registration | Low — throwaway accounts possible | Low |
| Dependencies not pinned to exact versions | Low — `pip install` may pull breaking minor versions | Low |

### Missing Features (implied by current design)

| Feature | Notes |
|---|---|
| Multi-language fix support | AI fixer detects language but many auto-fixer patterns are Python-specific |
| CVE feed integration | Dependency scanner uses a static rule file |
| Scheduled/automated scans | All scans are manually triggered |
| Webhook / notification support | No alerts when scan completes |
| Role-based access control (RBAC) | User model has a `role` field but it is unused in access checks |
| Team / organization support | All projects are owned by a single user |

---

*End of onboarding report. For questions, refer to the existing docs in [FEATURES.md](../FEATURES.md), [QUICKSTART.md](../QUICKSTART.md), and [CLAUDE_SETUP.md](../CLAUDE_SETUP.md).*
