def affected_systems(family):

    mapping = {

        "Downloader":
        "Windows",

        "PDF Auto Execution":
        "Adobe Reader, Foxit Reader",

        "Obfuscated Script":
        "Windows, Linux",

        "Command Execution":
        "Windows"

    }

    return mapping.get(
        family,
        "Unknown"
    )