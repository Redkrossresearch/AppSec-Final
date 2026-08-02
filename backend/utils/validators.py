from pathlib import Path

# Shown whenever an operation needs the uploaded source that is no longer on disk.
# Free-tier hosts reset the filesystem on restart while the database survives, so a
# project row can outlive its files — see DEPLOY.md.
PROJECT_FILES_MISSING = (
    "Project files are no longer available on this server. Free-tier hosting resets "
    "uploaded files when the app restarts, so re-upload the project ZIP to scan or fix it again. "
    "Past scans, findings, and reports are unaffected."
)


def project_files_available(project_path):
    """True when a project's uploaded source is still present on disk."""
    return Path(project_path).is_dir()


def require_fields(data, *fields):
    missing = [field for field in fields if not str(data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def validate_password(password):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")


def validate_project_directory(path):
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError("Project path must be an existing directory.")
    return resolved


def project_file(project_root, relative_path):
    root = Path(project_root).resolve()
    target = (root / relative_path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("File path is outside the registered project.") from exc
    return target
