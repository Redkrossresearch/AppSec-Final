import re

def extract_shellcode(content):

    findings = []

    matches = re.findall(

        r'(\\x[0-9a-fA-F]{2}){10,}',

        content

    )

    findings.extend(matches)

    return findings