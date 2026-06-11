def find_rule_matches(content, rules, relative_path):
    findings = []
    for number, line in enumerate(content.splitlines(), start=1):
        for rule in rules:
            if rule["_compiled"].search(line):
                visible_line = "<redacted: possible secret>" if rule["category"] == "secrets" else line.strip()
                findings.append(
                    {
                        "rule_id": rule["id"],
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "title": rule["title"],
                        "description": rule["description"],
                        "file_path": relative_path,
                        "line_number": number,
                        "line_text": visible_line[:500],
                        "recommendation": rule["recommendation"],
                        "cvss_score": rule.get("cvss_score"),
                        "fixable": rule.get("fixable", False),
                    }
                )
    return findings
