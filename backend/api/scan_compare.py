from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from backend.models import Finding, Project, Scan

scan_compare_bp = Blueprint("scan_compare", __name__, url_prefix="/api/scan-compare")


def owned_scan(scan_id):
    return (
        Scan.query.join(Project)
        .filter(Scan.id == scan_id, Project.owner_id == current_user.id)
        .first_or_404()
    )


@scan_compare_bp.get("/<int:old_scan_id>/<int:new_scan_id>")
@login_required
def compare_scans(old_scan_id, new_scan_id):
    old_scan = owned_scan(old_scan_id)
    new_scan = owned_scan(new_scan_id)

    if old_scan.project_id != new_scan.project_id:
        return jsonify({"error": "Scans must belong to the same project."}), 400

    def key(f):
        return (f.rule_id, f.file_path, f.line_number)

    old_map = {key(f): f for f in old_scan.findings}
    new_map = {key(f): f for f in new_scan.findings}

    new_keys = new_map.keys() - old_map.keys()
    resolved_keys = old_map.keys() - new_map.keys()
    unchanged_keys = old_map.keys() & new_map.keys()

    return jsonify({
        "old_scan_id": old_scan.id,
        "new_scan_id": new_scan.id,
        "new_findings": [new_map[k].to_dict() for k in new_keys],
        "resolved_findings": [old_map[k].to_dict() for k in resolved_keys],
        "unchanged_count": len(unchanged_keys),
    })
