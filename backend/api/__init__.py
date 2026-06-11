from backend.api.auth import auth_bp
from backend.api.dashboard import dashboard_bp
from backend.api.findings import findings_bp
from backend.api.fixes import fixes_bp
from backend.api.projects import projects_bp
from backend.api.reports import reports_bp
from backend.api.scans import scans_bp
from backend.api.users import users_bp

API_BLUEPRINTS = [
    auth_bp, dashboard_bp, projects_bp, scans_bp,
    findings_bp, fixes_bp, reports_bp, users_bp
]
