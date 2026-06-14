def analyze_code(code):

    code = code.lower()

    if "eval(" in code:

        return {
            "risk": "HIGH",
            "family": "Obfuscated Script",
            "description":
            "Uses eval() which can execute arbitrary code."
        }

    if "powershell" in code:

        return {
            "risk": "CRITICAL",
            "family": "Downloader",
            "description":
            "PowerShell commonly used to download payloads."
        }

    if "cmd.exe" in code:

        return {
            "risk": "HIGH",
            "family": "Command Execution",
            "description":
            "Attempts operating system command execution."
        }

    return {
        "risk": "LOW",
        "family": "Unknown",
        "description":
        "No known malicious indicators."
    }