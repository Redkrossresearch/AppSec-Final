from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from backend.models import Finding, Project, Scan

false_positive_rate_bp = Blueprint("false_positive_rate", __name__, url_prefix="/api/false-positive-rate")


@false_positive_rate_bp.get("/<int:project_id>")
@login_required
def false_positive_rate(project_id):
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()

    findings = Finding.query.join(Scan).filter(Scan.project_id == project.id).all()
    total = len(findings)
    false_positives = sum(1 for f in findings if f.status == "false_positive")
    rate = round((false_positives / total) * 100, 1) if total else 0.0

    return jsonify({
        "project_id": project.id,
        "total_findings": total,
        "false_positives": false_positives,
        "false_positive_rate_percent": rate,
    })
