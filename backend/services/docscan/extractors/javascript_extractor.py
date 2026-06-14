import re

def extract_javascript(file_path):

    findings = []

    try:

        with open(
            file_path,
            "rb"
        ) as f:

            content = f.read().decode(
                errors="ignore"
            )

        patterns = [
            r"/JavaScript",
            r"/JS",
            r"eval\s*\(",
            r"app\.alert",
            r"OpenAction",
            r"/Launch"
        ]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                content,
                re.IGNORECASE
            )

            for match in matches:

                findings.append({
                    "type": "JavaScript Indicator",
                    "value": match
                })

    except Exception as e:

        findings.append({
            "type": "Error",
            "value": str(e)
        })

    return findings