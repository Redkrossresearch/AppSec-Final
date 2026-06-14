def lookup_indicator(indicator):

    indicator = indicator.lower()

    database = {

        "eval(": {
            "family": "Obfuscated Script",
            "risk": "HIGH",
            "systems": "Windows, Linux",
            "impact": "Code Execution"
        },

        "powershell": {
            "family": "Downloader",
            "risk": "CRITICAL",
            "systems": "Windows",
            "impact": "Payload Download"
        },

        "cmd.exe": {
            "family": "Command Execution",
            "risk": "HIGH",
            "systems": "Windows",
            "impact": "System Commands"
        },

        "openaction": {
            "family": "PDF Auto Execution",
            "risk": "HIGH",
            "systems": "PDF Readers",
            "impact": "Automatic Trigger"
        }
    }

    return database.get(
        indicator,
        {
            "family": "Unknown",
            "risk": "LOW",
            "systems": "Unknown",
            "impact": "Unknown"
        }
    )