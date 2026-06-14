import re

def extract_streams(content):

    streams = re.findall(

        r'stream(.*?)endstream',

        content,

        re.DOTALL

    )

    return streams