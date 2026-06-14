def confidence_score(findings):

    count = len(findings)

    if count >= 20:
        return "95%"

    if count >= 10:
        return "85%"

    return "70%"