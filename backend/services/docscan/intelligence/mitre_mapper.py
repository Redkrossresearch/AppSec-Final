def mitre_lookup(family):

    mapping = {

        "Downloader":
        "T1105",

        "Command Execution":
        "T1059",

        "PDF Auto Execution":
        "T1204",

        "Obfuscated Script":
        "T1027"
    }

    return mapping.get(
        family,
        "Unknown"
    )