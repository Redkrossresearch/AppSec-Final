import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # project root (appsec_final/)

# Load .env before the Config class body runs — its os.getenv() calls are evaluated
# at import time. Pinned to BASE_DIR so it resolves regardless of the working directory.
load_dotenv(BASE_DIR / ".env")


def _database_uri():
    """Resolve DATABASE_URL, tolerating the legacy ``postgres://`` scheme.

    Hosted Postgres providers (Neon, Supabase, Render) still hand out ``postgres://``
    URLs, which SQLAlchemy 2.x refuses to parse. With no override, fall back to an
    absolute SQLite path — a relative one breaks startup on Windows.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{(BASE_DIR / 'instance' / 'appsec.db').as_posix()}"
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


class Config:
    SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-change-in-production-xyz")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    # Free-tier Postgres (Neon, Supabase) autosuspends when idle and drops pooled
    # connections without telling the client; pool_pre_ping turns what would be a
    # "server closed the connection unexpectedly" 500 on the first request after a
    # wake-up into a transparent reconnect. Both options are no-ops on SQLite.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # Session cookie hardening. SECURE defaults off so plain-HTTP localhost still
    # works in dev; hosted deployments set SESSION_COOKIE_SECURE=1 (see DEPLOY.md).
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    # Sit behind a hosting proxy (Render, Fly, Cloud Run) that sets X-Forwarded-For.
    # Off by default: trusting those headers without a proxy in front lets any
    # client spoof its IP past the rate limiter.
    TRUST_PROXY = os.getenv("TRUST_PROXY", "0") == "1"
    MAX_SCAN_FILE_SIZE = int(os.getenv("MAX_SCAN_FILE_SIZE", str(512 * 1024)))
    MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200MB zip uploads
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # Flask request size limit
    SCAN_STORAGE = BASE_DIR / "scans"
    REPORT_STORAGE = BASE_DIR / "reports"
    UPLOAD_STORAGE = BASE_DIR / "uploads"
    FRONTEND_DIR = BASE_DIR / "frontend"
    RULES_DIR = BASE_DIR / "backend" / "rules"
    
    # Claude AI API configuration
    # Support both CLAUDE_API_KEY and the standard Anthropic env var name ANTHROPIC_API_KEY.
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
    ENABLE_AI_FIXER = os.getenv("ENABLE_AI_FIXER", "1") == "1"
    
    ALLOWED_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".php", ".java", ".rb",
        ".go", ".sql", ".html", ".env", ".yml", ".yaml", ".json",
        ".xml", ".sh", ".ps1", ".txt", ".cfg", ".ini", ".cs", ".cpp", ".c",
    }
    SCAN_IGNORED_DIRS = {
        ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
        "dist", "build", "scans", "reports", "logs", "instance", "uploads",
        ".venv", "env", ".env",
    }
