from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from backend.models import AuditLog

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.get("/me")
@login_required
def profile():
    events = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.created_at.desc()).limit(20).all()
    return jsonify({"user": current_user.to_dict(), "activity": [e.to_dict() for e in events]})
