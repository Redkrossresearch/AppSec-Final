import re

def extract_urls(content):

    urls = re.findall(
        r'https?://[^\s<>"]+',
        content
    )

    return urls