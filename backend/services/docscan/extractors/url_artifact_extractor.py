import re

def extract_urls(content):

    return re.findall(

        r'https?://[^\s<>"]+',

        content

    )