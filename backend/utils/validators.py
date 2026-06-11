from pathlib import Path


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
