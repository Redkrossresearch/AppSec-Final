from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, send_file
from flask_login import current_user, login_required

from backend.extensions import db
from backend.models import AuditLog, Finding, Project, Scan
from backend.services.scanner import scan_project
from backend.services.fixer.zip_exporter import create_fixed_project_zip, get_project_name_for_zip

scans_bp = Blueprint("scans", __name__, url_prefix="/api")


def owned_project(project_id):
    return Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()


def owned_scan(scan_id):
    return (
        Scan.query.join(Project)
        .filter(Scan.id == scan_id, Project.owner_id == current_user.id)
        .first_or_404()
    )


@scans_bp.post("/projects/<int:project_id>/scans")
@login_required
def start_scan(project_id):
    project = owned_project(project_id)
    scan = Scan(project_id=project.id, status="running")
    db.session.add(scan)
    db.session.commit()
    try:
        result = scan_project(
            project.path,
            current_app.config["RULES_DIR"],
            current_app.config["ALLOWED_EXTENSIONS"],
            current_app.config["SCAN_IGNORED_DIRS"],
            current_app.config["MAX_SCAN_FILE_SIZE"],
        )
        for item in result["findings"]:
            db.session.add(Finding(scan_id=scan.id, **item))
        scan.status = "completed"
        scan.total_files = result["files_scanned"]
        scan.set_summary(result["summary"])
    except Exception as error:
        current_app.logger.exception("Scan failed")
        scan.status = "failed"
        scan.error = str(error)
    scan.completed_at = datetime.now(timezone.utc)
    db.session.add(AuditLog(user_id=current_user.id, action="scan", entity_type="project", entity_id=project.id))
    db.session.commit()
    return jsonify({"scan": scan.to_dict()}), 201


@scans_bp.get("/projects/<int:project_id>/scans")
@login_required
def list_scans(project_id):
    project = owned_project(project_id)
    scans = Scan.query.filter_by(project_id=project.id).order_by(Scan.started_at.desc()).all()
    return jsonify({"scans": [s.to_dict() for s in scans]})


@scans_bp.get("/scans/<int:scan_id>")
@login_required
def get_scan(scan_id):
    scan = owned_scan(scan_id)
    return jsonify({"scan": scan.to_dict(), "findings": [f.to_dict() for f in scan.findings]})


@scans_bp.get("/scans/<int:scan_id>/download-fixed")
@login_required
def download_fixed_project(scan_id):
    """Download the fixed project as a ZIP file."""
    scan = owned_scan(scan_id)
    project = scan.project
    
    # Count fixed findings
    fixed_count = sum(1 for f in scan.findings if f.status == "fixed")
    if fixed_count == 0:
        return jsonify({"error": "No fixes have been applied to this scan yet."}), 400
    
    try:
        # Create ZIP file
        zip_filename = f"{get_project_name_for_zip(project.name)}_fixed_scan_{scan.id}.zip"
        zip_path = current_app.config["REPORT_STORAGE"] / "downloads" / zip_filename
        
        zip_file = create_fixed_project_zip(project.path, str(zip_path))
        
        # Log the download
        db.session.add(AuditLog(
            user_id=current_user.id,
            action="download_fixed_project",
            entity_type="scan",
            entity_id=scan.id,
            details=f"Downloaded fixed project ZIP with {fixed_count} applied fixes"
        ))
        db.session.commit()
        
        return send_file(
            zip_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        current_app.logger.error(f"Failed to create fixed project ZIP: {str(e)}")
        return jsonify({"error": "Failed to create download file"}), 500
