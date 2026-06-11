import io
import zipfile
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from backend.extensions import db
from backend.models import AuditLog, Project

projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


def owned_project(project_id):
    return Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()


@projects_bp.get("")
@login_required
def list_projects():
    projects = Project.query.filter_by(owner_id=current_user.id).order_by(Project.created_at.desc()).all()
    return jsonify({"projects": [p.to_dict() for p in projects]})


@projects_bp.post("")
@login_required
def create_project():
    """Create project from JSON (path) or multipart (zip upload)."""
    # Handle ZIP file upload
    if "zip" in request.files:
        zip_file = request.files["zip"]
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        if not name:
            return jsonify({"error": "Project name is required."}), 400
        if not zip_file.filename.endswith(".zip"):
            return jsonify({"error": "Only .zip files are supported."}), 400

        # Save and extract zip
        upload_root = Path(current_app.config["UPLOAD_STORAGE"]) / str(current_user.id)
        upload_root.mkdir(parents=True, exist_ok=True)

        project_dir = upload_root / name.replace(" ", "_").replace("/", "_")
        project_dir.mkdir(parents=True, exist_ok=True)

        # Check upload size via the stream rather than reading all bytes into memory.
        max_upload = current_app.config.get("MAX_UPLOAD_SIZE", 50 * 1024 * 1024)
        stream = zip_file.stream
        stream.seek(0, io.SEEK_END)
        upload_size = stream.tell()
        stream.seek(0)
        if upload_size > max_upload:
            max_mb = max_upload // (1024 * 1024)
            return jsonify({"error": f"ZIP file is too large (max {max_mb}MB)."}), 413

        # Extract safely, streaming from the upload rather than buffering all bytes.
        project_root_resolved = project_dir.resolve()
        with zipfile.ZipFile(stream) as zf:
            # Security: prevent path traversal
            for member in zf.namelist():
                member_path = (project_dir / member).resolve()
                if member_path != project_root_resolved and project_root_resolved not in member_path.parents:
                    return jsonify({"error": "Invalid ZIP: path traversal detected."}), 400
            zf.extractall(project_dir)

        # If zip has a single root folder, use that as project root
        extracted = list(project_dir.iterdir())
        if len(extracted) == 1 and extracted[0].is_dir():
            project_path = extracted[0]
        else:
            project_path = project_dir

        project = Project(
            name=name,
            path=str(project_path),
            description=description,
            owner_id=current_user.id,
        )
        db.session.add(project)
        db.session.flush()
        db.session.add(AuditLog(user_id=current_user.id, action="create", entity_type="project", entity_id=project.id))
        db.session.commit()
        return jsonify({"project": project.to_dict()}), 201

    # Handle JSON (path)
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    path_str = str(data.get("path", "")).strip()
    if not name or not path_str:
        return jsonify({"error": "Name and path are required."}), 400
    path = Path(path_str).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        return jsonify({"error": "Path must be an existing directory."}), 400

    project = Project(
        name=name,
        path=str(path),
        description=str(data.get("description", "")).strip(),
        owner_id=current_user.id,
    )
    db.session.add(project)
    db.session.flush()
    db.session.add(AuditLog(user_id=current_user.id, action="create", entity_type="project", entity_id=project.id))
    db.session.commit()
    return jsonify({"project": project.to_dict()}), 201


@projects_bp.get("/<int:project_id>")
@login_required
def get_project(project_id):
    return jsonify({"project": owned_project(project_id).to_dict()})


@projects_bp.delete("/<int:project_id>")
@login_required
def delete_project(project_id):
    project = owned_project(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted."})
