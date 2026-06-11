import shutil
from pathlib import Path

from backend.utils.validators import project_file


def create_backup(project_root, relative_path, storage_root, project_id, fix_id):
    source = project_file(project_root, relative_path)
    target = Path(storage_root) / str(project_id) / "backup" / str(fix_id) / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target
