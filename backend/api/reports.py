from pathlib import Path
from flask import Blueprint, current_app, jsonify, send_file
from flask_login import current_user, login_required
from backend.extensions import db
from backend.models import Project, Report, Scan

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

def owned_scan(scan_id):
    return Scan.query.join(Project).filter(Scan.id == scan_id, Project.owner_id == current_user.id).first_or_404()

@reports_bp.get("")
@login_required
def list_reports():
    reports = Report.query.join(Scan).join(Project).filter(Project.owner_id == current_user.id).order_by(Report.created_at.desc()).all()
    return jsonify({"reports": [r.to_dict() for r in reports]})

@reports_bp.post("/scans/<int:scan_id>/<string:format_name>")
@login_required
def generate_report(scan_id, format_name):
    from backend.services.reporter import create_csv_report, create_pdf_report
    scan = owned_scan(scan_id)
    if format_name not in {"csv", "pdf"}:
        return jsonify({"error": "Supported formats: csv, pdf."}), 400
    destination = Path(current_app.config["REPORT_STORAGE"]) / format_name / f"scan-{scan.id}.{format_name}"
    if format_name == "csv":
        create_csv_report(scan, destination)
    else:
        create_pdf_report(scan, destination)
    report = Report(scan_id=scan.id, format=format_name, output_path=str(destination))
    db.session.add(report)
    db.session.commit()
    return jsonify({"report": report.to_dict()}), 201

@reports_bp.get("/<int:report_id>/download")
@login_required
def download_report(report_id):
    report = Report.query.join(Scan).join(Project).filter(Report.id == report_id, Project.owner_id == current_user.id).first_or_404()
    return send_file(report.output_path, as_attachment=True)
