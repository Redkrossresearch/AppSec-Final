import json
import os
from datetime import datetime

REPORT_FOLDER = "reports/json_reports"

os.makedirs(REPORT_FOLDER, exist_ok=True)

def generate_report(filename, findings):

    report = {
        "file": filename,
        "scan_time": str(datetime.now()),
        "findings": findings
    }

    output_file = os.path.join(
        REPORT_FOLDER,
        f"{filename}.json"
    )

    with open(output_file, "w") as f:
        json.dump(report, f, indent=4)

    return output_file