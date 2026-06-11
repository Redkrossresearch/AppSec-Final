from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from backend.extensions import db
from backend.models import Finding, Project, Scan

findings_bp = Blueprint("findings", __name__, url_prefix="/api/findings")


def owned_finding(finding_id):
    return (
        Finding.query.join(Scan).join(Project)
        .filter(Finding.id == finding_id, Project.owner_id == current_user.id)
        .first_or_404()
    )


@findings_bp.get("")
@login_required
def list_findings():
    query = Finding.query.join(Scan).join(Project).filter(Project.owner_id == current_user.id)
    if request.args.get("scan_id"):
        query = query.filter(Finding.scan_id == int(request.args["scan_id"]))
    if request.args.get("severity"):
        query = query.filter(Finding.severity == request.args["severity"])
    if request.args.get("status"):
        query = query.filter(Finding.status == request.args["status"])
    findings = query.order_by(Finding.cvss_score.desc(), Finding.id.desc()).all()
    return jsonify({"findings": [f.to_dict() for f in findings]})


@findings_bp.get("/<int:finding_id>")
@login_required
def get_finding(finding_id):
    return jsonify({"finding": owned_finding(finding_id).to_dict()})


@findings_bp.patch("/<int:finding_id>")
@login_required
def update_finding(finding_id):
    finding = owned_finding(finding_id)
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"open", "accepted", "false_positive"}:
        return jsonify({"error": "Unsupported finding status."}), 400
    finding.status = status
    db.session.commit()
    return jsonify({"finding": finding.to_dict()})
