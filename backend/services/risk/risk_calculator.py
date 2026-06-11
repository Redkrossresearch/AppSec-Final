from collections import Counter

from backend.services.risk.cvss_mapper import score_for_category
from backend.services.risk.severity import severity_from_score


def enrich_finding(finding):
    score = score_for_category(finding["category"], finding.get("cvss_score"))
    finding["cvss_score"] = score
    finding["severity"] = finding.get("severity") or severity_from_score(score)
    return finding


def calculate_risk(findings):
    counts = Counter(item["severity"] for item in findings)
    maximum = max((item["cvss_score"] for item in findings), default=0)
    return {
        "total": len(findings),
        "critical": counts["critical"],
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
        "max_cvss": maximum,
    }
