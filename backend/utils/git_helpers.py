import subprocess
from pathlib import Path


def is_git_repository(path):
    return (Path(path) / ".git").exists()


def changed_files(path):
    if not is_git_repository(path):
        return []
    result = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    return [line[3:] for line in result.stdout.splitlines() if len(line) > 3]
