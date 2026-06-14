def calculate_risk(findings):

    score = 0

    for finding in findings:

        value = str(finding["value"]).lower()

        if "javascript" in value:
            score += 40

        if "openaction" in value:
            score += 30

        if "launch" in value:
            score += 30

    if score >= 60:
        return "HIGH"

    if score >= 30:
        return "MEDIUM"

    return "LOW"