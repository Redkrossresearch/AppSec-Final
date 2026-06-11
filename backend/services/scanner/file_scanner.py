from pathlib import Path

from backend.services.risk.risk_calculator import calculate_risk, enrich_finding
from backend.services.scanner.dependency_scanner import scan_dependencies
from backend.services.scanner.pattern_matcher import find_rule_matches
from backend.services.scanner.rule_engine import RuleEngine
from backend.utils.file_helpers import read_text_safely


def _suffix(path):
    return ".env" if path.name == ".env" else path.suffix.lower()


def _iter_files(root, allowed_extensions, ignored_dirs, maximum_size):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_dirs for part in path.relative_to(root).parts[:-1]):
            continue
        if _suffix(path) not in allowed_extensions:
            continue
        try:
            if path.stat().st_size > maximum_size:
                continue
        except OSError:
            continue
        yield path


def scan_project(project_root, rules_dir, allowed_extensions, ignored_dirs, maximum_size):
    root = Path(project_root).resolve()
    engine = RuleEngine(rules_dir)
    findings = []
    file_count = 0
    for path in _iter_files(root, allowed_extensions, ignored_dirs, maximum_size):
        file_count += 1
        relative_path = path.relative_to(root).as_posix()
        content = read_text_safely(path)
        findings.extend(find_rule_matches(content, engine.matching_rules(_suffix(path)), relative_path))
    findings.extend(scan_dependencies(root, rules_dir))
    findings = [enrich_finding(finding) for finding in findings]
    return {"files_scanned": file_count, "findings": findings, "summary": calculate_risk(findings)}
