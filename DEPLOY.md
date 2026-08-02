# Deploying AppSec Orchestrator (free tier)

Target: a public HTTPS URL you can hand to anyone, at **zero cost**, using
[Render](https://render.com)'s free web service. No credit card required.

Everything the host needs is already in the repo:

| File | Purpose |
| --- | --- |
| `Procfile` | gunicorn start command (works on Render, Railway, Heroku-likes) |
| `render.yaml` | Render blueprint — service settings + env vars, so you don't click through forms |
| `requirements.txt` | now includes `gunicorn` (prod server) and `psycopg2-binary` (optional Postgres) |

---

## 1. Push to GitHub

The remote already exists (`Redkrossresearch/AppSec-Final`). Commit the deploy files
and push to `main`:

```powershell
git add Procfile render.yaml DEPLOY.md requirements.txt app.py backend/config.py
git commit -m "chore: add free-tier deployment config"
git push origin main
```

Confirm `.env` is **not** in the commit — `.gitignore` already covers it, but check
`git status` before pushing. Your Claude API key must never reach GitHub.

## 2. Create the Render service

1. Sign up at [render.com](https://render.com) with your GitHub account.
2. **New → Blueprint**, pick the `AppSec-Final` repo. Render reads `render.yaml`
   and pre-fills everything.
3. Click **Apply**. First build takes ~3–5 minutes (compiling nothing, just wheels).
4. Your app is live at `https://appsec-orchestrator.onrender.com` (or whatever
   name Render assigns).

`APP_SECRET_KEY` is generated automatically by the blueprint — you never set it by hand.

If you'd rather not use the blueprint, create a **Web Service** manually with:

- Build command: `pip install -r requirements.txt`
- Start command: the single line inside `Procfile`
- Env vars: `PYTHON_VERSION=3.13.4`, `APP_SECRET_KEY=<random 32+ chars>`,
  `FLASK_DEBUG=0`, `SESSION_COOKIE_SECURE=1`, `TRUST_PROXY=1`, `ENABLE_AI_FIXER=0`

## 3. Know the free-tier limits

These are real constraints, not warnings to skip:

- **The service sleeps after 15 minutes of no traffic.** The next visitor waits
  ~50 seconds for a cold start. Open the URL yourself a minute before a demo.
- **The disk is ephemeral.** Every restart, redeploy, and wake-from-sleep resets
  the filesystem, wiping `scans/`, `uploads/`, and generated reports — and, on the
  default SQLite setup, every account along with them. **Step 4 is not optional**
  if you want logins to survive; do it before sharing the URL with anyone.
- **512 MB RAM, shared CPU.** Fine for the rule engine on normal repos. A 200 MB
  ZIP full of large source files can exhaust memory, because `start_scan` runs
  the whole scan inside the request thread. Consider lowering `MAX_SCAN_FILE_SIZE`
  or uploading modest test projects for demos.
- **AI fix previews are off** (`ENABLE_AI_FIXER=0`). The Claude API is paid and
  billed separately from hosting — that is the one part of this stack that cannot
  be free. `auto_fixer.py` still produces deterministic fixes for `SEC001`,
  `FUNC001`, etc., so the fix-preview flow still demos without it. To turn AI
  fixes on, add `CLAUDE_API_KEY` in the Render dashboard and flip
  `ENABLE_AI_FIXER=1`.

## 4. Make accounts and scan history persist (required)

Free Postgres that doesn't expire: [Neon](https://neon.tech) (free tier, autosuspends
when idle, no card). Render's own free Postgres is deleted after 30 days, so prefer
Neon for a project you'll keep. [Supabase](https://supabase.com) also works, but pauses
free projects after ~7 days idle.

1. Create a Neon project, copy the connection string
   (`postgresql://user:pass@host/dbname?sslmode=require`).
2. In Render → your service → **Environment**, add `DATABASE_URL` with that value.
3. Redeploy. `db.create_all()` builds the schema on boot; `psycopg2-binary` is
   already in `requirements.txt`.

`backend/config.py` rewrites a legacy `postgres://` prefix to `postgresql://`
automatically (SQLAlchemy 2.x rejects the old form), and sets `pool_pre_ping` so the
first request after Neon wakes from idle reconnects instead of erroring.

> Do not point `DATABASE_URL` at a relative SQLite path. `backend/config.py`
> builds the correct absolute SQLite URI itself; a relative override breaks startup.

### What survives a restart, and what doesn't

Only the database moves to Neon — uploaded source and generated files still sit on
the ephemeral disk. Most of the product is DB-backed, so that split covers more than
it sounds like:

| Survives | Gone after a restart |
| --- | --- |
| Logins and accounts | Uploaded project source in `uploads/` |
| Projects, scans, scan history | Applied-fix backups in `scans/` |
| Every finding, with file, line, severity, CVSS | Sanitized document downloads from `docscans` |
| Fix previews and diffs already generated | |
| Dashboard and analytics | |
| PDF/CSV reports — **regenerated on download** | |

Report content derives entirely from `scan.findings`, so `download_report` rebuilds a
missing file on the fly. Downloads keep working indefinitely with no storage at all.

What needs the original source is re-scanning a project, generating a *new* fix
preview, applying or rolling back a fix, and the fixed-project ZIP. Those return a
clear "re-upload the project ZIP" message rather than failing obscurely. Note in
particular that re-scanning a project whose files are gone reports **`failed` with that
message — never "completed, 0 findings"** ([file_scanner.py](backend/services/scanner/file_scanner.py)),
since a false all-clear from a security scanner is worse than an error.

To make project files durable too, see Phase 2 in the plan notes: persist the uploaded
ZIP as a Postgres column (~25 MB cap against Neon's 0.5 GB free tier) and re-extract it
on demand.

## 5. Verify

```
GET https://<your-app>.onrender.com/api/health   ->  {"status": "ok"}
```

Then register an account, upload a small ZIP, run a code scan and a document
scan, and download a PDF report. Watch **Logs** in the Render dashboard if
anything 500s.

---

## Other free options

| Host | Why you'd pick it | Catch |
| --- | --- | --- |
| **Render** (recommended) | No card, blueprint-driven, HTTPS, GitHub auto-deploy | Sleeps at 15 min, ephemeral disk |
| **Hugging Face Spaces** (Docker SDK) | 16 GB RAM, only sleeps after 48h idle | Needs a Dockerfile; Space is public by default |
| **Google Cloud Run** | Genuinely free at this traffic level, scales to zero | Requires a billing account/card on file |
| **Oracle Cloud Always Free VM** | A real VM with a persistent disk — nothing resets | Card for verification, manual nginx/systemd setup |
| **PythonAnywhere** free | Persistent disk, no sleep | Outbound network is whitelist-only, so the Claude API is unreachable |

## Security note before you make it public

A public URL changes the threat model from "localhost demo":

- **Registration is open.** Anyone who finds the URL can create an account and
  upload ZIPs to your instance. If this is only for evaluators, either take it
  down between demos or add an invite check to `backend/api/auth.py`.
- ZIP extraction already blocks path traversal (`backend/api/projects.py:60-64`),
  but there is no zip-bomb guard — a small crafted archive can fill the disk.
- The in-memory rate limiter resets on every restart and only covers `/api/`.

None of these block a demo deploy. They matter if you leave it running.
