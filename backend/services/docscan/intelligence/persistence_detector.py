def detect_persistence(content):

    indicators = [

        "RunRegistry",

        "Startup",

        "ScheduledTask",

        "HKCU\\Software"

    ]

    found = []

    for item in indicators:

        if item.lower() in content.lower():

            found.append(item)

    return found