import secrets
import zipfile
from pathlib import Path

from flask import Blueprint, Flask, jsonify, request, send_from_directory, session
from flask_login import current_user

from backend.api import API_BLUEPRINTS
from backend.config import Config
from backend.extensions import db, init_extensions
from backend.middlewares import SimpleRateLimiter, register_error_handlers


PAGES = {
    "": "index.html",
    "login": "login.html",
    "register": "register.html",
    "dashboard": "dashboard.html",
    "projects": "projects.html",
    "project-detail": "project_detail.html",
    "findings": "findings.html",
    "fix-preview": "fix_preview.html",
    "reports": "reports.html",
    "scan-detail": "scan_detail.html",
    "settings": "settings.html",
}


def _register_frontend(app):
    pages = Blueprint("pages", __name__)

    @pages.get("/")
    def home():
        return send_from_directory(app.config["FRONTEND_DIR"], PAGES[""])

    @pages.get("/<string:page>")
    def page(page):
        if page not in PAGES:
            return jsonify({"error": "Not found"}), 404
        return send_from_directory(app.config["FRONTEND_DIR"], PAGES[page])

    @pages.get("/css/<path:filename>")
    def css(filename):
        return send_from_directory(Path(app.config["FRONTEND_DIR"]) / "css", filename)

    @pages.get("/js/<path:filename>")
    def javascript(filename):
        return send_from_directory(Path(app.config["FRONTEND_DIR"]) / "js", filename)

    @pages.get("/assets/<path:filename>")
    def assets(filename):
        return send_from_directory(Path(app.config["FRONTEND_DIR"]) / "assets", filename)

    app.register_blueprint(pages)


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_override:
        app.config.update(config_override)

    Path(app.config["SCAN_STORAGE"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["REPORT_STORAGE"]).mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_STORAGE"]).mkdir(parents=True, exist_ok=True)

    if app.config["ENABLE_AI_FIXER"]:
        if not app.config["CLAUDE_API_KEY"]:
            app.logger.warning(
                "AI fixer is enabled but CLAUDE_API_KEY or ANTHROPIC_API_KEY is not set. "
                "Set the environment variable before restarting the app."
            )
        try:
            import anthropic  # noqa: F401
        except ImportError:
            app.logger.warning(
                "AI fixer is enabled but the anthropic Python SDK is not installed. "
                "Run `pip install anthropic` to enable AI fix previews."
            )

    init_extensions(app)
    register_error_handlers(app)
    limiter = SimpleRateLimiter()

    @app.before_request
    def api_guards():
        limited = limiter.check()
        if limited:
            return limited
        if (
            request.path.startswith("/api/")
            and request.method in {"POST", "PATCH", "DELETE"}
            and request.path not in {"/api/auth/register", "/api/auth/login", "/api/auth/logout"}
            and current_user.is_authenticated
        ):
            sent = request.headers.get("X-CSRF-Token", "")
            expected = session.get("csrf_token", "")
            if not sent or not secrets.compare_digest(sent, expected):
                return jsonify({"error": "Invalid CSRF token."}), 403
        return None

    for blueprint in API_BLUEPRINTS:
        app.register_blueprint(blueprint)
    _register_frontend(app)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    with app.app_context():
        from backend import models  # noqa: F401
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
