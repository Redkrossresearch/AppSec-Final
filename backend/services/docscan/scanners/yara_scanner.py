def yara_scan(content):

    findings = []

    rules = {

        "PowerShell Downloader":
        "powershell",

        "Command Execution":
        "cmd.exe",

        "Encoded Payload":
        "base64",

        "Obfuscation":
        "eval("
    }

    for rule, signature in rules.items():

        if signature.lower() in content.lower():

            findings.append({

                "rule": rule,

                "matched":
                signature

            })

    return findings