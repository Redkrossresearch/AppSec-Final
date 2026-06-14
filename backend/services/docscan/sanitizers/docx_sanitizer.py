import shutil
import os

def sanitize_docx(
    source,
    output_folder="sanitized/docx"
):

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    filename = os.path.basename(
        source
    )

    destination = os.path.join(
        output_folder,
        filename
    )

    shutil.copy2(
        source,
        destination
    )

    return destination