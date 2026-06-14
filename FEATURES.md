# 🚀 AppSec Orchestrator - Unified Two-Engine Security Platform

A complete security platform with **two scan engines behind one login, dashboard, and findings view**:

- **🧑‍💻 Code engine (AppSec)** — scans uploaded source code for vulnerabilities (secrets, SQL/command injection, dangerous functions, vulnerable dependencies) and **uses AI to fix any code vulnerability**, not just pattern-matched ones.
- **📑 Document engine (DeepSec)** — analyzes uploaded documents (PDF, DOCX, XLSX, PPTX, ZIP, images) for hidden malware, payloads, shellcode, embedded objects and indicators of compromise, with threat-intelligence enrichment (threat family, MITRE technique, attack chain) and a sanitized copy of the file.

Both engines write to the **same `Scan → Finding → Report` data model** (distinguished by `Scan.scan_type` = `"code"` | `"document"`), so document scans ride the existing findings UI, reporting and audit log for free. Document findings are analysis-only (`fixable=False`) and are never routed through the code auto-fixer.

## ✨ What's New (6 Major Upgrades)

### 1. 🤖 AI-Powered Fixer
- **Auto-fixes ANY security issue**, not just hardcoded rules
- Uses Claude 3.5 Sonnet API for intelligent code fixing
- Falls back to pattern-matching for common issues (faster)
- Preserves code logic while fixing security vulnerabilities

### 2. 👁️ Side-by-Side Diff Viewer  
- **Visual comparison** of vulnerable vs fixed code
- Line-by-line highlighting of changes
- Color-coded: red (removed), green (added), gray (context)
- Makes it easy to understand exactly what changed

### 3. 📄 Detailed PDF Reports
- **Per-finding breakdown** with code snippets
- Shows the vulnerable code, what was wrong, and how it was fixed
- Color-coded by severity (Critical/High/Medium/Low)
- Professional formatting for sharing with teams

### 4. ⬇️ Download Fixed ZIP
- **Download the entire corrected project** after fixes are applied
- Includes all your changes in one ZIP file
- Automatically excludes .venv, node_modules, .git, etc.
- Ready to deploy or share with your team

### 5. ⚡ Fix All That Actually Works
- **One-click security remediation** for your entire codebase
- AI intelligently fixes every finding
- Creates backups before applying fixes
- Roll back any change if needed

### 6. 💻 AI Code Editor
- **View & edit proposed fixes** before applying
- Ask AI to improve the fix with custom suggestions
- Test variations of the fix
- Accept or reject before applying to code

## 🎯 Quick Start

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get your Claude API key
# Visit: https://console.anthropic.com/
# Create an API key in your account

# 3. Set up environment
cp .env.example .env
# Edit .env and add your CLAUDE_API_KEY:
# CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxx
```

### Running the App

```bash
python run.py
# Open http://localhost:5000
```

### Demo Workflow

1. **Register** a new account
2. **Create Project** → Upload your ZIP file (up to 200MB)
3. **Run Scan** → Detects all security issues
4. **View Findings** → See all vulnerabilities with severity
5. **Generate Fix** → Click any finding to generate AI fix
6. **Review** → Side-by-side diff shows exactly what changes
7. **Apply** → Click "Apply Fix" (backup created automatically)
8. **Download** → Get the corrected project as ZIP
9. **Generate Report** → PDF/CSV with all details

## 🔑 Features by Category

### 🔍 Code Security Scanner
- Detects: Hardcoded secrets, SQL injection, XSS, command injection, eval/exec, pickle, dangerous functions
- Supports: Python, JavaScript, TypeScript, Java, PHP, Ruby, Go, C/C#, SQL, Bash
- Smart filtering: Skips .venv, node_modules, .git, __pycache__, etc.
- Detailed reporting: File, line number, vulnerable code snippet

### 📑 Document Malware Scanner (DeepSec engine)
- **Upload a document** (PDF, DOCX, XLSX, PPTX, ZIP, PNG/JPG) at **Documents → Scan Document**
- Detects: embedded payloads, shellcode, hidden/obfuscated code, suspicious APIs, PowerShell & exploit
  indicators, malware signatures, YARA matches, embedded files/objects, IOCs (URLs, IPs)
- **Threat intelligence**: threat family, MITRE technique, attack chain, reputation, exploitability and an
  executive summary — folded into the scan summary and the downloadable JSON report
- **Sanitized copy**: a cleaned version of the document is produced and downloadable as a report artifact
- Results open in the **same findings view** as code scans; findings are analysis-only (no auto-fix)
- Severity/CVSS are mapped per indicator (e.g. Payload/Shellcode/YARA → critical, Embedded File → high)

### 🛠️ Auto-Fixer
#### AI-Based (Falls back from pattern matcher)
- **For ANY finding**: Claude API generates context-aware fixes
- **Smart imports**: Adds necessary imports automatically
- **Preserves code**: Only changes the vulnerable line, keeps everything else
- **Validates**: Checks fix doesn't duplicate original code

#### Pattern-Based (Fast)
- **SEC001**: Hardcoded secrets → environment variables
- **FUNC001**: eval() → ast.literal_eval()
- **More**: Expandable rule definitions in backend/rules/

### 📊 Reporting
- **PDF**: Full report with code snippets and fixes
- **CSV**: Spreadsheet export for analysis
- **Dashboard**: Real-time metrics and status
- **Audit Log**: Track all scans, fixes, and changes

## 📁 Project Structure

```
appsec_final/
├── app.py                          # Flask app entry point
├── run.py                          # Development server
├── requirements.txt                # Python dependencies
├── .env.example                    # Configuration template
│
├── backend/
│   ├── config.py                   # Settings (DB, API keys, limits)
│   ├── extensions.py               # Flask extensions (DB, Login)
│   ├── models.py                   # Database models
│   │
│   ├── api/                        # REST API endpoints
│   │   ├── auth.py                 # Login/Register/Logout
│   │   ├── projects.py             # Project management + ZIP upload
│   │   ├── scans.py                # Start scans, download fixed ZIP
│   │   ├── findings.py             # View/filter findings
│   │   ├── fixes.py                # Generate/apply/rollback fixes
│   │   ├── reports.py              # PDF/CSV generation
│   │   └── ...
│   │
│   ├── services/
│   │   ├── scanner/                # Pattern-based code security scanning
│   │   ├── docscan/                # 🆕 DeepSec document/malware engine
│   │   │   ├── adapter.py          #   scan_document() → AppSec Finding contract
│   │   │   ├── scanners/           #   pdf/docx/xlsx/pptx/zip/image scanners
│   │   │   ├── extractors/         #   payload/shellcode/embedded-file extraction
│   │   │   ├── intelligence/       #   MITRE, threat family, attack chain, CVE
│   │   │   └── sanitizers/         #   produce cleaned copies of documents
│   │   ├── fixer/
│   │   │   ├── ai_fixer.py         # Claude API-based fixing (code only)
│   │   │   ├── auto_fixer.py       # Pattern-based quick fixes
│   │   │   ├── zip_exporter.py     # ZIP creation for download
│   │   │   └── ...
│   │   ├── reporter/               # PDF/CSV generation (both engines)
│   │   └── ...
│   │
│   ├── rules/                      # Detection rule definitions (JSON)
│   │   ├── secrets/
│   │   ├── injection/
│   │   ├── dangerous_funcs/
│   │   └── dependencies/
│   │
│   └── utils/                      # Helpers (file I/O, validators, etc.)
│
├── frontend/                       # HTML/CSS/JS Web UI
│   ├── *.html                      # 10 pages (login, dashboard, etc.)
│   ├── css/style.css               # Dark theme with security colors
│   └── js/                         # Page logic + API communication
│
└── instance/                       # Runtime (SQLite DB, logs)
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Required for AI fixer
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxx

# Optional
FLASK_DEBUG=1                       # Enable debug mode (dev only)
ENABLE_AI_FIXER=1                   # Set to 0 to disable AI
DATABASE_URL=sqlite:///...          # Custom database
```

### API Reference

#### Code Scan Endpoints
- `POST /api/projects/<id>/scans` - Start new code scan (`scan_type="code"`)
- `GET /api/projects/<id>/scans` - List project scans
- `GET /api/scans/<id>` - Get scan details + findings (shared by both engines)
- `GET /api/scans/<id>/download-fixed` - Download fixed ZIP

#### Document Scan Endpoints
- `POST /api/docscans` - 🆕 Upload + scan a document (multipart `file`); creates a `scan_type="document"`
  scan under the per-user "Documents" project, with `json` + `sanitized` reports. Returns the scan;
  results render at `/scan-detail?id=<scan_id>`.

#### Fix Endpoints
- `POST /api/findings/<id>/fix-preview` - 🆕 Generate AI fix
- `POST /api/fixes/<id>/apply` - Apply fix to file
- `POST /api/fixes/<id>/rollback` - Restore from backup
- `POST /api/scans/<id>/fix-all` - Fix all findings at once

#### Report Endpoints
- `POST /api/reports/scans/<id>/<format>` - Generate PDF/CSV
- `GET /api/reports/<id>/download` - Download report file

## 🎓 How It Works

### Scanning Process
1. User uploads ZIP → Extracted to `scans/` folder
2. Scanner recursively finds all source files
3. Pattern engine checks each file against rules
4. Finds reported with line numbers, code snippets, severity
5. Results stored in SQLite database

### Fixing Process
1. **User clicks "Generate Fix"**:
   - System checks if it's a known pattern (SEC001, FUNC001, etc.)
   - If yes → Quick pattern-based fix
   - If no → Send to Claude AI API for intelligent fix
   
2. **Claude receives context**:
   - Vulnerability type, file, line, code snippet
   - Full file content for context
   - Programming language for syntax awareness

3. **Claude generates fix**:
   - Understands the security issue
   - Proposes context-aware fix
   - Returns complete fixed file

4. **System validates**:
   - Checks fix is different from original
   - Parses code for syntax errors
   - Shows diff to user

5. **User reviews & applies**:
   - Side-by-side diff shows changes
   - Can edit fix in AI editor
   - Click "Apply" to write to disk
   - Backup created automatically

6. **Rollback ready**:
   - Original file backed up in `scans/<project_id>/backup/`
   - User can rollback anytime

### Download Process
1. Scan completed with fixes applied
2. User clicks "Download Fixed"
3. System creates ZIP of project dir
4. Automatically excludes: .venv, node_modules, .git, __pycache__, etc.
5. User gets: `projectname_fixed_scan_123.zip`

## 🚨 Security Features

- **No credentials stored**: Secrets detected and replaced with env vars
- **Backups before fixes**: Every change can be rolled back
- **User isolation**: Each user only sees their own projects
- **CSRF protection**: All forms protected
- **Rate limiting**: API calls throttled to prevent abuse
- **Audit logging**: All actions logged to database

## 🐛 Troubleshooting

### "CLAUDE_API_KEY not set" Error
1. Get key from https://console.anthropic.com/
2. Add to `.env`: `CLAUDE_API_KEY=sk-ant-xxxx`
3. Restart the app

### "Fix failed" Error
- AI fixer may have trouble with complex code
- Try: Edit code in "AI Editor" and ask AI to improve
- Fallback: Apply pattern-based fix (if available)

### ZIP Upload Fails
- Max size: 200MB
- Check .env: `MAX_UPLOAD_SIZE=209715200`
- Increase if needed

### PDF Not Generating
- Check Python version: 3.7+ required
- Ensure reportlab installed: `pip install reportlab`

## 📈 Next Steps

1. **Try it now**: `python run.py` → http://localhost:5000
2. **Upload sample project**: Any Python/JS project
3. **Run scan**: See all vulnerabilities
4. **Fix with AI**: Click any finding, review diff, apply
5. **Download**: Get the corrected project
6. **Demo to your internship**: Show the before/after!

## 📞 Support

- **API Docs**: Check comments in `/backend/api/`
- **Config**: See `backend/config.py` for all settings
- **Rules**: Edit JSON files in `backend/rules/` to customize detection

---

Built with ❤️ for secure development. Your code, automatically secured. 🔒
