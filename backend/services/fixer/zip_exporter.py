"""Service for creating downloadable ZIP files of fixed projects."""
import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile


def create_fixed_project_zip(project_path: str, output_path: str, excluded_dirs=None) -> Path:
    """
    Create a ZIP file of the fixed project for download.
    
    Args:
        project_path: Path to the scanned/fixed project
        output_path: Where to save the ZIP file
        excluded_dirs: Set of directory names to exclude from ZIP
    
    Returns:
        Path to the created ZIP file
    """
    if excluded_dirs is None:
        excluded_dirs = {
            '.git', '.venv', 'venv', 'node_modules', '__pycache__',
            '.pytest_cache', 'dist', 'build', '.egg-info',
            'scans', 'reports', 'logs', 'instance', 'uploads',
        }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    project_dir = Path(project_path)
    
    # Create ZIP with filtered contents
    with ZipFile(output_file, 'w') as zipf:
        for item in project_dir.rglob('*'):
            # Skip excluded directories
            if any(excluded in item.parts for excluded in excluded_dirs):
                continue
            
            # Skip hidden files/dirs except .env
            if any(part.startswith('.') and part not in {'.env', '.gitignore', '.github'} 
                   for part in item.parts):
                continue
            
            # Add to ZIP
            arcname = item.relative_to(project_dir)
            if item.is_file():
                zipf.write(item, arcname)
            elif item.is_dir() and not any(child.is_file() for child in item.rglob('*')):
                # Skip empty directories
                continue
    
    return output_file


def get_project_name_for_zip(project_name: str) -> str:
    """Sanitize project name for use in ZIP filename."""
    import re
    # Replace spaces and special chars with underscores
    sanitized = re.sub(r'[^\w\-]', '_', project_name)
    return sanitized.strip('_')
