def detect_family(indicators):

    text = str(indicators).lower()

    if "powershell" in text:
        return "Downloader"

    if "eval(" in text:
        return "Obfuscated Script"

    if "cmd.exe" in text:
        return "Command Execution"

    if "openaction" in text:
        return "PDF Auto Execution"

    return "Unknown"