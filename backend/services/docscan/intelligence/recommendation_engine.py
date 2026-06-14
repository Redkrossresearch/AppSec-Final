def generate_recommendations(
    family,
    risk
):

    recommendations = []

    if risk == "CRITICAL":

        recommendations.append(
            "Do not open this file."
        )

        recommendations.append(
            "Isolate the document."
        )

    if family == "Downloader":

        recommendations.append(
            "Block external connections."
        )

    if family == "PDF Auto Execution":

        recommendations.append(
            "Remove OpenAction entries."
        )

    if family == "Obfuscated Script":

        recommendations.append(
            "Review encoded payloads."
        )

    return recommendations