def analyze_behavior(content):

    behavior = []

    if "powershell" in content.lower():

        behavior.append(
            "Command Execution"
        )

    if "http://" in content.lower():

        behavior.append(
            "Network Communication"
        )

    if "eval(" in content.lower():

        behavior.append(
            "Code Obfuscation"
        )

    return behavior