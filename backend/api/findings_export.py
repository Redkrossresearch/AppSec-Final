import csv
import io

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user, login_required

from backend.extensions import db
from backend.models import Finding, Project, Scan

findings_export_bp = Blueprint("findings_export", __name__, url_prefix="/api/findings-export")


@findings_export_bp.get("")
@login_required
def export_findings():
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

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Severity", "Category", "File", "Line", "CVSS", "Status"])
    for f in findings:
        writer.writerow([f.id, f.title, f.severity, f.category, f.file_path, f.line_number, f.cvss_score, f.status])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=findings_export.csv"},
    )
