from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from backend.models import Finding, Project, Scan

project_risk_bp = Blueprint("project_risk", __name__, url_prefix="/api/project-risk")

SEVERITY_WEIGHTS = {"critical": 10, "high": 5, "medium": 2, "low": 1}


def owned_project(project_id):
    return Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()


@project_risk_bp.get("/<int:project_id>")
@login_required
def project_risk_score(project_id):
    project = owned_project(project_id)
    findings = (
        Finding.query.join(Scan)
        .filter(Scan.project_id == project.id, Finding.status == "open")
        .all()
    )
    breakdown = {}
    score = 0
    for f in findings:
        sev = (f.severity or "").lower()
        breakdown[sev] = breakdown.get(sev, 0) + 1
        score += SEVERITY_WEIGHTS.get(sev, 0)
    return jsonify({
        "project_id": project.id,
        "risk_score": score,
        "open_findings": len(findings),
        "breakdown": breakdown,
    })
