import secrets

from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_user, logout_user

from backend.extensions import db
from backend.models import AuditLog, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(24)
    return session["csrf_token"]


@auth_bp.get("/csrf")
def csrf():
    return jsonify({"csrf_token": _csrf_token()})


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists."}), 409
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({"user": user.to_dict(), "csrf_token": _csrf_token()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401
    login_user(user)
    db.session.add(AuditLog(user_id=user.id, action="login", entity_type="user", entity_id=user.id))
    db.session.commit()
    return jsonify({"user": user.to_dict(), "csrf_token": _csrf_token()})


@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    session.clear()
    return jsonify({"message": "Logged out."})


@auth_bp.get("/me")
def me():
    return jsonify({
        "user": current_user.to_dict() if current_user.is_authenticated else None,
        "csrf_token": _csrf_token(),
    })
