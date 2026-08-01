from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from backend.models import AuditLog

audit_logs_bp = Blueprint("audit_logs", __name__, url_prefix="/api/audit-logs")


@audit_logs_bp.get("")
@login_required
def list_audit_logs():
    query = AuditLog.query.filter_by(user_id=current_user.id)
    if request.args.get("entity_type"):
        query = query.filter(AuditLog.entity_type == request.args["entity_type"])
    logs = query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return jsonify({"audit_logs": [log.to_dict() for log in logs]})
