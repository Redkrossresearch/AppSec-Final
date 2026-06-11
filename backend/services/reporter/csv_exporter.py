import csv
from pathlib import Path


def create_csv_report(scan, destination):
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["severity", "category", "title", "file", "line", "status", "recommendation"])
        for finding in scan.findings:
            writer.writerow(
                [
                    finding.severity,
                    finding.category,
                    finding.title,
                    finding.file_path,
                    finding.line_number or "",
                    finding.status,
                    finding.recommendation,
                ]
            )
    return path
