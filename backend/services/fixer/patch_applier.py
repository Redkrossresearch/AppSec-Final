from backend.utils.file_helpers import atomic_write_text, read_text_safely
from backend.utils.validators import project_file


def apply_generated_patch(project_root, relative_path, expected_content, fixed_content):
    target = project_file(project_root, relative_path)
    current = read_text_safely(target)
    if current != expected_content:
        raise ValueError("The source file changed after preview; generate a new fix preview.")
    atomic_write_text(target, fixed_content)
    return target
