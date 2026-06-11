import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # project root (appsec_final/)


class Config:
    SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-change-in-production-xyz")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{(BASE_DIR / 'instance' / 'appsec.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
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
