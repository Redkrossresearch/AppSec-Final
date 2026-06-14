def detect_powershell(content):

    findings = []

    indicators = [

        "powershell",

        "invoke-webrequest",

        "downloadstring",

        "iex"

    ]

    for item in indicators:

        if item.lower() in content.lower():

            findings.append(item)

    return findings