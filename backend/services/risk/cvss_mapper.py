DEFAULT_SCORES = {
    "secrets": 9.1,
    "injection": 8.8,
    "dangerous_functions": 7.8,
    "dependencies": 7.0,
    "configuration": 5.3,
}


def score_for_category(category, requested_score=None):
    return float(requested_score or DEFAULT_SCORES.get(category, 4.0))
