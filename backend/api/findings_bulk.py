from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from backend.extensions import db
from backend.models import Finding, Project, Scan

findings_bulk_bp = Blueprint("findings_bulk", __name__, url_prefix="/api/findings-bulk")


@findings_bulk_bp.patch("")
@login_required
def bulk_update_findings():
    payload = request.get_json(silent=True) or {}
    ids = payload.get("finding_ids", [])
    status = payload.get("status")
    if status not in {"open", "accepted", "false_positive"}:
        return jsonify({"error": "Unsupported finding status."}), 400
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "finding_ids must be a non-empty list."}), 400

    findings = (
        Finding.query.join(Scan).join(Project)
        .filter(Finding.id.in_(ids), Project.owner_id == current_user.id)
        .all()
    )
    for f in findings:
        f.status = status
    db.session.commit()
    return jsonify({"updated": len(findings)})