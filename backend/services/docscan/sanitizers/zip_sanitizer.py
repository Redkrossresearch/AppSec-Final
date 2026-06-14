import shutil
import os

def sanitize_zip(
    source,
    output_folder="sanitized/zip"
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