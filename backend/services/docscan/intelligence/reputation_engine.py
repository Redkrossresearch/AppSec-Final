def reputation(family):

    bad = [

        "Downloader",

        "Command Execution",

        "PDF Auto Execution"

    ]

    if family in bad:

        return "Malicious"

    return "Unknown"