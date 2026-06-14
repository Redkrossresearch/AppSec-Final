import re

def clean_code(code):

    patterns = [

        r'eval\s*\(.*?\)',

        r'OpenAction',

        r'/Launch',

        r'powershell',

        r'cmd\.exe'
    ]

    cleaned = code

    for pattern in patterns:

        cleaned = re.sub(
            pattern,
            '',
            cleaned,
            flags=re.IGNORECASE
        )

    return cleaned