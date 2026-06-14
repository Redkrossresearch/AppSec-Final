import re

def extract_payloads(content):

    payloads = []

    patterns = [

        r'base64,[A-Za-z0-9+/=]+',

        r'powershell\s+.*',

        r'cmd\.exe\s+.*'

    ]

    for pattern in patterns:

        matches = re.findall(

            pattern,

            content,

            re.IGNORECASE

        )

        payloads.extend(matches)

    return payloads