import re

def detect_shellcode(content):

    matches = re.findall(

        r'(\\x[0-9a-fA-F]{2}){10,}',

        content

    )

    return matches