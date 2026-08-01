from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from backend.extensions import db
from backend.models import Finding, Project, Scan

findings_search_bp = Blueprint("findings_search", __name__, url_prefix="/api/findings-search")


@findings_search_bp.get("")
@login_required
def search_findings():
    query = Finding.query.join(Scan).join(Project).filter(Project.owner_id == current_user.id)
    if request.args.get("scan_id"):
        try:
            scan_id = int(request.args["scan_id"])
        except ValueError:
            return jsonify({"error": "scan_id must be an integer."}), 400
        query = query.filter(Finding.scan_id == scan_id)
    if request.args.get("severity"):
        query = query.filter(Finding.severity == request.args["severity"])
    if request.args.get("status"):
        query = query.filter(Finding.status == request.args["status"])
    if request.args.get("q"):
        term = f"%{request.args['q']}%"
        query = query.filter(db.or_(Finding.title.ilike(term), Finding.description.ilike(term)))
    findings = query.order_by(Finding.cvss_score.desc(), Finding.id.desc()).all()
    return jsonify({"findings": [f.to_dict() for f in findings]})
