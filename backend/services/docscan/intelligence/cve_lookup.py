def lookup_cve(indicator):

    database = {

        "openaction":
        "CVE-like PDF execution behavior",

        "eval":
        "Dynamic code execution behavior",

        "powershell":
        "Common malware delivery technique"
    }

    return database.get(
        indicator.lower(),
        "No CVE information available"
    )