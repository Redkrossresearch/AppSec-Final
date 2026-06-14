import os

def file_size(file_path):

    return round(
        os.path.getsize(
            file_path
        ) / 1024,
        2
    )

def extension(filename):

    return os.path.splitext(
        filename
    )[1].lower()