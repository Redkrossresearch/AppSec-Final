import hashlib

def calculate_sha256(file_path):

    sha = hashlib.sha256()

    with open(file_path, "rb") as f:

        while True:

            data = f.read(4096)

            if not data:
                break

            sha.update(data)

    return sha.hexdigest()