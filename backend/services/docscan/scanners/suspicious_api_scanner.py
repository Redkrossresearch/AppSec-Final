def detect_suspicious_apis(content):

    findings = []

    apis = [

        "VirtualAlloc",

        "WriteProcessMemory",

        "CreateRemoteThread",

        "WinExec",

        "ShellExecute"
    ]

    for api in apis:

        if api.lower() in content.lower():

            findings.append(api)

    return findings