import json
import re
from pathlib import Path


def _version_tuple(value):
    numbers = re.findall(r"\d+", value)
    return tuple(int(number) for number in numbers[:3])


def _read_baselines(rules_dir):
    path = Path(rules_dir) / "dependencies" / "vulnerable_packages.json"
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)["packages"]


def scan_dependencies(project_root, rules_dir):
    baselines = _read_baselines(rules_dir)
    findings = []
    requirements = Path(project_root) / "requirements.txt"
    if not requirements.exists():
        return findings
    for number, line in enumerate(requirements.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        match = re.match(r"^\s*([A-Za-z0-9_-]+)\s*==\s*([0-9][^;\s]*)", line)
        if not match:
            continue
        name, installed = match.groups()
        baseline = baselines.get(name.lower())
        if baseline and _version_tuple(installed) < _version_tuple(baseline["below"]):
            findings.append(
                {
                    "rule_id": f"DEP-{name.lower()}",
                    "category": "dependencies",
                    "severity": baseline["severity"],
                    "title": baseline["title"],
                    "description": f"{name}=={installed} is below {baseline['below']}.",
                    "file_path": "requirements.txt",
                    "line_number": number,
                    "line_text": line.strip(),
                    "recommendation": f"Upgrade and test {name}>={baseline['below']}.",
                    "cvss_score": None,
                    "fixable": False,
                }
            )
    return findings
