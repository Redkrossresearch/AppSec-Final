from collections import Counter

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from backend.models import Finding, Project, Scan

category_summary_bp = Blueprint("category_summary", __name__, url_prefix="/api/category-summary")


@category_summary_bp.get("/<int:project_id>")
@login_required
def category_summary(project_id):
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()

    findings = (
        Finding.query.join(Scan)
        .filter(Scan.project_id == project.id, Finding.status == "open")
        .all()
    )

    by_category = Counter(f.category for f in findings)
    by_severity = Counter(f.severity for f in findings)

    return jsonify({
        "project_id": project.id,
        "total_open_findings": len(findings),
        "by_category": dict(by_category),
        "by_severity": dict(by_severity),
    })
