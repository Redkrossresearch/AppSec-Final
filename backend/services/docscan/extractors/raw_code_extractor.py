import re

def extract_raw_code(content):

    patterns = [

        r'eval\s*\(.*?\)',

        r'powershell.*',

        r'cmd\.exe.*',

        r'OpenAction',

        r'/Launch',

        r'/JavaScript'

    ]

    code = []

    for pattern in patterns:

        matches = re.findall(

            pattern,

            content,

            re.IGNORECASE

        )

        code.extend(matches)

    return code