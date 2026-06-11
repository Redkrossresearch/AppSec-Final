import shutil
from pathlib import Path

from backend.utils.validators import project_file


def restore_backup(project_root, relative_path, backup_path):
    backup = Path(backup_path)
    if not backup.exists():
        raise ValueError("Backup file is unavailable.")
    target = project_file(project_root, relative_path)
    shutil.copy2(backup, target)
    return target
