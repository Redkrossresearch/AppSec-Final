def calculate_risk(
    code_count,
    action_count,
    embedded_count
):

    score = (
        code_count * 30
        + action_count * 20
        + embedded_count * 15
    )

    if score >= 100:
        return "CRITICAL"

    if score >= 60:
        return "HIGH"

    if score >= 30:
        return "MEDIUM"

    return "LOW"