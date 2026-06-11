from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func
from backend.extensions import db
from backend.models import Finding, Project, Scan

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

@dashboard_bp.get("")
@login_required
def dashboard():
    projects = Project.query.filter_by(owner_id=current_user.id)
    scans = Scan.query.join(Project).filter(Project.owner_id == current_user.id)
    findings = Finding.query.join(Scan).join(Project).filter(Project.owner_id == current_user.id)
    severity_rows = (
        db.session.query(Finding.severity, func.count(Finding.id))
        .join(Scan).join(Project)
        .filter(Project.owner_id == current_user.id)
        .group_by(Finding.severity).all()
    )
    latest = scans.order_by(Scan.started_at.desc()).limit(5).all()
    return jsonify({
        "project_count": projects.count(),
        "scan_count": scans.count(),
        "open_findings": findings.filter(Finding.status == "open").count(),
        "fixed_findings": findings.filter(Finding.status == "fixed").count(),
        "severity": {key: count for key, count in severity_rows},
        "recent_scans": [s.to_dict() for s in latest],
    })
