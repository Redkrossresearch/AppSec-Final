def explain_code(code):

    text = str(code).lower()

    if "eval(" in text:

        return """
Risk: HIGH

Reason:
eval() executes dynamically generated code.

Impact:
Remote Code Execution.

Recommendation:
Remove eval() usage.
"""

    if "powershell" in text:

        return """
Risk: CRITICAL

Reason:
PowerShell can download and execute payloads.

Impact:
Malware Infection.

Recommendation:
Block PowerShell execution.
"""

    if "openaction" in text:

        return """
Risk: HIGH

Reason:
Automatically executes when PDF opens.

Impact:
User interaction not required.

Recommendation:
Remove OpenAction object.
"""

    return """
Risk: LOW

No major malicious indicators found.
"""