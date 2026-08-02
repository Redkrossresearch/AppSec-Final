from backend.api.audit_logs import audit_logs_bp
from backend.api.auth import auth_bp
from backend.api.category_summary import category_summary_bp
from backend.api.dashboard import dashboard_bp
from backend.api.docscans import docscans_bp
from backend.api.false_positive_rate import false_positive_rate_bp
from backend.api.findings import findings_bp
from backend.api.findings_bulk import findings_bulk_bp
from backend.api.findings_export import findings_export_bp
from backend.api.findings_search import findings_search_bp
from backend.api.fixes import fixes_bp
from backend.api.project_risk import project_risk_bp
from backend.api.projects import projects_bp
from backend.api.reports import reports_bp
from backend.api.rule_catalog import rule_catalog_bp
from backend.api.scan_compare import scan_compare_bp
from backend.api.scans import scans_bp
from backend.api.top_files import top_files_bp
from backend.api.users import users_bp


API_BLUEPRINTS = [
    auth_bp, dashboard_bp, projects_bp, scans_bp,
    findings_bp, fixes_bp, reports_bp, users_bp, docscans_bp,
    audit_logs_bp, findings_search_bp, findings_export_bp,
    findings_bulk_bp, project_risk_bp,
    rule_catalog_bp, scan_compare_bp, top_files_bp,
    category_summary_bp, false_positive_rate_bp,
]

