import re

def extract_embedded_files(content):

    findings = []

    patterns = [

        r'.*\.exe',

        r'.*\.js',

        r'.*\.vbs',

        r'.*\.bat',

        r'.*\.cmd',

        r'.*\.docm'

    ]

    lines = content.splitlines()

    for line in lines:

        for pattern in patterns:

            if re.search(
                pattern,
                line,
                re.IGNORECASE
            ):

                findings.append(
                    line.strip()
                )

    return findings