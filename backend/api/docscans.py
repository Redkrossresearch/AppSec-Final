import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from backend.extensions import db
from backend.models import AuditLog, Finding, Project, Report, Scan
from backend.services.docscan.adapter import scan_document
from backend.services.docscan.adapter import _DISPATCH as SUPPORTED_SCANNERS

docscans_bp = Blueprint("docscans", __name__, url_prefix="/api/docscans")

SUPPORTED_EXTENSIONS = set(SUPPORTED_SCANNERS)  # {.pdf, .docx, .xlsx, .pptx, .zip, .png, ...}
DOCUMENTS_PROJECT_NAME = "Documents"


def _documents_project():
    """Get-or-create the current user's pseudo-project that holds document scans.

    Document scans need a Project (Scan.project_id is non-nullable); routing them through
    a per-user "Documents" project keeps AppSec's ownership/isolation model intact.
    """
    project = Project.query.filter_by(
        owner_id=current_user.id, name=DOCUMENTS_PROJECT_NAME
    ).first()
    if project is None:
        path = Path(current_app.config["UPLOAD_STORAGE"]) / str(current_user.id) / "documents"
        path.mkdir(parents=True, exist_ok=True)
        project = Project(
            name=DOCUMENTS_PROJECT_NAME,
            path=str(path),
            description="Uploaded documents analyzed by the DeepSec engine.",
            owner_id=current_user.id,
        )
        db.session.add(project)
        db.session.flush()
    return project


@docscans_bp.post("")
@login_required
def upload_document():
    """Upload a single document, scan it via the DeepSec adapter, persist findings + reports.

    Mirrors backend/api/scans.py::start_scan: create the Scan row first (to get an id),
    run the scan synchronously in the request thread, then write findings and mark status.
    """
    if "file" not in request.files:
        return jsonify({"error": "No document uploaded (expected form field 'file')."}), 400
    upload = request.files["file"]
    filename = secure_filename(upload.filename or "")
    if not filename:
        return jsonify({"error": "Invalid file name."}), 400
    if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return jsonify({"error": f"Unsupported document type. Supported: {supported}."}), 400

    project = _documents_project()
    doc_dir = Path(project.path)
    doc_dir.mkdir(parents=True, exist_ok=True)
    saved_path = doc_dir / filename
    upload.save(str(saved_path))  # streams to disk

    scan = Scan(project_id=project.id, status="running", scan_type="document")
    db.session.add(scan)
    db.session.commit()
    try:
        scan_dir = Path(current_app.config["REPORT_STORAGE"]) / str(scan.id)
        result = scan_document(str(saved_path), sanitized_dir=str(scan_dir / "sanitized"))
        for item in result["findings"]:
            db.session.add(Finding(scan_id=scan.id, **item))
        scan.status = "completed"
        scan.total_files = result["files_scanned"]
        scan.set_summary(result["summary"])

        # Persist DeepSec's JSON report + sanitized file as Report rows (strategy step 14).
        scan_dir.mkdir(parents=True, exist_ok=True)
        json_path = scan_dir / f"scan-{scan.id}.json"
        json_path.write_text(
            json.dumps(
                {
                    "scan_id": scan.id,
                    "file": filename,
                    "summary": result["summary"],
                    "findings": result["findings"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        db.session.add(Report(scan_id=scan.id, format="json", output_path=str(json_path)))

        sanitized_file = result["summary"].get("document", {}).get("sanitized_file")
        if sanitized_file and Path(sanitized_file).exists():
            db.session.add(Report(scan_id=scan.id, format="sanitized", output_path=str(sanitized_file)))
    except Exception as error:
        current_app.logger.exception("Document scan failed")
        scan.status = "failed"
        scan.error = str(error)
    scan.completed_at = datetime.now(timezone.utc)
    db.session.add(AuditLog(user_id=current_user.id, action="scan", entity_type="document", entity_id=scan.id))
    db.session.commit()
    return jsonify({"scan": scan.to_dict()}), 201
