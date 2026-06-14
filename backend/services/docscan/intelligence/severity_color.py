def severity_color(risk):

    mapping = {

        "LOW":
        "green",

        "MEDIUM":
        "orange",

        "HIGH":
        "red",

        "CRITICAL":
        "darkred"
    }

    return mapping.get(
        risk,
        "gray"
    )