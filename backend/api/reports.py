from pathlib import Path
from flask import Blueprint, current_app, jsonify, send_file
from flask_login import current_user, login_required
from backend.extensions import db
from backend.models import Project, Report, Scan

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

def owned_scan(scan_id):
    return Scan.query.join(Project).filter(Scan.id == scan_id, Project.owner_id == current_user.id).first_or_404()

def _report_destination(scan_id, format_name):
    return Path(current_app.config["REPORT_STORAGE"]) / format_name / f"scan-{scan_id}.{format_name}"

def _write_report(scan, format_name, destination):
    """Render a report to disk. Reads only scan.findings, never project source."""
    from backend.services.reporter import create_csv_report, create_pdf_report
    if format_name == "csv":
        create_csv_report(scan, destination)
    else:
        create_pdf_report(scan, destination)
    return destination

@reports_bp.get("")
@login_required
def list_reports():
    reports = Report.query.join(Scan).join(Project).filter(Project.owner_id == current_user.id).order_by(Report.created_at.desc()).all()
    return jsonify({"reports": [r.to_dict() for r in reports]})

@reports_bp.post("/scans/<int:scan_id>/<string:format_name>")
@login_required
def generate_report(scan_id, format_name):
    scan = owned_scan(scan_id)
    if format_name not in {"csv", "pdf"}:
        return jsonify({"error": "Supported formats: csv, pdf."}), 400
    destination = _write_report(scan, format_name, _report_destination(scan.id, format_name))
    report = Report(scan_id=scan.id, format=format_name, output_path=str(destination))
    db.session.add(report)
    db.session.commit()
    return jsonify({"report": report.to_dict()}), 201

@reports_bp.get("/<int:report_id>/download")
@login_required
def download_report(report_id):
    report = Report.query.join(Scan).join(Project).filter(Report.id == report_id, Project.owner_id == current_user.id).first_or_404()
    # Report files live on the ephemeral disk, but their content comes entirely from
    # scan.findings — so a file lost to a host restart is rebuilt on demand rather than
    # 404ing. The stored path may also be stale (written by a previous container), so
    # regenerate to a freshly resolved destination and record it.
    if not Path(report.output_path).is_file():
        destination = _write_report(report.scan, report.format, _report_destination(report.scan_id, report.format))
        report.output_path = str(destination)
        db.session.commit()
    return send_file(report.output_path, as_attachment=True)
