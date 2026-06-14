import re

def extract_hidden_code(content):

    code = []

    patterns = [

        r'eval\s*\(.*?\)',

        r'app\.alert\s*\(.*?\)',

        r'/JavaScript',

        r'/JS',

        r'OpenAction',

        r'/Launch'

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            content,
            re.IGNORECASE
        )

        for match in matches:

            code.append(match)

    return code