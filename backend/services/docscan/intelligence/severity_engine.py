def severity_score(risk):

    mapping = {

        "LOW": 20,

        "MEDIUM": 50,

        "HIGH": 80,

        "CRITICAL": 100
    }

    return mapping.get(
        risk,
        0
    )