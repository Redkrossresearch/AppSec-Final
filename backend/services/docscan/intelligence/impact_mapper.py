def impact_lookup(family):

    impacts = {

        "Downloader":
        "Downloads malware payloads",

        "PDF Auto Execution":
        "Runs automatically on open",

        "Obfuscated Script":
        "Hides malicious behavior",

        "Command Execution":
        "Runs operating system commands"
    }

    return impacts.get(
        family,
        "Unknown"
    )