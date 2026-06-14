import re

def extract_commands(content):

    findings = []

    patterns = [

        r'cmd\.exe.*',

        r'powershell.*',

        r'bash.*',

        r'wscript.*'

    ]

    for pattern in patterns:

        findings.extend(

            re.findall(

                pattern,

                content,

                re.IGNORECASE

            )

        )

    return findings