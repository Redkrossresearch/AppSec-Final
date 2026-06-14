# Merge Strategy: AppSec Orchestrator + DeepSec

**Goal:** One product. AppSec is the host; DeepSec is absorbed as a second scan engine ("document / malware analysis"). Approach is a **pragmatic stitch** — get them running as one app under shared login and navigation, reusing AppSec's existing scan/finding/report machinery, and clean up internals later.

_Generated 2026-06-12._

---

## 1. Where each project stands

| | AppSec Orchestrator (host) | DeepSec (absorbed) |
|---|---|---|
| Purpose | Scans **source code** for vulns (secrets, SQLi, XSS, injection) and AI-fixes them | Analyzes **uploaded documents** (PDF/DOCX/ZIP) for hidden malware, payloads, IOCs |
| App structure | Flask **app factory** + blueprints | Single flat `app.py`, inline routes |
| Frontend | Static HTML/CSS/JS → REST API | Server-rendered Jinja templates |
| Auth / multi-user | Flask-Login, per-user projects, CSRF, rate limiting | **None** |
| Persistence | SQLAlchemy (`User/Project/Scan/Finding/Fix/Report`), SQLite | **None** (`ScanResult` is a throwaway class) |
| AI | Single Claude client | **Multi-provider router** (Claude/OpenAI/Gemini/DeepSeek/local) — currently a stub |
| Domain depth | Solid but ordinary scanners | **Rich**: extractors, `intelligence/` (MITRE, threat families, attack chains, CVE, exploitability), sanitizers |
| Reports | PDF + CSV | JSON + sanitized-file copy |

**The takeaway:** AppSec has the *skeleton* (auth, DB, API, frontend shell), DeepSec has the *brains* (document threat analysis). The merge = put DeepSec's brains inside AppSec's skeleton. They don't really compete — they're two scan types of one security platform.

---

## 2. The one clean seam to build around

AppSec's scanner already returns a plain contract that the API writes straight into the database:

```python
result = scan_project(...)          # -> {"findings": [ {...}, ... ], "files_scanned": N, "summary": {...}}
for item in result["findings"]:
    db.session.add(Finding(scan_id=scan.id, **item))
```

So a `Finding` is just a dict with these keys: `rule_id, category, severity, title, description, file_path, line_number, line_text, recommendation, cvss_score, fixable`.

**Strategy in one sentence:** wrap DeepSec's document scanners behind *exactly this contract* — one adapter function `scan_document(path) -> {"findings": [...], "files_scanned": 1, "summary": {...}}` — and DeepSec rides AppSec's entire Scan → Finding → Report → frontend pipeline for free. That is the whole trick that makes this a "stitch" instead of a rewrite.

---

## 3. Target shape (after the stitch)

```
appsec_final/                       # the one app
├── app.py                          # unchanged factory; one extra blueprint registered
├── backend/
│   ├── models.py                   # Scan gains a `scan_type` column ("code" | "document")
│   ├── api/
│   │   ├── scans.py                # existing code-scan entry point
│   │   └── docscans.py             # NEW: upload doc -> scan_document() -> Finding rows
│   └── services/
│       ├── scanner/                # existing AppSec code scanner
│       ├── docscan/                # NEW: DeepSec lives here
│       │   ├── __init__.py         #   exposes scan_document(path) -> AppSec contract
│       │   ├── adapter.py          #   maps DeepSec findings -> Finding dict schema
│       │   ├── scanners/           #   (moved from deepsec/scanners)
│       │   ├── extractors/         #   (moved from deepsec/extractors)
│       │   ├── intelligence/       #   (moved from deepsec/intelligence)
│       │   └── sanitizers/         #   (moved from deepsec/sanitizers)
│       └── ai/                     # adopt DeepSec's multi-provider router as the shared AI layer
└── frontend/                       # one new page: document upload + results (reuses findings UI)
```

Two scan engines, one shell, one login, one dashboard, one findings view.

---

## 4. Key decisions (made for a pragmatic stitch)

1. **AppSec's app factory and frontend win.** DeepSec's flat `app.py` and Jinja pages are dropped as the entry point. Its scan *result* page can be reused short-term as a single embedded view, but new work uses AppSec's REST + static-page pattern.
2. **DeepSec becomes a service package, not an app.** Move `scanners/ extractors/ intelligence/ sanitizers/` under `backend/services/docscan/`. Fix imports from `from scanners.x` → `from backend.services.docscan.scanners.x`.
3. **One Scan/Finding model, distinguished by `scan_type`.** Add `scan_type` (default `"code"`) to `Scan`. Document findings map onto the same `Finding` table via the adapter. DeepSec-specific fields (MITRE technique, threat family, attack chain, confidence, exploitability) go into the `Scan.summary_json` blob and/or `Finding.description`/`recommendation` for now — no new tables in the stitch phase.
4. **Adopt DeepSec's AI router as the shared AI layer** (it already supports multiple providers; AppSec only had Claude). Note: it's currently a stub returning offline mode — wire it to AppSec's existing Claude client so both engines share one config.
5. **Reports converge on AppSec's reporter.** Keep DeepSec's JSON report + sanitized-file output as extra `Report` rows (format `"json"`, plus a `"sanitized"` artifact path). AppSec's PDF/CSV generators then work on document scans too, since findings are unified.
6. **Port collision is non-negotiable:** both bind `127.0.0.1:5000`. Only AppSec's server runs after the merge; DeepSec's `app.run(...)` is deleted.
7. **Dependency union:** add DeepSec's libs to AppSec's `requirements.txt` — `PyPDF2, python-docx, openpyxl, python-pptx, Pillow, requests, yara-python`. Both already share Flask + reportlab + anthropic. Pin Werkzeug to one version.

---

## 5. Step-by-step plan

### Phase 0 — Safety net (before touching code)
1. Branch both repos; pick `appsec_final` as the merge target repo.
2. Copy DeepSec into it on a throwaway path first so nothing is lost; commit.
3. Get AppSec running clean (`python run.py`) and confirm a code scan works end to end. This is your known-good baseline.

### Phase 1 — Drop DeepSec in as a service package
4. Move `deepsec/{scanners,extractors,intelligence,sanitizers,ai,utils}` → `appsec_final/backend/services/docscan/` (keep DeepSec's `ai/` aside — it merges in Phase 4).
5. Rewrite internal imports (`scanners.x` → `backend.services.docscan.scanners.x`, etc.). A find-replace + a quick `python -c "import ..."` smoke test per subpackage catches most of it.
6. Delete DeepSec's `app.py`, `config.py`, `requirements.txt` (its entry point and config are superseded).
7. Merge DeepSec's pip deps into AppSec's `requirements.txt`; `pip install -r requirements.txt` in the venv.

### Phase 2 — Build the one adapter (the heart of the stitch)
8. Write `backend/services/docscan/adapter.py` with `scan_document(path) -> {"findings": [...], "files_scanned": 1, "summary": {...}}`.
9. Inside it, call DeepSec's `scan_pdf/scan_docx/scan_zip` based on extension, collect their raw findings, and **map each one to AppSec's `Finding` dict schema** (`rule_id, category, severity, title, description, file_path, line_number, line_text, recommendation, cvss_score, fixable`). Set `fixable=False` for document findings (DeepSec sanitizes, it doesn't code-fix). Fold MITRE/threat-family/attack-chain into `description`/`recommendation` and the scan `summary`.
10. Unit-test the adapter on a sample PDF/DOCX/ZIP: assert every returned finding has all required keys.

### Phase 3 — Wire it into the app
11. Add `scan_type` column to `Scan` (default `"code"`); delete the SQLite DB so `db.create_all()` rebuilds it (dev only — no migration tooling here).
12. Create `backend/api/docscans.py` blueprint: authenticated document upload → save to `uploads/` → `scan_document()` → write `Scan(scan_type="document")` + `Finding` rows + `AuditLog`, mirroring `scans.py::start_scan`. Register it in `backend/api/__init__.py`.
13. Add one frontend page (`document_scan.html` + a JS file) for upload, reusing the existing findings/results components. Add a nav entry.
14. Persist DeepSec's JSON report + sanitized file as `Report` rows so they show up in the existing reports view.

### Phase 4 — Unify AI and reporting
15. Replace AppSec's lone Claude call with DeepSec's `ai_router`; point the router at `Config.CLAUDE_API_KEY` and finish the API-mode branch (it's a stub today). Both engines now share one AI config.
16. Confirm PDF/CSV report generation runs over a document scan (it should, since findings are unified).

### Phase 5 — Verify
17. End-to-end: register/login → run a **code** scan (regression) → run a **document** scan → both show in dashboard, findings, and reports.
18. Confirm only one server/port, no import errors, sanitized-file download works, AI summary renders for both scan types.
19. Update `README` / `FEATURES.md` to describe the unified two-engine product.

---

## 6. Risks & watch-items

- **Import rewrites are the biggest time sink**, not the logic. DeepSec uses deep relative imports across `scanners↔extractors↔intelligence`; budget time for a clean pass and per-package smoke imports.
- **Finding-schema mismatch** is where data gets lost. DeepSec's `{"type","value"}` shape is much looser than AppSec's structured `Finding`. The adapter is load-bearing — get its mapping right and review what fields get flattened into `description`/`summary`.
- **No DB migrations exist.** In dev you can drop `instance/appsec.db` and recreate. If there's real data later, you'll need Alembic before adding `scan_type`.
- **DeepSec's AI router is a stub** (returns offline mode regardless). Don't assume cloud AI works on day one — Phase 4 actually implements it.
- **`fixable` semantics differ.** AppSec "fixes" code; DeepSec "sanitizes" documents. Keep them as distinct actions; don't try to route document findings through the code auto-fixer.
- **Werkzeug version pin** — AppSec uses ranges, DeepSec pins `3.1.3`. Reconcile to avoid a resolver conflict.

---

## 7. Effort sketch

The stitch is realistically **Phases 1–3 for a working merged app** (drop-in + adapter + one API route + one page), with Phases 4–5 to make AI and reporting first-class. The adapter and the import rewrites are the two real pieces of work; everything else is reuse of what AppSec already has.
