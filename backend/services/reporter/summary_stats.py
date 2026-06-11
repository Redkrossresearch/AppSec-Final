from collections import Counter


def scan_stats(scan):
    counts = Counter(finding.severity for finding in scan.findings)
    resolved = sum(1 for finding in scan.findings if finding.status in {"fixed", "accepted"})
    return {
        "total": len(scan.findings),
        "critical": counts["critical"],
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
        "resolved": resolved,
    }
