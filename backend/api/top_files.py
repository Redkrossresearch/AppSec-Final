from collections import Counter

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from backend.models import Finding, Project, Scan

top_files_bp = Blueprint("top_files", __name__, url_prefix="/api/top-files")


@top_files_bp.get("/<int:project_id>")
@login_required
def top_vulnerable_files(project_id):
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()
    limit = int(request.args.get("limit", 10))

    findings = (
        Finding.query.join(Scan)
        .filter(Scan.project_id == project.id, Finding.status == "open")
        .all()
    )

    counts = Counter(f.file_path for f in findings)
    ranked = [{"file_path": path, "finding_count": count} for path, count in counts.most_common(limit)]

    return jsonify({"project_id": project.id, "top_files": ranked})