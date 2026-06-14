def detect_javascript(content):

    findings = []

    keywords = [
        "/JavaScript",
        "/JS",
        "eval(",
        "app.alert",
        "OpenAction",
        "/Launch"
    ]

    for keyword in keywords:

        if keyword.lower() in content.lower():

            findings.append(keyword)

    return findings