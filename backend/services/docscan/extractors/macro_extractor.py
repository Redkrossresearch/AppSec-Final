import re

def extract_macros(content):

    findings = []

    patterns = [

        r'AutoOpen',
        r'Document_Open',
        r'Workbook_Open',
        r'Shell\s*\(',
        r'CreateObject',
        r'WScript\.Shell',
        r'PowerShell'

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            content,
            re.IGNORECASE
        )

        for match in matches:

            findings.append(match)

    return findings