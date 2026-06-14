def remediation_advice(family):

    advice = {
        "Downloader": "Remove download commands and external URLs.",
        "Obfuscated Script": "Remove eval() and decode hidden payloads.",
        "PDF Auto Execution": "Remove OpenAction and Launch actions.",
        "Command Execution": "Remove command execution functions."
    }

    return advice.get(
        family,
        "Manual review recommended."
    )