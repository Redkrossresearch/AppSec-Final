import re

def extract_hidden_code(content):

    code = []

    patterns = [

        r'eval\s*\(.*?\)',

        r'base64',

        r'cmd\.exe',

        r'powershell',

        r'wscript',

        r'cscript'

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            content,
            re.IGNORECASE
        )

        code.extend(matches)

    return code