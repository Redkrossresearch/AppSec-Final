import os
import re

def sanitize_pdf(
    source,
    output_folder="sanitized/pdf"
):

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    with open(
        source,
        "rb"
    ) as f:

        content = f.read().decode(
            errors="ignore"
        )

    dangerous_patterns = [

        r'/JavaScript',
        r'/JS',
        r'OpenAction',
        r'/Launch',
        r'eval\s*\(.*?\)'

    ]

    cleaned = content

    for pattern in dangerous_patterns:

        cleaned = re.sub(
            pattern,
            '',
            cleaned,
            flags=re.IGNORECASE
        )

    filename = os.path.basename(
        source
    )

    output_file = os.path.join(
        output_folder,
        filename
    )

    with open(
        output_file,
        "wb"
    ) as f:

        f.write(cleaned.encode("latin-1", errors="replace"))

    return output_file